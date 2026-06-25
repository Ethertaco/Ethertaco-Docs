---
description: Define custom liquids that fill containers, can be drunk, injected, or used medically.
---

# Custom liquids

A custom liquid is a substance that can fill a [liquid container](items.md) — drunk,
injected, or applied to a limb. Like items, you build one with a fluent builder and
register it under your mod's name. Unlike items, there's no separate "spawn" step:
a liquid exists in the game's liquid registry and is referenced by id wherever a
container holds it.

The flow is **build → register**, and the result is referenced by id from item
`DefaultContents`, recipes, and gameplay code.

```csharp
using ScavLib.liquid;
using UnityEngine;

CustomLiquidBuilder.Create("mymod_moonshine", "MyMod")
    .LocaleName("Moonshine")
    .Tint(new Color(0.9f, 0.85f, 0.5f))
    .ValuePerLiter(8f)
    .OnDrink((amount, body) => PlayerUtil.Feed(amount * 10f))
    .Register();
```

As with items, the two constants are the **id** (unique; convention
`<modname>_<liquidid>`) and the **owner** (your mod's name, for cross-mod safety).

## Creating a liquid

`CustomLiquidBuilder.Create(id, owner)` starts a builder backed by a fresh
`LiquidType`. It begins with sensible defaults you can override: the locale name is
the id, the colour is white, and the value is `1` per litre.

## Properties

| Method | Sets |
| --- | --- |
| `LocaleName(string)` | Display name shown in tooltips and UI. |
| `Tint(Color)` | The liquid's colour. (Named `Tint`, not `Color`, to avoid clashing with the `Color` type.) |
| `ValuePerLiter(float)` | Trade value per litre. |
| `Injectable(bool=true)` | Whether the liquid can be injected. |
| `InjectionSickness(float)` | Sickness applied on injection. |
| `HealthUsable(bool=true)` | Whether it can be used as a medical/health item. |
| `LocaleFromItem(bool=true)` | Take the display name from the containing item instead of `LocaleName`. |
| `MarkDangerous(bool=true)` | Flags the liquid as dangerous (adds it to the game's danger list on register). |
| `Quality(string id, float amount=1f)` | Adds a crafting quality. Call repeatedly to add several. |

## Behaviour callbacks

Two hooks let the liquid do something when consumed:

```csharp
.OnDrink((amount, body) => { /* amount: float, body: Body */ })
.OnHealthUse((amount, limb) => { /* amount: float, limb: Limb */ })
```

`OnDrink` fires when the liquid is drunk and receives the amount and the drinking
`Body`. `OnHealthUse` fires for medical/limb application and receives the amount and
the target `Limb`. Pair `OnHealthUse` with `HealthUsable(true)` (and
`Injectable`/`InjectionSickness` if it's an injectable) so the game offers the
medical-use interaction.

## Registering

End with `Register()`; the overload returns the error text:

```csharp
if (!builder.Register(out string error))
    ScavLibPlugin.Log.LogError($"Liquid failed: {error}");
```

!!! tip "Register in `OnEnabled` — timing is handled"

    Custom liquids are flushed into the game's registry early in item setup —
    before liquid containers build their default contents — so a container that
    pre-fills with your liquid resolves correctly. Register from your mod's
    `OnEnabled` and ScavLib applies it at the right moment. Registering mid-game is
    also supported: the liquid is written into the live registry immediately.

### Ids and ownership

The owner ledger rejects a liquid id that a **different** mod already registered,
with a clear error. Re-registering your own id overwrites your previous definition.

!!! warning "Vanilla-id collisions are not guarded — prefix your ids"

    Unlike the item registry, the liquid registry only checks ownership against
    other ScavLib mods. It does **not** stop you from reusing a *vanilla* liquid id,
    and doing so overwrites that vanilla liquid (last writer wins). Always prefix
    with `<modname>_` unless you deliberately intend to replace a built-in liquid.

## Using the liquid

Once registered, reference the liquid by its id. The most common use is pre-filling
a custom container via the item builder's `DefaultContents`:

```csharp
CustomItemBuilder.Canteen("mymod_flask", "MyMod")
    .Capacity(0.5f)
    .DefaultContents(("mymod_moonshine", 0.5f))   // fill with the custom liquid
    .Register();
```

Because liquids are registered ahead of item default-contents during setup, a flask
and the moonshine that fills it can both be registered in the same `OnEnabled` and
the reference resolves correctly.

!!! note "Multiplayer sync with KrokMP"

    If you register a liquid mid-game while
    [KrokoshaCasualtiesMP](https://github.com/Krokosha666/cas-unk-krokosha-multiplayer-coop)
    is active, ScavLib also syncs it into that mod's network-id table so the liquid
    has a consistent id across LAN co-op. This bridge is best-effort and silently
    does nothing when the multiplayer mod isn't present.

## Queries

`CustomLiquidRegistry.Contains(id)` reports whether a liquid id has been registered
(case-insensitive) — handy for soft integrations that react to another mod's liquid.

## Where to next

The last piece of the content trio is [recipes](recipes.md) — how to make your
custom items and liquids craftable. Containers and their liquid settings live on the
[items](items.md) page.

*[LiquidType]: The game's data object describing a liquid; the builder configures one for you.
*[CustomLiquidBuilder]: Fluent builder that configures a LiquidType and registers a custom liquid.
*[CustomLiquidRegistry]: The shared registry every ScavLib liquid mod registers through.
*[LiquidStack]: A liquid id paired with an amount, used for a container's default contents.
*[KrokoshaCasualtiesMP]: The LAN co-op multiplayer mod ScavLib optionally bridges to.
