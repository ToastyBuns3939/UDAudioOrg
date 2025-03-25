import json
import os
from utils import copy_file_with_logging, show_message
import logging

def process_audio_events(json_file, wem_dir, output_dir, move_back=False):
    """Copies audio files based on DebugName and MediaPathName with logging."""
    logging.debug(f"Processing JSON file: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for event in data:
            if "EventCookedData" in event and "EventLanguageMap" in event["EventCookedData"]:
                for language_map in event["EventCookedData"]["EventLanguageMap"]:
                    if "Value" in language_map and "Media" in language_map["Value"]:
                        for media in language_map["Value"]["Media"]:
                            media_path = media.get("MediaPathName")
                            debug_name = media.get("DebugName")

                            if media_path and debug_name:

                                if move_back:
                                    # Use the .wem filename from DebugName, ignoring .wav extension.
                                    source_path = os.path.join(wem_dir, os.path.basename(debug_name).replace(".wav", ".wem"))
                                    dest_path = os.path.join(output_dir, media_path) #output to the original media path.
                                    logging.debug(f"Move back: Source={source_path}, Dest={dest_path}")
                                else:
                                    source_path = os.path.join(wem_dir, media_path)
                                    debug_name_base = os.path.basename(debug_name)
                                    original_extension = os.path.splitext(media_path)[1]  # Extract extension from media_path
                                    output_filename = f"{os.path.splitext(debug_name_base)[0]}{original_extension}" # Use original extension
                                    dest_path = os.path.join(output_dir, os.path.dirname(debug_name), output_filename)
                                    logging.debug(f"Move forward: Source={source_path}, Dest={dest_path}")

                                copy_file_with_logging(source_path, dest_path)

    except FileNotFoundError:
        show_message("Error", f"File not found: {json_file}", "error")
        logging.error(f"File not found: {json_file}")
    except json.JSONDecodeError:
        show_message("Error", f"Invalid JSON format in {json_file}", "error")
        logging.error(f"Invalid JSON format in {json_file}")
    except Exception as e:
        show_message("Error", f"An unexpected error occurred: {e}", "error")
        logging.error(f"An unexpected error occurred: {e}")

def process_directory(json_dir, wem_dir, output_dir, move_back=False, specific_folder=None):
    """Processes all JSON files within a directory (or specific subfolder) and its subdirectories with logging."""
    logging.debug(f"Processing JSON directory: {json_dir}")
    for root, _, files in os.walk(json_dir):
        if specific_folder is None or os.path.basename(root) == specific_folder or specific_folder in root:
            for filename in files:
                if filename.endswith(".json"):
                    json_path = os.path.join(root, filename)
                    process_audio_events(json_path, wem_dir, output_dir, move_back)