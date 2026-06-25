---
description: Add owner-attributed console commands with autofill and nested subcommands.
---

# Console commands

ScavLib lets you add console commands by subclassing `BaseCommand` instead of
wrestling with the game's raw `Command` constructor. You get owner attribution,
name validation, tab-completion helpers, and a built-in subcommand router — and
ScavLib registers exactly one command per name, so vanilla and other mods' commands
are never clobbered.

```csharp
using ScavLib.command;

public class HelloCommand : BaseCommand
{
    public override string Name => "mymod_hello";
    public override string Description => "Prints a greeting.";

    public override void Execute(string[] args)
    {
        // args[0] is the command name; user arguments start at args[1].
        string who = args.Length > 1 ? args[1] : "world";
        LogLine($"Hello, {who}!");
    }
}

// Register it, attributing it to your mod (e.g. in OnEnabled):
CommandRegistry.TryRegister(new HelloCommand(), "MyMod", out _);
```

## The `BaseCommand` contract

| Member | Required? | Purpose |
| --- | --- | --- |
| `Name` | yes | The keyword typed in the console. No spaces; must not collide with a built-in. |
| `Description` | yes | One-line text shown by the vanilla `help` command. |
| `Execute(string[] args)` | yes | The command body. `args[0]` is the name; user args start at `args[1]`. |
| `ArgDescription` | optional | Per-argument `(short, long)` labels; also drives auto-injected autofill (see below). |
| `ArgAutofill` | optional | Tab-completion candidates keyed by argument index (key `0` = first user arg). |
| `SubCommands` | optional | First-level subcommand table (see [Subcommands](#subcommands)). |

`LogLine(string)` is available inside any command to print a line to the in-game
console (it splits multi-line strings correctly).

!!! note "Names are validated for you"

    A command name is rejected if it's empty, contains spaces (the console splits on
    whitespace), or collides with a built-in game command. A name with no `_` (and
    not literally `scavlib`) registers but earns a warning — follow the
    `<modname>_<command>` convention to avoid clashing with other mods.

## Arguments and autofill

Inside `Execute`, remember the offset: `args[0]` is the command name itself, so the
first thing the user typed is `args[1]`.

`ArgDescription` documents each positional argument and doubles as an autofill
trigger. The game's command constructor scans the **short label** for two special
prefixes and injects completion candidates automatically:

- a label starting with `bool` injects `true` / `false`
- a label starting with `position` injects `cursor` / `player` / `random` / `#.#`

```csharp
public override (string, string)[] ArgDescription => new (string, string)[]
{
    ("string name", "Who to greet."),
};
```

For your own candidates, return them from `ArgAutofill`, keyed by argument index
(index `0` is the first user argument):

```csharp
public override Dictionary<int, List<string>> ArgAutofill => new Dictionary<int, List<string>>
{
    { 0, new List<string> { "red", "green", "blue" } },
};
```

!!! warning "Don't double up autofill on a `bool` / `position` index"

    The auto-injection for `bool` and `position` uses an `Add` call, not an indexer
    assignment. If you *also* list `ArgAutofill` candidates for that same index, the
    game constructor throws an `ArgumentException` at registration. Pick one source
    per index. (ScavLib rejects the specific case of `SubCommands` combined with a
    `bool`/`position` first argument up front, with a clear error.)

## Subcommands

Set `SubCommands` to a dictionary of **lowercase** keys to child `BaseCommand`s, and
delegate `Execute` to the router. ScavLib auto-merges the subcommand names into the
first argument's tab completion, so `mycommand <Tab>` lists them for free.

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

`ExecuteSubCommand` handles the routing: no subcommand prints usage; `help`, `?`, or
`--help` prints usage; an unknown key prints an error plus usage; a known key forwards
the full `args` array to that child's `Execute`. The default `PrintUsage` lists each
subcommand with its `Description`; override it to customise the formatting.

The built-in **`scavlib`** command is the reference implementation — it routes
`status` and `check` exactly this way.

!!! note "Only the first subcommand level is auto-completed"

    ScavLib merges first-level subcommand names into tab completion, but the vanilla
    console only consults the top-level command's autofill. Deeper levels (a
    subcommand's own subcommands) still work, but their names must be discovered
    through your help text rather than Tab.

## Registering

| Call | Use |
| --- | --- |
| `CommandRegistry.TryRegister(command, ownerModName, out error)` | The full form — attribute the command to your mod and learn why it failed. |
| `CommandRegistry.Register(command)` | Convenience: no owner, discards the error. |

Pass the same mod name you used with `ModRegistry.Register` as `ownerModName` — it's
what powers `GetOwner` and the `scavlib check` diagnostic. Passing `null` opts out of
the owner ledger but still registers.

!!! tip "Register in `OnEnabled`"

    Commands are injected when the console initialises. Register before that — in
    `OnEnabled` — and ScavLib queues the command and flushes it at the right moment,
    after the vanilla command list exists, so the duplicate-name check sees every
    built-in. `TryRegister` returns `true` whether the command was injected
    immediately or queued.

A name already present in the console — built-in, another mod's, or your own
duplicate — is rejected with a logged reason rather than overwriting anything.

## Unregistering

`CommandRegistry.Unregister(name)` removes a command ScavLib registered (whether it
was already injected or still queued) and returns whether anything was removed.

!!! note "Game-native commands can't be removed"

    Only commands in ScavLib's own injected ledger are removable. Built-in game
    commands were never added by ScavLib, so they aren't in the ledger and
    `Unregister` refuses them — vanilla protection with no hardcoded list to
    maintain.

## Errors and diagnostics

Throwing inside `Execute` is safe: the vanilla console catches it and shows the
message inline to the player, and ScavLib additionally logs it against the owning mod
in the BepInEx log. You don't need your own try/catch for display.

For querying, `GetOwner(name)` returns the owning mod (or `null` for native /
no-owner commands), and `GetAllRegistered()` returns every ScavLib-injected command
with its owner. In-game, the built-in command surfaces all of this:

- `scavlib status` — ScavLib's version and every mod registered with `ModRegistry`
  (with a `[F]` marker for mods that have a lifecycle, and their declared `Deps`).
- `scavlib check` — a diagnostic dump for bug reports: Harmony patch status
  (`[OK]`/`[FAIL]`), ScavLib-injected commands and their owners, and registered
  keybinds with their current key, owner, and category. Bindings sharing a key are
  flagged with `[!]`.

## Where to next

Commands often pair with [keybinds](input.md) for the same actions, and with
[localization](i18n.md) for their output text. For state your command changes that
must survive a save, see [save data](save.md).

*[BaseCommand]: The base class every ScavLib-managed console command inherits from.
*[CommandRegistry]: The single injection point for ScavLib-managed console commands.
*[Command]: The game's native console command type, which ScavLib constructs for you.
*[ConsoleScript]: The game's console controller; ScavLib flushes commands into it at startup.
