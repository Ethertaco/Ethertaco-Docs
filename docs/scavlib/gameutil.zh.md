---
description: 通往世界与玩家状态、物品生成、控制台输出与 UI 检查的入口。
---

# GameUtil

`GameUtil` 是常见游戏状态操作的入口:检查世界是否加载、触达玩家、生成物品、写控制台、显示提示。
和其余[工具类](utilities.md)一样,每个方法都优雅地处理空游戏状态——全部**可在主菜单安全调用**,
此时它只是返回一个安全值或空操作。

## 世界与玩家状态

| 成员 | 返回 |
| --- | --- |
| `IsInGame` | 加载了世界时(玩家相机存在)为 `true`,主菜单中为 `false`。 |
| `IsWorldLoaded` | 更严格的检查,询问世界生成系统世界数据是否确实存在。 |
| `GetWorld()` | `WorldGeneration` 实例,或 `null`。 |
| `GetBody()` | 玩家的 `Body`,不在游戏中时为 `null`。 |
| `TryGetBody(out body)` | 可用则返回 `true` 与 `Body`——便捷的带判断形式。 |
| `GetPlayerPosition()` | 玩家的世界位置,不在游戏中时为 `Vector2.zero`。 |

`GetBody` / `TryGetBody` 是其余工具类构建于其上的基础,所以触达玩家通常就是一行:

```csharp
if (GameUtil.TryGetBody(out var body))
{
    // 此处可安全读取或操作玩家
}
```

!!! note "`IsInGame` 与 `IsWorldLoaded` 的区别"

    `IsInGame` 检查玩家是否存在,对大多数玩法代码已足够。`IsWorldLoaded` 更进一步,确认世界生成
    数据已就位——当你确实依赖世界数据(而不仅是玩家)时用它。

## 生成物品

| 方法 | 作用 |
| --- | --- |
| `SpawnItem(id, position, rotation=0)` | 在一个世界位置生成物品或建筑。返回 `GameObject`,若 id 无效或未加载世界则为 `null`。 |
| `SpawnItemAt(id, transform)` | 在某 transform 的位置生成,并复制它的 Z 轴旋转。 |
| `SpawnAtPlayer(id)` | 在玩家处生成,若为物品则自动拾取。 |

`id` 与 `spawn` 控制台命令用的资源 id 相同,生成走的是游戏的 `Utils.Create`——和自定义物品同一
条路径——所以**已注册的自定义物品 id 在这里同样可用**。在世界加载前生成已被妥善处理:你会得到
一条记录的警告和一个 `null` 结果,而非异常。

```csharp
GameUtil.SpawnAtPlayer("bandage");          // 给玩家一卷绷带
GameUtil.SpawnItem("mymod_flask", pos);     // 一个已注册的自定义物品,生成到世界里
```

## 控制台输出

| 方法 | 作用 |
| --- | --- |
| `Log(message)` | 向游戏内开发者控制台写一行。 |
| `Alert(text, important=false)` | 显示屏幕提示弹窗。`important` 会显著地居中显示。 |
| `Notify(text, important=false)` | 同时 `Alert` **和** `Log` 同一段文本——既让玩家看到,又能从控制台回溯。 |

`Log` 在控制台尚不存在时调用是安全的(消息会被静默丢弃)。它也处理多行文本:按换行切分、去掉
CRLF 的 `\r`、每行输出一行控制台、并跳过空行。

!!! warning "控制台会折叠连续空格"

    游戏的 `log` 命令按空格分词,并会折叠一行内的连续空格,所以别靠多个空格在日志输出里对齐列
    ——那种对齐保不住。

## UI

`IsPointerOverUI()` 在鼠标悬停于某个游戏 UI 元素上时返回 `true`。在你自己的菜单和点击处理里检查
它,以免拦截了本该给下方游戏的点击。

## 下一步去哪

构建在 `GetBody` 之上的类型化助手——玩家生命体征、肢体、物品与技能——见[工具类](utilities.md)。

*[Body]: 玩家的核心组件;GameUtil.GetBody 返回它,PlayerUtil 助手封装它。
*[WorldGeneration]: 游戏的世界系统;IsWorldLoaded 与 GetWorld 查询它。
*[Utils.Create]: GameUtil 与自定义物品系统都经由的游戏生成方法。
