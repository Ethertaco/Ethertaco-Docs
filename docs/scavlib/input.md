---
description: Register keybinds that appear in the game's Input settings, persist, and fire callbacks or events.
---

# Keybinds

ScavLib keybinds show up in the game's own **Input settings tab**, remember the
player's rebinds across sessions, and notify your mod when pressed — through a
convenience callback or through events. You define one with a builder, register it,
and react to it.

```csharp
using UnityEngine;
using ScavLib.input;

KeyBindBuilder.Create("MyMod", "dash")
    .Default(KeyCode.G)
    .DisplayName("Dash")
    .Description("Quick forward dash.")
    .Category("MyMod")
    .OnPressed(() => DoDash())
    .Register();
```

Two identifiers define a keybind: the **owner** (your mod's name) and a **localId**
unique within your mod. ScavLib combines them into a sanitized **FullId**
(`owner_localId`) — that's the id you'll see in `scavlib check` and on the keybind
events.

## Builder reference

| Method | Purpose |
| --- | --- |
| `Create(ownerModName, localId)` | Start a builder. |
| `Default(KeyCode)` | The default key. Omit it (or `KeyCode.None`) to ship unbound. |
| `DisplayName(string)` / `DisplayName(dict)` | The label in the settings row. The dictionary overload supplies several languages; both flow into [localization](i18n.md). |
| `Description(string)` / `Description(dict)` | Longer description text, also localizable. |
| `Category(string)` | Group header shown above the row in the Input tab. Rendered verbatim — add your own decoration (`"─── My Mod ───"`, `"[ My Mod ]"`, …) if you want. Binds sharing a category string are grouped under one header. |
| `OnPressed(Action)` | A callback fired on each press (see below). |
| `Register()` / `Register(out error)` | Finalize and register. Returns `bool`. |

## Reacting to a keybind

There are two ways to respond, and you can use either or both.

**The `OnPressed` callback** is the simplest — it runs once each time the key is
pressed, already focus-gated (see below), with no event-bus indirection:

```csharp
.OnPressed(() => DoDash())
```

**The events** give you press, hold, and release, and let any object subscribe via
`[Subscribe]`. They live in `ScavLib.input.events_`:

```csharp
using ScavLib.input.events_;
using ScavLib.event_bus;

[Subscribe]
private void OnAnyKeyPressed(KeyBindPressedEvent e)
{
    if (e.OwnerModName == "MyMod" && e.LocalId == "dash")
        DoDash();
}
```

| Event | Fires |
| --- | --- |
| `KeyBindPressedEvent` | Once, on the frame the key goes down. |
| `KeyBindHeldEvent` | Every frame the key is held — use sparingly. |
| `KeyBindReleasedEvent` | Once, on the frame the key goes up. |

Each event exposes the `KeyBindDefinition` as `Bind`, plus shortcuts `FullId`,
`OwnerModName`, and `LocalId`. Filtering on `OwnerModName` + `LocalId` is the
clearest way to identify which bind fired.

!!! warning "Keybinds are suppressed while the player is busy"

    Both the callback and all three events are gated by focus: they do **not** fire
    while the settings menu is open, the console is open, the game is paused, or a
    text input field is focused. This keeps a keybind from firing while the player is
    typing a console command or rebinding keys. Your handler can assume the player is
    actually in gameplay.

## Settings menu and persistence

A registered keybind appears automatically in the game's Input settings tab, under
its `Category` header, with its localized display name. When the player rebinds it
there, ScavLib saves the new key to a per-mod `keybinds.json` and reloads it on the
next launch — you never touch that file. The store writes atomically and tolerates a
corrupt file by treating it as empty, so a bad write can't brick a player's binds.

If you register a keybind after settings have already loaded, ScavLib injects the
row (and the persisted or default key) on the spot, so registering from your mod's
`OnEnabled` is fine.

## Querying and polling

Beyond callbacks and events, you can read a bind's state directly:

| Method | Returns |
| --- | --- |
| `KeyBindRegistry.GetKeyCode(owner, localId)` | The currently bound `KeyCode` (`None` if unbound). |
| `GetKeyCodeRaw(fullId)` | Same, by FullId. |
| `IsDown(owner, localId)` / `IsHeld(...)` / `IsUp(...)` | Focus-gated polling, analogous to `Input.GetKeyDown/GetKey/GetKeyUp`. |
| `GetAllRegistered()` | Every registered `KeyBindDefinition`. |

The `IsDown` / `IsHeld` / `IsUp` helpers apply the same focus gate as the events, so
they return `false` while a menu or text field has focus — prefer them over raw
`Input` checks if you poll a bind yourself.

## Managing handlers

Re-registering a keybind under the **same** owner + localId does not overwrite it —
ScavLib **merges** the new `OnPressed` handler into the existing bind and keeps the
original default key and category. That makes accidental double-registration safe,
but means you manage handlers explicitly when you need to remove them:

| Method | Effect |
| --- | --- |
| `KeyBindRegistry.RemoveHandler(owner, localId, action)` | Remove one specific callback. |
| `KeyBindRegistry.ClearHandlers(owner, localId)` | Remove all callbacks from the bind. |
| `KeyBindRegistry.Unregister(owner, localId)` | Remove the bind entirely, including its settings row. |

## Where to next

Keybinds, like commands, usually drive actions your players see — pair their labels
with [localization](i18n.md). To inspect every registered bind and spot two binds
sharing a key, run `scavlib check` (see [commands](commands.md)).

*[KeyBindBuilder]: Fluent builder that defines and registers a keybind.
*[KeyBindDefinition]: The registered description of a keybind: ids, default key, category, handlers, and localized text.
*[KeyBindRegistry]: The registry that stores keybinds and exposes query, polling, and handler-management APIs.
*[KeyBindPressedEvent]: BusEvent fired once when a registered keybind is pressed.
*[KeyBindHeldEvent]: BusEvent fired every frame a registered keybind is held.
*[KeyBindReleasedEvent]: BusEvent fired once when a registered keybind is released.
