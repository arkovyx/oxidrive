import os
import shlex

from ui import say, cyan, red, yellow, green, dim, bold, reset
from helpers import run, run_as_root, fix_path
from devices import pick_device, device_ok, mounted_at, check_before_writing


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
    mount_line = ", ".join(mounts) if mounts else "not mounted"

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
