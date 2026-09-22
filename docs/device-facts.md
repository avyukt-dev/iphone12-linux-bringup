# G0: collect non-unique facts from the physical iPhone 12

This is the first hardware-observation checkpoint. **No jailbreak, exploit, kernel boot,
recovery/DFU mode, partition write or firmware change is requested.**

We need four non-unique values from the actual connected phone:
\`ProductType\`, \`HardwareModel\`, \`ProductVersion\`, and \`BuildVersion\`.
The public iPhone 12 catalog is not a measurement of your particular phone.

## On the Linux host

1. Install the ordinary, open-source iOS diagnostic tools:
   \`sudo apt update && sudo apt install -y libimobiledevice-utils usbmuxd\`.
   WSL2 users may need to configure USB passthrough; a native Linux USB host is simpler.
2. Connect **only the target phone** over a USB data cable. Unlock it and confirm the
   normal Trust This Computer prompt if needed. If not already paired, perform ordinary
   USB pairing; this is **not** a jailbreak or a firmware operation.
3. In your local checkout of this project, run:

\`\`\`bash
python3 scripts/collect_device_facts.py
\`\`\`

Share only the resulting small JSON object from this script. It queries exactly four
allowlisted keys, one at a time, with \`ideviceinfo -s -k KEY\` (the \`-s\` mode
avoids automatic pairing), checks their format and **does not** query or log the
device name, UDID, serial number, ECID, IMEI, Wi-Fi MAC address or the full
unfiltered \`ideviceinfo\` dump. No unique identifiers are needed for G0.

If your phone is not paired, the tool may report \`device_query_failed\` for the
requested keys. That is an incomplete observation, **not** evidence that the
hardware is unsupported. Do not share pairing records or private debugging logs.

## What a result can establish

- \`target_product_type_verified: true\`: the attached, responding phone reports
  \`iPhone13,2\` (assuming there is only one phone connected).
- \`HardwareModel\`: board configuration reported through the ordinary iOS interface.
- \`ProductVersion\` and \`BuildVersion\`: measured firmware identifiers used to
  scope subsequent research and avoid confusing firmware releases.
- \`boot_chain_verified: false\`: **always false** here. iOS lockdown information
  cannot establish that a custom A14 kernel can boot.

Do not fabricate a result by editing the JSON: any fixture used by unit tests is
synthetic and must not be presented as live device evidence.

See upstream tool documentation:
https://github.com/libimobiledevice/libimobiledevice/blob/master/docs/ideviceinfo.1
and https://libimobiledevice.org/ .
