# main.py
import datetime
import logging
import os
from utils import select_directory, show_message, configure_logger, close_and_remove_handlers
from processing import process_directory
from dialogue_organizer import organize_dialogue_json_files  # Import the new function

def select_event_audio_operation(operation_choice):
    """Handles the selection and execution of event audio operations."""
    if operation_choice == "1":
        select_directories_and_process(False, "Events")
    elif operation_choice == "2":
        select_directories_and_process(True)
    else:
        print("Invalid choice for event audio processing.")

def select_directories_and_process(move_back, specific_json_folder=None):
    """Opens directory selection dialogs and processes the chosen directories with logging."""
    default_json_dir = os.path.join("Bates", "Content", "WwiseAudio")
    initial_json_dir = default_json_dir
    json_prompt = f"Select JSON Directory ({default_json_dir})"
    if specific_json_folder:
        initial_json_dir = os.path.join(default_json_dir, specific_json_folder)
        json_prompt = f"Select JSON Directory ({os.path.join(default_json_dir, specific_json_folder)})"

    json_dir = select_directory(title=json_prompt, initialdir=initial_json_dir)
    if not json_dir:
        logging.debug("JSON directory selection canceled.")
        return

    wem_dir = select_directory(title="Select WEM Directory (Bates\\Content\\WwiseStaged)", initialdir=os.path.join("Bates", "Content", "WwiseStaged"))
    if not wem_dir:
        logging.debug("WEM directory selection canceled.")
        return

    output_dir = select_directory(title="Select Output Directory")
    if not output_dir:
        logging.debug("Output directory selection canceled.")
        return

    process_directory(json_dir, wem_dir, output_dir, move_back, specific_json_folder)
    show_message("Complete", "Operation completed.")
    logging.info("Operation completed.")

def main():
    """Main function to handle command-line arguments and processing."""
    log_file_name = f"wem_processor_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    configure_logger(log_file_name)
    logging.info(f"Log file created: {log_file_name}")
    try:
        print("Choose operation:")
        print("1. Process event audio")
        print("2. Process dialogue files")  # Modified choice

        main_choice = input("Enter 1 or 2: ")

        if main_choice == "1":
            print("  Process event audio:")
            print("   1. Unobfuscate .wem files from Bates\\Content\\WwiseAudio\\Events (DebugName -> Output)")
            print("   2. Obfuscate .wem files (MediaPathName -> Output)")
            event_audio_choice = input("   Enter 1 or 2: ")
            select_event_audio_operation(event_audio_choice)
        elif main_choice == "2":
            print("Process dialogue files:")
            source_dialogue_dir = select_directory(title="Select Source Dialogue JSON Directory (Bates\\Content\\WwiseAudio\\ExternalSources)", initialdir=os.path.join("Bates", "Content", "WwiseAudio", "ExternalSources"))
            if source_dialogue_dir:
                output_dialogue_dir = select_directory(title="Select Output Dialogue JSON Directory")
                if output_dialogue_dir:
                    organize_dialogue_json_files(source_dialogue_dir, output_dialogue_dir)  # Call the function from dialogue_organizer.py
                    show_message("Complete", "Dialogue file organization completed.")
                    logging.info("Dialogue file organization completed.")
        else:
            print("Invalid choice.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        close_and_remove_handlers()

if __name__ == "__main__":
    main()