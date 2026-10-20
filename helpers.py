import os
import subprocess

from ui import is_root


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
