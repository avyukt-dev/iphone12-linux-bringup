# Repository and change policy

- `iphone12-linux-bringup`: scripts, tests, source/boot evidence, reproducible build configuration. Never vendor a full kernel tree into this repository.
- `avyukt-dev/linux`: kernel platform changes and device-tree work only after verifying the target board and datasheets or observed hardware behavior. Keep `hoolock` unchanged; use `research/iphone12-a14`.
- `avyukt-dev/m1n1`: bootloader experiments on `research/iphone12-a14`, leaving `idevice` unchanged. **A source branch is not an A14 entry exploit.**
- Record source SHA and target hardware/firmware before reporting a successful experiment.
- Treat source audits, cross-builds, emulator experiments, and real hardware tests as separate milestones.
- Avoid guessed MMIO/IRQ/device-tree values, writes to phone storage, and steps that risk loss of the original iOS installation.
- Never claim iPhone 12 boot, a working driver, or a complete test server without captured on-device evidence.
- Do not copy code from Sandcastle, Asahi or other projects without checking the applicable license and preserving required notices.
