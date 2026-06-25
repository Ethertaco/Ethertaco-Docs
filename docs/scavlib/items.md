---
description: Define custom items by cloning a vanilla template and overriding what you need.
---

# Custom items

ScavLib creates custom items by **cloning a vanilla item as a template** and
applying your overrides on top. You never build an `ItemInfo` from scratch — you
pick the closest vanilla item (a pistol, a canteen, a helmet), change the fields
you care about, give it an id and a sprite, and register it. Every mod registers
through one shared registry, so two mods can't silently corrupt each other's items.

The flow is always the same: **build → register → spawn.**

```csharp
using ScavLib.item;

CustomItemBuilder.Canteen("mymod_flask", "MyMod")   // clone the canteen
    .DisplayName("Old Flask")
    .Description("A dented metal flask.")
    .Sprite(flaskSprite)
    .Capacity(0.5f)
    .DefaultContents(("mymod_moonshine", 0.5f))      // a custom liquid
    .Register();
```

Two arguments appear everywhere: the **id** (a unique string; convention is
`<modname>_<itemid>`) and the **owner** (your mod's name, used for cross-mod
collision safety).

## Choosing a template

The clone source is an `ItemTemplate` — an enum of vanilla items, each mapping to a
game resource id. Pass it to `CustomItemBuilder.Create(id, owner, template)`, or
use one of the named factory shortcuts:

```csharp
CustomItemBuilder.Create("mymod_thing", "MyMod", ItemTemplate.FoodSimple);
CustomItemBuilder.Pistol("mymod_holdout", "MyMod");   // same as Create(..., ItemTemplate.Pistol)
```

Named factories exist for the common cases: weapons (`Pistol`, `Rifle`, `Shotgun`,
`Magazine`, `Explosive`), gear (`SmallBattery`/`MediumBattery`/`LargeBattery`,
`Canteen`, `Flashlight`, `Backpack`), and a large set of wearables (`Helmet`,
`Hoodie`, `Shirt`, `TorsoArmor`, `Belt`, `Boots`, `Gloves`, `Goggles`,
`Balaclava`, and more). You can also pass a raw resource-id string to
`Create(id, owner, "resourceid")` if you need a template the enum doesn't cover.

!!! note "The clone is deep and vanilla-safe"

    Registration deep-clones the template's `ItemInfo`, preserving its real
    subtype — a `LiquidItemInfo` stays a `LiquidItemInfo`, a `BatteryInfo` stays a
    `BatteryInfo` — and re-clones its list fields. Your overrides never mutate the
    original vanilla item. A few enum entries intentionally share a resource (for
    example `Helmet` and `BikeHelmet` both map to the bike helmet), so the named
    factory is just a readable alias over the underlying template.

## Configuring the item

All setters return the builder, so they chain. They fall into a few groups.

### Core properties

These write directly onto the cloned `ItemInfo`.

| Method | Sets |
| --- | --- |
| `Category(string)` | Loot/spawn category. Also controls which loot pool the item joins. |
| `Weight(float)` / `Value(int)` | Inventory weight and trade value. |
| `SlotRotation(float)` | Rotation of the item in its inventory slot. |
| `Combineable(bool=true)` | Whether copies stack/combine. |
| `DecayMinutes(float)` / `RotSpeed(float)` / `DecayInfo(...)` | Spoilage. `DecayInfo` takes either an `ItemInfo.DecayType` flags value or a raw `byte`. |
| `DestroyAtZeroCondition(bool=true)` | Destroy the item when its condition hits zero. |
| `ScaleWeightWithCondition(bool=true)` | Weight tracks condition. |
| `OnlyHoldInHands(bool=true)` | Can only be held, not stowed in a slot. |
| `AutoAttack(bool=true)` / `UsableWithLMB(bool=true)` / `IgnoreDepression(bool=true)` | Combat/use flags. |
| `Tags(params string[])` | Item tags (joined into the vanilla comma-separated form). |
| `Recognition(int)` | Recognition level. |
| `Quality(string id, float amount=1f)` | Adds a crafting quality. Call repeatedly to add several. |

### Use actions

`Usable` and `UsableOnLimb` attach the callback the game runs when the item is
used. Each has a `replace` flag:

```csharp
.Usable((body, item) => PlayerUtil.Feed(20f))            // replace=true (default): override vanilla
.Usable((body, item) => DoExtra(body), replace: false)   // append: vanilla runs first, then yours
```

With `replace: false`, the vanilla use action runs first and yours runs after —
each wrapped so one throwing doesn't stop the other.

### Wearables

| Method | Purpose |
| --- | --- |
| `Wearable(VanillaLimb, VanillaWearSlot, float armor=0, float isolation=0)` | The all-in-one: marks the item wearable, sets the limb + slot, and optionally armor/isolation. |
| `WearSlot(VanillaLimb, VanillaWearSlot)` | Just the limb + slot. |
| `WearableArmor(float)` / `WearableIsolation(float)` | Protection values. |
| `WearableHitDurabilityLossMultiplier(float)` | Durability loss per hit. |
| `WearableVisualOffset(int)` / `WearableCanBeHeld(bool=true)` / `JumpHeightMultChange(float)` | Visual and movement tweaks. |

Use the `VanillaLimb` and `VanillaWearSlot` enums rather than raw strings — the
game looks limbs and slots up by name, and the enums (with their `ToName()` /
`ToSlotId()` mappings) keep you from silently mistyping `"uptorso"`. Items sharing
a wear slot are mutually exclusive in-game.

### Liquid and battery templates

These only make sense on the matching template type:

| Method | Applies to |
| --- | --- |
| `Capacity(float)` | Liquid containers (`Canteen`, `WaterContainer`, …) |
| `AutoFill(bool=true)` | Liquid containers |
| `DefaultContents(params (string liquidId, float amount)[])` | Liquid containers — pre-fill on spawn |
| `MaxCharge(float)` | Batteries |

!!! warning "Category-specific setters are silently skipped on the wrong template"

    `Capacity`, `MaxCharge`, and the like map to fields that exist only on
    `LiquidItemInfo` / `BatteryInfo`. If you call one on a template that isn't that
    subtype, the override field isn't found, and ScavLib logs a **warning and moves
    on** — the item still registers, just without that property. If a liquid or
    battery setting seems to have no effect, check the BepInEx log and confirm your
    template actually clones a liquid/battery item.

### Runtime component tuning

Some properties live on MonoBehaviours that only exist on a spawned instance, not
on `ItemInfo`. These setters register an **`OnSpawn` hook** that configures the
component after the instance is created:

| Method | Component touched |
| --- | --- |
| `AmmoType(GunScript.AmmoType)` | `AmmoScript` / `GunScript` |
| `AmmoMaxRounds(int)` | `AmmoScript` |
| `GunMagCapacity(int)` / `GunShotsPerFire(int)` / `GunVerticalSpread(float)` | `GunScript` |
| `GunDamage(float structureDamage, float animalDamage)` | `GunScript` |
| `GunSprites(normal, racked, normalNoMag, rackedNoMag)` | `GunScript` |
| `ContainerCapacity(float maxWeight, float maxWeightPerItem)` | `Container` |
| `ContainerTagRestriction(params string[])` | `Container` |
| `ContainerItemsVisible(bool=true)` / `ContainerEncumberance(float)` | `Container` |

Each hook null-checks its component, so calling a gun setter on a non-gun item is
harmless (it just finds no `GunScript`).

### Names, descriptions, and your own spawn hook

`DisplayName(string)` and `Description(string)` set the English text (the English
display name becomes the item's `fullName`). Pass an `IDictionary<string,string>`
overload to provide several languages at once; these flow into ScavLib's
[localization](i18n.md) system. Finally, `OnSpawn(Action<GameObject>)` adds your
own post-spawn hook — it runs after all the built-in component hooks above, and
after the instance's `Awake`.

## Registering

End the chain with `Register()`. The parameterless form returns `bool`; an overload
gives you the error text:

```csharp
if (!builder.Register(out string error))
    ScavLibPlugin.Log.LogError($"Item failed: {error}");
```

!!! tip "Register whenever — ScavLib handles the timing"

    A custom item can only finish registering after the game's item table
    (`Item.SetupItems`) has run. If you register before that — for example in your
    mod's `OnEnabled` — the builder **defers itself and returns `true`**, and
    ScavLib retries it automatically once the table is ready. You do **not** need to
    wait for `OnWorldLoaded`. `OnEnabled` is the recommended place.

    Once the table is loaded, registered items are injected into the game's
    `GlobalItems`, their tags are initialized, and the loot pool is rebuilt — so a
    custom item with a `Category` shows up in that category's drops automatically.
    Registering mid-game (after the table already loaded) works too and rebuilds
    the loot pool on the spot.

### Ids and ownership

The **owner** ledger is what makes multiple item mods safe together:

- **Same owner, same id** → treated as an idempotent overwrite (logged as a
  warning). This is what lets your mod re-prepare its items across run boundaries
  without error.
- **Different owner, same id** → rejected with a clear error. Another mod cannot
  claim your id, and you can't claim theirs.
- **No prefix** → the item still registers, but ScavLib warns you. Follow the
  `<modname>_<itemid>` convention to avoid collisions in the first place.

!!! danger "Never patch `Utils.Create` yourself"

    ScavLib patches the game's spawn method exactly once, at low priority, and
    dispatches by id. If your mod also patches `Utils.Create`, you reintroduce the
    very framework-conflict problem the single-registry design exists to prevent.
    Register through `CustomItemBuilder` and let ScavLib own the spawn path.

## Spawning

A registered item spawns through the game's normal `Utils.Create(id, …)` using your
id — no special ScavLib call. Custom ids are also added to the `spawn` console
command's autofill, so you can `spawn mymod_flask` in-game to test.

Under the hood the spawn patch clones the template prefab, swaps in your id,
sprite, and a `CustomItemTag`, and takes care of a subtle ordering problem:
several vanilla components read item data in their `Awake`, which runs the instant
a clone activates. ScavLib suspends that `Awake` until **after** your id is in
place, so those components read *your* `ItemInfo`, not the template's. Your
`OnSpawn` hook then runs once, after `Awake`, with the instance fully initialized.

## Per-instance data

Every spawned custom item carries a `CustomItemTag` MonoBehaviour. It holds the
`CustomItemId`, the `Owner`, and a free-form `InstanceData` bag for state that
varies per spawned copy:

```csharp
var tag = go.GetComponent<CustomItemTag>();
tag.Set("charges", 3);
if (tag.TryGet<int>("charges", out var n)) { /* ... */ }
```

This is the supported way to attach per-instance data — the item id itself stays
clean, which is what keeps ScavLib's patch surface small.

## Querying the registry

`CustomItemRegistry` exposes simple lookups:

| Method | Returns |
| --- | --- |
| `Contains(id)` | `bool` (case-insensitive). |
| `TryGet(id, out CustomItem)` | The registered definition. |
| `GetOwner(id)` | The owning mod name, or `null`. |
| `GetAllIds()` | All registered ids. |
| `GetAllRegistered()` | `(id, owner)` pairs. |

!!! note "`RegisterItem(id, ItemInfo)` is obsolete"

    The old `CustomItemRegistry.RegisterItem` overload still exists for source
    compatibility but is marked `[Obsolete]`: it can only register a *definition*,
    never spawn an instance. Use `CustomItemBuilder` for anything new.

## Where to next

Custom items often come with custom [recipes](recipes.md) to craft them and custom
[liquids](liquids.md) to fill them — those are the next two pages. For the
display-name and description localization touched on above, see [i18n](i18n.md).

*[ItemInfo]: The game's data object describing an item; ScavLib clones a vanilla one as your template.
*[ItemTemplate]: Enum of vanilla items you can clone from, each mapping to a game resource id.
*[CustomItemBuilder]: Fluent builder that clones a template, applies overrides, and registers a custom item.
*[CustomItem]: The immutable result of a builder — the registered definition of a custom item.
*[CustomItemRegistry]: The single shared registry every ScavLib item mod registers through.
*[CustomItemTag]: MonoBehaviour attached to each spawned custom item, carrying its id, owner, and per-instance data.
*[VanillaLimb]: Typed enum of vanilla limb names, used for wearable placement.
*[VanillaWearSlot]: Typed enum of vanilla wear-slot ids; items sharing a slot are mutually exclusive.
*[LiquidItemInfo]: ItemInfo subtype for liquid containers (capacity, default contents).
*[BatteryInfo]: ItemInfo subtype for batteries (max charge).
