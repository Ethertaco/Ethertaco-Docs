---
description: How ScavLib coexists with the multiplayer mod and other item frameworks.
---

# Compatibility

Compatibility in ScavLib is **automatic and internal** — there are no APIs to call on
this page. It exists so you understand what ScavLib does behind the scenes: how it
bridges custom content into multiplayer, and how it behaves when another item
framework is installed alongside it. Knowing this is mostly useful for diagnosing odd
behaviour and writing good bug reports.

## Multiplayer (KrokMP)

ScavLib treats
[KrokoshaCasualtiesMP](https://github.com/Krokosha666/cas-unk-krokosha-multiplayer-coop)
— the LAN co-op mod — as a **soft dependency**. If it isn't installed, nothing happens
and your mod runs in single-player as normal. If it is installed, ScavLib detects it at
startup and activates a bridge that makes your custom content work over the network,
with **no extra work on your part**. The bridge handles:

- **Spawning** — when multiplayer spawns a custom item onto a player (e.g. via its give
  command), the request is routed through ScavLib's own spawn path, with ammo and gun
  state filled in and pickup / container loading handled.
- **Network sync** — this is the key fix. Multiplayer normally re-creates a networked
  object by loading a prefab by id, which fails for a custom id with no prefab. ScavLib
  intercepts the sync, instantiates the item from its template, injects the custom id,
  tag, and `OnSpawn` hook, and registers it into the multiplayer object table — so
  custom items appear correctly on every client.
- **Object validation** — custom items are flagged as network-relevant so the
  multiplayer mod won't mistake them for stray objects and destroy them.
- **Save location** — while a multiplayer session is running, the
  [companion save file](save.md) is written into the multiplayer save folder instead of
  the single-player location, so co-op saves keep their custom-item data together.

Custom liquids are bridged too: a liquid registered while multiplayer is active is
synced into its network id table (see [liquids](liquids.md)).

!!! note "Detecting multiplayer from your own mod"

    ScavLib's bridge is internal — you don't call it. If your own code needs to know
    whether the multiplayer mod is present, check BepInEx directly:
    `Chainloader.PluginInfos.ContainsKey("KrokoshaCasualtiesMP")`, or declare a soft
    `[BepInDependency]` on its GUID.

## Coexisting with other item frameworks

More than one custom-item framework can be installed at once. ScavLib is built to be a
**good citizen** in that situation, but there's an honest limit to what any framework
can do here.

ScavLib's design keeps its footprint deliberately small:

- its spawn patch runs at **low priority**, so other frameworks' patches run first;
- it only claims the ids **it** registered — there's no blanket interception of every
  spawn;
- it never patches the broad shared entry points (`Body`, `Recipe.fullName`,
  `SaveSystem`, `BuildingEntity`), keeping the smallest possible surface for conflicts.

What it **doesn't** do is try to reconcile two frameworks fighting over the same global
entry point — that genuinely can't be auto-resolved. Instead, when ScavLib detects a
known coexisting framework (such as RshLib) at startup, it logs a prominent warning so
the cause is obvious from the logs.

!!! warning "If custom items misbehave with another framework installed"

    Duplicate ids or mutually exclusive spawn overrides between two frameworks can't be
    fixed automatically. If custom items act up and you have another item framework
    installed, that coexistence is the likely cause — check the BepInEx log for the
    coexistence warning and mention it in any bug report.

## Diagnosing

The in-game `scavlib check` command (see [commands](commands.md)) is the fastest way to
see the state of things: it lists every ScavLib Harmony patch as `[OK]` or `[FAIL]`,
which immediately shows whether a patch was blocked by a conflict. Combined with the
startup warnings described above, it usually pinpoints a compatibility problem on the
first look.

## That's the tour

You've now seen every system ScavLib offers — from [registering a mod](mods.md) and
[reacting to the world](events.md), through [custom content](items.md), [player-facing
features](commands.md), and [persistence](save.md), to the [utility](utilities.md)
helpers and this compatibility layer. The [overview](index.md) ties them together if
you want to start building.

*[KrokoshaCasualtiesMP]: The LAN co-op multiplayer mod ScavLib bridges to as a soft dependency.
*[CustomItemTag]: Component on every spawned custom item; the multiplayer bridge uses it to keep items network-relevant.
*[Utils.Create]: The game's spawn method; ScavLib patches it at low priority and only for its own ids.
