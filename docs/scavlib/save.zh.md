---
description: 自定义物品自动持久化;实现一个接口即可保存每实例数据。
---

# 存档数据

自定义物品在保存和重载后会**自动**留存——你不用写任何存档代码,自定义物品就会回到玩家离开时
的位置、耐久原样保留。你唯一要实现的只是一个接口,而且仅当某个物品携带你想持久化的额外每实例
状态时才需要。

ScavLib 把数据存进原版存档旁边的一个伴生文件里,绝不写进原版存档内部,所以玩家的主存档永不
处于风险中。

## 自动持久化如何工作

游戏自己的存档系统处理不了自定义物品:它通过按 id 加载 prefab 来重载每个已存物品,而自定义 id
没有这样的 prefab。放任不管的话,原版存档会悄悄丢弃你的物品——或者更糟,让其内部索引错位,
污染重力袋之类容器的内容物。

ScavLib 彻底绕开了这点。就在游戏保存之前,它会 detach 场景里的每个自定义物品(包括嵌套在容器
内的),让原版存档只对它能理解的物品干净地运行,再把它们 reattach,并把自定义物品的记录写进
伴生文件。加载时,它会重生每个自定义物品并放回原位。对每个物品,它会持久化:

- **身份** —— 自定义物品 id 和拥有它的 Mod;
- **位置** —— 世界位置与旋转,或它所在的容器 / 手持 / 穿戴槽位;
- **状态** —— 耐久与收藏标志;
- **你的每实例 blob**,下面会讲。

这些你都不用调。像往常一样注册你的物品(见[物品](items.md)),它们就会持久化。

## 每实例数据:`ICustomItemSaveable`

当一个物品实例携带自己的状态——剩余次数、已配置的模式、一个存储值——在一个 MonoBehaviour 上
实现 `ICustomItemSaveable`,并通过 `OnSpawn` 把它挂到物品上:

```csharp
using UnityEngine;
using ScavLib.save;
using ScavLib.item;

public class FlaskState : MonoBehaviour, ICustomItemSaveable
{
    public int charges = 3;

    public string Save() => charges.ToString();   // 返回 null 表示不持久化任何东西

    public void Load(string blob)
    {
        if (int.TryParse(blob, out var n)) charges = n;
    }
}

// 物品生成时挂上它:
CustomItemBuilder.Canteen("mymod_flask", "MyMod")
    .OnSpawn(go => go.AddComponent<FlaskState>())
    .Register();
```

契约很小:

- `Save()` 返回一个**不透明字符串**——JSON、CSV、一个裸数字,随你。返回 `null` 表示"无可持久化",
  blob 会被省略。
- `Load(blob)` 在**物品重生之后、玩家可与之交互之前调用一次**,传入 `Save()` 当初产出的那个
  确切字符串。
- 两个方法抛异常都会被捕获并记录,绝不向外传播——一个行为不端的物品不会破坏其余所有物品的加载。

这正是持久化你在 [`CustomItemTag`](items.md#每实例数据) 上设置的每实例 `InstanceData` 的受支持
方式:在 `Save()` 里序列化它,在 `Load()` 里还原它。

## 当拥有它的 Mod 缺失时

如果一份存档含有某个自定义物品、而它的 Mod 在加载时未安装,ScavLib 不会丢弃它。它会用一个占位
原样保留原始记录,使下一次保存能让这份数据原封不动地往返——**重装该 Mod 即可完整恢复物品**。
临时移除某个 Mod 的玩家不会丢失任何与之相关的东西。

## 伴生文件

ScavLib 的数据存放在游戏持久化数据文件夹里、原版存档旁边的 `save.scavlib.sv` 中。它是带版本化
schema 的 GZip 压缩 JSON,与原版存档的存储风格一致。

!!! note "它永远不会破坏玩家存档"

    失败策略是刻意单向的。**读取**失败(伴生文件缺失或损坏)被当作"无伴生数据"——和全新存档完全
    一样——所以坏文件会优雅降级而非崩溃。**写入**失败会被记录但绝不抛出,因为丢失伴生数据远好过
    中断玩家的主存档。加载成功后伴生文件会被删除,与原版存档被消费的方式一致。

自定义**配方**进度(某配方是否曾被制作过)也持久化在同一文件里,所以自定义配方会跨存档记住它的
"首次制作"状态。

## 持久化其他 Mod 数据

这套系统专用于**自定义物品实例**(以及配方进度)。伴生文件中**没有**面向任意 Mod 全局状态的
公开通用键值存储。对于设置或与世界无关的数据,请用你自己的 BepInEx 配置文件或你自管的文件;
对于附着在某个具体生成物品上的任何东西,用 `ICustomItemSaveable`。

## 下一步去哪

这就完成了面向玩家的系统。剩下的页面属于参考:贯穿这些示例的[工具类](utilities.md)助手,
以及处理联机与框架冲突的[兼容性](compatibility.md)。

*[ICustomItemSaveable]: 一个自定义物品的 MonoBehaviour 实现来保存与还原每实例状态的接口。
*[CustomItemTag]: 每个生成的自定义物品上的 MonoBehaviour;其每实例数据经由 ICustomItemSaveable 持久化。
*[MissingItemTag]: 当拥有它的 Mod 未加载时,保留自定义物品已存记录的占位。
*[SaveCompanionData]: 伴生存档文件的版本化 schema。
*[OnSpawn]: 用于给每个生成实例挂上可存档组件的 CustomItemBuilder 钩子。
