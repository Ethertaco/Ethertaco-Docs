---
description: ScavLib — the base API library for Casualties Unknown (Scav Prototype) mods.
---

# ScavLib API

ScavLib API is the base API library for **Casualties Unknown** (*Scav Prototype*) mods.
It sits between BepInEx and your plugin and turns the game's fragile internals —
Harmony patches, world-load timing, the console, the save file — into a small set
of stable, well-behaved APIs you can build on.

It is not a gameplay mod on its own. You install it once, and the mods that depend
on it gain a shared event bus, a mod registry, custom-content builders, keybinds,
localization, and save persistence — all fault-isolated so one broken feature can
never take the whole library down with it.

!!! info "Requirements"

    - **Casualties Unknown** (*Scav Prototype*)
    - **BepInEx 5** (Mono / .NET Framework 4.8 build)
    - *Optional:* [KrokoshaCasualtiesMP] — enables the multiplayer compatibility layer when present. ScavLib treats it as a **soft dependency**, so it loads fine with or without it.

## Install (players)

1. Install **BepInEx 5** into your game folder and launch the game once so it
   generates its directories.
2. Drop `ScavLib API.dll` into `BepInEx/plugins/`.
3. Launch the game again. You should see a line like
   `ScavLib 0.8.0 loaded successfully` in the BepInEx console — that means it's
   active and any dependent mods can find it.

!!! tip "Verify it loaded"

    Open the in-game console and run `scavlib check`. It lists which ScavLib
    patches applied, which (if any) failed, and the mods currently registered.

## What's inside

<div class="grid cards" markdown>

-   :material-package-variant-closed:{ .lg .middle } __Register your mod__

    ---

    Announce your mod to ScavLib with `ModInfo`, and let `IModLifecycle` wire you
    into the world lifecycle automatically.

    [:octicons-arrow-right-24: Mods & lifecycle](mods.md)

-   :material-bell-ring-outline:{ .lg .middle } __React to the world__

    ---

    Subscribe to world-loaded, layer-loaded, item-dropped and more through a
    central `EventBus` with simple `[Subscribe]` methods.

    [:octicons-arrow-right-24: Events](events.md)

-   :material-console:{ .lg .middle } __Add console commands__

    ---

    Register `BaseCommand` subclasses with owner attribution, autofill, and
    nested subcommands — without touching the vanilla console type.

    [:octicons-arrow-right-24: Commands](commands.md)

-   :material-treasure-chest:{ .lg .middle } __Create custom content__

    ---

    Build custom items, recipes, and liquids with fluent builders that handle
    prefab cloning, sprites, and deferred registration for you.

    [:octicons-arrow-right-24: Items](items.md)

-   :material-keyboard-outline:{ .lg .middle } __Bind keys__

    ---

    Define keybinds that appear in the game's own settings menu and raise
    pressed / held / released events.

    [:octicons-arrow-right-24: Input](input.md)

-   :material-content-save-outline:{ .lg .middle } __Persist data__

    ---

    Store your mod's state in a companion save file that lives beside the
    vanilla save and never corrupts it.

    [:octicons-arrow-right-24: Save](save.md)

</div>

## Your first mod

A complete ScavLib mod is just a BepInEx plugin that **declares a dependency**,
**registers itself**, and **waits for the world** before touching the player.

```csharp
using BepInEx;
using ScavLib.event_bus.events;
using ScavLib.mods;
using ScavLib.util;

namespace MyFirstMod
{
    [BepInPlugin("com.example.myfirstmod", "My First Mod", "1.0.0")]
    [BepInDependency("com.kanisuko.scavlib")]   // ScavLib loads before you
    public class Plugin : BaseUnityPlugin
    {
        private void Awake()
        {
            // Register with a lifecycle object — no need to call
            // EventBus.Register or scatter [Subscribe] attributes.
            ModRegistry.Register(
                new ModInfo(
                    "My First Mod",
                    "1.0.0",
                    "Feeds the player when the world loads.",
                    "You"),
                new Lifecycle());
        }

        private class Lifecycle : ModLifecycleBase
        {
            // Only override the callbacks you care about.
            public override void OnWorldLoaded(WorldLoadedEvent e)
            {
                // The world is ready here — touching the player is safe.
                PlayerUtil.Feed(50f);
            }
        }
    }
}
```

!!! danger "Don't touch the player in `Awake()`"

    `Awake()` runs **before the world exists**. Reading `PlayerCamera.main` or
    `WorldGeneration.world` there throws a `NullReferenceException`. Always wait
    for `OnWorldLoaded` (via `IModLifecycle`) — or, if you need finer timing,
    `GameUtil.AwaitWorldGeneration`.

### Prefer attributes over a lifecycle class?

If you'd rather keep your handlers inline, register a plain `ModInfo` and opt
into the bus yourself:

```csharp
private void Awake()
{
    ModRegistry.Register(
        new ModInfo("My First Mod", "1.0.0", "Feeds the player.", "You"));
    EventBus.Register(this);   // scans this object for [Subscribe] methods
}

[Subscribe]
private void OnWorldLoaded(WorldLoadedEvent e)
{
    PlayerUtil.Feed(50f);
}
```

Both styles are equivalent — pick one. The lifecycle object is tidier for larger
mods; inline `[Subscribe]` is fine for a handful of handlers.

## Develop against ScavLib

- Target **.NET Framework 4.8** and reference `ScavLib API.dll` (root namespace
  `ScavLib`).
- Add `[BepInDependency("com.kanisuko.scavlib")]` to your plugin so BepInEx loads
  ScavLib first.
- The shared log source is public: write through `ScavLibPlugin.Log` if you want
  your messages to share ScavLib's logging channel.

## Where to next

New to the library? Start with **[Mods & lifecycle](mods.md)** to understand how
registration works, then **[Events](events.md)** for everything that happens
during play. From there, jump to whichever feature your mod needs.

  [KrokoshaCasualtiesMP]: https://github.com/Krokosha666/cas-unk-krokosha-multiplayer-coop

*[BepInEx]: The Unity Mono mod loader ScavLib runs on top of.
*[ModInfo]: Metadata (name, version, description, author) describing a mod registered with ScavLib.
*[IModLifecycle]: Optional interface whose callbacks ScavLib invokes across the world lifecycle.
*[ModLifecycleBase]: Abstract base giving every IModLifecycle callback a no-op default, so you override only what you need.
*[EventBus]: ScavLib's central publish/subscribe hub for world and gameplay events.
*[WorldLoadedEvent]: Fired once the world has finished loading and the player Body is safe to access.
*[PlayerUtil]: Utility class for reading and modifying player vitals, skills, appearance and more.
*[GameUtil]: General-purpose helpers for timing, PlayerPrefs, in-world actions and console output.