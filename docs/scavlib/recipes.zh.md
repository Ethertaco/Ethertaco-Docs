---
description: 用 owner 感知的配方构建器,让你的自定义物品和液体可被制作。
---

# 自定义配方

配方把材料变成产物——而产物可以是自定义[物品](items.md)或[液体](liquids.md)。你用流式
构建器描述它并注册;ScavLib 会在原版配方构建完成后把它追加进游戏的配方列表,并替你处理那些
琐碎的收尾工作(配方索引、"别吃掉自己产物"的守卫、制作 UI 贴图)。

流程与物品、液体一致:**构建 → 注册。**

```csharp
using ScavLib.recipe;

RecipeBuilder.Create("mymod_super_bandage", "MyMod")
    .Category(Recipes.RecipeCategory.Medicine)
    .RequireINT(5)
    .Ingredient("bandage", minCondition: 0.9f)
    .IngredientByQuality("disinfectant", amount: 30f, isLiquid: true)
    .Register();
```

## 创建配方

先确定产物类型:

| 工厂 | 产物 |
| --- | --- |
| `RecipeBuilder.Create(resultId, owner)` | 一个固体物品。默认:数量 `1`、产物耐久 `1`。 |
| `RecipeBuilder.CreateLiquid(resultId, owner, resultCondition)` | 一个液体产物。 |

`resultId` 是被产出的东西——通常是你的某个自定义 id。`owner` 是你的 Mod 名。新配方默认处于
`Materials` 分类,无 INT 要求。

## 配方设置

| 方法 | 效果 |
| --- | --- |
| `RequireINT(int)` | 配方所需的 INT 技能等级。 |
| `Category(Recipes.RecipeCategory)` | 出现在哪个制作页签下(如 `Materials`、`Medicine`)。 |
| `Amount(int)` | 产出多少个产物。 |
| `IsRepair(bool=true)` | 标记为维修配方。 |
| `SpecialKnown(bool=true)` | 无视 INT 始终可见。通常配方在 INT 达到"所需值减 3"前保持隐藏;用于教程或始终已知的配方。 |
| `DontDrainResultLiquid(bool=true)` | 保留制作出的容器里的液体。默认容器产物生成时为空;当你的配方意在产出一个*已填充*的容器时设置它。 |

## 材料

匹配材料有两种方式,而且区别很重要:

```csharp
.Ingredient("scrapmetal", minCondition: 0.9f)              // 匹配特定物品 id
.IngredientByQuality("water", amount: 50f, isLiquid: true) // 匹配任何带某品质标签的东西
```

`Ingredient` 匹配**精确的物品(或液体)id**。`IngredientByQuality` 匹配**任何携带某制作品质
标签的物品**——所以一个"需要 50 单位 water 品质"的材料会接受任何提供该品质的液体。两者都接收
一个 `destroy` 标志(默认 `true`),控制材料是否被消耗。

!!! warning "`minCondition` 有两种含义"

    对**固体**材料,`minCondition` *既是*耐久阈值*也是*消耗量——游戏做的是
    `condition -= minCondition`。`0.9` 是原版"消耗一个"的常用值;`0` 表示"任意耐久、不消耗"。

    对**液体**材料(`isLiquid: true`),所需/抽取的量是毫升数——在 `Ingredient` 上是
    `minCondition`,在 `IngredientByQuality` 上是 `amount`。把这两者搞混是最常见的配方 bug,
    所以请明确哪个材料是液体。

## 注册

最后调用 `Register()`。若配方有有效的 result id 并已入队则返回 `true`,否则返回 `false`
(并记录一条错误)。

!!! tip "在 `OnEnabled` 里注册"

    入队的配方会在游戏构建完自己的配方列表后紧接着被追加,所以提早注册——在你 Mod 的
    `OnEnabled` 里——是正确的。ScavLib 会在那一刻清空它的队列,因此即便之后配方列表再次被
    构建,同一配方也绝不会被追加两次。

ScavLib 在那次追加中替你做了两件事,省得你操心:

- **产物贴图。** 产物是已注册自定义物品的配方,会在制作 UI 中自动显示该物品的贴图。(原版会
  试图按 id 加载一个 prefab,对自定义 id 会失败。)
- **"别吃掉自己产物"。** 每个材料的内部 ignore-id 会被设为 result id(对非维修配方而言),
  这样配方就不会把先前制作出的同名产物副本当材料消耗——与原版行为一致。

!!! note "配方的 `owner` 仅供参考"

    与物品和液体注册中心不同,配方注册中心不拒绝跨 Mod 的 id 冲突——配方只是被追加进一个列表,
    并不按 id 索引。你传入的 `owner` 仅用于日志。多个 Mod 可自由添加配方,包括产出相同产物的
    配方。

## 实例:制作一个已填充的容器

把三页内容串起来——一个从[物品](items.md)制作自定义水壶、并用[液体](liquids.md)的自定义
私酒填充它的配方:

```csharp
RecipeBuilder.Create("mymod_flask", "MyMod")
    .Category(Recipes.RecipeCategory.Materials)
    .RequireINT(2)
    .Ingredient("scrapmetal", minCondition: 0.9f)               // 一块废金属
    .IngredientByQuality("mymod_moonshine", amount: 0.5f, isLiquid: true)
    .DontDrainResultLiquid()                                     // 保持已填充
    .Register();
```

要改为制作一个自定义**液体**,用 `CreateLiquid`:

```csharp
RecipeBuilder.CreateLiquid("mymod_moonshine", "MyMod", resultCondition: 1f)
    .RequireINT(4)
    .Ingredient("mymod_mash", minCondition: 0.9f)
    .Register();
```

## 下一步去哪

这就完成了内容三件套——物品、液体与配方。从这里开始,文档转向面向玩家的系统:
[控制台命令](commands.md)、[键位绑定](input.md)、[本地化](i18n.md)与[存档数据](save.md)。
要在制作出的自定义物品上持久化每实例状态,见[存档](save.md)。

*[RecipeBuilder]: 带 owner 感知、有守卫的制作配方流式构建器。
*[CustomRecipeRegistry]: 把入队的自定义配方追加进游戏配方列表的注册中心。
*[Recipe]: builder 所配置的游戏配方数据对象。
*[RecipeItem]: 配方中的单个材料,按精确 id 或按品质匹配。
*[CraftingQuality]: 一个标签与数量的配对,用于按品质而非精确 id 匹配材料。
