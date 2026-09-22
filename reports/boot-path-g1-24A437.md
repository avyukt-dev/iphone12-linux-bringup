# G1 boot-entry feasibility: observed iPhone 12 on iOS 27.0 (24A437)

Date: 2026-09-22. **Research status: no verified A14 custom-code boot path.** This document separates physical identity facts from boot-execution evidence.

## Physical device observation

The owner ran `python3 scripts/collect_device_facts.py` against the connected phone on a trusted Linux host. The third execution returned all four requested keys successfully:

| Query | Observed value |
| --- | --- |
| ProductType | `iPhone13,2` |
| HardwareModel | `D53gAP` |
| ProductVersion | `27.0` |
| BuildVersion | `24A437` |

The first two executions reported `device_query_failed` for all four keys. The reason for those failures is **unidentified**; subsequent success establishes ordinary USB-lockdown diagnostic communication, not a DFU, iBoot or boot-chain capability. The collector does not query identifiers unique to the owner or device. The owner-supplied output has not been independently re-run by project maintainers.

Public identifiers for the iPhone 12 match `t8101` / A14 and the board configuration above: https://ipsw.me/iPhone13%2C2/info/ . Public firmware listings also associate iOS 27.0 with build 24A437 for this device: https://ipsw.dev/iPhone13%2C2 .

## Explicit boot-chain prerequisite

Apple documents signature verification along the iPhone Boot ROM → iBoot → iOS kernel chain: https://support.apple.com/en-au/guide/security/secb3000f149/web . The fact that an iPhone responds to `ideviceinfo`, can run an iOS app, or can be placed in ordinary recovery mode does **not** authorize the execution of an unsigned native Linux kernel.

| Candidate path | Reviewed evidence | Status on iPhone 12 / A14 / 24A437 |
| --- | --- | --- |
| Hoolock m1n1 via PongoOS | [Hoolock PongoOS guide](https://github.com/HoolockLinux/docs/blob/master/tutorials/SETUP_pongoOS.md) invokes palera1n to gain a supported-device boot entry before sending m1n1 and Linux. [Supported devices](https://github.com/HoolockLinux/docs/blob/master/README.md) list A7–A11 and T2. | **Unverified / no published A14 adaptation in these sources.** Compiling m1n1 or PongoOS does not establish an A14 boot entry. |
| Hoolock m1n1 via iBoot / restore-like mode | [Hoolock iBoot guide](https://github.com/HoolockLinux/docs/blob/master/tutorials/SETUP_iBoot.md) documents an exploit-dependent preparation on its supported older devices before modified boot images can be loaded. | **Unverified for A14.** Normal iBoot/recovery mode is not an arbitrary-code loader. No execution test is authorized at this stage. |
| checkm8 / ipwndfu | [ipwndfu README](https://github.com/axi0mX/ipwndfu/blob/master/README.md) enumerates supported older chip codes through `t8015`; it does not list `t8101`. | **Not a documented A14 entry point.** Do not attempt an older-device exploit against this phone on the assumption it will work. |
| Existing kernel or m1n1 branches | [Pinned source audit](a14-baseline-2026-09-22.md) found no `t8101` DTB declaration in the selected kernel, while the m1n1 fork contains a chainloader. | **No on-device boot evidence.** A chainloader requires an earlier authorized entry; a DTB is additionally required for meaningful kernel bring-up. |

The table is scoped to the *reviewed projects and public documentation*. It is **not** proof that no undisclosed exploit or alternative A14 research route exists.

## Decision and next experimental gate

- G0 (model / board / firmware identity and initial source audit): complete. Full hardware register map, host recovery exercise, and console details are **not** established by G0.
- G1: blocked pending a reproducible, authorized route to run a small custom test payload *outside iOS* on `iPhone13,2` / `D53gAP` / `24A437`, with observable logs and a device-specific recovery plan. A mere jailbreak, a signed OS restore, a successful kernel build or a device-tree declaration does not meet this acceptance condition.
- G2+: kernel initialization, RAM filesystem and networking are not yet demonstrated and must not be represented as implemented.

**No phone-modifying commands or speculative boot firmware patches are authorized by this research.** Future kernel/bootloader changes need their own evidence, review, and non-destructive test plan. Do not publish serial number, UDID, ECID, IMEI, pairing files or raw unfiltered device logs.
