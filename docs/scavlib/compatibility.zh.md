---
description: ScavLib 如何与联机 Mod 及其他物品框架共存。
---

# 兼容性

ScavLib 的兼容性是**自动且内部的**——本页没有要调用的 API。它的存在是为了让你理解 ScavLib 在
幕后做了什么:它如何把自定义内容桥接进联机,以及当另一个物品框架与它并存时它如何表现。了解这些
主要用于诊断异常行为和写出好的 bug 报告。

## 联机(KrokMP)

ScavLib 把
[KrokoshaCasualtiesMP](https://github.com/Krokosha666/cas-unk-krokosha-multiplayer-coop)
——那个 LAN 合作 Mod——当作**软依赖**。如果它没安装,什么都不会发生,你的 Mod 照常在单人模式
运行。如果它装了,ScavLib 会在启动时检测到它,并激活一个桥接,让你的自定义内容能在网络上工作,
**而你无需任何额外工作**。该桥接处理:

- **生成** —— 当联机在某个玩家身上生成自定义物品(例如通过它的 give 命令)时,请求会被路由到
  ScavLib 自己的生成路径,弹药与枪械状态会被填好,拾取 / 容器装载也会被处理。
- **网络同步** —— 这是关键修复。联机通常通过按 id 加载 prefab 来重建一个网络对象,这对没有
  prefab 的自定义 id 会失败。ScavLib 拦截该同步,从模板实例化物品,注入自定义 id、tag 和
  `OnSpawn` 钩子,并把它登记进联机对象表——于是自定义物品在每个客户端上都正确出现。
- **对象校验** —— 自定义物品被标记为网络相关,这样联机 Mod 不会把它们误当作游离对象而销毁。
- **存档位置** —— 在联机会话运行期间,[伴生存档文件](save.md)会被写进联机存档文件夹而非单人
  位置,使合作存档把自定义物品数据保存在一起。

自定义液体也被桥接:在联机激活时注册的液体会被同步进它的网络 id 表(见[液体](liquids.md))。

!!! note "从你自己的 Mod 检测联机"

    ScavLib 的桥接是内部的——你不调用它。如果你自己的代码需要知道联机 Mod 是否在场,直接查
    BepInEx:`Chainloader.PluginInfos.ContainsKey("KrokoshaCasualtiesMP")`,或对其 GUID 声明一个
    软 `[BepInDependency]`。

## 与其他物品框架共存

可以同时安装不止一个自定义物品框架。ScavLib 被设计为在那种情况下做个**好公民**,但任何框架在这里
能做的事都有一个诚实的上限。

ScavLib 的设计刻意把自己的足迹保持得很小:

- 它的生成补丁以**低优先级**运行,所以其他框架的补丁先跑;
- 它只认领**它自己**注册的 id——不对每次生成做全局拦截;
- 它从不 patch 那些宽泛的共享入口(`Body`、`Recipe.fullName`、`SaveSystem`、`BuildingEntity`),
  把冲突面积保持到最小。

它**不**做的,是试图调和两个争抢同一全局入口的框架——那确实无法自动解决。取而代之,当 ScavLib
在启动时检测到一个已知的共存框架(例如 RshLib),它会记录一条醒目的警告,让原因从日志里一目了然。

!!! warning "若装了另一个框架后自定义物品出问题"

    两个框架间重复的 id 或互斥的生成 override 无法自动修复。如果自定义物品出毛病、而你又装了另一个
    物品框架,那种共存很可能就是原因——查 BepInEx 日志里的共存警告,并在任何 bug 报告中提到它。

## 诊断

游戏内的 `scavlib check` 命令(见[命令](commands.md))是查看现状最快的方式:它把每个 ScavLib
Harmony 补丁列为 `[OK]` 或 `[FAIL]`,立刻显示某个补丁是否被冲突挡掉。结合上面描述的启动警告,
通常第一眼就能定位兼容性问题。

## 至此一览完毕

你现在已经看过 ScavLib 提供的每个系统——从[注册 Mod](mods.md) 和[响应世界](events.md),经过
[自定义内容](items.md)、[面向玩家的功能](commands.md)与[持久化](save.md),到[工具类](utilities.md)
助手和这一层兼容性。若你想动手构建,[总览](index.md)会把它们串在一起。

*[KrokoshaCasualtiesMP]: ScavLib 作为软依赖桥接的 LAN 合作联机 Mod。
*[CustomItemTag]: 每个生成的自定义物品上的组件;联机桥接用它来保持物品的网络相关性。
*[Utils.Create]: 游戏的生成方法;ScavLib 以低优先级、且只为自己的 id patch 它。
