import json
import os
import logging
from utils import copy_file_with_logging

def process_audio_events(json_file, wem_dir, output_dir, move_back=False, error_list=None, mapping=None):
    """Processes a single JSON file and copies associated .wem files."""
    logging.info(f"Processing: {json_file}")
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

                            if not media_path or not debug_name:
                                continue

                            if move_back:
                                # Obfuscation mode
                                mapped_debug_name = mapping.get(media_path) if mapping else None
                                if not mapped_debug_name:
                                    if error_list is not None:
                                        error_list.append(f"Mapping missing for: {media_path}")
                                    continue

                                wem_filename = os.path.basename(mapped_debug_name).replace(".wav", ".wem")
                                source_path = os.path.normpath(os.path.join(wem_dir, wem_filename))
                                dest_path = os.path.normpath(os.path.join(output_dir, media_path))
                            else:
                                # Unobfuscation mode
                                source_path = os.path.normpath(os.path.join(wem_dir, media_path))
                                debug_name_base = os.path.basename(debug_name)
                                original_extension = os.path.splitext(media_path)[1]
                                output_filename = f"{os.path.splitext(debug_name_base)[0]}{original_extension}"
                                dest_path = os.path.normpath(os.path.join(output_dir, os.path.dirname(debug_name), output_filename))

                                if mapping is not None:
                                    mapping[media_path] = debug_name

                            success = copy_file_with_logging(source_path, dest_path)
                            if not success and move_back and error_list is not None:
                                error_list.append(f"File not found: {source_path}")

    except FileNotFoundError:
        logging.error(f"File not found: {json_file}")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in {json_file}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def process_directory(json_dir, wem_dir, output_dir, move_back=False, specific_folder=None):
    """Processes all JSON files in a directory. Uses or builds mapping depending on mode."""
    mapping = {} if not move_back else None
    error_list = [] if move_back else None

    # Load mapping if obfuscating
    if move_back:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(script_dir, "wem_mapping.json")
        if os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        else:
            print("❌ Mapping file not found. Run unobfuscation first to generate it.")
            return

    for root, _, files in os.walk(json_dir):
        if specific_folder is None or os.path.basename(root) == specific_folder or specific_folder in root:
            for filename in files:
                if filename.endswith(".json"):
                    json_path = os.path.join(root, filename)
                    process_audio_events(json_path, wem_dir, output_dir, move_back, error_list, mapping)

    # Save mapping if unobfuscating
    if not move_back and mapping:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(script_dir, "wem_mapping.json")
        with open(map_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2)
        print(f"✅ Mapping saved to: {map_path}")

    # Save error log if any errors occurred during obfuscation
    if move_back and error_list:
        if error_list:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            error_log_path = os.path.join(script_dir, "error_log.log")
            with open(error_log_path, "w", encoding="utf-8") as f:
                for error in error_list:
                    f.write(f"{error}\n")
            print(f"⚠ Some files were not found or mapped. See error log: {error_log_path}")
