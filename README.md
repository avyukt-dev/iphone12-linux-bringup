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
# Only on your local Linux host, with the actual iPhone connected and paired:
python3 scripts/collect_device_facts.py
```

The audit returns exit code 2 when there is no A14 DTB declaration, the matching DTS source is missing, or a requested verified DTB suffix is absent. An exit code of 0 only means that the requested source declarations are present; it **does not** mean that A14 boots. Apple BoardConfig `D53gAP` is not a validated Linux DTB filename suffix.

For a privacy-preserving physical-device observation, follow [G0: read-only iPhone facts](docs/device-facts.md). No phone identifiers, unique IDs, or firmware images should be committed to this repository.

See the [pinned, evidence-based A14 source baseline](reports/a14-baseline-2026-09-22.md), [engineering gates](docs/bringup-plan.md), [repository inventory](reports/upstream-inventory.md), and the [development policy](docs/development-policy.md). Hardware/bootloader changes belong on the `research/iphone12-a14` branch in each fork, not on the default branches.

**Safety:** No firmware exploit, flashing, partition writing, or guessed hardware register values are included. Do not test unverified boot procedures on a daily-use device.
