---
description: The gateway to world and player state, item spawning, console output, and UI checks.
---

# GameUtil

`GameUtil` is the entry point to common game-state operations: checking whether a
world is loaded, reaching the player, spawning items, writing to the console, and
showing alerts. Like the rest of the [utilities](utilities.md), every method handles a
null game state gracefully — all of it is **safe to call from the main menu**, where
it simply returns a safe value or no-ops.

## World and player state

| Member | Returns |
| --- | --- |
| `IsInGame` | `true` when a world is loaded (the player camera exists). `false` in the menu. |
| `IsWorldLoaded` | A stricter check that asks the world-generation system whether the world data is actually present. |
| `GetWorld()` | The `WorldGeneration` instance, or `null`. |
| `GetBody()` | The player's `Body`, or `null` when not in game. |
| `TryGetBody(out body)` | `true` and the `Body` if available — the convenient guarded form. |
| `GetPlayerPosition()` | The player's world position, or `Vector2.zero` when not in game. |

`GetBody` / `TryGetBody` are the foundation the other utility classes are built on, so
reaching the player is usually a one-liner:

```csharp
if (GameUtil.TryGetBody(out var body))
{
    // safe to read or act on the player here
}
```

!!! note "`IsInGame` vs `IsWorldLoaded`"

    `IsInGame` checks that the player exists, which is enough for most gameplay code.
    `IsWorldLoaded` goes further and confirms the world-generation data is present —
    use it when you specifically depend on world data, not just the player.

## Spawning items

| Method | Does |
| --- | --- |
| `SpawnItem(id, position, rotation=0)` | Spawn an item or building at a world position. Returns the `GameObject`, or `null` if the id is invalid or no world is loaded. |
| `SpawnItemAt(id, transform)` | Spawn at a transform's position, copying its Z rotation. |
| `SpawnAtPlayer(id)` | Spawn at the player and auto-pick-it-up if it's an item. |

The `id` is the same resource id the `spawn` console command uses, and spawning goes
through the game's `Utils.Create` — the same path custom items use — so a **registered
custom item id works here too**. Spawning before a world loads is handled: you get a
logged warning and a `null` result rather than an exception.

```csharp
GameUtil.SpawnAtPlayer("bandage");          // hand the player a bandage
GameUtil.SpawnItem("mymod_flask", pos);     // a registered custom item, in the world
```

## Console output

| Method | Does |
| --- | --- |
| `Log(message)` | Write a line to the in-game developer console. |
| `Alert(text, important=false)` | Show an on-screen alert popup. `important` displays it prominently, centered. |
| `Notify(text, important=false)` | `Alert` **and** `Log` the same text — visible to the player and recoverable from console scrollback. |

`Log` is safe to call before the console exists (the message is silently dropped). It
also handles multi-line text: it splits on newlines, strips `\r` from CRLF endings,
and emits one console line per line, skipping empty lines.

!!! warning "The console collapses runs of spaces"

    The game's `log` command tokenizes on spaces and collapses consecutive spaces
    within a line, so don't rely on multiple spaces to align columns in your log
    output — the alignment won't survive.

## UI

`IsPointerOverUI()` returns `true` when the mouse is hovering over a game UI element.
Check it in your own menus and click handlers to avoid intercepting clicks meant for
the game underneath.

## Where to next

For the typed helpers built on top of `GetBody` — player vitals, limbs, items, and
skills — see [utilities](utilities.md).

*[Body]: The player's core component; GameUtil.GetBody returns it, and the PlayerUtil helpers wrap it.
*[WorldGeneration]: The game's world system; IsWorldLoaded and GetWorld query it.
*[Utils.Create]: The game's spawn method that GameUtil and the custom-item system both route through.
