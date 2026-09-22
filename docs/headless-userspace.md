# Host-built AArch64 early-init initramfs

Status: **host QEMU user-mode smoke test only**. No A14 boot chain, Linux kernel,
interactive shell, USB drivers, SSH, HTTP server or phone installation is provided
by this milestone.

## Build on Ubuntu / Debian Linux

Install host dependencies:

`sudo apt update && sudo apt install -y gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu qemu-user python3`

From this repository:

```bash
bash scripts/build_headless.sh
python3 -m unittest discover -s tests -v
```

Outputs (ignored by Git): `build/headless/init` and `build/headless/early-initramfs.cpio.gz`. The build:

1. Cross-compiles a **statically linked AArch64 Linux** `/init` executable with ELF PT_LOAD segments aligned for 16 KiB pages.
2. Checks ELF architecture, static linking, section bounds and segment alignment.
3. Runs only its explicit `--self-test` entry under host `qemu-aarch64`. QEMU user mode does NOT boot a kernel or emulate iPhone hardware.
4. Packages a deterministic gzip-compressed `cpio newc` image with `/init`, directories and a `/dev/console` character node (major 5, minor 1).
5. The kernel-mode entry prints diagnostics, attempts to mount proc/sysfs/devtmpfs, and maintains PID 1. **There is no shell in this image**; it is a preliminary console-signalling artifact, not the G3 acceptance criterion.

The build never touches a connected phone. Do not send this artifact to
PongoOS, iBoot, a restore tool or your iPhone 12: no verified A14 entry path
or device-specific Linux kernel and debug console have been established.

## Evidence boundaries

- Successful compilation or ELF checks: native ARM64 userspace *file format* only.
- Successful QEMU user-mode self-test: the ARM64 executable runs in a **host Linux process**.
- A successful archive check: packaging only.
- Actual G2/G3 success would require captured kernel + userspace logs on the **physical iPhone 12** after passing G1 and validating hardware description/console access.

References: [G1 boot-path research](../reports/boot-path-g1-24A437.md),
[development gates](bringup-plan.md).
