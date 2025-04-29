import json
import os
import logging
import multiprocessing
from collections import defaultdict # Import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import copy_file_with_logging

MAX_WORKERS = multiprocessing.cpu_count() * 2

def generate_mapping_from_json(json_dir, specific_folder=None):
    """
    Generates a mapping from PC version JSON files to Wwise IDs and DebugNames,
    including the source JSON files (relative paths to the input json_dir) for each mapping.
    This is specifically for the PC version's obfuscated files.
    """
    mapping = {} # Structure will be {MediaPathName: {"DebugName": "...", "SourceJsons": [...]}}
    total_files = 0
    logging.info(f"Starting PC mapping generation from JSON directory: {json_dir}")

    # The base path for relative paths will be the input json_dir
    base_path_for_relative = os.path.normpath(json_dir)
    # Ensure consistent separators and trailing slash for reliable comparison
    if not base_path_for_relative.endswith(os.sep):
        base_path_for_relative += os.sep


    for root, _, files in os.walk(json_dir):
        if specific_folder is None or os.path.basename(root) == specific_folder or specific_folder in root:
            for filename in files:
                if filename.endswith(".json"):
                    json_path = os.path.join(root, filename)
                    logging.info(f"📄 Scanning: {json_path}")
                    total_files += 1
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # Calculate the relative path for the source JSON using os.path.relpath
                        relative_json_path = os.path.relpath(json_path, json_dir)
                        # Normalize separators for consistency
                        relative_json_path = relative_json_path.replace("\\", "/")


                        for event in data:
                            if "EventCookedData" in event and "EventLanguageMap" in event["EventCookedData"]:
                                for lang_map in event["EventCookedData"]["EventLanguageMap"]:
                                    if "Value" in lang_map and "Media" in lang_map["Value"]:
                                        for media in lang_map["Value"]["Media"]:
                                            media_path = media.get("MediaPathName")
                                            debug_name = media.get("DebugName")
                                            if media_path and debug_name:
                                                if media_path not in mapping:
                                                    # New MediaPathName, create entry
                                                    mapping[media_path] = {
                                                        "DebugName": debug_name,
                                                        "SourceJsons": [relative_json_path] # Store relative path
                                                    }
                                                    logging.debug(f"  - New mapping for {media_path}: {debug_name} from {relative_json_path}")
                                                else:
                                                    # Existing MediaPathName
                                                    # Add the current relative JSON path to the list if not already present
                                                    if relative_json_path not in mapping[media_path]["SourceJsons"]:
                                                         mapping[media_path]["SourceJsons"].append(relative_json_path)

                                                    # Check for conflicting DebugNames
                                                    if mapping[media_path]["DebugName"] != debug_name:
                                                        logging.warning(f"⚠️ Conflicting DebugName for {media_path}: Found '{debug_name}' in {relative_json_path}, already mapped as '{mapping[media_path]['DebugName']}'")
                                                        # Keep the latest DebugName found (or could choose first, or list them)
                                                        mapping[media_path]["DebugName"] = debug_name
                                                    logging.debug(f"  - Updated mapping for {media_path}: added {relative_json_path}")

                    except Exception as e:
                        logging.error(f"❌ Failed to process {json_path}: {e}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "wem_mapping.json")

    # Write the mapping to a JSON file with sorted keys
    with open(map_path, "w", encoding="utf-8") as f:
        # Sort the source JSON lists within each entry for consistent output
        sorted_mapping = {}
        for media_path, data in sorted(mapping.items()):
             data["SourceJsons"] = sorted(data["SourceJsons"])
             sorted_mapping[media_path] = data

        json.dump(sorted_mapping, f, indent=2)

    logging.info(f"✅ PC mapping generated and saved to: {map_path} ({len(mapping)} entries from {total_files} file(s))")

def threaded_copy_tasks(copy_tasks):
    """Helper function to execute file copy tasks using a thread pool."""
    success_count = 0
    error_list = []

    # Ensure destination directories exist before starting threads
    for _, dst in copy_tasks:
        os.makedirs(os.path.dirname(dst), exist_ok=True)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit copy tasks to the thread pool
        future_to_task = {executor.submit(copy_file_with_logging, src, dst): (src, dst) for src, dst in copy_tasks}

        # Process results as they complete
        for future in as_completed(future_to_task):
            src, _ = future_to_task[future]
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    error_list.append(f"File not found or failed: {src}")
            except Exception as e:
                error_list.append(f"Exception while copying {src}: {e}")

    return success_count, error_list

def unobfuscate_from_mapping(wem_dir, output_dir):
    """
    Unobfuscates WEM files using the PC version mapping.
    Renames files from Wwise ID to DebugName. Reads new mapping structure.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "wem_mapping.json")

    if not os.path.exists(map_path):
        logging.error("❌ wem_mapping.json (PC mapping) not found. Please generate it first using option 1.")
        return

    with open(map_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    copy_tasks = []

    # Create copy tasks: source is Wwise ID path, destination is DebugName path
    # Iterate through the mapping, accessing DebugName from the nested structure
    for media_path, map_data in mapping.items():
        debug_name = map_data.get("DebugName") # Get DebugName from the nested object
        if not debug_name:
             logging.warning(f"⚠️ Missing DebugName for {media_path} in mapping, skipping.")
             continue

        source_path = os.path.normpath(os.path.join(wem_dir, media_path))
        debug_base = os.path.basename(debug_name)
        ext = os.path.splitext(media_path)[1] # Use original extension
        output_filename = f"{os.path.splitext(debug_base)[0]}{ext}"
        dest_path = os.path.normpath(os.path.join(output_dir, os.path.dirname(debug_name), output_filename))
        copy_tasks.append((source_path, dest_path))

    logging.info(f"Starting unobfuscation of {len(copy_tasks)} files...")
    success_count, error_list = threaded_copy_tasks(copy_tasks)

    logging.info(f"✅ PC Unobfuscation completed. Files copied: {success_count}")
    if error_list:
        log_path = os.path.join(script_dir, "unobfuscate_error_log.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for line in error_list:
                f.write(f"{line}\n")
        logging.warning(f"⚠️ Some files could not be copied during unobfuscation. See: {log_path}")

def obfuscate_from_mapping(wem_dir, output_dir):
    """
    Obfuscates WEM files using the PC version mapping.
    Renames files from DebugName back to Wwise ID. Reads new mapping structure.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "wem_mapping.json")

    if not os.path.exists(map_path):
        logging.error("❌ wem_mapping.json (PC mapping) not found. Please generate it first using option 1.")
        return

    with open(map_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    copy_tasks = []

    # Create copy tasks: source is DebugName path, destination is Wwise ID path
    # Need to build an inverted mapping from the new structure: DebugName -> MediaPathName
    inverted_mapping = {}
    for media_path, map_data in mapping.items():
        debug_name = map_data.get("DebugName")
        if debug_name:
             # If multiple MediaPaths map to the same DebugName, the last one processed wins
             if debug_name in inverted_mapping:
                 logging.warning(f"⚠️ Duplicate DebugName '{debug_name}' found in mapping. Keeping mapping to '{media_path}' and discarding mapping to '{inverted_mapping[debug_name]}'.")
             inverted_mapping[debug_name] = media_path
        else:
             logging.warning(f"⚠️ Missing DebugName for {media_path} in mapping, cannot create inverted mapping entry.")


    for debug_name, media_path in inverted_mapping.items():
        # The source file will have the debug name, potentially with .wem extension
        # based on how the unobfuscation saved it.
        # We need to account for both .wav (from debug_name) and .wem extensions.
        source_base = os.path.splitext(debug_name)[0]
        source_path_wem = os.path.normpath(os.path.join(wem_dir, f"{source_base}.wem"))
        source_path_wav = os.path.normpath(os.path.join(wem_dir, f"{source_base}.wav")) # Might exist if converted

        # Determine the actual source file path
        source_file_found = None
        if os.path.exists(source_path_wem):
            source_file_found = source_path_wem
        elif os.path.exists(source_path_wav):
             source_file_found = source_path_wav

        if source_file_found:
            # The destination path is the original Wwise ID path
            dest_path = os.path.normpath(os.path.join(output_dir, media_path))
            copy_tasks.append((source_file_found, dest_path))
        else:
            logging.warning(f"⚠️ Source file not found for obfuscation: {source_path_wem} or {source_path_wav} (expected from debug name: {debug_name})")


    logging.info(f"Starting obfuscation of {len(copy_tasks)} files...")
    success_count, error_list = threaded_copy_tasks(copy_tasks)

    logging.info(f"✅ PC Obfuscation completed. Files copied: {success_count}")
    if error_list:
        log_path = os.path.join(script_dir, "obfuscate_error_log.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for line in error_list:
                f.write(f"{line}\n")
        logging.warning(f"⚠️ Some files could not be copied during obfuscation. See: {log_path}")


def list_ps4_wem_files(ps4_wem_dir):
    """
    Lists all .wem files within a given directory for the PS4 version,
    saving their relative paths to a JSON file.
    """
    wem_files_list = []
    if not os.path.isdir(ps4_wem_dir):
        logging.error(f"❌ Directory not found: {ps4_wem_dir}")
        return

    logging.info(f"Scanning directory for PS4 WEM files: {ps4_wem_dir}")
    for root, _, files in os.walk(ps4_wem_dir):
        for filename in files:
            if filename.lower().endswith(".wem"):
                # Get the path relative to the input directory
                relative_path = os.path.relpath(os.path.join(root, filename), ps4_wem_dir)
                wem_files_list.append(relative_path)
                # logging.info(f"Found: {relative_path}") # Reduced logging for brevity

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "ps4_wem_list.json")

    # Write the list to a JSON file with sorted entries
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted(wem_files_list), f, indent=2) # Sort the list for consistency

    logging.info(f"✅ PS4 WEM file list generated and saved to: {output_path} ({len(wem_files_list)} files found)")

def find_ps4_wem_duplicates(ps4_wem_dir):
    """
    Finds and lists ALL .wem files within a given directory for the PS4 version,
    organized by specified folder types.
    Outputs relative paths and lists all categories the file appears in.
    """
    file_locations = defaultdict(list)
    filename_all_categories = defaultdict(set) # To store all categories for each filename
    categorized_files = defaultdict(dict) # Use a dict for filenames within each category

    # Define the prefixes for categorization
    folder_types = [
        "Act_", "Ambience_", "Foley_", "Footsteps_", "Generic_", "music_",
        "Sequences_", "SFX_", "Choices", "Butterfly_effect_bank", "Frontend",
        "Global_", "VFX_", "Wendigo_"
    ]
    other_category = "Other"

    if not os.path.isdir(ps4_wem_dir):
        logging.error(f"❌ Directory not found: {ps4_wem_dir}")
        return

    logging.info(f"Scanning directory for PS4 WEM files: {ps4_wem_dir}")
    for root, _, files in os.walk(ps4_wem_dir):
        for filename in files:
            if filename.lower().endswith(".wem"):
                full_path = os.path.join(root, filename)
                # Store the full path keyed by the filename
                file_locations[filename].append(full_path)
                logging.debug(f"Scanning: {full_path}") # Debug logging for each file found

    # Determine all categories for each filename (whether duplicate or not)
    all_filenames = list(file_locations.keys())

    logging.info(f"Found {len(all_filenames)} unique filenames.")

    logging.debug("Starting categorization and population of categorized_files...")

    for filename in all_filenames:
        logging.debug(f"Processing filename for categorization: {filename}")
        for path in file_locations[filename]:
            parent_dir = os.path.basename(os.path.dirname(path))
            matched_category = other_category # Default to Other
            category_matched = False # Flag to check if any specific category matched

            logging.debug(f"  - Checking parent directory '{parent_dir}' for prefixes for file '{filename}'...")
            for prefix in folder_types:
                # Check if parent_dir starts with the prefix (case-insensitive)
                logging.debug(f"    - Comparing '{parent_dir.lower()}' with prefix '{prefix.lower()}'")
                if parent_dir.lower().startswith(prefix.lower()):
                    matched_category = prefix # Use the original prefix casing for the category key
                    category_matched = True
                    logging.debug(f"    - Match found! Assigned Category: '{matched_category}' for path '{path}'")
                    break # Found a match, no need to check other prefixes

            filename_all_categories[filename].add(matched_category)
            logging.debug(f"  - Path: {path}, Parent Dir: '{parent_dir}', Final Assigned Category for this path: '{matched_category}' (Matched: {category_matched})")


    # Populate the categorized_files structure with relative paths and all categories
    logging.debug("Populating categorized_files structure...")
    for filename in all_filenames:
        all_categories_list = sorted(list(filename_all_categories[filename])) # Get sorted list of all categories
        logging.debug(f"  - All categories for {filename}: {all_categories_list}")

        for path in file_locations[filename]:
            parent_dir = os.path.basename(os.path.dirname(path))
            matched_category = other_category
            for prefix in folder_types:
                if parent_dir.lower().startswith(prefix.lower()):
                    matched_category = prefix
                    break

            relative_path = os.path.relpath(path, ps4_wem_dir)

            # Add the entry to the categorized_files structure
            # The value for the filename will now be an object containing paths and all_categories
            logging.debug(f"  - Attempting to add path '{relative_path}' for filename '{filename}' to category '{matched_category}'")
            if filename not in categorized_files[matched_category]:
                 logging.debug(f"    - Creating new entry for filename '{filename}' in category '{matched_category}'")
                 categorized_files[matched_category][filename] = {
                     "paths": [],
                     "all_categories": all_categories_list # Add the list of all categories here
                 }
            categorized_files[matched_category][filename]["paths"].append(relative_path)
            logging.debug(f"  - Successfully added '{relative_path}' to category '{matched_category}' for filename '{filename}'")


    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "ps4_wem_analysis.json") # Changed output filename

    # Sort the categories, ensuring "Other" is last
    sorted_categories = sorted(categorized_files.keys())
    if other_category in sorted_categories:
        sorted_categories.remove(other_category)
        sorted_categories.append(other_category)

    sorted_categorized_files = {}
    for category in sorted_categories:
        if category in categorized_files: # Ensure category exists after sorting
            # Sort filenames within each category
            sorted_filenames_in_category = dict(sorted(categorized_files[category].items()))
            # Sort paths within each filename entry (already done during population, but re-sort for safety)
            for filename, data in sorted_filenames_in_category.items():
                 data["paths"] = sorted(data["paths"]) # Ensure paths are sorted

            sorted_categorized_files[category] = sorted_filenames_in_category


    # Write the categorized file information to a JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_categorized_files, f, indent=2)

    total_files_found = sum(len(files_data) for files_data in categorized_files.values())
    logging.info(f"✅ PS4 WEM file analysis generated and saved to: {output_path} ({total_files_found} files categorized across {len(categorized_files)} categories).")

