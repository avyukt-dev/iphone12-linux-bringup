# G2/G3 software integration: generic ARM64 virtual-machine boot

**This is not an Apple iPhone emulator.** QEMU `virt` emulates a generic ARM64
board with different boot firmware, UART, interrupt controller, clocks, and
peripheral mappings from the iPhone 12/A14. This test cannot satisfy the
physical-device G1/G2/G3 acceptance gates.

## Purpose

Our earlier QEMU *user-mode* tests validated ARM64 binaries, but did not
verify that a Linux kernel can unpack our `cpio newc` archive, execute
`/init` as PID 1, provide `/dev/console`, or accept commands from a
BusyBox child shell. This full-system test exercises those integration
boundaries under a generic, separately supplied Debian ARM64 kernel.

## Run locally on Ubuntu 24.04 / Debian

```bash
sudo apt-get update
sudo apt-get install -y gcc-aarch64-linux-gnu libc6-dev-arm64-cross \
  binutils-aarch64-linux-gnu qemu-user qemu-system-arm make curl bzip2 python3
bash scripts/build_busybox.sh
bash scripts/build_headless.sh --with-busybox
python3 scripts/test_qemu_arm64_system.py --timeout 100
```

The test downloads only Debian's published ARM64 *generic installer kernel*
from https://deb.debian.org/debian/dists/bookworm/main/installer-arm64/current/images/netboot/debian-installer/arm64/linux
and checks its SHA-256 against that release's
[SHA256SUMS](https://deb.debian.org/debian/dists/bookworm/main/installer-arm64/current/images/SHA256SUMS).
The downloaded Debian ARM64 kernel is pinned to SHA-256
`84b9c190bb4589c4a9527e3191fec051f9f115e88f0a3e8afae96ba0dfb4dfef`,
measured during the passing full-system CI run on 2026-09-22. The test rejects
changes to Debian's mutable `current` kernel rather than silently using a
new kernel; a future update requires an explicit code change and a new test.
The checksum manifest is fetched over HTTPS from the same distributor and
is an integrity check, not independent cryptographic signature verification.

QEMU parameters: `-machine virt -cpu cortex-a72 -m 768M -smp 2`,
an isolated generic ARM64 kernel, our gzip initramfs, serial console
`ttyAMA0`, and `-nic none` so this VM cannot access the host's external
network. The script waits for our early-init diagnostic, sends
`echo QEMU_SYSTEM_ARM64_SHELL_OK` to the **emulated** serial console,
verifies the response, and stops QEMU.

The earlier QEMU user-mode HTTP test uses *host loopback* and does not
depend on this isolated full-system VM's network; **no iPhone SSH,
networking, bootloader bypass or A14 kernel driver is demonstrated**.

Evidence to advance a *physical* iPhone milestone still requires an
authorized A14 custom-code boot entry (G1), validated hardware description,
and real on-device Linux console logs. See
[the blocker report](../reports/boot-path-g1-24A437.md).

## Optional virtual network experiment — not yet passing

A host-only network probe is available in `scripts/test_qemu_arm64_network.py`, but is **deliberately not a required CI check**. With the pinned Debian ARM64 installer kernel and a QEMU `virtio-net-device`, the generic ARM64 guest reached our `/init` and interactive shell, but `ip link show eth0` returned `ip: can't find device 'eth0'`. The guest consequently could not serve the test page through the forwarded host port. [Unsuccessful, recorded CI experiment](https://github.com/avyukt-dev/iphone12-linux-bringup/actions/runs/35768405105).

The exact reason `eth0` is missing has **not** been determined: the kernel's built-in VirtIO network support, loadable module availability, and alternative interface names remain to be checked. Installing a driver, building a suitably configured **generic VM** kernel, or inspecting the guest's detected devices are host-only possible next steps. This is **not evidence about the A14's USB or Wi-Fi driver support**, and no actual iPhone was involved.

Do not mark G4 networking complete on the basis of earlier QEMU *user-mode* HTTP tests; those use the **host** Linux network stack. Real iPhone networking still requires the independent G1 native boot entry and appropriate platform drivers.
