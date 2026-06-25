---
description: 面向玩家生命体征、肢体、物品与技能的 null 安全助手。
---

# 工具类

ScavLib 的 `util` 命名空间是一组静态助手类,把游戏的玩家、肢体、物品与技能内部封装在一个安全、
一致的接口之后。它们共享一个让你在任何地方调用都很舒服的保证:

!!! note "这里的一切都是 null 安全的"

    每个方法无论是否加载了世界都能工作。读取返回安全默认值(`0`、`false`、`null`),没有玩家时
    写入是空操作——它们都不会抛 `NullReferenceException`。你可以在主菜单调用它们而无需加判断。

这些类是 `PlayerUtil`(玩家生命体征、状态、恢复)、`LimbUtil`(逐肢体健康)、`ItemUtil`(世界
中的物品)和 `SkillUtil`(三项属性)。世界/玩家入口、物品生成与控制台输出——[`GameUtil`](gameutil.md)
——有它自己的页面。

## 两条写入路径

在改动玩家或技能状态之前,最重要的一点是:ScavLib 提供**两种写入方式**,它们的行为差别很大:

- **推荐路径**尊重游戏自身的逻辑——动画、音效与副作用都会像变化自然发生那样触发。
  `PlayerUtil.Feed`、`Hydrate`、`HealAll` 以及 `SkillUtil.AddExperience` 属于这一类。
- **Raw 路径**,即每个带 `Raw` 后缀的方法,会用 `Mathf.Clamp` 限制到游戏的有效范围后**直接写
  底层字段**,并**绕过所有游戏逻辑**。`SetHungerRaw`、`SetLevelRaw` 等属于这一类。

优先用推荐路径。只有当你确实需要设一个精确值而不触发正常后果时,才动用 `Raw`——并且要清楚那个
字段的作用。

## `PlayerUtil`

玩家助手分散在若干区域,但都在同一个 `PlayerUtil` 类上。

### 背包

| 方法 | 作用 |
| --- | --- |
| `GiveItem(id)` | 在玩家处生成一个物品并自动拾取。返回该 `GameObject`。 |
| `TakeItem(id)` | 丢弃第一个匹配该 id 的背包物品。返回是否找到。 |
| `HasItem(id)` | 玩家身上任意位置是否携带该 id。 |
| `GetAllItems()` | 玩家表层背包中的每个物品。 |
| `FindItemById(id, out item)` / `FindItemByTag(tag, out item)` | 定位一个携带的物品。 |

### 读取生命体征

`PlayerUtil` 为每项受追踪的生命体征都暴露一个 `Get*` 读取器——`GetHunger`、`GetThirst`、
`GetStamina`、`GetEnergy`、`GetHeartRate`、`GetBloodPressure`、`GetBloodOxygen`、
`GetTemperature`、`GetConsciousness`、`GetHappiness` 等等,外加派生读数如
`GetBloodVolumePercentage`、`GetTempDiffFromNormal`、`GetBloodPressureReadout`。它们都遵循
`Get<Vital>()` 命名模式,在游玩之外返回 `0`。

### 状态查询

对玩家当前状况的布尔检查:`IsAlive`、`IsConscious`、`IsDying`、`IsInCardiacArrest`、`IsSleeping`、
`IsInWater`、`IsStanding`、`IsCrouching`、`IsExercising`、`HasScubaGear`、`CanTakeNap`、
`AllowUseItem` 等——没有玩家时各自返回 `false`。在外观、药物、睡眠与背水一战区域还有成组查询
(`IsDisfigured`、`HasPainkillers`、`GetBadSleepAmount`、`GetLastStandTime` 等)。

### 恢复(推荐写法)

| 方法 | 效果 |
| --- | --- |
| `Feed(amount)` | 降低饥饿。 |
| `Hydrate(amount)` | 降低口渴。 |
| `RestoreStamina(amount)` / `RestoreEnergy(amount)` | 补充耐力 / 精力。 |
| `HealAll(body)` | 完全恢复给定的 body。 |

### Raw 写入

每项生命体征都有一个 `Set<Vital>Raw(value)`,在其限制范围内直接写字段。数量很多——`SetHungerRaw`、
`SetHeartRateRaw`、`SetBloodPressureRaw`、`SetConsciousnessRaw` 等等,也包括布尔状态如
`SetSleepingRaw`。如上所述,它们绕过游戏逻辑;请审慎使用。

### 阈值

`PlayerUtil.Thresholds` 持有游戏 moodle 系统用作边界的每个值的命名常量——直接从游戏中提取,
让你的 Mod 与其 UI 保持一致。用它们代替硬编码的魔法数字:

```csharp
if (PlayerUtil.GetBloodOxygen() < PlayerUtil.Thresholds.BLOOD_OXYGEN_LOW)
    GameUtil.Alert("Oxygen low!");
```

它们涵盖血压、血氧、心率、体温、出血速度等,每项都有命名分级(如
`TEMPERATURE_HYPOTHERMIA_SEVERE`、`HEART_RATE_TACHYCARDIA_MILD`)。

## `LimbUtil`

逐肢体健康,可按索引、`LimbSlot` 或名称寻址:

| 方法 | 作用 |
| --- | --- |
| `GetLimb(index)` / `GetLimb(slot)` / `GetLimbByName(name)` | 取一个肢体。 |
| `GetAllLimbs()` | 每个肢体。 |
| `HasBrokenBone()` / `HasDislocation()` / `HasInfection()` / `HasDismemberment()` | 全身范围的状况检查。 |
| `GetMaxInfection()` / `GetAveragePain()` / `GetTotalBleedSpeed()` | 聚合读数。 |
| `HealLimb(limb)` / `HealLimb(index)` | 完全治愈一个肢体(推荐路径)。 |
| `DamageSkin(limb, amount)` / `DamageMuscle(limb, amount)` | 施加伤害。 |
| `SetSkinHealthRaw` / `SetMuscleHealthRaw` / `SetBleedRaw` / `SetPainRaw` / `SetInfectionRaw` | 逐肢体的 Raw 字段写入。 |

## `ItemUtil`

面向世界中的物品(区别于玩家背包)的助手:

| 方法 | 作用 |
| --- | --- |
| `FindNearby(center, radius, includeContained=false)` | 半径内的所有物品。可选包含容器内的物品。 |
| `FindClosest(center, maxRadius=∞, includeContained=false)` | 最近的物品。 |
| `SetCondition(item, condition)` / `Repair(item)` | 调整耐久。 |
| `SetFavourited(item, bool)` | 切换收藏标志。 |
| `Destroy(item)` | 从世界中移除一个物品。 |
| `GetInfo(id)` / `IsKnownId(id)` / `GetAllIds()` | 查找物品定义,包括自定义的。 |

## `SkillUtil`

三项角色属性通过 `SkillType` 枚举寻址——`Strength`、`Resilience`、`Intelligence`(值与游戏自身
索引一致):

| 方法 | 作用 |
| --- | --- |
| `GetLevel(skill)` | 当前等级(游玩之外为 `0`)。 |
| `GetExperience(skill)` | 绝对 XP。 |
| `GetExperienceInLevel(skill)` / `GetExperienceForNextLevel(skill)` | 当前等级内的 XP / 到下一级所需。 |
| `GetProgress(skill)` | 到下一级的进度,`0`–`1`。 |
| `AddExperience(skill, xp)` | 以正常方式给予 XP(推荐路径)。 |
| `SetLevelRaw(skill, level)` | 直接强制一个等级(Raw 路径)。 |

`SkillUtil.XpMultiplier` 暴露当前的全局 XP 倍率。

```csharp
SkillUtil.AddExperience(SkillType.Intelligence, 25f);
int intLevel = SkillUtil.GetLevel(SkillType.Intelligence);
```

## 下一步去哪

这是功能页面的最后一页。[兼容性](compatibility.md)讲解 ScavLib 如何与联机 Mod 共存,
以及如何检测与其他框架的冲突。

*[PlayerUtil]: 面向玩家生命体征、状态、背包与恢复的静态助手。
*[LimbUtil]: 面向逐肢体健康与伤情的静态助手。
*[ItemUtil]: 面向查找与修改世界中物品的静态助手。
*[SkillUtil]: 面向三项角色属性(力量、韧性、智力)的静态助手。
*[SkillType]: 命名三项属性的枚举;值与游戏内部索引一致。
*[GameUtil]: 世界/玩家入口、物品生成与控制台助手类,在它自己的页面中讲解。
