import logging
import os
from utils import select_directory, configure_logger
from processing import process_directory

def select_event_audio_operation(operation_choice):
    """Handles the selection and execution of event audio operations."""
    if operation_choice == "1":
        select_directories_and_process(False, "Events")
    elif operation_choice == "2":
        select_directories_and_process(True)
    else:
        print("Invalid choice for event audio processing.")

def select_directories_and_process(move_back, specific_json_folder=None):
    """Opens directory selection dialogs and processes the chosen directories."""
    default_json_dir = os.path.join("Bates", "Content", "WwiseAudio")
    initial_json_dir = default_json_dir
    if specific_json_folder:
        initial_json_dir = os.path.join(default_json_dir, specific_json_folder)

    json_dir = select_directory(title="Select JSON Directory", initialdir=initial_json_dir)
    if not json_dir:
        return

    wem_dir = select_directory(title="Select WEM/WwiseStaged Directory (Bates\\Content)", initialdir=os.path.join("Bates", "Content", "WwiseStaged"))
    if not wem_dir:
        return

    output_dir = select_directory(title="Select Output Directory")
    if not output_dir:
        return

    process_directory(json_dir, wem_dir, output_dir, move_back, specific_json_folder)
    print("✔ Operation completed.\n")

def main():
    """Main function to launch event audio processing directly."""
    configure_logger()
    try:
        while True:
            print("  UD REMAKE event audio tool\n\n  This tool assumes that you've already exported the Wwise folders in the WwiseAudio folder\n  as .json files and the WwiseStaged .wem audio files via Fmodel.\n\n   Unobfuscation guide:\n   1. Select Bates\\Content\\WwiseAudio\\Events\n   2. Select Bates\\Content\\WwiseStaged\n   3. Select export directory\n==========================================================================\n   Obfuscation guide:\n   1. Select Bates\\Content\\WwiseAudio\\Events\n   2. Select Obfuscation export directory\n   3. Select export directory\n==========================================================================\n\n  Process event audio:")
            print("   1. Unobfuscate .wem files from Bates\\Content\\WwiseAudio\\Events")
            print("   2. Obfuscate .wem files")
            print("   3. Exit")
            event_audio_choice = input("   Enter 1, 2, or 3: ")

            if event_audio_choice == "3":
                print("Exiting.")
                break
            select_event_audio_operation(event_audio_choice)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
