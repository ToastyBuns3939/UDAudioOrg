import logging
import os
from utils import select_directory, configure_logger
from processing import generate_mapping_from_json, unobfuscate_from_mapping, obfuscate_from_mapping, list_ps4_wem_files, find_ps4_wem_duplicates
from json_to_excel import convert_duplicates_json_to_excel # Import the conversion function

def main():
    configure_logger()
    try:
        while True:
            print("\n  UD REMAKE event audio tool")
            print("  This tool assumes you have extracted game data using Fmodel (for PC) or other tools (for PS4).")
            print("==========================================================================")
            print("   PC Version Operations:")
            print("   1. Generate mapping file from [Bates\\Content\\WwiseAudio\\Events] (PC)")
            print("   2. Unobfuscate .wem files from [Bates\\Content\\WwiseStaged] (PC)")
            print("   3. Obfuscate .wem files (PC)")
            print("--------------------------------------------------------------------------")
            print("   PS4 Version Operations:")
            print("   4. Analyze PS4 WEM directory (List all files, find duplicates, and export duplicates to Excel)")
            print("--------------------------------------------------------------------------")
            print("   5. Exit")
            print("==========================================================================")
            choice = input("   Enter your choice (1-5): ")

            if choice == "1":
                json_dir = select_directory(title="Select JSON Directory (PC Events)", initialdir=os.path.join("Bates", "Content", "WwiseAudio", "Events"))
                if json_dir:
                    generate_mapping_from_json(json_dir)
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
                    list_ps4_wem_files(ps4_wem_dir) # Call the function to list files
                    find_ps4_wem_duplicates(ps4_wem_dir) # Call the function to find duplicates (saves JSON)
                    # Automatically call the Excel conversion function
                    convert_duplicates_json_to_excel()
            elif choice == "5":
                print("Exiting.")
                break
            else:
                print("Invalid choice.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
