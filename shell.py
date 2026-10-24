import shlex
import difflib

from ui import (
    say, show_banner, clear_screen, help_menu,
    version, red, yellow, cyan, dim, green, reset, magenta
)
from devices import show_devices
from commands import show_info, burn, format_drive, wipe_drive


known = [
    "list", "info", "format", "wipe", "burn",
    "clear", "help", "version", "q", "quit", "exit",
]


def suggest(word):
    hits = difflib.get_close_matches(word, known, n=1, cutoff=0.6)
    if hits:
        return hits[0]
    return None


def handle(raw):
    try:
        argv = shlex.split(raw)
    except ValueError as e:
        say("  [!] bad quoting: " + str(e), red)
        return True

    if not argv:
        return True

    if argv[0] == "oxidrive" and len(argv) > 1:
        argv = argv[1:]

    cmd = argv[0]

    if cmd in ("q", "quit", "exit"):
        say("bye", cyan)
        return False
    if cmd == "help":
        print(help_menu)
        return True
    if cmd == "version":
        say("  oxidrive " + version, cyan, True)
        return True
    if cmd in ("clear", "cls"):
        clear_screen()
        show_banner()
        return True
    if cmd == "list":
        show_devices()
        return True
    if cmd == "info":
        if len(argv) < 2:
            say("  usage: info <dev>", yellow)
        else:
            show_info(argv[1])
        return True
    if cmd == "format":
        if len(argv) < 2:
            say("  usage: format <dev>", yellow)
        else:
            format_drive(argv[1])
        return True
    if cmd == "wipe":
        if len(argv) < 2:
            say("  usage: wipe <dev>", yellow)
        else:
            say("  this will delete everything on the drive.", red)
            ans = input("  are you sure? [y/N] ").strip().lower()
            if ans == "y":
                wipe_drive(argv[1])
            else:
                say("  cancelled.", dim)
        return True
    if cmd == "burn":
        if len(argv) < 3:
            say("  usage: burn <iso> <dev>", yellow)
        else:
            burn(argv[1], argv[2])
        return True

    say("  unknown command: " + cmd, yellow)
    hint = suggest(cmd)
    if hint:
        say("  did you mean: " + hint + "?", dim)
    else:
        say("  type 'help' for usage.", dim)
    return True


def shell():
    show_banner()
    say("  type 'help' for commands, 'q' to quit.", dim)
    print()

    while True:
        try:
            line = input(green + "oxidrive" + reset + " " + magenta + ">" + reset + " ")
            line = line.strip()
            if not line:
                continue
            if not handle(line):
                break
        except KeyboardInterrupt:
            say("")
            say("bye", cyan)
            break
        except EOFError:
            say("")
            say("bye", cyan)
            break
