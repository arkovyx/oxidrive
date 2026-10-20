import os

reset = "\033[0m"
bold = "\033[1m"
dim = "\033[2m"
red = "\033[91m"
green = "\033[92m"
yellow = "\033[93m"
cyan = "\033[96m"
magenta = "\033[95m"

version = "v1.2.0"

banner = """
> ======================================================== <
 ██████╗ ██╗  ██╗██╗██████╗ ██████╗ ██╗██╗   ██╗███████╗
██╔═══██╗╚██╗██╔╝██║██╔══██╗██╔══██╗██║██║   ██║██╔════╝
██║   ██║ ╚███╔╝ ██║██║  ██║██████╔╝██║██║   ██║█████╗
██║   ██║ ██╔██╗ ██║██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝
╚██████╔╝██╔╝ ██╗██║██████╔╝██║  ██║██║ ╚████╔╝ ███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
> ======================================================== <
"""


def say(text, color=reset, is_bold=False):
    if is_bold:
        print(bold + color + text + reset)
    else:
        print(color + text + reset)


def is_root():
    return hasattr(os, "geteuid") and os.geteuid() == 0


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def show_banner():
    say(banner, magenta, True)
    say("           USB / ISO flashing utility  ·  " + version, cyan)
    if not is_root():
        say("           running unprivileged — will ask for sudo when needed", dim)
    print()


help_menu = """
USAGE:
  list                      list removable devices
  info <dev>                show device details
  format <dev>              format a device
  wipe <dev>                wipe filesystem signatures
  burn <iso> <dev>          write an ISO to a device
  clear                     clear the screen
  help                      show this menu
  version                   show version
  q                         quit

EXAMPLES:
  list
  info 1
  info /dev/sdc
  format 2
  wipe 1
  burn ~/Downloads/arch.iso 1
  burn /home/me/ubuntu.iso /dev/sdc

TIP: you can use the number next to a device instead of its full path.
"""
