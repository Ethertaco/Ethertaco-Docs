---
description: 通过 ScavLib 的 EventBus 订阅世界与玩法事件。
---

# 事件

`EventBus` 是 ScavLib 的中央枢纽,游玩过程中发生的一切都经由它——世界加载、层生成、
物品掉落与拾取。你把一个方法订阅到某个事件类型,该事件被发布时总线就会调用它。
[IModLifecycle](mods.md) 在内部也是这么实现的:生命周期对象不过是一个预先接好线的
总线监听器。

本页内容分布在两个命名空间:`ScavLib.event_bus`(总线、`[Subscribe]` 特性、`BusEvent`
基类)和 `ScavLib.event_bus.events`(各事件类)。

## 订阅

给方法加上 `[Subscribe]`,再注册拥有它的对象。总线会扫描该实例上带特性的方法,
并按参数类型把每个方法接到对应事件上:

```csharp
using ScavLib.event_bus;
using ScavLib.event_bus.events;

public class MyListener
{
    public MyListener()
    {
        EventBus.Register(this);   // 扫描并接好所有 [Subscribe] 方法
    }

    [Subscribe]
    private void OnWorldLoaded(WorldLoadedEvent e)
    {
        PlayerUtil.Feed(50f);
    }
}
```

处理方法必须**恰好一个参数**,且该参数派生自 `BusEvent`。事件类型由这个参数推断——
你不需要在别处再写一遍。`public` 和 `private` 方法都会被扫描,所以你尽可把处理函数设为私有。

!!! note "注册是幂等的"

    把*同一个实例*注册两次并不会让它的处理函数触发两遍——总线会在重新扫描前先清掉该实例
    已有的处理函数。因此从一个可能跨场景重载被多次调用的 `Awake()` 里调用
    `EventBus.Register(this)` 是安全的。

    带 `[Subscribe]` 但签名不对的方法(无参数、多于一个、或参数非 `BusEvent`)会被跳过,
    并在 BepInEx 日志里留下一条警告——某个处理函数始终不触发时去那里查。

要停止接收事件,注销同一个实例:

```csharp
EventBus.Unregister(this);   // 移除该对象拥有的每一个处理函数
```

!!! warning "`[Subscribe]` 不会被重写继承"

    该特性声明为 `Inherited = false`。如果基类方法带 `[Subscribe]`,而子类重写了它,
    这个重写**不会**被识别。请把 `[Subscribe]` 直接加在真正处理事件的那个具体方法上。

## 派发机制

事件被发布时,总线会做三件值得了解的事:

**它沿继承链向上派发。** 发布一个事件,会调用订阅了它**确切运行时类型**的处理函数,
*以及*沿继承链向上、直到 `BusEvent` 的每一个基类型的处理函数。也就是说,订阅某个基类
事件的处理函数会收到它的所有子类型——而订阅 `BusEvent` 本身的处理函数会收到总线上的
**每一个**事件。这正是写全局日志器的惯用方式:

```csharp
[Subscribe]
private void LogEverything(BusEvent e)
{
    ScavLibPlugin.Log.LogInfo($"Event: {e.GetType().Name} @ {e.Timestamp}");
}
```

**它同步调用处理函数,按注册顺序。** 没有队列、没有多线程——`Post` 返回时,每个处理函数
都已执行完毕。顺序取决于各监听器的注册先后。

**它隔离失败。** 每个处理函数跑在 try/catch 里;某个处理函数的异常会被记录(含处理函数名
和事件类型),派发继续走完其余。派发还会对处理函数列表的快照进行迭代,所以处理函数可以在
某事件正被投递的过程中安全地注册或注销监听器。

每个 `BusEvent` 都带一个 `Timestamp`(构造时的 `Time.realtimeSinceStartup` 值),
下列所有事件均可用。

## 内置事件

ScavLib 通过 Harmony 补丁替你发布这些事件。你可以用 `[Subscribe]` 直接订阅,
也可以通过对应的 `IModLifecycle` 回调处理。

| 事件 | 触发时机 | 主要载荷 |
| --- | --- | --- |
| `WorldLoadedEvent` | 世界场景初始化完成、玩家可安全操作时。 | *(无)* |
| `LayerLoadedEvent` | 某层(生物群系)生成完成、可游玩时。 | `BiomeDepth`、`IsFirstLoad` |
| `WorldUnloadingEvent` | 某层即将被拆除前(下潜或退出到主菜单)。 | `CurrentBiomeDepth`、`NextBiomeDepth`、`IsExitToMenu` |
| `WorldDestroyedEvent` | 世界 GameObject 真正被销毁时。 | `LastBiomeDepth`、`WasSaveAndExit` |
| `ItemDroppedEvent` | 物品离开玩家背包、掉进世界之后。 | `Item`、`Slot`、`Body`、`ItemId` |
| `ItemPickedUpEvent` | 物品被拾取进某个背包格之后。 | `Item`、`Slot`、`Body`、`ItemId` |

### 世界生命周期

**`WorldLoadedEvent`** 由 `ConsoleScript.Start()` 的 postfix 发布。它在**你每次进入
世界时触发一次**——*不是*每层一次。在层与层之间下潜不会重触发它(那种切换不会重启
`ConsoleScript`),但退回主菜单后再开一局会**再次**触发。它不带载荷:事件本身就是
"世界现在就绪"的信号。这是首次读取玩家或世界状态的正确位置。

**`LayerLoadedEvent`** 每次某层生成完成时触发,**包括第一层**。由于第一层会同时触发
`WorldLoadedEvent` 和一个 `LayerLoadedEvent`,请用 `IsFirstLoad` 来区分"玩家刚进入
世界"和"玩家下潜了一层"。`BiomeDepth` 是该层的深度,0 为最顶层。

**`WorldUnloadingEvent`** 在当前层即将被拆除前触发——是你在一切被清空前最后一次安全读取
玩家和世界状态的机会。它在下潜和退出主菜单时都会触发;`NextBiomeDepth` 是即将生成的
深度,退出到主菜单时为 `-1`(也通过 `IsExitToMenu` 暴露)。

**`WorldDestroyedEvent`** 在世界对象真正被销毁(场景卸载)时触发。此时世界状态已不存在,
所以只用它做必须跨越换层的全局清理——清空静态缓存、释放原生资源。`WasSaveAndExit` 区分
"退出到主菜单"与其他卸载;`LastBiomeDepth` 是拆除前读到的深度(读不到则为 `-1`)。
按层清理请改用 `WorldUnloadingEvent`。

### 物品

**`ItemDroppedEvent`** 由 `Body.DropItem(Item)` 的 postfix 发布,且在确认掉落确实发生
之后才触发。它携带被丢出的 `Item`(仍存在于世界中)、它原先所在的 `Slot`,以及丢出它的
`Body`。`ItemId` 是物品资源 id 的便捷访问器。

**`ItemPickedUpEvent`** 由 `Body.PickUpItem()` 的 postfix 发布,携带被拾取的 `Item`、
目标 `Slot` 和 `Body`。

!!! note "物品事件对任意 Body 触发,不止玩家"

    两个物品事件都会对执行该动作的那个 `Body` 触发。如今那是玩家,但若游戏将来生成带有
    各自 `Body` 的 NPC,这些事件也会为它们触发。如果你只关心玩家自己的动作,请用
    `e.Body == GameUtil.GetBody()` 加以判断。

## 定义你自己的事件

`EventBus.Post` 是公开的,所以一个 Mod 可以发布自己的事件,供其他 Mod(或它自己的
监听器)消费。继承 `BusEvent`,加上你需要的载荷,然后发布:

```csharp
using ScavLib.event_bus;

public class BossDefeatedEvent : BusEvent
{
    public string BossId { get; }
    public BossDefeatedEvent(string bossId) { BossId = bossId; }
}

// Boss 死亡时:
EventBus.Post(new BossDefeatedEvent("warden"));
```

任何带 `[Subscribe] void OnBoss(BossDefeatedEvent e)` 的监听器都会收到它——而且得益于
沿继承链派发,任何订阅 `BusEvent` 的全局监听器也会收到。

## 诊断

`GetHandlerCount` 报告某个事件类型当前有多少处理函数订阅——可用于 `scavlib` 控制台输出,
或在无人监听时跳过昂贵的载荷准备:

```csharp
if (EventBus.GetHandlerCount<ItemPickedUpEvent>() > 0)
{
    // 只有真的有人会用时才构建载荷。
    EventBus.Post(new ItemPickedUpEvent(item, slot, body));
}
```

!!! warning "它只统计直接订阅者"

    `GetHandlerCount<T>()` 只统计订阅了**确切** `T` 的处理函数。订阅基类型(或 `BusEvent`)
    的处理函数不计入,因为总线是在发布时才解析继承链,而非注册时。因此计数为 `0` 并不能
    保证*没有人*会收到该事件。

## 下一步去哪

事件讲完,你已经掌握了框架核心的两半。从这里开始,挑你 Mod 需要的功能:
[自定义物品](items.md)、[控制台命令](commands.md)、[键位绑定](input.md)
或[存档数据](save.md)。

*[EventBus]: ScavLib 的中央发布/订阅枢纽,用于世界与玩法事件。
*[BusEvent]: 所有事件的抽象基类;携带 Timestamp,也是你继承来定义自己事件的类型。
*[IModLifecycle]: 其回调由 ScavLib 替你接到世界事件上的接口。
*[WorldLoadedEvent]: 在世界场景每次初始化、玩家可安全访问时触发一次。
*[LayerLoadedEvent]: 每次某层生成完成时触发,包括第一层。
*[WorldUnloadingEvent]: 在某层被拆除前触发,下潜或退出到主菜单皆会。
*[WorldDestroyedEvent]: 在世界 GameObject 真正被销毁时触发。
*[ItemDroppedEvent]: 在物品从背包掉入世界之后触发。
*[ItemPickedUpEvent]: 在物品被拾取进某个背包格之后触发。
