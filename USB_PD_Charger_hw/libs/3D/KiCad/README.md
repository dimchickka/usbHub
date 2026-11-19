# Project copies of KiCad 3D models

These STEP files were downloaded from the [official KiCad 3D model library](https://gitlab.com/kicad/libraries/kicad-packages3D). The repository license is included in `LICENSE.md`. Board and project footprint references use `${KIPRJMOD}`, so these models resolve without a local KiCad model installation.

The following models are visual package equivalents, not verified mechanical models of the exact purchased parts:

- CJAB25N04S: DFN-8 3 × 3 mm
- TMPC1265 inductor: Sunlord MWSA1265S
- Omron XF2M 40-pin FFC: Hirose FH12 40-pin FFC
- SOT-89-5 regulator: SOT-89-3 body
- PLS-7 header: generic 1 × 7 2.54 mm pin header
- DPAK diode: generic TO-252-3 package

Check these models against the manufacturer's mechanical drawings before using a 3D assembly for enclosure design. The copper footprints are not changed by the substitutions.

The `USBC_10PF-074.STEP` file at `../USBC_10PF-074.STEP` is the model used by the identical `Connectors:USBC_DS1144-18` footprint in the LoRa_Project board. It was copied from that board's KiCad library installation and is now project-local.
