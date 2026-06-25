---
description: ScavLib —— 《Casualties Unknown》(Scav Prototype)的 Mod 基础 API 库。
---

# ScavLib API

ScavLib API 是 **《Casualties Unknown》**(*Scav Prototype*)的 Mod 基础 API 库。
它位于 BepInEx 和你的插件之间,把游戏脆弱的内部细节——Harmony 补丁、世界加载时序、
控制台、存档文件——封装成一小套稳定、行为可控、可供你直接构建的 API。

它本身不是一个玩法 Mod。你只需安装一次,所有依赖它的 Mod 就能共享:事件总线、
Mod 注册中心、自定义内容构建器、键位绑定、本地化、存档持久化——而且全部**故障隔离**,
任何一个功能出错都绝不会拖垮整个库。

!!! info "环境要求"

    - **《Casualties Unknown》**(*Scav Prototype*)
    - **BepInEx 5**(Mono / .NET Framework 4.8 版本)
    - *可选:* [KrokoshaCasualtiesMP] —— 存在时会启用联机兼容层。ScavLib 把它当作**软依赖**,装不装它都能正常加载。

## 安装(玩家)

1. 将 **BepInEx 5** 安装进游戏目录,并启动一次游戏让它生成相关文件夹。
2. 把 `ScavLib API.dll` 放进 `BepInEx/plugins/`。
3. 再次启动游戏。如果在 BepInEx 控制台看到类似
   `ScavLib 0.8.0 loaded successfully` 的日志,说明它已激活,依赖它的 Mod 就能找到它了。

!!! tip "确认是否加载成功"

    打开游戏内控制台,输入 `scavlib check`。它会列出哪些 ScavLib 补丁已应用、
    哪些(如果有)应用失败,以及当前已注册的 Mod。

## 库里有什么

<div class="grid cards" markdown>

-   :material-package-variant-closed:{ .lg .middle } __注册你的 Mod__

    ---

    用 `ModInfo` 把你的 Mod 告知 ScavLib,再让 `IModLifecycle` 自动把你接入世界生命周期。

    [:octicons-arrow-right-24: Mod 与生命周期](mods.md)

-   :material-bell-ring-outline:{ .lg .middle } __响应世界事件__

    ---

    通过中央 `EventBus`,用简单的 `[Subscribe]` 方法订阅世界加载、层加载、物品掉落等事件。

    [:octicons-arrow-right-24: 事件](events.md)

-   :material-console:{ .lg .middle } __添加控制台命令__

    ---

    注册 `BaseCommand` 子类,自带归属标记、自动补全和嵌套子命令——无需接触原版控制台类型。

    [:octicons-arrow-right-24: 命令](commands.md)

-   :material-treasure-chest:{ .lg .middle } __创建自定义内容__

    ---

    用流式构建器创建自定义物品、配方和液体,预制体克隆、贴图、延迟注册都帮你处理好。

    [:octicons-arrow-right-24: 物品](items.md)

-   :material-keyboard-outline:{ .lg .middle } __绑定按键__

    ---

    定义会出现在游戏自身设置菜单里的键位,并触发按下 / 长按 / 松开事件。

    [:octicons-arrow-right-24: 输入](input.md)

-   :material-content-save-outline:{ .lg .middle } __持久化数据__

    ---

    把你 Mod 的状态存进一个伴生存档文件,它与原版存档并存,且永不损坏原版存档。

    [:octicons-arrow-right-24: 存档](save.md)

</div>

## 你的第一个 Mod

一个完整的 ScavLib Mod,本质上就是一个 BepInEx 插件:**声明依赖**、**注册自己**,
然后在触碰玩家之前**等待世界就绪**。

```csharp
using BepInEx;
using ScavLib.event_bus.events;
using ScavLib.mods;
using ScavLib.util;

namespace MyFirstMod
{
    [BepInPlugin("com.example.myfirstmod", "My First Mod", "1.0.0")]
    [BepInDependency("com.kanisuko.scavlib")]   // ScavLib 会先于你加载
    public class Plugin : BaseUnityPlugin
    {
        private void Awake()
        {
            // 用生命周期对象注册——无需手动调用 EventBus.Register,
            // 也不必到处撒 [Subscribe] 特性。
            ModRegistry.Register(
                new ModInfo(
                    "My First Mod",
                    "1.0.0",
                    "Feeds the player when the world loads.",
                    "You"),
                new Lifecycle());
        }

        private class Lifecycle : ModLifecycleBase
        {
            // 只重写你关心的回调。
            public override void OnWorldLoaded(WorldLoadedEvent e)
            {
                // 此处世界已就绪——可以安全地操作玩家。
                PlayerUtil.Feed(50f);
            }
        }
    }
}
```

!!! danger "不要在 `Awake()` 里操作玩家"

    `Awake()` 在**世界存在之前**就会运行。此时读取 `PlayerCamera.main` 或
    `WorldGeneration.world` 会抛出 `NullReferenceException`。请始终等待
    `OnWorldLoaded`(通过 `IModLifecycle`)——若需要更精细的时序,可用
    `GameUtil.AwaitWorldGeneration`。

### 更想用特性而不是生命周期类?

如果你更喜欢把处理函数写在插件里,可以只注册一个普通 `ModInfo`,自己接入总线:

```csharp
private void Awake()
{
    ModRegistry.Register(
        new ModInfo("My First Mod", "1.0.0", "Feeds the player.", "You"));
    EventBus.Register(this);   // 扫描本对象上的 [Subscribe] 方法
}

[Subscribe]
private void OnWorldLoaded(WorldLoadedEvent e)
{
    PlayerUtil.Feed(50f);
}
```

两种写法完全等价,任选其一。生命周期对象更适合较大的 Mod;少量处理函数时,
内联 `[Subscribe]` 就够了。

## 基于 ScavLib 开发

- 目标框架选 **.NET Framework 4.8**,引用 `ScavLib API.dll`(根命名空间为 `ScavLib`)。
- 给你的插件加上 `[BepInDependency("com.kanisuko.scavlib")]`,让 BepInEx 先加载 ScavLib。
- 共享日志源是公开的:想让你的日志走 ScavLib 的日志通道,直接用 `ScavLibPlugin.Log` 输出即可。

## 下一步去哪

刚接触这个库?先从 **[Mod 与生命周期](mods.md)** 了解注册机制,再看 **[事件](events.md)**
掌握游玩过程中发生的一切。之后,按你的 Mod 需要,跳到对应的功能页即可。

  [KrokoshaCasualtiesMP]: https://github.com/Krokosha666/cas-unk-krokosha-multiplayer-coop

*[BepInEx]: ScavLib 所运行的 Unity Mono Mod 加载器。
*[ModInfo]: 描述一个已注册 Mod 的元数据(名称、版本、描述、作者)。
*[IModLifecycle]: 可选接口,其回调由 ScavLib 在世界生命周期各阶段自动调用。
*[ModLifecycleBase]: 抽象基类,为每个 IModLifecycle 回调提供空实现,让你只重写需要的部分。
*[EventBus]: ScavLib 的中央发布/订阅枢纽,用于世界与玩法事件。
*[WorldLoadedEvent]: 在世界加载完成、玩家 Body 可安全访问时触发。
*[PlayerUtil]: 用于读取和修改玩家生命值、技能、外观等的工具类。
*[GameUtil]: 通用辅助类,涵盖时序、PlayerPrefs、世界内操作与控制台输出。