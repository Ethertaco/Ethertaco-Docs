---
description: Null-safe helpers for player vitals, limbs, items, and skills.
---

# Utilities

ScavLib's `util` namespace is a set of static helper classes that wrap the game's
player, limb, item, and skill internals behind a safe, consistent surface. They share
one guarantee that makes them pleasant to call from anywhere:

!!! note "Everything here is null-safe"

    Every method works whether or not a world is loaded. Reads return a safe default
    (`0`, `false`, `null`) and writes no-op when there's no player — none of them throw
    a `NullReferenceException`. You can call them from the main menu without guarding.

The classes are `PlayerUtil` (player vitals, state, recovery), `LimbUtil` (per-limb
health), `ItemUtil` (items in the world), and `SkillUtil` (the three attributes).
The world/player gateway, item spawning, and console output — [`GameUtil`](gameutil.md)
— has its own page.

## Two write paths

The most important thing to understand before changing player or skill state is that
ScavLib offers **two ways to write**, and they behave very differently:

- **The recommended path** respects the game's own logic — animations, sounds, and
  side effects all fire as if the change happened naturally. `PlayerUtil.Feed`,
  `Hydrate`, `HealAll`, and `SkillUtil.AddExperience` are these.
- **The raw path**, every method suffixed `Raw`, writes the underlying field directly
  with a `Mathf.Clamp` to the game's valid range, and **bypasses all game logic**.
  `SetHungerRaw`, `SetLevelRaw`, and the rest are these.

Prefer the recommended path. Reach for `Raw` only when you specifically need to set an
exact value without triggering the normal consequences — and know what that field
does.

## `PlayerUtil`

The player helper is split across several areas, all on the one `PlayerUtil` class.

### Inventory

| Method | Does |
| --- | --- |
| `GiveItem(id)` | Spawn an item at the player and auto-pick-it-up. Returns the `GameObject`. |
| `TakeItem(id)` | Drop the first inventory item matching the id. Returns whether one was found. |
| `HasItem(id)` | Whether the player carries the id anywhere on their person. |
| `GetAllItems()` | Every item in the player's surface inventory. |
| `FindItemById(id, out item)` / `FindItemByTag(tag, out item)` | Locate a carried item. |

### Reading vitals

`PlayerUtil` exposes a `Get*` reader for every tracked vital — `GetHunger`,
`GetThirst`, `GetStamina`, `GetEnergy`, `GetHeartRate`, `GetBloodPressure`,
`GetBloodOxygen`, `GetTemperature`, `GetConsciousness`, `GetHappiness`, and many more,
plus derived readings like `GetBloodVolumePercentage`, `GetTempDiffFromNormal`, and
`GetBloodPressureReadout`. They all follow the `Get<Vital>()` naming pattern and return
`0` outside of gameplay.

### State queries

Boolean checks for the player's current condition: `IsAlive`, `IsConscious`, `IsDying`,
`IsInCardiacArrest`, `IsSleeping`, `IsInWater`, `IsStanding`, `IsCrouching`,
`IsExercising`, `HasScubaGear`, `CanTakeNap`, `AllowUseItem`, and more — each returning
`false` when there's no player. There are also grouped queries in the appearance, drug,
sleep, and last-stand areas (`IsDisfigured`, `HasPainkillers`, `GetBadSleepAmount`,
`GetLastStandTime`, …).

### Recovery (recommended writes)

| Method | Effect |
| --- | --- |
| `Feed(amount)` | Reduce hunger. |
| `Hydrate(amount)` | Reduce thirst. |
| `RestoreStamina(amount)` / `RestoreEnergy(amount)` | Top up stamina / energy. |
| `HealAll(body)` | Full restore of the given body. |

### Raw writes

For every vital there is a `Set<Vital>Raw(value)` that writes the field directly within
its clamped range. There are dozens — `SetHungerRaw`, `SetHeartRateRaw`,
`SetBloodPressureRaw`, `SetConsciousnessRaw`, and so on, including boolean states like
`SetSleepingRaw`. As covered above, these bypass game logic; use them deliberately.

### Thresholds

`PlayerUtil.Thresholds` holds named constants for every value the game's moodle system
uses as a boundary — extracted directly from the game so your mod stays consistent with
its UI. Use these instead of hard-coding magic numbers:

```csharp
if (PlayerUtil.GetBloodOxygen() < PlayerUtil.Thresholds.BLOOD_OXYGEN_LOW)
    GameUtil.Alert("Oxygen low!");
```

They cover blood pressure, blood oxygen, heart rate, temperature, bleeding speed, and
more, each with named tiers (e.g. `TEMPERATURE_HYPOTHERMIA_SEVERE`,
`HEART_RATE_TACHYCARDIA_MILD`).

## `LimbUtil`

Per-limb health, addressed by index, `LimbSlot`, or name:

| Method | Does |
| --- | --- |
| `GetLimb(index)` / `GetLimb(slot)` / `GetLimbByName(name)` | Fetch one limb. |
| `GetAllLimbs()` | Every limb. |
| `HasBrokenBone()` / `HasDislocation()` / `HasInfection()` / `HasDismemberment()` | Body-wide condition checks. |
| `GetMaxInfection()` / `GetAveragePain()` / `GetTotalBleedSpeed()` | Aggregate readings. |
| `HealLimb(limb)` / `HealLimb(index)` | Fully heal a limb (recommended path). |
| `DamageSkin(limb, amount)` / `DamageMuscle(limb, amount)` | Apply damage. |
| `SetSkinHealthRaw` / `SetMuscleHealthRaw` / `SetBleedRaw` / `SetPainRaw` / `SetInfectionRaw` | Raw per-limb field writes. |

## `ItemUtil`

Helpers for items out in the world (as opposed to the player's inventory):

| Method | Does |
| --- | --- |
| `FindNearby(center, radius, includeContained=false)` | All items within a radius. Optionally include items inside containers. |
| `FindClosest(center, maxRadius=∞, includeContained=false)` | The nearest item. |
| `SetCondition(item, condition)` / `Repair(item)` | Adjust durability. |
| `SetFavourited(item, bool)` | Toggle the favourite flag. |
| `Destroy(item)` | Remove an item from the world. |
| `GetInfo(id)` / `IsKnownId(id)` / `GetAllIds()` | Look up item definitions, including custom ones. |

## `SkillUtil`

The three character attributes are addressed through the `SkillType` enum —
`Strength`, `Resilience`, `Intelligence` (values matching the game's own indices):

| Method | Does |
| --- | --- |
| `GetLevel(skill)` | Current level (`0` outside gameplay). |
| `GetExperience(skill)` | Absolute XP. |
| `GetExperienceInLevel(skill)` / `GetExperienceForNextLevel(skill)` | XP within the current level / to the next. |
| `GetProgress(skill)` | Progress to next level, `0`–`1`. |
| `AddExperience(skill, xp)` | Grant XP the normal way (recommended path). |
| `SetLevelRaw(skill, level)` | Force a level directly (raw path). |

`SkillUtil.XpMultiplier` exposes the current global XP multiplier.

```csharp
SkillUtil.AddExperience(SkillType.Intelligence, 25f);
int intLevel = SkillUtil.GetLevel(SkillType.Intelligence);
```

## Where to next

This is the last of the feature pages. [Compatibility](compatibility.md) covers how
ScavLib coexists with the multiplayer mod and detects conflicts with other frameworks.

*[PlayerUtil]: Static helper for the player's vitals, state, inventory, and recovery.
*[LimbUtil]: Static helper for per-limb health and injury.
*[ItemUtil]: Static helper for finding and modifying items in the world.
*[SkillUtil]: Static helper for the three character attributes (Strength, Resilience, Intelligence).
*[SkillType]: Enum naming the three attributes; values match the game's internal indices.
*[GameUtil]: The world/player gateway, item spawning, and console helper class, documented on its own page.
