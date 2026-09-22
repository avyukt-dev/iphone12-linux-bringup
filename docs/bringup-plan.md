# Engineering gates for native Linux on iPhone 12 (A14 / T8101)

**Scope:** first headless Linux boot, then console, networking, SSH, and an HTTP test server. No display, camera, cellular, persistent installation, or write access to iOS storage during initial bring-up.

## G0: Document exact hardware and source baselines (host only)
- Record the precise device model/board code and firmware build from evidence, not a guessed memory map.
- Record exact kernel and bootloader commit SHAs; audit driver and device-tree declarations.
- Establish a documented host-side diagnostic transport and a non-destructive recovery procedure.
- Evidence: source inventory and references to actual hardware/firmware data.

## G1: Demonstrate an A14 custom-code boot path (blocking)
- Establish a repeatable, authorized way to launch a custom payload outside iOS on the exact device and firmware build.
- Evidence: observed payload output, boot-stage identification, and demonstrated recovery path.
- A cross-compiled kernel, a jailbreak, or an added device-tree entry does *not* satisfy G1.

## G2: Boot the native ARM64 Linux kernel
- Validate CPU, RAM, exception levels, interrupt controller, clocks/timers and device-tree information for this board.
- Evidence: captured, reproducible kernel log and initramfs handoff. Never use unverified hardware register values.

## G3: Run a headless userspace
- Boot a minimal initramfs with shell and commands. Do not write internal storage.
- Evidence: native Linux shell output tied to device/boot log.

## G4: Connect host and run a test server
- Validate a real USB or wireless transport, then add SSH and a small HTTP server.
- Evidence: remote terminal and repeatable HTTP request served by the device.

## Explicitly out of scope
- Guessing A14 register addresses or porting device-tree addresses solely from A10/A11/M1.
- Flashing, partition editing, altering iOS boot policy, persistent installation, or production use until a verified boot/recovery path exists.
- Claims that Hoolock's older-device chainloader automatically provides a boot exploit on A14.
