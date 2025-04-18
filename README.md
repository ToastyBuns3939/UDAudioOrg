# Until Dawn Remake - Audio Renamer Tool

This tool helps rename the obfuscated `.wem` audio files extracted from the **Until Dawn Remake** using FModel, giving them meaningful names based on their in-game events.

## Prerequisites

1.  **Game:** Until Dawn Remake (PC version assumed).
2.  **FModel:** The **newest nightly build** is required. Older versions might not correctly extract the `Events` JSON data needed for mapping. Download from [FModel's GitHub Releases](https://github.com/4sval/FModel/releases) or [official website](https://fmodel.app/).
3.  **Extracted Game Data:** You **must** have already used FModel to extract the following complete folders from the game's assets:
    * `[Your_FModel_Output_Path]\Bates\Content\WwiseAudio\Events` (Extract everything here as `.json` files)
    * `[Your_FModel_Output_Path]\Bates\Content\WwiseStaged` (Contains `.wem` audio files with random ID names)

## How it Works

Wwise audio often uses numeric IDs for filenames. This tool reads the `.json` files in the `Events` folder (extracted by FModel) to create a map between these IDs and their descriptive event names. It then uses this map to rename the corresponding `.wem` files found in the `WwiseStaged` folder.

## Usage Guide


1.  **Generate Mapping:**
    * **Input:** Path to the `Bates\Content\WwiseAudio\Events` folder.
    * **Output:** This will generate a mapping file (e.g., `wem_mapping.json`) in the same folder as the script. This file will be needed by the script for both unbobfuscation and obfuscation process.

2.  **Rename .wem Files (Unobfuscate):**

    * **Input:**
        * Path to the `Bates\Content\WwiseStaged` folder (containing the original `.wem` files).
    * **Output:** A folder containing the renamed `.wem` files.

3.  **Revert Renaming (Obfuscate):**
    * Run the tool's function responsible for reverting names.
    * **Input:**
        * Path to the folder containing the *renamed* `.wem` files.
    * **Output:** A folder containing the `.wem` files renamed back to their original IDs (or renames them in place).

## Important Notes

* This tool is specifically designed for `.json` and `.wem` files extracted from the **Until Dawn Remake** via **FModel**. It will likely not work for other games or extraction methods.
* The accuracy of the renaming depends entirely on the quality and completeness of the extracted `Events` JSON data from FModel.
* Do note that some `.wem` files extracted might be corrupted due to the work in progress nature of **FModel**
