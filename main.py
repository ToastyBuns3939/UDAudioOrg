import logging
import os
from utils import select_directory, configure_logger
from processing import generate_mapping_from_json, unobfuscate_from_mapping, obfuscate_from_mapping, list_ps4_wem_files, find_ps4_wem_duplicates # find_ps4_wem_duplicates now finds all files
from json_to_excel import convert_duplicates_json_to_excel, convert_mapping_json_to_excel # Import both conversion functions

def main():
    configure_logger()
    try:
        while True:
            print("\n  UD REMAKE event audio tool")
            print("  This tool assumes you have extracted game data using Fmodel (for PC) or other tools (for PS4).")
            print("==========================================================================")
            print("   PC Version Operations:")
            print("   1. Generate mapping file from [Bates\\Content\\WwiseAudio\\Events] (PC) and export to Excel") # Updated description
            print("   2. Unobfuscate .wem files from [Bates\\Content\\WwiseStaged] (PC)")
            print("   3. Obfuscate .wem files (PC)")
            print("--------------------------------------------------------------------------")
            print("   PS4 Version Operations:")
            print("   4. Analyze PS4 WEM directory (List all files, categorize, and export to Excel)")
            print("      Files are categorized by folder prefixes: Act_, Ambience_, Choices, Butterfly_effect_bank,")
            print("      Foley_, Footsteps_, Frontend, Generic_, Global_, music_, Sequences_, SFX_, VFX_, Wendigo_")
            print("--------------------------------------------------------------------------")
            print("   5. Exit")
            print("==========================================================================")
            choice = input("   Enter your choice (1-5): ")

            if choice == "1":
                json_dir = select_directory(title="Select JSON Directory (PC Events)", initialdir=os.path.join("Bates", "Content", "WwiseAudio", "Events"))
                if json_dir:
                    generate_mapping_from_json(json_dir) # Generates wem_mapping.json
                    convert_mapping_json_to_excel() # Automatically convert wem_mapping.json to Excel
            elif choice == "2":
                wem_dir = select_directory(title="Select Source WEM Directory (PC WwiseStaged)", initialdir=os.path.join("Bates", "Content", "WwiseStaged"))
                if not wem_dir:
                    continue
                output_dir = select_directory(title="Select Output Directory for Unobfuscated PC WEMs")
                if not output_dir:
                    continue
                unobfuscate_from_mapping(wem_dir, output_dir)
            elif choice == "3":
                wem_dir = select_directory(title="Select Source WEM Directory (Renamed PC WEMs)", initialdir=os.path.join("Obfuscation", "Export")) # Suggest a potential default
                if not wem_dir:
                    continue
                output_dir = select_directory(title="Select Output Directory for Obfuscated PC WEMs")
                if not output_dir:
                    continue
                obfuscate_from_mapping(wem_dir, output_dir)
            elif choice == "4":
                # Combined PS4 analysis and Excel export
                ps4_wem_dir = select_directory(title="Select the root directory of PS4 WEM files for analysis")
                if ps4_wem_dir:
                    # list_ps4_wem_files(ps4_wem_dir) # This function is now redundant with the updated find_ps4_wem_duplicates
                    find_ps4_wem_duplicates(ps4_wem_dir) # This function now finds and categorizes ALL files (saves JSON as ps4_wem_analysis.json)
                    # Automatically call the Excel conversion function for PS4 analysis
                    convert_duplicates_json_to_excel(json_path="ps4_wem_analysis.json", excel_path="ps4_wem_analysis.xlsx")
            elif choice == "5":
                print("Exiting.")
                break
            else:
                print("Invalid choice.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
