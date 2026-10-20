import os
import re
import platform

from ui import say, cyan, red, yellow, dim, bold, green, reset
from helpers import run


def get_devices():
    system = platform.system()
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
    devices = []
    out = run("lsblk -dpno NAME,SIZE,TYPE,RM,MODEL 2>/dev/null")
    if not out:
        return devices

    for line in out.splitlines():
        bits = line.split(None, 4)
        if len(bits) < 4:
            continue

        name, size, kind, removable = bits[0], bits[1], bits[2], bits[3]
        model = bits[4].strip() if len(bits) > 4 else "Unknown"

        if kind != "disk" or removable != "1":
            continue
        if "loop" in name or name.startswith("/dev/sr"):
            continue

        devices.append({"path": name, "size": size, "model": model or "Unknown"})

    return devices


def mac_devices():
    devices = []
    out = run("diskutil list external physical 2>/dev/null")
    if not out:
        return devices

    for line in out.splitlines():
        m = re.match(r"^(/dev/disk\d+)\s+.*?(\*?[\d.]+\s*[KMGT]B)\s+(\S.*)?$",
                     line.strip())
        if m:
            devices.append({
                "path": m.group(1),
                "size": m.group(2),
                "model": (m.group(3) or "External").strip(),
            })

    return devices


def windows_devices():
    devices = []
    cmd = ('powershell -NoProfile -Command '
           '"Get-Disk | Where-Object BusType -eq USB | '
           'Select-Object Number,FriendlyName,Size | ConvertTo-Csv -NoTypeInformation"')
    out = run(cmd)
    if not out:
        return devices

    for line in out.splitlines()[1:]:
        cols = [c.strip('"') for c in line.split('","')]
        if len(cols) >= 3:
            num, name, size = cols[0], cols[1], cols[2]
            try:
                size_gb = str(round(int(size) / (1024 ** 3), 1)) + " GB"
            except ValueError:
                size_gb = size
            devices.append({
                "path": "\\\\.\\PhysicalDrive" + num,
                "size": size_gb,
                "model": name,
            })

    return devices


def show_devices():
    devices = get_devices()

    if not devices:
        say("")
        say("[!] no removable devices found.", yellow)
        return devices

    print()
    say("  available devices", cyan, True)
    say("  " + "-" * 60, dim)
    print("  " + bold + "IDX  DEVICE                SIZE        MODEL" + reset)
    say("  " + "-" * 60, dim)

    for i in range(len(devices)):
        d = devices[i]
        num = str(i + 1)
        print("  " + green + "[" + num + "]" + reset + "  "
              + d["path"].ljust(20) + yellow + d["size"].ljust(12)
              + reset + d["model"])

    say("  " + "-" * 60, dim)
    return devices


def pick_device(value):
    if not value:
        return value

    devices = get_devices()

    if value.isdigit() and devices:
        idx = int(value) - 1
        if 0 <= idx < len(devices):
            return devices[idx]["path"]

    return value


def device_ok(path):
    if platform.system() == "Windows":
        return True
    return os.path.exists(path)


def mounted_at(path):
    if platform.system() != "Linux":
        return []
    out = run("lsblk -no MOUNTPOINT " + path + " 2>/dev/null")
    if not out:
        return []
    return [x.strip() for x in out.splitlines() if x.strip()]


def check_before_writing(path):
    if not device_ok(path):
        say("  [!] device not found: " + path, red)
        return False

    mounts = mounted_at(path)
    if mounts:
        say("  [!] device is mounted at: " + ", ".join(mounts), red)
        say("      unmount first: sudo umount " + mounts[0], yellow)
        return False

    if platform.system() == "Linux":
        root = run("findmnt -no SOURCE /")
        if root and root.startswith(path):
            say("  [!] " + path + " is your root disk. refusing.", red)
            return False

    return True
