# Until Dawn Remake - Audio Renamer Tool

This tool helps manage `.wem` audio files extracted from the **Until Dawn Remake**. It currently supports renaming obfuscated PC files, analyzing files from PS4 extractions, and automatically converting PS4 analysis results to a multi-sheet Excel file.

## Prerequisites

1. **Game:** Until Dawn Remake (PC or PS4 version).

2. **Extraction Tool:** A tool capable of extracting game assets, such as **FModel** for PC (a **recent nightly build** is required for PC JSON data) or other tools for PS4 assets.

3. **Extracted Game Data:** You **must** have already extracted the relevant audio files and/or metadata.

4. **Python Libraries:** For the Excel conversion, you need `pandas` and `openpyxl` (`pip install pandas openpyxl`).

## How it Works

* **PC Version:** Wwise audio often uses numeric IDs for filenames. This tool reads `.json` files (extracted by FModel from the PC version's `Events` folder) to create a map between these IDs and their descriptive event names. It then uses this map to rename the corresponding `.wem` files found in the `WwiseStaged` folder. It can also revert this process.

* **PS4 Version:** The PS4 version's files may already have descriptive names within their folder structure. This tool can analyze **all** `.wem` files within a specified directory, listing their paths relative to the chosen root directory and indicating which ones appear in multiple locations. Files are categorized by common folder prefixes (Act\_, Ambience\_, Choices, Butterfly_effect_bank, Foley\_, Footsteps\_, Frontend, Generic\_, Global\_, music\_, Sequences\_, SFX\_, VFX\_, Wendigo\_). This analysis automatically generates a JSON file and converts it to a multi-sheet Excel file.

* **JSON to Excel Conversion:** A separate script is provided to convert the PS4 analysis JSON output into a more user-friendly Excel format.

## Usage Guide

Run the `main.py` script from your terminal. Follow the on-screen prompts to select the desired operation.

1. **Generate Mapping (PC):**

   * **Input:** Path to the PC version's `Bates\Content\WwiseAudio\Events` folder (extracted as `.json`).

   * **Output:** Generates `wem_mapping.json` in the script's directory.

2. **Rename .wem Files (Unobfuscate PC):**

   * **Prerequisite:** Generate the PC mapping first (Option 1).

   * **Input:** Path to the PC version's `Bates\Content\WwiseStaged` folder (containing the original `.wem` files).

   * **Output:** A folder containing the renamed `.wem` files.

3. **Revert Renaming (Obfuscate PC):**

   * **Prerequisite:** Generate the PC mapping first (Option 1).

   * **Input:** Path to the folder containing the *renamed* PC `.wem` files.

   * **Output:** A folder containing the `.wem` files renamed back to their original IDs.

4. **Analyze PS4 WEM directory:**

   * **Input:** Path to the root directory containing the PS4 `.wem` files (e.g., `UD_PS4_WEM`).

   * **Output:**

     * Generates `ps4_wem_analysis.json` (listing **all** `.wem` files found, their respective paths *relative to the input directory*, and a list of *all* categories the file appears in, organized by categories like "Act\_", "Ambience\_", etc., with "Other" listed last) in the script's directory.

     * **Automatically** generates `ps4_wem_analysis.xlsx` containing the same information, with each category of files placed in a separate worksheet. Each row in the Excel file will include a column listing all the categories that specific filename was found in.

5. **Exit**

To convert the `ps4_wem_analysis.json` file to Excel manually (if needed):

* Run the `json_to_excel.py` script from your terminal (`python json_to_excel.py`). This will create `ps4_wem_analysis.xlsx` in the same directory.

## Important Notes

* The PC mapping and renaming functions are specifically designed for `.json` and `.wem` files extracted from the **Until Dawn Remake PC** via **FModel**.

* The PS4 analysis function is a general utility to inventory and categorize all `.wem` files within a directory structure.

* The accuracy of PC renaming depends entirely on the quality and completeness of the extracted `Events` JSON data from FModel.

* Excel sheet names have a character limit (typically 31 characters) and cannot contain certain characters. The script attempts to sanitize category names for use as sheet names.