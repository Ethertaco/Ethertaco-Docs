---
description: 定义可填充容器、可饮用、可注射或可作医疗用途的自定义液体。
---

# 自定义液体

自定义液体是一种可以填充[液体容器](items.md)的物质——可饮用、注射,或施用于肢体。
和物品一样,你用流式构建器创建它,并以你的 Mod 名注册。与物品不同的是,液体没有单独的
"生成"步骤:它存在于游戏的液体注册表中,在任何容器盛放它的地方通过 id 被引用。

流程是**构建 → 注册**,其结果可被物品的 `DefaultContents`、配方以及玩法代码按 id 引用。

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

和物品一样,两个常量是 **id**(唯一;约定 `<modname>_<liquidid>`)和 **owner**
(你的 Mod 名,用于跨 Mod 安全)。

## 创建液体

`CustomLiquidBuilder.Create(id, owner)` 启动一个以全新 `LiquidType` 为底的 builder。
它带有可覆盖的合理默认值:locale 名为 id、颜色为白色、每升价值为 `1`。

## 属性

| 方法 | 设置 |
| --- | --- |
| `LocaleName(string)` | 在提示框和 UI 中显示的名称。 |
| `Tint(Color)` | 液体的颜色。(命名为 `Tint` 而非 `Color`,以避免与 `Color` 类型冲突。) |
| `ValuePerLiter(float)` | 每升的交易价值。 |
| `Injectable(bool=true)` | 液体是否可注射。 |
| `InjectionSickness(float)` | 注射时施加的不适。 |
| `HealthUsable(bool=true)` | 是否可作为医疗/健康物品使用。 |
| `LocaleFromItem(bool=true)` | 从盛放它的物品取显示名,而非用 `LocaleName`。 |
| `MarkDangerous(bool=true)` | 将液体标记为危险(注册时加入游戏的危险列表)。 |
| `Quality(string id, float amount=1f)` | 添加一项制作品质。可多次调用以添加多项。 |

## 行为回调

两个钩子让液体在被消耗时做点事:

```csharp
.OnDrink((amount, body) => { /* amount: float, body: Body */ })
.OnHealthUse((amount, limb) => { /* amount: float, limb: Limb */ })
```

`OnDrink` 在液体被饮用时触发,接收用量和饮用的 `Body`。`OnHealthUse` 在医疗/肢体施用时
触发,接收用量和目标 `Limb`。把 `OnHealthUse` 与 `HealthUsable(true)` 配合(若是可注射物
还配 `Injectable`/`InjectionSickness`),游戏才会提供医疗使用交互。

## 注册

用 `Register()` 结束;重载会返回错误文本:

```csharp
if (!builder.Register(out string error))
    ScavLibPlugin.Log.LogError($"Liquid failed: {error}");
```

!!! tip "在 `OnEnabled` 里注册——时机已处理"

    自定义液体会在物品 setup 早期被刷入游戏注册表——早于液体容器构建其默认内容物——所以一个
    用你的液体预填充的容器能正确解析。从你 Mod 的 `OnEnabled` 注册,ScavLib 会在恰当时刻应用
    它。中途注册也受支持:液体会被立即写入实时注册表。

### id 与归属

owner 账本会以明确错误拒绝**另一个** Mod 已注册的液体 id。重新注册你自己的 id 会覆盖你
先前的定义。

!!! warning "不防撞原版 id——请给 id 加前缀"

    与物品注册中心不同,液体注册中心只对其他 ScavLib Mod 做归属检查。它**不会**阻止你复用
    某个*原版*液体 id,这样做会覆盖那个原版液体(last-writer 胜)。除非你有意替换某个内置
    液体,否则请始终用 `<modname>_` 前缀。

## 使用液体

注册后,按 id 引用液体。最常见的用途是通过物品 builder 的 `DefaultContents` 预填充一个
自定义容器:

```csharp
CustomItemBuilder.Canteen("mymod_flask", "MyMod")
    .Capacity(0.5f)
    .DefaultContents(("mymod_moonshine", 0.5f))   // 用自定义液体填充
    .Register();
```

由于在 setup 期间液体先于物品默认内容物注册,一个水壶和填充它的私酒可以在同一个 `OnEnabled`
里一起注册,引用也能正确解析。

!!! note "与 KrokMP 的联机同步"

    如果你在游戏中途、且
    [KrokoshaCasualtiesMP](https://github.com/Krokosha666/cas-unk-krokosha-multiplayer-coop)
    已激活时注册液体,ScavLib 还会把它同步进该 Mod 的网络 id 表,使液体在 LAN 联机中拥有
    一致的 id。这个桥接是尽力而为的,联机 Mod 不存在时会静默地什么都不做。

## 查询

`CustomLiquidRegistry.Contains(id)` 报告某个液体 id 是否已注册(不区分大小写)——便于对
另一个 Mod 液体作出反应的软集成。

## 下一步去哪

内容三件套的最后一块是[配方](recipes.md)——如何让你的自定义物品和液体可被制作。容器及其
液体设置位于[物品](items.md)页。

*[LiquidType]: 游戏中描述一种液体的数据对象;builder 替你配置一个。
*[CustomLiquidBuilder]: 配置 LiquidType 并注册自定义液体的流式构建器。
*[CustomLiquidRegistry]: 每个 ScavLib 液体 Mod 都通过它注册的共享注册中心。
*[LiquidStack]: 一个液体 id 与用量的配对,用于容器的默认内容物。
*[KrokoshaCasualtiesMP]: ScavLib 可选桥接的 LAN 联机合作 Mod。
