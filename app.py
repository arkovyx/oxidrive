import os
import re
import sys
import shlex
import difflib
import platform
import subprocess

version = "v1.2.0"

reset = "\033[0m"
bold = "\033[1m"
dim = "\033[2m"
red = "\033[91m"
green = "\033[92m"
yellow = "\033[93m"
cyan = "\033[96m"
magenta = "\033[95m"


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


def run(cmd, wait=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=wait)
        if r.returncode == 0:
            return r.stdout.strip()
        return None
    except Exception:
        return None


def run_as_root(cmd, wait=None):
    if is_root():
        full = cmd
    else:
        full = "sudo " + cmd

    try:
        r = subprocess.run(full, shell=True, text=True, timeout=wait)
        return r.returncode
    except subprocess.TimeoutExpired:
        return 124
    except FileNotFoundError:
        return 127


def fix_path(p):
    p = p.strip().strip('"').strip("'")
    p = os.path.expanduser(p)
    p = os.path.expandvars(p)
    return os.path.abspath(p)


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

        name = bits[0]
        size = bits[1]
        kind = bits[2]
        removable = bits[3]
        model = bits[4].strip() if len(bits) > 4 else "Unknown"

        if kind != "disk":
            continue
        if removable != "1":
            continue
        if "loop" in name or name.startswith("/dev/sr"):
            continue

        devices.append({
            "path": name,
            "size": size,
            "model": model or "Unknown",
        })

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
            num = cols[0]
            name = cols[1]
            size = cols[2]
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


def show_info(value):
    path = pick_device(value)
    print()
    say("  device info: " + path, cyan, True)
    say("  " + "-" * 52, dim)

    if not device_ok(path):
        say("  [!] device does not exist: " + path, red)
        return

    size = run("lsblk -dno SIZE " + path + " 2>/dev/null") or "unknown"
    model = run("lsblk -dno MODEL " + path + " 2>/dev/null") or "unknown"
    fs = run("lsblk -no FSTYPE " + path + " 2>/dev/null") or "none"
    label = run("lsblk -no LABEL " + path + " 2>/dev/null") or "-"
    mounts = mounted_at(path)

    if mounts:
        mount_line = ", ".join(mounts)
    else:
        mount_line = "not mounted"

    print("  " + bold + "path".ljust(12) + reset + " " + path)
    print("  " + bold + "size".ljust(12) + reset + " " + size)
    print("  " + bold + "model".ljust(12) + reset + " " + model.strip())
    print("  " + bold + "filesystem".ljust(12) + reset + " " + fs)
    print("  " + bold + "label".ljust(12) + reset + " " + label)
    print("  " + bold + "mounted".ljust(12) + reset + " " + mount_line)


def burn(iso, value):
    iso = fix_path(iso)
    path = pick_device(value)

    if not os.path.isfile(iso):
        say("  [!] ISO not found: " + iso, red)
        return

    iso_size = os.path.getsize(iso)

    if not check_before_writing(path):
        return

    size_str = run("lsblk -bdno SIZE " + path + " 2>/dev/null")
    try:
        dev_size = int(size_str) if size_str else 0
    except ValueError:
        dev_size = 0

    if dev_size and iso_size > dev_size:
        say("  [!] ISO is bigger than the device.", red)
        return

    print()
    say("  !! WRITE OPERATION", yellow, True)
    say("  " + "-" * 52, dim)
    print("  ISO     : " + cyan + iso + reset)
    print("  size    : " + str(round(iso_size / (1024 * 1024), 1)) + " MB")
    print("  target  : " + red + path + reset)
    say("  " + "-" * 52, dim)
    say("  everything on the target will be erased.", red)

    answer = input("  proceed? [y/N] ").strip().lower()
    if answer != "y":
        say("  cancelled.", dim)
        return

    for m in mounted_at(path):
        say("  unmounting " + m + " ...", dim)
        run_as_root("umount " + m)

    say("")
    say("  writing " + iso + " -> " + path + " ...", cyan)

    cmd = ("dd if=" + shlex.quote(iso) + " of=" + shlex.quote(path)
           + " bs=4M status=progress oflag=direct conv=fsync")
    code = run_as_root(cmd)

    if code == 0:
        run_as_root("sync")
        say("  done. safe to remove the device.", green, True)
    else:
        say("  write failed (exit " + str(code) + ").", red)


def format_drive(value):
    path = pick_device(value)

    if not check_before_writing(path):
        return

    print()
    say("  !! FORMAT OPERATION", yellow, True)
    say("  " + "-" * 52, dim)
    print("  target: " + red + path + reset)
    say("  " + "-" * 52, dim)

    fs = input("  filesystem [vfat/ext4/ntfs/exfat] (default vfat): ").strip().lower()
    if not fs:
        fs = "vfat"

    if fs not in ("vfat", "ext4", "ntfs", "exfat"):
        say("  [!] unsupported filesystem: " + fs, red)
        return

    label = input("  label (optional): ").strip()

    answer = input("  erase " + path + " as " + fs + "? [y/N] ").strip().lower()
    if answer != "y":
        say("  cancelled.", dim)
        return

    for m in mounted_at(path):
        say("  unmounting " + m + " ...", dim)
        run_as_root("umount " + m)

    say("  clearing old signatures ...", dim)
    run_as_root("wipefs -a " + shlex.quote(path))

    if fs == "vfat":
        cmd = "mkfs.vfat -F 32 "
        if label:
            cmd += "-n " + shlex.quote(label[:11]) + " "
        cmd += shlex.quote(path)

    elif fs == "ext4":
        cmd = "mkfs.ext4 -F "
        if label:
            cmd += "-L " + shlex.quote(label[:16]) + " "
        cmd += shlex.quote(path)

    elif fs == "ntfs":
        cmd = "mkfs.ntfs -F "
        if label:
            cmd += "-L " + shlex.quote(label[:32]) + " "
        cmd += shlex.quote(path)

    else:
        cmd = "mkfs.exfat "
        if label:
            cmd += "-n " + shlex.quote(label[:11]) + " "
        cmd += shlex.quote(path)

    say("")
    say("  formatting " + path + " as " + fs + " ...", cyan)
    code = run_as_root(cmd)

    if code == 0:
        run_as_root("sync")
        say("  format complete.", green, True)
    else:
        say("  format failed (exit " + str(code) + ").", red)
        say("  hint: is mkfs." + fs + " installed?", dim)


def wipe_drive(value):
    path = pick_device(value)

    if not check_before_writing(path):
        return

    for m in mounted_at(path):
        say("  unmounting " + m + " ...", dim)
        run_as_root("umount " + m)

    say("")
    say("  wiping signatures on " + path + " ...", yellow)
    code = run_as_root("wipefs -a " + shlex.quote(path))

    if code == 0:
        run_as_root("sync")
        say("  wiped.", green, True)
    else:
        say("  wipe failed (exit " + str(code) + ").", red)


known = [
    "list", "info", "format", "wipe", "burn",
    "clear", "help", "version", "q", "quit", "exit",
]


def suggest(word):
    hits = difflib.get_close_matches(word, known, n=1, cutoff=0.6)
    if hits:
        return hits[0]
    return None


def grab(argv, *flags):
    for i in range(len(argv)):
        if argv[i] in flags and i + 1 < len(argv):
            return argv[i + 1]
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


if __name__ == "__main__":
    shell()
