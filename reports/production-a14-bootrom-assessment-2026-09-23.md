# A14 boot-entry assessment — production versus prototype ROM

Research date: **2026-09-23**. Target: owner-reported physical iPhone 12 `iPhone13,2`, board configuration `D53gAP`, Apple A14/`t8101`, iOS `27.0` (OS build `24A437`). G0 observed those four fields over ordinary iOS USB lockdown; it **did not measure the device's Boot ROM revision**. These identifiers are not interchangeable.

## Newly reviewed primary research

Proteas, “usbliter8 on A14,” published 2026-08-31:
https://proteas.github.io/sec/2026/08/31/usbliter8-on-a14.html

The author compares three A14 application-processor Boot ROM revisions. Reported USB DART/DMA configurations differ; the reported *usbliter8* susceptibility differs with them:

| A14 silicon/ROM class in the research | Boot ROM build reported by researcher | Researcher's usbliter8 conclusion |
| --- | --- | --- |
| A0 / early development | `iBoot-5281.0.0.100.22` | Affected |
| B0 / intermediate development | `iBoot-5281.0.0.100.34` | Affected |
| B1 / production | `iBoot-5281.0.0.100.45` | **Not affected** |

**Precision:** The “iBoot-...” string in the above table identifies the *Boot ROM build* in the research; it must not be confused with the updatable, later-stage iBoot component or the separately observed iOS `BuildVersion=24A437`. The owner's read-only iOS diagnostic output establishes neither a Boot ROM build nor a working payload entry.

The public T8101 hardware catalogue also lists `5281.0.0.100.45` as the production Boot ROM: https://theapplewiki.com/wiki/BootROM and https://www.theiphonewiki.com/wiki/bootrom . This is a **public device-model expectation**, not an independent read of the owner's phone.

**Interpretation:** A statement such as “usbliter8 affects A14” is true of the researcher's A0/B0 prototype ROM revisions, but is **not** evidence of an entry on a regular production iPhone 12. The production A14 B1 result is method-specific: it is *not* evidence that every conceivable Boot ROM, later-stage, or future boot method is impossible.

## Other evaluated boot routes and missing requirements

| Route / artifact | What existing published work actually shows | Applicability to observed iPhone 12 |
| --- | --- | --- |
| checkm8 via Hoolock / palera1n / PongoOS | Hoolock's published instructions are for A7–A11/T2 devices; custom payload loading follows an existing supported-device exploit entry. Source: https://github.com/HoolockLinux/docs/blob/master/README.md and https://github.com/HoolockLinux/docs/blob/master/tutorials/SETUP_pongoOS.md . | No supported A14 custom-code entry demonstrated. m1n1's presence in a fork cannot supply that missing prior stage. |
| usbliter8 on A12/A13 | A12/A13 research establishes a different set of affected Boot ROM revisions; the later Proteas report finds a specific vulnerability in *pre-production* A14, not production A14 B1. | Do not transpose prototype A14 proof or A12/A13 instructions to production A14. |
| iOS app, SSH, ordinary jailbreak or iOS lockdown USB | Can run code or read identity inside Apple's running iOS environment. | **Not** evidence of unsigned native kernel execution or control of the Boot ROM/iBoot chain. |
| QEMU generic ARM64 boot, m1n1 binary, Linux kernel image, device tree | Can validate build formats or generic ARM64 boot integration; host VM has different hardware and firmware. | Does not provide an iPhone 12 execution entry or hardware compatibility evidence. |

Apple's security architecture documents signature checks through Boot ROM, iBoot and kernel: https://support.apple.com/en-in/guide/security/secb3000f149/web . The ability to communicate with an unlocked, paired iPhone does not bypass those checks.

## Evidence required to reopen G1

A new claim of iPhone 12 boot support should *first* supply: (1) an authoritative public technical source and a reproducible payload launch method explicitly covering **production A14 / `t8101`**, rather than pre-production silicon or A12/A13; (2) exact target **hardware/ROM variant** and supported iOS/iBoot constraints; (3) captured execution of a custom payload *outside iOS*, with an observable and identified boot stage; (4) a credible **non-destructive, device-specific recovery procedure**. A source read, compile or demonstration on a different device does not satisfy these requirements. An alternative method need not rely on the same USB vulnerability; assess its exact prerequisites independently.

Decision on 2026-09-23: **No demonstrated, compatible, publicly documented native-boot method emerged from these reviewed sources for an ordinary production iPhone 12. G1 remains BLOCKED**, pending a genuinely new compatible entry route. Do **not** try the A14 A0/B0 proof, A12/A13 exploits, older-chip palera1n/PongoOS commands, guessed MMIO, restore, or partition modifications against the owner's production phone. No extra device observation is needed merely to reconfirm an iOS version or to run an unsuitable exploit.

Source URLs and the result are research snapshots; revisit claims and validate exact device coverage before any subsequent experiment.
