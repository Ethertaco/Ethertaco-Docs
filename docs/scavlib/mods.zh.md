---
description: 把你的 Mod 注册进 ScavLib API,并接入它的世界生命周期。
---

# Mod 与生命周期

每个支持 ScavLib 的 Mod,第一步都是向注册中心**声明自己**。这样做能带来三样东西:
你的 Mod 会出现在游戏内 `scavlib` 诊断信息里、其他 Mod 能发现并依赖你、而且——只要你
提供一个生命周期对象——ScavLib 就会替你驱动代码走完世界的加载/卸载流程。

注册只需在插件的 `Awake()` 里调用一次。本页所有内容都围绕 `ModRegistry.Register` 展开。

## 注册一个 Mod

最简形式只需一个 `ModInfo`:

```csharp
using ScavLib.mods;

ModRegistry.Register(
    new ModInfo("My Mod", "1.0.0", "Does a thing.", "You"));
```

这会记录该 Mod 并执行一次建议性的依赖检查,但**不会**把你接入任何事件。要响应世界,
再传入一个生命周期对象:

```csharp
ModRegistry.Register(
    new ModInfo("My Mod", "1.0.0", "Does a thing.", "You"),
    new MyLifecycle());      // 见下文「生命周期」
```

`Register` 依次做这些事:构建一个 session、存储它、按名称建立索引、把生命周期(如果有)
接入 [EventBus]、执行依赖检查、打印一行确认日志,最后触发 `OnEnabled()`。

!!! note "它绝不会朝你抛异常"

    `Register(null)` 是静默空操作。重名会打印警告但仍然注册成功。而且每个生命周期回调
    都跑在 try/catch 里——你自己 `OnWorldLoaded` 里的异常会以你的 Mod 名记进日志后被吞掉,
    不会拖垮 ScavLib 或其他 Mod。如果某个回调看起来"什么都没干",请查 BepInEx 日志。

## `ModInfo`

`ModInfo` 是描述你 Mod 的不可变元数据。三个构造函数,逐级链向最具体的那个:

| 构造函数 | 适用场景 |
| --- | --- |
| `ModInfo(name, version, description)` | 无依赖。`author` 默认 `"Unknown"`。 |
| `ModInfo(name, version, description, author)` | 最常见的情况。 |
| `ModInfo(name, version, description, author, VersionedDependency[])` | 声明带版本的依赖。 |

另有一个接收 `string[]` 的旧版重载(用于 0.4.x 兼容,仅传依赖名),内部会转换成
`VersionedDependency`。

| 属性 | 说明 |
| --- | --- |
| `Name` | 用于查找和依赖解析的标识。匹配时**不区分大小写**。 |
| `Version` | 自由格式字符串;仅在做版本范围检查时才会被宽松解析。 |
| `Description` | 一句话简介。 |
| `Author` | 传 `null` 时回退为 `"Unknown"`。 |
| `VersionedDependencies` | 声明的依赖(可为空)。 |
| `Dependencies` | 向后兼容垫片,以 `string[]` 返回依赖**名称**。 |

!!! warning "注册名是 `ScavLib`,不是 `ScavLib API`"

    ScavLib API 以名称 **`ScavLib`** 注册自己(`com.kanisuko.scavlib` 是 BepInEx 的
    GUID;`ScavLib` 是注册名)。当你声明对它的依赖时,要用 `"ScavLib"`——产品的显示名
    (`ScavLib API`)并不是注册中心用来匹配的那个名字。

## 生命周期

把一个 `IModLifecycle` 传给 `Register`,ScavLib 就会替你把它的回调订阅到世界事件上——
不用调 `EventBus.Register`,也不用写 `[Subscribe]` 特性。最省事的实现方式是继承
`ModLifecycleBase`,它为每个回调提供空实现,让你只重写需要的部分:

```csharp
using ScavLib.event_bus.events;
using ScavLib.mods;

public class MyLifecycle : ModLifecycleBase
{
    public override void OnWorldLoaded(WorldLoadedEvent e)
    {
        // 此处可安全操作玩家。
    }

    public override void OnLayerLoaded(LayerLoadedEvent e)
    {
        if (e.IsFirstLoad)
            ScavLibPlugin.Log.LogInfo("Entered the world.");
        else
            ScavLibPlugin.Log.LogInfo($"Descended to depth {e.BiomeDepth}.");
    }
}
```

### 回调及其触发时机

| 回调 | 触发时机 | 事件载荷 |
| --- | --- | --- |
| `OnEnabled()` | `Register` 成功后立即触发。 | — |
| `OnWorldLoaded(e)` | **每局一次**,世界首次加载完成时。 | `WorldLoadedEvent`(无字段) |
| `OnLayerLoaded(e)` | 每次某层生成完成时,**包括第一层**。 | `LayerLoadedEvent.BiomeDepth`、`.IsFirstLoad` |
| `OnWorldUnloading(e)` | 某层被拆除前——下潜**和**退出到主菜单都会触发。 | `WorldUnloadingEvent.CurrentBiomeDepth`、`.NextBiomeDepth`、`.IsExitToMenu` |
| `OnWorldDestroyed(e)` | 场景真正卸载时。此时世界状态已不存在。 | `WorldDestroyedEvent` |
| `OnDisabled()` | 保留——见下方注意事项。 | — |

一次典型的下潜流程:`OnEnabled` → `OnWorldLoaded` → `OnLayerLoaded`(第一层) →
`OnWorldUnloading` → `OnLayerLoaded`(下一层) → … → `OnWorldDestroyed`。

!!! danger "不要在 `Awake()` 或 `OnEnabled()` 里操作玩家"

    两者都在**世界存在之前**运行。在那里读取 `PlayerCamera.main` 或
    `WorldGeneration.world` 会抛 `NullReferenceException`。`OnEnabled` 适合做*不*需要
    世界的、依赖 ScavLib 的初始化(注册命令、物品、键位)。要读取玩家或世界状态,
    请等到 `OnWorldLoaded` / `OnLayerLoaded`。

!!! warning "`OnDisabled()` 目前不会被调用"

    它所属的启用/禁用系统仍在开发中。本版本**没有任何代码调用 `OnDisabled()`**——
    连关闭时也不会——所以**不要**依赖它做清理或释放资源。如果你需要在世界拆除时清理,
    请改用 `OnWorldUnloading` 或 `OnWorldDestroyed`。

#### `OnLayerLoaded` 与 `OnWorldLoaded` 的区别

`OnWorldLoaded` 恰好触发一次,即本局世界首次可游玩时。`OnLayerLoaded` 对*每一*层都触发
——包括第一层——所以 `IsFirstLoad` 就是你用来区分"玩家刚进入世界"和"玩家下潜了一层"的
依据。如果你的逻辑只关心进入游戏,用 `OnWorldLoaded`;如果关心每个生物群系,用
`OnLayerLoaded`。

### 更想用 `[Subscribe]`?

生命周期对象只是 [EventBus] 之上的一层便利封装。如果你更想把处理函数写在插件里,
就注册一个普通 `ModInfo`,自己订阅:

```csharp
ModRegistry.Register(new ModInfo("My Mod", "1.0.0", "Does a thing.", "You"));
EventBus.Register(this);

[Subscribe]
private void OnWorldLoaded(WorldLoadedEvent e) { /* ... */ }
```

两条路通向同一批事件。生命周期对象更适合较大的 Mod;少量处理函数时,内联 `[Subscribe]`
就够了。完整事件目录见 [事件](events.md)。

## 声明依赖

`VersionedDependency` 记录一个名称和可选的版本范围:

```csharp
ModRegistry.Register(new ModInfo(
    "My Mod", "1.0.0", "Needs ScavLib 0.8 or newer.", "You",
    new[]
    {
        new VersionedDependency("ScavLib", minVersion: "0.8.0"),
        // 上下界都是可选的:
        new VersionedDependency("SomeOtherMod", "1.2.0", "2.0.0"),
    }));
```

ScavLib 会在注册时检查它们,若依赖缺失或版本落在范围外,就打印一条警告。

!!! important "依赖检查只是建议,不强制"

    检查**绝不阻止加载**——它只往日志写警告。有两个后果值得理解:

    - **它对顺序敏感。** 检查只看你 `Register` 运行时*已经注册*的内容。如果你的依赖在
      你*之后*才注册,你会收到一条"尚未注册"的警告,即便它其实能正常加载。要保证真正的
      加载顺序,请用 BepInEx 的 `[BepInDependency("their.guid")]`——那才是权威机制;
      `VersionedDependency` 只是叠在上面的一层软性、信息性的标注。
    - **版本解析 fail-open。** 版本会被宽松解析(末尾的 `-beta` 或 `+build` 后缀会被
      去掉,单个 `1` 会变成 `1.0`)。如果某个版本串完全无法解析,范围检查会被**跳过**并
      视为满足,同时打印警告。所以"检查通过"并不是硬保证。

## 查询注册中心

Mod 注册之后,你可以在运行时检视它们——这对软集成很有用("如果存在 Mod X,就启用功能 Y")。

| 方法 | 返回 |
| --- | --- |
| `GetAll()` | 按注册顺序返回 `IReadOnlyList<ModInfo>`。 |
| `TryFind(name, out info)` | 找到则返回 `true` + 该 `ModInfo`(不区分大小写)。 |
| `IsRegistered(name)` | `bool`,不区分大小写。 |
| `GetLifecycle(mod)` | 该 Mod 的 `IModLifecycle`,若注册时未提供则为 `null`。 |
| `HasLifecycle(mod)` | `bool`。 |
| `GetSession(name)` | 该 `ModSession`,或 `null`。 |

```csharp
if (ModRegistry.IsRegistered("SomeOtherMod"))
{
    // 点亮一个可选集成。
}
```

!!! note "重名时解析到第一个注册的"

    允许重名(带警告)。所有副本都会出现在 `GetAll()` 里,但按名查找——`TryFind`、
    `IsRegistered`、`GetSession`——永远只看到该名下**第一个**注册的 Mod。请保持 Mod 名
    唯一以避免歧义。

## `ModSession`

`GetSession(name)` 返回一个已注册 Mod 背后的运行时记录。本版本中它是一个只读数据容器,
暴露 `Info`、`Lifecycle`,以及一个**永远为 `true`** 的 `IsEnabled` 标志——它当初设计要
配合的启用/禁用操作尚未开放。如今它主要用于诊断。

## 下一步去哪

现在你已经注册了一个 Mod 并让它响应世界。接下来,[事件](events.md) 会讲解你能订阅的全部
事件——包括物品掉落与拾取——以及 `EventBus` 的派发机制。

*[EventBus]: ScavLib 的中央发布/订阅枢纽,用于世界与玩法事件。
*[ModInfo]: 描述一个已注册 Mod 的不可变元数据(名称、版本、描述、作者、依赖)。
*[IModLifecycle]: 其回调由 ScavLib 在世界生命周期各阶段自动调用的接口。
*[ModLifecycleBase]: 抽象基类,为每个 IModLifecycle 回调提供空实现,让你只重写需要的部分。
*[ModSession]: 一个已注册 Mod 的运行时记录:其 ModInfo、生命周期与启用状态。
*[VersionedDependency]: 一条依赖声明,含名称及可选的 min/max 版本上下界。
*[WorldLoadedEvent]: 在世界加载完成、玩家可安全访问时触发一次。
*[LayerLoadedEvent]: 每次某层生成完成时触发,包括第一层。
*[WorldUnloadingEvent]: 在某层被拆除前触发,下潜或退出到主菜单皆会。
*[WorldDestroyedEvent]: 在世界场景真正卸载时触发。