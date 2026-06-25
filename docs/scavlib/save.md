---
description: Custom items persist automatically; implement one interface to save per-instance data.
---

# Save data

Custom items survive a save and reload **automatically** — you don't write any save
code to make a custom item come back where the player left it, with its condition
intact. The only thing you implement is an interface, and only when an item carries
extra per-instance state you want to persist.

ScavLib stores its data in a companion file beside the vanilla save, never inside it,
so the player's main save is never put at risk.

## How automatic persistence works

The game's own save system can't handle custom items: it reloads each saved item by
loading a prefab by id, and a custom id has no such prefab. Left alone, the vanilla
save would silently drop your items — or worse, drift its internal index and corrupt
the contents of containers like gravity bags.

ScavLib sidesteps this entirely. Just before the game saves, it detaches every custom
item in the scene (including ones nested inside containers), lets the vanilla save run
cleanly on only the items it understands, reattaches them, and writes its own record
of the custom items to the companion file. On load it respawns each custom item and
puts it back. For each item it persists:

- **identity** — the custom item id and owning mod;
- **position** — world position and rotation, or the container / hand / wear slot it
  lived in;
- **state** — condition and favourited flag;
- **your per-instance blob**, described next.

You don't call any of this. Register your items as usual (see [items](items.md)) and
they persist.

## Per-instance data: `ICustomItemSaveable`

When an item instance carries state of its own — charges left, a configured mode, a
stored value — implement `ICustomItemSaveable` on a MonoBehaviour and attach it to the
item via `OnSpawn`:

```csharp
using UnityEngine;
using ScavLib.save;
using ScavLib.item;

public class FlaskState : MonoBehaviour, ICustomItemSaveable
{
    public int charges = 3;

    public string Save() => charges.ToString();   // return null to persist nothing

    public void Load(string blob)
    {
        if (int.TryParse(blob, out var n)) charges = n;
    }
}

// Attach it when the item spawns:
CustomItemBuilder.Canteen("mymod_flask", "MyMod")
    .OnSpawn(go => go.AddComponent<FlaskState>())
    .Register();
```

The contract is small:

- `Save()` returns an **opaque string** — JSON, CSV, a raw number, whatever you like.
  Returning `null` means "nothing to persist," and the blob is omitted.
- `Load(blob)` is called **once, after the item respawns and before the player can
  interact with it**, with the exact string `Save()` produced.
- Throwing from either method is caught and logged, never propagated — one
  misbehaving item can't break the load for every other item.

This is the supported way to persist the per-instance `InstanceData` you set on a
[`CustomItemTag`](items.md#per-instance-data): serialize it in `Save()`, restore it in
`Load()`.

## When the owning mod is missing

If a save contains a custom item whose mod isn't installed at load time, ScavLib
doesn't discard it. It keeps the original record intact behind a placeholder, so the
next save round-trips that data unchanged — **reinstalling the mod fully restores the
item**. A player who temporarily removes a mod won't lose anything tied to it.

## The companion file

ScavLib's data lives in `save.scavlib.sv` next to the vanilla save in the game's
persistent data folder. It's GZip-compressed JSON with a versioned schema, mirroring
the vanilla save's storage style.

!!! note "It can never corrupt the player's save"

    The failure policy is deliberately one-sided. A **read** failure (missing or
    corrupt companion file) is treated as "no companion data" — exactly like a fresh
    save — so a bad file degrades gracefully instead of crashing. A **write** failure
    is logged but never throws, because losing companion data is strictly less bad
    than interrupting the player's main save. After a successful load the companion
    file is deleted, matching how the vanilla save is consumed.

Custom **recipe** progress (whether a recipe has been crafted before) is persisted in
the same file, so a custom recipe remembers its "first craft" state across saves.

## Persisting other mod data

This system is specifically for **custom item instances** (and recipe progress). There
is no public general-purpose key/value store in the companion file for arbitrary
mod-global state. For settings or world-independent data, use your own BepInEx config
file or a file you manage; for anything attached to a specific spawned item, use
`ICustomItemSaveable`.

## Where to next

That completes the player-facing systems. The remaining pages are reference: the
[utilities](utilities.md) helpers used throughout these examples, and
[compatibility](compatibility.md) for multiplayer and framework-conflict handling.

*[ICustomItemSaveable]: Interface a custom item's MonoBehaviour implements to save and restore per-instance state.
*[CustomItemTag]: MonoBehaviour on every spawned custom item; its per-instance data is persisted via ICustomItemSaveable.
*[MissingItemTag]: Placeholder that preserves a custom item's saved record when its owning mod isn't loaded.
*[SaveCompanionData]: The versioned schema of the companion save file.
*[OnSpawn]: CustomItemBuilder hook used to attach a saveable component to each spawned instance.
