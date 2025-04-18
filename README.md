# UNTIL DAWN REMAKE Audio renamer

The latest nightly build of FModel is required for a proper dump of the `Events` json files.
This tool assumes that you already got both `WwiseAudio` and `WwiseStaged` folders extracted from Until Dawn via FModel.
This tool also only works with extracted `.json` and `.wem` files from that game.

## Guide
1. Generate `wem_mapping.json` file from `Bates\Content\WwiseAudio\Events`
2. Unobfuscate `.wem` files from `Bates\Content\WwiseStaged`
3. Obfuscate renamed `.wem` files to their original random ID names
