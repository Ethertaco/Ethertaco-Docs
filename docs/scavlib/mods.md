---
description: Register your mod with ScavLib API and opt into its world lifecycle.
---

# Mods & lifecycle

Every ScavLib-aware mod starts by **announcing itself** to the registry. Doing so
gives you three things: your mod shows up in the in-game `scavlib` diagnostics,
other mods can discover and depend on you, and — if you provide a lifecycle
object — ScavLib drives your code through the world's load/unload cycle for you.

Registration is one call in your plugin's `Awake()`. Everything on this page hangs
off `ModRegistry.Register`.

## Registering a mod

The minimal form takes just a `ModInfo`:

```csharp
using ScavLib.mods;

ModRegistry.Register(
    new ModInfo("My Mod", "1.0.0", "Does a thing.", "You"));
```

That records the mod and runs an advisory dependency check, but does **not** wire
you into any events. To react to the world, pass a lifecycle object as well:

```csharp
ModRegistry.Register(
    new ModInfo("My Mod", "1.0.0", "Does a thing.", "You"),
    new MyLifecycle());      // see "The lifecycle" below
```

What `Register` does, in order: builds a session, stores it, indexes it by name,
wires the lifecycle (if any) into the [EventBus], runs the dependency check, logs
a confirmation line, and finally fires `OnEnabled()`.

!!! note "It never throws on you"

    `Register(null)` is a silent no-op. A duplicate mod name logs a warning but
    still registers. And every lifecycle callback runs inside a try/catch — an
    exception in *your* `OnWorldLoaded` is logged against your mod name and
    swallowed, so it can't break ScavLib or other mods. Check the BepInEx log if
    a callback seems to "do nothing."

## `ModInfo`

`ModInfo` is the immutable metadata describing your mod. Three constructors, each
chaining down to the most specific one:

| Constructor | Use it for |
| --- | --- |
| `ModInfo(name, version, description)` | No dependencies. `author` defaults to `"Unknown"`. |
| `ModInfo(name, version, description, author)` | The common case. |
| `ModInfo(name, version, description, author, VersionedDependency[])` | Declaring versioned dependencies. |

A legacy `string[]` overload also exists for plain dependency names (0.4.x
compatibility) and is converted to `VersionedDependency` internally.

| Property | Notes |
| --- | --- |
| `Name` | Identity for lookups and dependency resolution. Case-insensitive when matched. |
| `Version` | Free-form string; parsed loosely only when version ranges are checked. |
| `Description` | One-line summary. |
| `Author` | Falls back to `"Unknown"` if you pass `null`. |
| `VersionedDependencies` | The declared dependencies (may be empty). |
| `Dependencies` | Back-compat shim returning the dependency **names** as `string[]`. |

!!! warning "The registry name is `ScavLib`, not `ScavLib API`"

    ScavLib API registers itself under the name **`ScavLib`** (`com.kanisuko.scavlib`
    is the BepInEx GUID; `ScavLib` is the registry name). When you declare a
    dependency on it, use `"ScavLib"` — the product's display name (`ScavLib API`)
    is not what the registry matches on.

## The lifecycle

Pass an `IModLifecycle` to `Register` and ScavLib subscribes its callbacks to the
world events for you — no `EventBus.Register` call, no `[Subscribe]` attributes.
The easiest way to implement it is to inherit `ModLifecycleBase`, which gives
every callback a no-op default so you override only what you need:

```csharp
using ScavLib.event_bus.events;
using ScavLib.mods;

public class MyLifecycle : ModLifecycleBase
{
    public override void OnWorldLoaded(WorldLoadedEvent e)
    {
        // Player is safe to touch here.
    }

    public override void OnLayerLoaded(LayerLoadedEvent e)
    {
        if (e.IsFirstLoad)
            ScavLibPlugin.Log.LogInfo("Entered the world.");
        else
            ScavLibPlugin.Log.LogInfo($"Descended to depth {e.BiomeDepth}.");
    }
}
```

### Callbacks and when they fire

| Callback | Fires | Event payload |
| --- | --- | --- |
| `OnEnabled()` | Immediately after `Register` succeeds. | — |
| `OnWorldLoaded(e)` | **Once per session**, when the world has finished its first load. | `WorldLoadedEvent` (no fields) |
| `OnLayerLoaded(e)` | Every time a layer finishes generating, **including the first**. | `LayerLoadedEvent.BiomeDepth`, `.IsFirstLoad` |
| `OnWorldUnloading(e)` | Before a layer is torn down — on descent **and** quit-to-menu. | `WorldUnloadingEvent.CurrentBiomeDepth`, `.NextBiomeDepth`, `.IsExitToMenu` |
| `OnWorldDestroyed(e)` | When the scene actually unloads. World state is gone by now. | `WorldDestroyedEvent` |
| `OnDisabled()` | Reserved — see the caveat below. | — |

A typical descent runs: `OnEnabled` → `OnWorldLoaded` → `OnLayerLoaded` (first) →
`OnWorldUnloading` → `OnLayerLoaded` (next) → … → `OnWorldDestroyed`.

!!! danger "Don't touch the player in `Awake()` or `OnEnabled()`"

    Both run **before the world exists**. Reading `PlayerCamera.main` or
    `WorldGeneration.world` there throws `NullReferenceException`. `OnEnabled` is
    the place for ScavLib-dependent setup that does *not* need the world
    (registering commands, items, keybinds). Wait for `OnWorldLoaded` /
    `OnLayerLoaded` to read player or world state.

!!! warning "`OnDisabled()` is not invoked yet"

    The enable/disable system it belongs to is still being built. In this version
    no code calls `OnDisabled()` — not even at shutdown — so do **not** rely on it
    for teardown or resource release. If you need cleanup tied to world teardown,
    use `OnWorldUnloading` or `OnWorldDestroyed` instead.

#### `OnLayerLoaded` vs `OnWorldLoaded`

`OnWorldLoaded` fires exactly once, when the session's world first becomes
playable. `OnLayerLoaded` fires for *every* layer — including that first one — so
`IsFirstLoad` is how you tell "the player just entered the world" apart from "the
player descended a level." If your logic only cares about entering the game, use
`OnWorldLoaded`; if it cares about each biome, use `OnLayerLoaded`.

### Prefer `[Subscribe]` instead?

The lifecycle object is just a convenience wrapper over the [EventBus]. If you'd
rather keep handlers inline, register a plain `ModInfo` and subscribe yourself:

```csharp
ModRegistry.Register(new ModInfo("My Mod", "1.0.0", "Does a thing.", "You"));
EventBus.Register(this);

[Subscribe]
private void OnWorldLoaded(WorldLoadedEvent e) { /* ... */ }
```

Both reach the same events. The lifecycle object is tidier for larger mods; inline
`[Subscribe]` is fine for a handful of handlers. See [Events](events.md) for the
full event catalog.

## Declaring dependencies

A `VersionedDependency` records a name and an optional version range:

```csharp
ModRegistry.Register(new ModInfo(
    "My Mod", "1.0.0", "Needs ScavLib 0.8 or newer.", "You",
    new[]
    {
        new VersionedDependency("ScavLib", minVersion: "0.8.0"),
        // Both bounds are optional:
        new VersionedDependency("SomeOtherMod", "1.2.0", "2.0.0"),
    }));
```

ScavLib checks these at registration and logs a warning if a dependency is
missing or its version falls outside the range.

!!! important "Dependency checks are advisory, not enforced"

    The check **never blocks loading** — it only writes warnings to the log. Two
    consequences worth understanding:

    - **It is order-sensitive.** The check looks at what is *already registered*
      when your `Register` runs. If your dependency registers *after* you, you'll
      get a "not registered yet" warning even though it loads fine. For real load
      ordering, use BepInEx's `[BepInDependency("their.guid")]` — that is the
      authoritative mechanism; `VersionedDependency` is just a soft, informational
      layer on top.
    - **Version parsing fails open.** Versions are parsed loosely (a trailing
      `-beta` or `+build` suffix is stripped, a bare `1` becomes `1.0`). If a
      version string can't be parsed at all, the range check is **skipped** and
      treated as satisfied, with a warning. So a passing check is not a hard
      guarantee.

## Querying the registry

Once mods are registered you can inspect them at runtime — useful for soft
integrations ("if mod X is present, enable feature Y").

| Method | Returns |
| --- | --- |
| `GetAll()` | `IReadOnlyList<ModInfo>` in registration order. |
| `TryFind(name, out info)` | `true` + the `ModInfo` if found (case-insensitive). |
| `IsRegistered(name)` | `bool`, case-insensitive. |
| `GetLifecycle(mod)` | The mod's `IModLifecycle`, or `null` if it registered without one. |
| `HasLifecycle(mod)` | `bool`. |
| `GetSession(name)` | The `ModSession`, or `null`. |

```csharp
if (ModRegistry.IsRegistered("SomeOtherMod"))
{
    // Light up an optional integration.
}
```

!!! note "Duplicate names resolve to the first registration"

    Duplicate names are allowed (with a warning). All copies appear in `GetAll()`,
    but the name-keyed lookups — `TryFind`, `IsRegistered`, `GetSession` — only
    ever see the **first** mod registered under that name. Keep mod names unique
    to avoid ambiguity.

## `ModSession`

`GetSession(name)` returns the runtime record behind a registered mod. In this
version it is a read-only data holder exposing `Info`, `Lifecycle`, and an
`IsEnabled` flag that is always `true` — the enable/disable operations it was
designed for are not exposed yet. It's primarily useful for diagnostics today.

## Where to next

You now have a mod registered and reacting to the world. Next, [Events](events.md)
covers the full set of events you can subscribe to — including item drops and
pickups — and how `EventBus` dispatch works.

*[EventBus]: ScavLib's central publish/subscribe hub for world and gameplay events.
*[ModInfo]: Immutable metadata (name, version, description, author, dependencies) describing a registered mod.
*[IModLifecycle]: Interface whose callbacks ScavLib invokes across the world lifecycle.
*[ModLifecycleBase]: Abstract base giving every IModLifecycle callback a no-op default, so you override only what you need.
*[ModSession]: Runtime record of a registered mod: its ModInfo, lifecycle, and enabled state.
*[VersionedDependency]: A dependency declaration with a name and optional min/max version bounds.
*[WorldLoadedEvent]: Fired once when the world has finished loading and the player is safe to access.
*[LayerLoadedEvent]: Fired each time a layer finishes generating, including the first.
*[WorldUnloadingEvent]: Fired before a layer is torn down, on descent or quit-to-menu.
*[WorldDestroyedEvent]: Fired when the world scene actually unloads.