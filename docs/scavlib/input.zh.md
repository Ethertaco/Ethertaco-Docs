---
description: 注册会出现在游戏输入设置中、可持久化、并触发回调或事件的键位。
---

# 键位绑定

ScavLib 键位会出现在游戏自己的**输入设置页签**里,跨会话记住玩家的重绑,并在按下时通知你的
Mod——通过一个便捷回调,或通过事件。你用构建器定义它、注册它,然后响应它。

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

两个标识定义一个键位:**owner**(你的 Mod 名)和一个在你 Mod 内唯一的 **localId**。
ScavLib 把它们合成一个经过 sanitize 的 **FullId**(`owner_localId`)——这就是你在 `scavlib check`
和键位事件里会看到的 id。

## 构建器参考

| 方法 | 用途 |
| --- | --- |
| `Create(ownerModName, localId)` | 启动一个构建器。 |
| `Default(KeyCode)` | 默认键。省略它(或 `KeyCode.None`)即以未绑定状态发布。 |
| `DisplayName(string)` / `DisplayName(dict)` | 设置行中的标签。字典重载可提供多种语言;两者都流入[本地化](i18n.md)。 |
| `Description(string)` / `Description(dict)` | 更长的描述文本,同样可本地化。 |
| `Category(string)` | 输入页签中该行上方的分组标题。原样渲染——想要装饰自己加(`"─── My Mod ───"`、`"[ My Mod ]"` 等)。共用同一分类字符串的键位会归在一个标题下。 |
| `OnPressed(Action)` | 每次按下时触发的回调(见下)。 |
| `Register()` / `Register(out error)` | 完成并注册。返回 `bool`。 |

## 响应键位

有两种响应方式,任选其一或两者都用。

**`OnPressed` 回调**最简单——每次按键时运行一次,已经受焦点门控(见下),没有事件总线的中转:

```csharp
.OnPressed(() => DoDash())
```

**事件**给你按下、长按、松开三种,并让任何对象都能用 `[Subscribe]` 订阅。它们位于
`ScavLib.input.events_`:

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

| 事件 | 触发 |
| --- | --- |
| `KeyBindPressedEvent` | 按键按下那一帧,一次。 |
| `KeyBindHeldEvent` | 按键被按住的每一帧——慎用。 |
| `KeyBindReleasedEvent` | 按键松开那一帧,一次。 |

每个事件都以 `Bind` 暴露 `KeyBindDefinition`,外加快捷属性 `FullId`、`OwnerModName`、
`LocalId`。按 `OwnerModName` + `LocalId` 过滤,是识别哪个键位触发的最清晰方式。

!!! warning "玩家忙碌时键位会被抑制"

    回调和三个事件都受焦点门控:在设置菜单打开、控制台打开、游戏暂停、或有文本输入框获得焦点时,
    它们**都不会**触发。这能避免玩家在输入控制台命令或重绑按键时误触发键位。你的处理函数可以
    假定玩家确实处于游玩中。

## 设置菜单与持久化

已注册的键位会自动出现在游戏的输入设置页签里,位于它的 `Category` 标题下,显示其本地化名称。
当玩家在那里重绑时,ScavLib 会把新键保存到每个 Mod 一份的 `keybinds.json`,并在下次启动时
重新加载——你永远不用碰那个文件。该存储原子写入,并对损坏文件以"视为空"的方式容错,所以一次
坏的写入不会毁掉玩家的绑定。

如果你在设置已加载之后才注册键位,ScavLib 会就地注入该行(以及持久化或默认的键),所以从你
Mod 的 `OnEnabled` 注册没有问题。

## 查询与轮询

除了回调和事件,你还可以直接读取一个绑定的状态:

| 方法 | 返回 |
| --- | --- |
| `KeyBindRegistry.GetKeyCode(owner, localId)` | 当前绑定的 `KeyCode`(未绑定则为 `None`)。 |
| `GetKeyCodeRaw(fullId)` | 同上,按 FullId。 |
| `IsDown(owner, localId)` / `IsHeld(...)` / `IsUp(...)` | 受焦点门控的轮询,类比 `Input.GetKeyDown/GetKey/GetKeyUp`。 |
| `GetAllRegistered()` | 每个已注册的 `KeyBindDefinition`。 |

`IsDown` / `IsHeld` / `IsUp` 助手施加与事件相同的焦点门控,所以在菜单或文本框获得焦点时它们
返回 `false`——若你自己轮询某个绑定,优先用它们而非裸的 `Input` 检查。

## 管理回调

在**相同的** owner + localId 下重新注册一个键位**不会**覆盖它——ScavLib 会把新的 `OnPressed`
回调**合并**进已有绑定,并保留原来的默认键和分类。这让意外的重复注册是安全的,但也意味着当你
需要移除回调时,要显式管理它们:

| 方法 | 效果 |
| --- | --- |
| `KeyBindRegistry.RemoveHandler(owner, localId, action)` | 移除某一个特定回调。 |
| `KeyBindRegistry.ClearHandlers(owner, localId)` | 移除该绑定的所有回调。 |
| `KeyBindRegistry.Unregister(owner, localId)` | 整个移除该绑定,包括它的设置行。 |

## 下一步去哪

键位和命令一样,通常驱动玩家能看到的动作——把它们的标签与[本地化](i18n.md)搭配。要检视每个
已注册绑定、并发现两个绑定共用一个键,运行 `scavlib check`(见[命令](commands.md))。

*[KeyBindBuilder]: 定义并注册一个键位的流式构建器。
*[KeyBindDefinition]: 一个键位的已注册描述:各 id、默认键、分类、回调与本地化文本。
*[KeyBindRegistry]: 存储键位并暴露查询、轮询与回调管理 API 的注册中心。
*[KeyBindPressedEvent]: 注册键位被按下时触发一次的 BusEvent。
*[KeyBindHeldEvent]: 注册键位被按住的每一帧触发的 BusEvent。
*[KeyBindReleasedEvent]: 注册键位被松开时触发一次的 BusEvent。
