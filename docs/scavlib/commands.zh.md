---
description: 添加带 owner 归属、支持自动补全与嵌套子命令的控制台命令。
---

# 控制台命令

ScavLib 让你通过继承 `BaseCommand` 来添加控制台命令,而不必跟游戏原始的 `Command` 构造函数
搏斗。你能得到 owner 归属、名称校验、Tab 补全辅助,以及内置的子命令路由——而且 ScavLib 对每个
名称只注册一个命令,所以原版和其他 Mod 的命令绝不会被覆盖。

```csharp
using ScavLib.command;

public class HelloCommand : BaseCommand
{
    public override string Name => "mymod_hello";
    public override string Description => "Prints a greeting.";

    public override void Execute(string[] args)
    {
        // args[0] 是命令名;用户参数从 args[1] 开始。
        string who = args.Length > 1 ? args[1] : "world";
        LogLine($"Hello, {who}!");
    }
}

// 注册它,归属到你的 Mod(例如在 OnEnabled 里):
CommandRegistry.TryRegister(new HelloCommand(), "MyMod", out _);
```

## `BaseCommand` 契约

| 成员 | 必需? | 用途 |
| --- | --- | --- |
| `Name` | 是 | 控制台中输入的关键字。不含空格;不得与内置命令冲突。 |
| `Description` | 是 | 原版 `help` 命令显示的一行文本。 |
| `Execute(string[] args)` | 是 | 命令主体。`args[0]` 是命令名;用户参数从 `args[1]` 开始。 |
| `ArgDescription` | 可选 | 每参数的 `(short, long)` 标签;也驱动自动注入的补全(见下)。 |
| `ArgAutofill` | 可选 | 按参数索引(键 `0` = 第一个用户参数)排列的 Tab 补全候选。 |
| `SubCommands` | 可选 | 第一层子命令表(见[子命令](#子命令))。 |

在任何命令内部都可用 `LogLine(string)` 向游戏内控制台打印一行(它会正确切分多行字符串)。

!!! note "名称会被替你校验"

    名称为空、含空格(控制台按空白切分)、或与内置游戏命令冲突时会被拒绝。不含 `_`(且不是
    字面量 `scavlib`)的名称会注册成功但收到警告——请遵循 `<modname>_<command>` 约定以避免
    与其他 Mod 冲突。

## 参数与补全

在 `Execute` 内部记住这个偏移:`args[0]` 是命令名本身,所以用户键入的第一个东西是 `args[1]`。

`ArgDescription` 为每个位置参数提供文档,同时兼作补全触发器。游戏的命令构造函数会扫描**短标签**
中的两个特殊前缀并自动注入补全候选:

- 以 `bool` 开头的标签注入 `true` / `false`
- 以 `position` 开头的标签注入 `cursor` / `player` / `random` / `#.#`

```csharp
public override (string, string)[] ArgDescription => new (string, string)[]
{
    ("string name", "Who to greet."),
};
```

要提供你自己的候选,从 `ArgAutofill` 返回,按参数索引排列(索引 `0` 是第一个用户参数):

```csharp
public override Dictionary<int, List<string>> ArgAutofill => new Dictionary<int, List<string>>
{
    { 0, new List<string> { "red", "green", "blue" } },
};
```

!!! warning "别在 `bool` / `position` 索引上重复设补全"

    `bool` 和 `position` 的自动注入用的是 `Add` 调用,而非索引器赋值。如果你*又*为同一索引列出
    `ArgAutofill` 候选,游戏构造函数会在注册时抛 `ArgumentException`。每个索引只用一个来源。
    (ScavLib 会预先以明确错误拒绝 `SubCommands` 与 `bool`/`position` 首参的特定组合。)

## 子命令

把 `SubCommands` 设为一个**小写**键到子 `BaseCommand` 的字典,并把 `Execute` 委托给路由器。
ScavLib 会自动把子命令名合并进第一个参数的 Tab 补全,所以 `mycommand <Tab>` 会免费把它们列出来。

```csharp
using System.Collections.Generic;
using ScavLib.command;

public class MyToolCommand : BaseCommand
{
    public override string Name => "mymod_tool";
    public override string Description => "MyMod tools.";

    private readonly Dictionary<string, BaseCommand> _subs =
        new Dictionary<string, BaseCommand>
        {
            { "reload", new ReloadSub() },
            { "dump",   new DumpSub()   },
        };

    public override Dictionary<string, BaseCommand> SubCommands => _subs;

    public override void Execute(string[] args) => ExecuteSubCommand(args, subArgIndex: 1);
}
```

`ExecuteSubCommand` 处理路由:没有子命令则打印用法;`help`、`?` 或 `--help` 打印用法;未知键
打印一条错误加用法;已知键把完整的 `args` 数组转发给该子命令的 `Execute`。默认的 `PrintUsage`
会列出每个子命令及其 `Description`;重写它可自定义格式。

内置的 **`scavlib`** 命令就是参考实现——它正是这样路由 `status` 和 `check` 的。

!!! note "只有第一层子命令会自动补全"

    ScavLib 把第一层子命令名合并进 Tab 补全,但原版控制台只查顶层命令的补全。更深的层级
    (某个子命令自己的子命令)仍可用,但它们的名称要通过你的帮助文本来发现,而非 Tab。

## 注册

| 调用 | 用途 |
| --- | --- |
| `CommandRegistry.TryRegister(command, ownerModName, out error)` | 完整形式——把命令归属到你的 Mod,并得知失败原因。 |
| `CommandRegistry.Register(command)` | 便捷形式:无 owner,丢弃错误。 |

把你在 `ModRegistry.Register` 用的同一个 Mod 名作为 `ownerModName` 传入——它正是 `GetOwner`
和 `scavlib check` 诊断的依据。传 `null` 会放弃 owner 账本但仍能注册。

!!! tip "在 `OnEnabled` 里注册"

    命令在控制台初始化时注入。在那之前——在 `OnEnabled` 里——注册,ScavLib 会把命令入队并在
    恰当时刻(原版命令列表已存在后)刷入,这样重名检查能看到每个内置命令。无论命令是被立即注入
    还是被入队,`TryRegister` 都返回 `true`。

控制台中已存在的名称——内置的、其他 Mod 的、或你自己的重复——会被以记录的原因拒绝,而不会覆盖
任何东西。

## 注销

`CommandRegistry.Unregister(name)` 移除一个 ScavLib 注册的命令(无论已注入还是仍在排队),
并返回是否真的移除了东西。

!!! note "原版命令无法被移除"

    只有 ScavLib 自己注入账本里的命令才可移除。内置游戏命令从未被 ScavLib 添加,所以不在账本里,
    `Unregister` 会拒绝它们——无需维护硬编码名单的原版保护。

## 错误与诊断

在 `Execute` 内部抛异常是安全的:原版控制台会捕获它并把消息内联显示给玩家,而 ScavLib 还会在
BepInEx 日志里以拥有它的 Mod 名记录。你不需要为显示而自己写 try/catch。

查询方面,`GetOwner(name)` 返回拥有它的 Mod(原版/无 owner 命令则为 `null`),`GetAllRegistered()`
返回每个 ScavLib 注入的命令及其 owner。在游戏里,内置命令把这一切都呈现出来:

- `scavlib status` —— ScavLib 的版本,以及每个用 `ModRegistry` 注册的 Mod(有生命周期的标
  `[F]`,并列出其声明的 `Deps`)。
- `scavlib check` —— 用于 bug 报告的诊断转储:Harmony 补丁状态(`[OK]`/`[FAIL]`)、ScavLib
  注入的命令及其 owner,以及已注册键位及其当前按键、owner 和分类。共用同一按键的绑定会被标 `[!]`。

## 下一步去哪

命令常与[键位绑定](input.md)为同一动作搭配,并与[本地化](i18n.md)搭配处理其输出文本。
若你的命令改动了必须在存档间留存的状态,见[存档数据](save.md)。

*[BaseCommand]: 每个 ScavLib 管理的控制台命令所继承的基类。
*[CommandRegistry]: ScavLib 管理的控制台命令的单一注入点。
*[Command]: 游戏原生控制台命令类型,ScavLib 替你构造它。
*[ConsoleScript]: 游戏的控制台控制器;ScavLib 在启动时把命令刷入它。
