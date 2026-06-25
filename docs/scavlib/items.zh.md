---
description: 通过克隆一个原版模板并只覆盖你需要的字段来定义自定义物品。
---

# 自定义物品

ScavLib 创建自定义物品的方式,是**克隆一个原版物品作为模板**,再在其上应用你的覆盖。
你永远不用从零构造 `ItemInfo`——挑一个最接近的原版物品(手枪、水壶、头盔),改你在意的
字段,给它一个 id 和贴图,然后注册。每个 Mod 都通过同一个共享注册中心注册,所以两个 Mod
不会悄无声息地破坏彼此的物品。

流程永远一致:**构建 → 注册 → 生成。**

```csharp
using ScavLib.item;

CustomItemBuilder.Canteen("mymod_flask", "MyMod")   // 克隆水壶
    .DisplayName("Old Flask")
    .Description("A dented metal flask.")
    .Sprite(flaskSprite)
    .Capacity(0.5f)
    .DefaultContents(("mymod_moonshine", 0.5f))      // 一种自定义液体
    .Register();
```

有两个参数无处不在:**id**(唯一字符串;约定为 `<modname>_<itemid>`)和 **owner**
(你的 Mod 名,用于跨 Mod 冲突安全)。

## 选择模板

克隆来源是一个 `ItemTemplate`——原版物品的枚举,每项映射到一个游戏资源 id。把它传给
`CustomItemBuilder.Create(id, owner, template)`,或使用某个命名工厂快捷方式:

```csharp
CustomItemBuilder.Create("mymod_thing", "MyMod", ItemTemplate.FoodSimple);
CustomItemBuilder.Pistol("mymod_holdout", "MyMod");   // 等同于 Create(..., ItemTemplate.Pistol)
```

命名工厂覆盖了常见场景:武器(`Pistol`、`Rifle`、`Shotgun`、`Magazine`、`Explosive`)、
装备(`SmallBattery`/`MediumBattery`/`LargeBattery`、`Canteen`、`Flashlight`、`Backpack`),
以及一大批可穿戴物(`Helmet`、`Hoodie`、`Shirt`、`TorsoArmor`、`Belt`、`Boots`、`Gloves`、
`Goggles`、`Balaclava` 等)。若枚举未覆盖你想要的模板,也可以把原始资源 id 字符串传给
`Create(id, owner, "resourceid")`。

!!! note "克隆是深拷贝且不污染原版"

    注册时会深克隆模板的 `ItemInfo`,保留其真实子类型——`LiquidItemInfo` 仍是
    `LiquidItemInfo`,`BatteryInfo` 仍是 `BatteryInfo`——并重新克隆其列表字段。你的覆盖
    绝不会改动原始原版物品。少数枚举项有意共用同一资源(例如 `Helmet` 和 `BikeHelmet` 都
    映射到自行车头盔),所以命名工厂只是底层模板上一个易读的别名。

## 配置物品

所有 setter 都返回 builder,可以链式调用。它们分为几组。

### 核心属性

这些直接写到克隆后的 `ItemInfo` 上。

| 方法 | 设置 |
| --- | --- |
| `Category(string)` | 战利品/生成分类。也决定物品加入哪个掉落池。 |
| `Weight(float)` / `Value(int)` | 背包重量与交易价值。 |
| `SlotRotation(float)` | 物品在背包格中的旋转。 |
| `Combineable(bool=true)` | 副本是否堆叠/合并。 |
| `DecayMinutes(float)` / `RotSpeed(float)` / `DecayInfo(...)` | 腐坏。`DecayInfo` 接收 `ItemInfo.DecayType` 标志值或原始 `byte`。 |
| `DestroyAtZeroCondition(bool=true)` | 耐久归零时销毁物品。 |
| `ScaleWeightWithCondition(bool=true)` | 重量随耐久变化。 |
| `OnlyHoldInHands(bool=true)` | 只能持握,不能收进格子。 |
| `AutoAttack(bool=true)` / `UsableWithLMB(bool=true)` / `IgnoreDepression(bool=true)` | 战斗/使用标志。 |
| `Tags(params string[])` | 物品标签(拼成原版的逗号分隔形式)。 |
| `Recognition(int)` | 识别等级。 |
| `Quality(string id, float amount=1f)` | 添加一项制作品质。可多次调用以添加多项。 |

### 使用动作

`Usable` 和 `UsableOnLimb` 挂上物品被使用时游戏运行的回调。各带一个 `replace` 标志:

```csharp
.Usable((body, item) => PlayerUtil.Feed(20f))            // replace=true(默认):覆盖原版
.Usable((body, item) => DoExtra(body), replace: false)   // 追加:原版先跑,然后是你的
```

`replace: false` 时,原版使用动作先跑、你的随后——各自包了一层,一个抛异常不会阻止另一个。

### 可穿戴

| 方法 | 用途 |
| --- | --- |
| `Wearable(VanillaLimb, VanillaWearSlot, float armor=0, float isolation=0)` | 一站式:标记可穿戴、设置肢体 + 槽位,并可选设护甲/隔热。 |
| `WearSlot(VanillaLimb, VanillaWearSlot)` | 只设肢体 + 槽位。 |
| `WearableArmor(float)` / `WearableIsolation(float)` | 防护数值。 |
| `WearableHitDurabilityLossMultiplier(float)` | 每次受击的耐久损耗。 |
| `WearableVisualOffset(int)` / `WearableCanBeHeld(bool=true)` / `JumpHeightMultChange(float)` | 视觉与移动微调。 |

请用 `VanillaLimb` 和 `VanillaWearSlot` 枚举而非原始字符串——游戏按名称查找肢体和槽位,
枚举(及其 `ToName()` / `ToSlotId()` 映射)能避免你悄悄把 `"uptorso"` 打错。共用同一穿戴
槽位的物品在游戏中互斥。

### 液体与电池模板

这些只在对应模板类型上才有意义:

| 方法 | 适用于 |
| --- | --- |
| `Capacity(float)` | 液体容器(`Canteen`、`WaterContainer` 等) |
| `AutoFill(bool=true)` | 液体容器 |
| `DefaultContents(params (string liquidId, float amount)[])` | 液体容器——生成时预填充 |
| `MaxCharge(float)` | 电池 |

!!! warning "用错模板时,类别专属 setter 会被静默跳过"

    `Capacity`、`MaxCharge` 之类映射到只存在于 `LiquidItemInfo` / `BatteryInfo` 上的字段。
    如果你在并非该子类型的模板上调用它们,覆盖字段找不到,ScavLib 会**打一条警告然后继续**
    ——物品仍会注册,只是没有那个属性。若某个液体或电池设置看起来没生效,请查 BepInEx 日志,
    确认你的模板确实克隆了液体/电池物品。

### 运行时组件调参

有些属性位于只存在于生成实例上的 MonoBehaviour,而非 `ItemInfo`。这些 setter 会注册一个
**`OnSpawn` 钩子**,在实例创建后配置该组件:

| 方法 | 触及的组件 |
| --- | --- |
| `AmmoType(GunScript.AmmoType)` | `AmmoScript` / `GunScript` |
| `AmmoMaxRounds(int)` | `AmmoScript` |
| `GunMagCapacity(int)` / `GunShotsPerFire(int)` / `GunVerticalSpread(float)` | `GunScript` |
| `GunDamage(float structureDamage, float animalDamage)` | `GunScript` |
| `GunSprites(normal, racked, normalNoMag, rackedNoMag)` | `GunScript` |
| `ContainerCapacity(float maxWeight, float maxWeightPerItem)` | `Container` |
| `ContainerTagRestriction(params string[])` | `Container` |
| `ContainerItemsVisible(bool=true)` / `ContainerEncumberance(float)` | `Container` |

每个钩子都会对其组件做 null 检查,所以在非枪械物品上调用枪械 setter 是无害的(它只是找不到
`GunScript`)。

### 名称、描述与你自己的生成钩子

`DisplayName(string)` 和 `Description(string)` 设置英文文本(英文显示名会成为物品的
`fullName`)。传入 `IDictionary<string,string>` 重载可一次提供多种语言;这些会流入 ScavLib
的[本地化](i18n.md)系统。最后,`OnSpawn(Action<GameObject>)` 添加你自己的生成后钩子——
它在上述所有内置组件钩子**之后**、且在实例 `Awake` **之后**运行。

## 注册

用 `Register()` 结束链式调用。无参形式返回 `bool`;一个重载会给你错误文本:

```csharp
if (!builder.Register(out string error))
    ScavLibPlugin.Log.LogError($"Item failed: {error}");
```

!!! tip "随时注册——时机由 ScavLib 处理"

    自定义物品只能在游戏物品表(`Item.SetupItems`)跑完后才能完成注册。如果你在那之前注册
    ——例如在 Mod 的 `OnEnabled` 里——builder 会**把自己延迟并返回 `true`**,ScavLib 会在
    物品表就绪后自动重试。你**不需要**等 `OnWorldLoaded`。`OnEnabled` 是推荐的位置。

    物品表加载后,已注册物品会被注入游戏的 `GlobalItems`、初始化标签、并重建战利品池——所以
    一个带 `Category` 的自定义物品会自动出现在该分类的掉落中。游戏中途注册(物品表已加载后)
    同样有效,并会就地重建战利品池。

### id 与归属

**owner** 账本正是让多个物品 Mod 能安全共存的关键:

- **同 owner、同 id** → 视作幂等覆盖(以警告记录)。这正是让你的 Mod 能跨局重新准备物品而
  不报错的机制。
- **不同 owner、同 id** → 以明确错误拒绝。别的 Mod 不能抢你的 id,你也不能抢它们的。
- **无前缀** → 物品仍会注册,但 ScavLib 会警告你。遵循 `<modname>_<itemid>` 约定,从源头
  避免冲突。

!!! danger "绝不要自己 patch `Utils.Create`"

    ScavLib 在低优先级下只 patch 一次游戏的生成方法,并按 id 分发。如果你的 Mod 也去 patch
    `Utils.Create`,你就重新引入了单一注册中心设计本要防止的那种框架冲突问题。请通过
    `CustomItemBuilder` 注册,让 ScavLib 掌管生成路径。

## 生成

已注册物品通过游戏正常的 `Utils.Create(id, …)`、用你的 id 生成——不需要任何特殊的 ScavLib
调用。自定义 id 也会被加入 `spawn` 控制台命令的自动补全,所以你可以在游戏里 `spawn
mymod_flask` 来测试。

底层的生成补丁会克隆模板 prefab,换上你的 id、贴图和一个 `CustomItemTag`,并处理一个微妙的
顺序问题:若干原版组件在其 `Awake` 里读取物品数据,而 `Awake` 在克隆体激活的瞬间就运行。
ScavLib 把那个 `Awake` 挂起,直到你的 id **到位之后**才执行,这样那些组件读到的是*你的*
`ItemInfo` 而非模板的。随后你的 `OnSpawn` 钩子在 `Awake` 之后、实例完全初始化的状态下运行一次。

## 每实例数据

每个生成的自定义物品都带一个 `CustomItemTag` MonoBehaviour。它持有 `CustomItemId`、`Owner`,
以及一个用于存放逐副本变化状态的自由格式 `InstanceData` 数据袋:

```csharp
var tag = go.GetComponent<CustomItemTag>();
tag.Set("charges", 3);
if (tag.TryGet<int>("charges", out var n)) { /* ... */ }
```

这是附加每实例数据的受支持方式——物品 id 本身保持干净,而这正是让 ScavLib 的 patch 面积
保持很小的原因。

## 查询注册中心

`CustomItemRegistry` 暴露简单的查找:

| 方法 | 返回 |
| --- | --- |
| `Contains(id)` | `bool`(不区分大小写)。 |
| `TryGet(id, out CustomItem)` | 已注册的定义。 |
| `GetOwner(id)` | 拥有它的 Mod 名,或 `null`。 |
| `GetAllIds()` | 所有已注册 id。 |
| `GetAllRegistered()` | `(id, owner)` 对。 |

!!! note "`RegisterItem(id, ItemInfo)` 已废弃"

    旧的 `CustomItemRegistry.RegisterItem` 重载仍为源码兼容而保留,但标记了 `[Obsolete]`:
    它只能注册一个*定义*,永远无法生成实例。新代码请用 `CustomItemBuilder`。

## 下一步去哪

自定义物品常常配套自定义[配方](recipes.md)来制作它们,以及自定义[液体](liquids.md)来
填充它们——这正是接下来两页。上面提到的显示名与描述本地化,见 [i18n](i18n.md)。

*[ItemInfo]: 游戏中描述一个物品的数据对象;ScavLib 克隆一个原版的作为你的模板。
*[ItemTemplate]: 你可克隆的原版物品枚举,每项映射到一个游戏资源 id。
*[CustomItemBuilder]: 克隆模板、应用覆盖并注册自定义物品的流式构建器。
*[CustomItem]: 一个 builder 的不可变结果——自定义物品的已注册定义。
*[CustomItemRegistry]: 每个 ScavLib 物品 Mod 都通过它注册的那个单一共享注册中心。
*[CustomItemTag]: 附加到每个生成的自定义物品上的 MonoBehaviour,携带其 id、owner 与每实例数据。
*[VanillaLimb]: 原版肢体名称的类型化枚举,用于可穿戴物的放置。
*[VanillaWearSlot]: 原版穿戴槽位 id 的类型化枚举;共用一个槽位的物品互斥。
*[LiquidItemInfo]: 液体容器的 ItemInfo 子类型(容量、默认内容物)。
*[BatteryInfo]: 电池的 ItemInfo 子类型(最大电量)。
