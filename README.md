```
                    > ======================================================== <
                     ██████╗ ██╗  ██╗██╗██████╗ ██████╗ ██╗██╗   ██╗███████╗
                    ██╔═══██╗╚██╗██╔╝██║██╔══██╗██╔══██╗██║██║   ██║██╔════╝
                    ██║   ██║ ╚███╔╝ ██║██║  ██║██████╔╝██║██║   ██║█████╗
                    ██║   ██║ ██╔██╗ ██║██║  ██║██╔══██╗██║╚██╗ ██╔╝██╔══╝
                    ╚██████╔╝██╔╝ ██╗██║██████╔╝██║  ██║██║ ╚████╔╝ ███████╗
                     ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝
                    > ======================================================== <
```

# Features
- List removable devices with size and model
- Info — full device details (path, size, model, filesystem, label, mount point)
- Burn — write an ISO to a device with dd
- Format — vfat, ext4, ntfs, exfat with optional label
- Wipe — remove all filesystem signatures
- Safety checks — refuses root disk, auto-unmounts, checks ISO fits
- Auto-sudo — elevates only destructive operations
- Typo hints — "did you mean: list?"

# Installation
```
git clone https://github.com/arkovyx/oxidrive.git
pip install -r requirements.txt
python oxidrive.py
```

# Usage
```
list                                          # list removable devices
info <device-name/number>                     # show device details
format <device-name/number>                   # format a device
wipe <device-name/number>                     # wipe signatures
burn <path-to-iso> <device-name/number>       # write an ISO to a device
clear                                         # clear terminal
help                                          # show help menu
version                                       # show version
q                                             # quit

# TIP: you can use the number next to a device instead of its full path.

```
