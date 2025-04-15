import logging
import os
from utils import select_directory, configure_logger
from processing import generate_mapping_from_json, unobfuscate_from_mapping, obfuscate_from_mapping

def main():
    configure_logger()
    try:
        while True:
            print("  UD REMAKE event audio tool\n\n  This tool assumes that you've already exported the Wwise folders in the WwiseAudio folder\n  as .json files and the WwiseStaged .wem audio files via Fmodel.")
            print("==========================================================================")
            print("   1. Generate mapping file from [Bates\\Content\\WwiseAudio\\Events]")
            print("   2. Unobfuscate .wem files from [`]Bates\\Content\\WwiseStaged]")
            print("   3. Obfuscate .wem files")
            print("   4. Exit")
            print("==========================================================================")
            choice = input("   Enter 1, 2, 3, or 4: ")

            if choice == "1":
                json_dir = select_directory(title="Select JSON Directory", initialdir=os.path.join("Bates", "Content", "WwiseAudio", "Events"))
                if json_dir:
                    generate_mapping_from_json(json_dir)
            elif choice == "2":
                wem_dir = select_directory(title="Select Source WEM Directory (WwiseStaged)", initialdir=os.path.join("Bates", "Content", "WwiseStaged"))
                if not wem_dir:
                    continue
                output_dir = select_directory(title="Select Output Directory")
                if not output_dir:
                    continue
                unobfuscate_from_mapping(wem_dir, output_dir)
            elif choice == "3":
                wem_dir = select_directory(title="Select Obfuscated WEM Directory (named using DebugName)", initialdir=os.path.join("Obfuscation", "Export"))
                if not wem_dir:
                    continue
                output_dir = select_directory(title="Select Output Directory")
                if not output_dir:
                    continue
                obfuscate_from_mapping(wem_dir, output_dir)
            elif choice == "4":
                print("Exiting.")
                break
            else:
                print("Invalid choice.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
