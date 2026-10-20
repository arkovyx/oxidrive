import os
import re
import platform
from ui import say, cyan, red, yellow, dim, bold, green, reset
from helpers import run


def get_devices(system):
    if system == "Linux":
        return linux_devices()
    elif system == "Darwin":
        return mac_devices()
    elif system == "Windows":
        return windows_devices()
    else:
        say("[!] unsupported OS: " + system, red)
        return []

def linux_devices():
    pass

def mac_devices():
    pass

def windows_devices():
    pass

def show_devices():
    devices = get_devices(system)

    if not devices:
        say("")
        say("[!] no removable devices found...", yellow)

def pick_device():
    pass

def device_at(path):
    if platform.system() != "Linux":
        return[]
    out = run("lsblk -no MOUNTPOINT " + path + "2>/dev/null")
    if not out:
        return[]
    return [x.strip() for x in out.splitlines() if x.strip()]

def check_before_writing():
    pass
