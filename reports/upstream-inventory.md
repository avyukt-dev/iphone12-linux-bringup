# Initial source inventory — 2026-09-22

This is a targeted source inspection, **not** a complete code audit or an on-device test.

| Source and branch | Verified observation | What it does NOT establish |
| --- | --- | --- |
| [Hoolock Linux `hoolock`](https://github.com/HoolockLinux/linux/blob/hoolock/arch/arm64/boot/dts/apple/Makefile) | Its Apple device-tree Makefile declares numerous DTBs, but has no `t8101-*.dtb` entry for A14. | Does not prove an existing kernel driver cannot be adapted for A14. |
| [Hoolock m1n1 `idevice`](https://github.com/HoolockLinux/m1n1/blob/idevice/src/chainload.c) | Chainloading code exists for supported platforms. | Does not supply an A14 entry or boot exploit. |
| [Hoolock documentation](https://github.com/HoolockLinux/docs/blob/master/README.md) | The README identifies Apple A7–A11 and T2 device support. | Does not document native Linux boot on iPhone 12. |
| [HoolockRD](https://github.com/HoolockLinux/HoolockRD/blob/master/README.md) | A RAM-based test shell / test mode is documented. | Does not validate A14-specific peripheral drivers. |
| [Sandcastle tools](https://github.com/corellium/projectsandcastle/blob/master/README.md) | Includes PongoOS loader, hardware-configuration tools, and reference iPhone functionality. | Does not document a boot route for an A14 iPhone. |

Developer forks:
- https://github.com/avyukt-dev/linux (default branch `hoolock`)
- https://github.com/avyukt-dev/m1n1 (default branch `idevice`)

**Blocking unknown:** No supported, verified route to execute a custom Linux kernel on the target A14/iPhone 12 has been established by this inventory. Do not fabricate a device tree from other Apple boards. First identify the precise board, firmware build, and available safe diagnostic access.
