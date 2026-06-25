---
description: Make your custom items and liquids craftable with owner-aware recipe builders.
---

# Custom recipes

A recipe turns ingredients into a result — and the result can be a custom
[item](items.md) or [liquid](liquids.md). You describe one with a fluent builder and
register it; ScavLib appends it to the game's recipe list after the vanilla recipes
are built, and handles the finicky bookkeeping (recipe indexing, the "don't eat your
own output" guard, the crafting-UI sprite) for you.

The flow mirrors items and liquids: **build → register.**

```csharp
using ScavLib.recipe;

RecipeBuilder.Create("mymod_super_bandage", "MyMod")
    .Category(Recipes.RecipeCategory.Medicine)
    .RequireINT(5)
    .Ingredient("bandage", minCondition: 0.9f)
    .IngredientByQuality("disinfectant", amount: 30f, isLiquid: true)
    .Register();
```

## Creating a recipe

Pick the result type up front:

| Factory | Result |
| --- | --- |
| `RecipeBuilder.Create(resultId, owner)` | A solid item. Defaults: amount `1`, result condition `1`. |
| `RecipeBuilder.CreateLiquid(resultId, owner, resultCondition)` | A liquid result. |

`resultId` is what gets produced — usually one of your custom ids. `owner` is your
mod's name. A new recipe starts in the `Materials` category with no INT requirement.

## Recipe settings

| Method | Effect |
| --- | --- |
| `RequireINT(int)` | INT skill level the recipe needs. |
| `Category(Recipes.RecipeCategory)` | Which crafting tab it appears under (e.g. `Materials`, `Medicine`). |
| `Amount(int)` | How many of the result are produced. |
| `IsRepair(bool=true)` | Marks the recipe as a repair recipe. |
| `SpecialKnown(bool=true)` | Always visible regardless of INT. Normally a recipe stays hidden until INT reaches its requirement minus 3; use this for tutorial or always-known recipes. |
| `DontDrainResultLiquid(bool=true)` | Keep the liquid in the crafted container. By default a container result spawns empty; set this when your recipe is meant to produce a *filled* container. |

## Ingredients

There are two ways to match an ingredient, and the difference matters:

```csharp
.Ingredient("scrapmetal", minCondition: 0.9f)              // match a specific item id
.IngredientByQuality("water", amount: 50f, isLiquid: true) // match anything with a quality tag
```

`Ingredient` matches an **exact item (or liquid) id**. `IngredientByQuality` matches
**any item carrying a crafting-quality tag** — so a "needs 50 of water-quality"
ingredient accepts any liquid that provides that quality. Both take a `destroy` flag
(default `true`) controlling whether the ingredient is consumed.

!!! warning "`minCondition` means two different things"

    For a **solid** ingredient, `minCondition` is *both* the durability threshold and
    the amount consumed — the game does `condition -= minCondition`. `0.9` is the
    common vanilla "consume one" value; `0` means "any condition, consume nothing."

    For a **liquid** ingredient (`isLiquid: true`), the amount required/drained is the
    millilitre figure — `minCondition` on `Ingredient`, or `amount` on
    `IngredientByQuality`. Mixing these up is the most common recipe bug, so be
    explicit about which ingredient is a liquid.

## Registering

Call `Register()` last. It returns `true` if the recipe had a valid result id and was
queued, `false` (with a logged error) otherwise.

!!! tip "Register in `OnEnabled`"

    Queued recipes are appended right after the game finishes building its own recipe
    list, so registering early — in your mod's `OnEnabled` — is correct. ScavLib
    drains its queue at that point and clears it, so a recipe is never appended twice
    even if the recipe list is set up again later.

Two things ScavLib does for you during that append, so you don't have to:

- **Result sprite.** A recipe whose result is a registered custom item shows that
  item's sprite in the crafting UI automatically. (Vanilla would try to load a prefab
  by id and fail for a custom id.)
- **"Don't eat your own output."** Each ingredient's internal ignore-id is set to the
  result id (for non-repair recipes), so the recipe won't consume a previously-crafted
  copy of its own result as an ingredient — matching vanilla behaviour.

!!! note "`owner` is informational for recipes"

    Unlike the item and liquid registries, the recipe registry does not reject
    cross-mod id collisions — recipes are simply appended to a list, not keyed by id.
    The `owner` you pass is used for logging only. Multiple mods can freely add
    recipes, including recipes that produce the same result.

## Worked example: craft a filled container

Combining the three content pages — a recipe that crafts the custom flask from
[items](items.md), filled with the custom liquid from [liquids](liquids.md):

```csharp
RecipeBuilder.Create("mymod_flask", "MyMod")
    .Category(Recipes.RecipeCategory.Materials)
    .RequireINT(2)
    .Ingredient("scrapmetal", minCondition: 0.9f)               // one scrap metal
    .IngredientByQuality("mymod_moonshine", amount: 0.5f, isLiquid: true)
    .DontDrainResultLiquid()                                     // keep it filled
    .Register();
```

To craft a custom **liquid** instead, use `CreateLiquid`:

```csharp
RecipeBuilder.CreateLiquid("mymod_moonshine", "MyMod", resultCondition: 1f)
    .RequireINT(4)
    .Ingredient("mymod_mash", minCondition: 0.9f)
    .Register();
```

## Where to next

That completes the content trio — items, liquids, and recipes. From here the docs
move to player-facing systems: [console commands](commands.md), [keybinds](input.md),
[localization](i18n.md), and [save data](save.md). For persisting per-instance state
on a crafted custom item, see [save](save.md).

*[RecipeBuilder]: Fluent builder for a crafting recipe with an owner-aware, guarded API.
*[CustomRecipeRegistry]: The registry that appends queued custom recipes to the game's recipe list.
*[Recipe]: The game's recipe data object the builder configures.
*[RecipeItem]: A single ingredient within a recipe, matched by exact id or by quality.
*[CraftingQuality]: A tag-and-amount pair used to match ingredients by quality rather than exact id.
