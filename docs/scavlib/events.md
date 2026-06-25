---
description: Subscribe to world and gameplay events through ScavLib's EventBus.
---

# Events

The `EventBus` is ScavLib's central hub for everything that happens during play —
the world loading, layers generating, items being dropped and picked up. You
subscribe a method to an event type, and the bus calls it whenever that event is
posted. Internally this is how [IModLifecycle](mods.md) works too: the lifecycle
object is just a pre-wired bus listener.

Everything here lives in two namespaces: `ScavLib.event_bus` (the bus, the
`[Subscribe]` attribute, the `BusEvent` base) and `ScavLib.event_bus.events` (the
event classes).

## Subscribing

Mark a method with `[Subscribe]` and register the object that owns it. The bus
scans the instance for annotated methods and wires each one to the event type in
its parameter:

```csharp
using ScavLib.event_bus;
using ScavLib.event_bus.events;

public class MyListener
{
    public MyListener()
    {
        EventBus.Register(this);   // scan & wire all [Subscribe] methods
    }

    [Subscribe]
    private void OnWorldLoaded(WorldLoadedEvent e)
    {
        PlayerUtil.Feed(50f);
    }
}
```

A handler method must take **exactly one parameter**, and that parameter must
derive from `BusEvent`. The event type is inferred from that parameter — you never
name it anywhere else. Both `public` and `private` methods are scanned, so keep
handlers private if you like.

!!! note "Registration is idempotent"

    Registering the *same instance* twice does not double-fire its handlers — the
    bus strips that instance's existing handlers before re-scanning. This makes it
    safe to call `EventBus.Register(this)` from an `Awake()` that may run more than
    once across scene reloads.

    A method tagged `[Subscribe]` with the wrong signature (no parameter, more than
    one, or a non-`BusEvent` parameter) is skipped with a warning in the BepInEx
    log — check there if a handler never fires.

To stop receiving events, unregister the same instance:

```csharp
EventBus.Unregister(this);   // removes every handler owned by this object
```

!!! warning "`[Subscribe]` is not inherited by overrides"

    The attribute is declared with `Inherited = false`. If a base class method
    carries `[Subscribe]` and a subclass overrides it, the override is **not**
    picked up. Put `[Subscribe]` directly on the concrete method that should
    handle the event.

## How dispatch works

When an event is posted, the bus does three things worth knowing about:

**It dispatches up the inheritance chain.** Posting an event invokes handlers
registered for its exact runtime type *and* for every base type up to `BusEvent`.
That means a handler subscribed to a base event type receives all of its
subtypes — and a handler subscribed to `BusEvent` itself receives **every** event
on the bus. This is the idiomatic way to write a catch-all logger:

```csharp
[Subscribe]
private void LogEverything(BusEvent e)
{
    ScavLibPlugin.Log.LogInfo($"Event: {e.GetType().Name} @ {e.Timestamp}");
}
```

**It calls handlers synchronously, in registration order.** There is no queue and
no threading — by the time `Post` returns, every handler has run. Order follows
when each listener was registered.

**It isolates failures.** Each handler runs inside a try/catch; an exception in one
handler is logged (with the handler name and event type) and dispatch continues to
the rest. Dispatch also iterates over a snapshot of the handler list, so a handler
may safely register or unregister listeners while an event is being delivered.

Every `BusEvent` carries a `Timestamp` (the `Time.realtimeSinceStartup` value when
it was constructed), available on all events below.

## Built-in events

ScavLib posts these for you via Harmony patches. Subscribe to them directly with
`[Subscribe]`, or handle them through the matching `IModLifecycle` callback.

| Event | Fires when | Key payload |
| --- | --- | --- |
| `WorldLoadedEvent` | The world scene has finished initializing and the player is safe to touch. | *(none)* |
| `LayerLoadedEvent` | A layer (biome) has finished generating and is playable. | `BiomeDepth`, `IsFirstLoad` |
| `WorldUnloadingEvent` | Just before a layer is torn down (descent or quit-to-menu). | `CurrentBiomeDepth`, `NextBiomeDepth`, `IsExitToMenu` |
| `WorldDestroyedEvent` | The world GameObject is actually being destroyed. | `LastBiomeDepth`, `WasSaveAndExit` |
| `ItemDroppedEvent` | After an item leaves the player's inventory into the world. | `Item`, `Slot`, `Body`, `ItemId` |
| `ItemPickedUpEvent` | After an item is picked up into an inventory slot. | `Item`, `Slot`, `Body`, `ItemId` |

### World lifecycle

**`WorldLoadedEvent`** is posted from the postfix of `ConsoleScript.Start()`. It
fires **once each time you enter the world** — *not* once per layer. Descending
between layers does not re-fire it (those transitions don't restart
`ConsoleScript`), but quitting to the menu and starting a new run will fire it
again. It carries no payload: the event itself is the "world is ready now" signal.
This is the correct place to first read player or world state.

**`LayerLoadedEvent`** fires every time a layer finishes generating, **including
the first one**. Because the first layer triggers both `WorldLoadedEvent` and a
`LayerLoadedEvent`, use `IsFirstLoad` to tell "the player just entered the world"
apart from "the player descended a level." `BiomeDepth` is the layer's depth, where
0 is the top layer.

**`WorldUnloadingEvent`** fires just before the current layer is torn down — your
last safe chance to read player and world state before everything is cleared. It
fires both on descent and on quit-to-menu; `NextBiomeDepth` is the depth about to
generate, or `-1` when exiting to the menu (also exposed as `IsExitToMenu`).

**`WorldDestroyedEvent`** fires when the world object is actually destroyed (the
scene unloading). By this point world state is already gone, so use it only for
global cleanup that must outlive layer transitions — clearing static caches,
disposing native resources. `WasSaveAndExit` distinguishes a quit-to-menu from
other unloads; `LastBiomeDepth` is the depth read just before teardown (`-1` if it
couldn't be read). For per-layer cleanup, prefer `WorldUnloadingEvent` instead.

### Items

**`ItemDroppedEvent`** is posted from the postfix of `Body.DropItem(Item)`, after
the drop is confirmed to have actually happened. It carries the dropped `Item`
(still alive in the world), the `Slot` it came from, and the `Body` that dropped
it. `ItemId` is a convenience accessor for the item's resource id.

**`ItemPickedUpEvent`** is posted from the postfix of `Body.PickUpItem()`, carrying
the picked-up `Item`, the destination `Slot`, and the `Body`.

!!! note "Item events fire for any Body, not just the player"

    Both item events fire for whichever `Body` performed the action. Today that's
    the player, but if the game ever spawns NPCs with their own `Body`, these
    events will fire for them too. If you only care about the player's own actions,
    gate on `e.Body == GameUtil.GetBody()`.

## Defining your own events

`EventBus.Post` is public, so a mod can publish its own events for other mods (or
its own listeners) to consume. Inherit `BusEvent`, add whatever payload you need,
and post it:

```csharp
using ScavLib.event_bus;

public class BossDefeatedEvent : BusEvent
{
    public string BossId { get; }
    public BossDefeatedEvent(string bossId) { BossId = bossId; }
}

// When the boss dies:
EventBus.Post(new BossDefeatedEvent("warden"));
```

Any listener with `[Subscribe] void OnBoss(BossDefeatedEvent e)` will receive it,
and — thanks to inheritance-chain dispatch — so will any `BusEvent` catch-all
listener.

## Diagnostics

`GetHandlerCount` reports how many handlers are subscribed to an event type —
useful for the `scavlib` console output, or to skip expensive payload preparation
when nobody is listening:

```csharp
if (EventBus.GetHandlerCount<ItemPickedUpEvent>() > 0)
{
    // Only build the payload if someone will use it.
    EventBus.Post(new ItemPickedUpEvent(item, slot, body));
}
```

!!! warning "It counts direct subscribers only"

    `GetHandlerCount<T>()` counts handlers subscribed to **exactly** `T`. Handlers
    subscribed to a base type (or to `BusEvent`) are not counted, because the bus
    resolves the inheritance chain at post time, not at registration. A count of
    `0` therefore does not guarantee that *no one* would receive the event.

## Where to next

With events covered, you have the two halves of the framework's core. From here,
pick the feature your mod needs: [custom items](items.md), [console
commands](commands.md), [keybinds](input.md), or [save data](save.md).

*[EventBus]: ScavLib's central publish/subscribe hub for world and gameplay events.
*[BusEvent]: Abstract base class for every event; carries a Timestamp and is the type you inherit to define your own.
*[IModLifecycle]: Interface whose callbacks ScavLib wires to the world events for you.
*[WorldLoadedEvent]: Fired once each time the world scene initializes and the player is safe to access.
*[LayerLoadedEvent]: Fired each time a layer finishes generating, including the first.
*[WorldUnloadingEvent]: Fired just before a layer is torn down, on descent or quit-to-menu.
*[WorldDestroyedEvent]: Fired when the world GameObject is actually destroyed.
*[ItemDroppedEvent]: Fired after an item is dropped from an inventory into the world.
*[ItemPickedUpEvent]: Fired after an item is picked up into an inventory slot.
