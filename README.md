# iPhone 12 / A14 native Linux — bring-up workspace

**Status: host-side research only.** This project does not provide a working A14 boot method, verified iPhone 12 Linux drivers, an installable image, or a device flashing workflow.

Goal: a minimal headless native ARM64 Linux environment with a terminal and HTTP test server.

| Component | GitHub repository | Source branch |
| --- | --- | --- |
| Kernel fork | https://github.com/avyukt-dev/linux | `hoolock` |
| Bootloader fork | https://github.com/avyukt-dev/m1n1 | `idevice` |
| Integration workspace | https://github.com/avyukt-dev/iphone12-linux-bringup | `main` |

The existing Hoolock and Sandcastle boot paths do not establish custom-kernel execution on the iPhone 12's A14. A successful compile is **not** a successful device boot.

## Host setup

On Ubuntu/Debian or WSL2:

```bash
bash scripts/bootstrap.sh                 # clone small reference trees
bash scripts/bootstrap.sh --with-kernel   # REQUIRED before the kernel source audit; large checkout
python3 scripts/a14_audit.py --kernel vendor/linux --m1n1 vendor/m1n1 --json
python3 -m unittest discover -s tests -v
```

The audit returns exit code 2 when the selected kernel declares no A14 DTB. It inventories sources only and does not validate on-device functionality.

See [engineering gates](docs/bringup-plan.md), [repository inventory](reports/upstream-inventory.md), and the [development policy](docs/development-policy.md). Hardware/bootloader changes belong on the `research/iphone12-a14` branch in each fork, not on the default branches.

**Safety:** No firmware exploit, flashing, partition writing, or guessed hardware register values are included. Do not test unverified boot procedures on a daily-use device.
