import json
import os
import logging
import multiprocessing
import subprocess # Import for running external commands
import re # Import for parsing vgmstream output
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import copy_file_with_logging # Assuming utils.py exists with copy_file_with_logging

# Attempt to import mutagen (still needed for other formats if used elsewhere, but not WEM duration with vgmstream)
try:
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    # Mutagen is not strictly needed for WEM duration with vgmstream-cli,
    # but keep the flag for potential future use or other file types.
    logging.debug("Mutagen library not found. OGG duration reading functions may not work.")
    MUTAGEN_AVAILABLE = False


MAX_WORKERS = multiprocessing.cpu_count() * 2

# Define path to external tool (assuming it's in the vgmstream-win64 subdirectory within the script folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VGMSTREAM_DIR = os.path.join(SCRIPT_DIR, "vgmstream-win64") # Define the subdirectory
VGMSTREAM_PATH = os.path.join(VGMSTREAM_DIR, "vgmstream-cli.exe") # Adjust executable name/path if needed

# More Flexible Regex to find duration in vgmstream output
# This looks for "play duration:", any characters non-greedily, then captures time within parentheses (MM:SS.ms or H:MM:SS.ms) followed by " seconds)"
# Using \s+ to match one or more whitespace characters, and allowing any characters (.*?) before the time.
DURATION_REGEX = re.compile(r"play duration:.*?\((\d+:\d{2}(:\d{2})?\.\d{3})\s*seconds\)")
# Keeping the alternative regex just in case.
ALT_DURATION_REGEX = re.compile(r"total samples:\s*\d+\s*\((\d+:\d{2}:\d{2}\.\d{3})\)")


def run_command(command, cwd=None):
    """Helper function to run an external command and capture output/errors."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True # Raise CalledProcessError if command returns non-zero exit code
        )
        logging.debug(f"Command successful: {' '.join(command)}")
        if result.stdout:
            logging.debug(f"Stdout: {result.stdout.strip()}")
        if result.stderr:
            logging.debug(f"Stderr: {result.stderr.strip()}")
        return result.stdout # Return full stdout for parsing
    except FileNotFoundError:
        logging.error(f"❌ Error: Command not found. Make sure '{command[0]}' is in your PATH or script directory.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error running command: {' '.join(command)}")
        logging.error(f"Return code: {e.returncode}")
        if e.stdout:
             logging.error(f"Stdout: {e.stdout.strip()}")
        if e.stderr:
             logging.error(f"Stderr: {e.stderr.strip()}")
        return None # Return None to indicate failure
    except Exception as e:
        logging.error(f"❌ An unexpected error occurred while running command {' '.join(command)}: {e}")
        return None # Return None to indicate failure


def get_wem_duration_vgmstream(wem_file_path):
    """
    Gets the duration of a WEM file using vgmstream-cli.
    Returns duration string (MM:SS.ms or H:MM:SS.ms) or "N/A" if failed.
    """
    logging.debug(f"Attempting to get duration for: {wem_file_path}") # Added debug log
    if not os.path.exists(VGMSTREAM_PATH):
        logging.error("❌ vgmstream-cli not found at expected location.") # Changed to error
        return "N/A (vgmstream-cli not found at expected location)"
    if not os.path.exists(wem_file_path):
        logging.warning(f"⚠️ WEM file not found for duration check: {wem_file_path}")
        return "N/A (WEM not found)"

    duration = "N/A (Failed to parse)"

    try:
        # Run vgmstream-cli with the info flag (-i)
        # The output contains metadata including duration
        vgmstream_command = [VGMSTREAM_PATH, "-i", wem_file_path]
        logging.debug(f"Running vgmstream-cli command: {' '.join(vgmstream_command)}") # Added debug log
        vgmstream_output = run_command(vgmstream_command)
        logging.debug(f"vgmstream-cli command finished for: {wem_file_path}") # Added debug log


        if vgmstream_output is not None:
            # Parse the output to find the duration line
            match = DURATION_REGEX.search(vgmstream_output)
            if match:
                duration = match.group(1)
                logging.debug(f"Successfully parsed duration for {os.path.basename(wem_file_path)}: {duration}") # Added debug log
            else:
                # Try the alternative regex if the first one fails
                alt_match = ALT_DURATION_REGEX.search(vgmstream_output)
                if alt_match:
                    duration = alt_match.group(1)
                    logging.debug(f"Successfully parsed duration (alt regex) for {os.path.basename(wem_file_path)}: {duration}") # Added debug log
                else:
                    logging.warning(f"⚠️ Could not find duration in vgmstream-cli output for {os.path.basename(wem_file_path)}. Please check the regex patterns in processing.py. Output segment:\n{vgmstream_output[:500]}...") # Log partial output
                    duration = "N/A (Duration pattern not matched)"
        else:
            duration = "N/A (vgmstream-cli failed)"

    except Exception as e:
        logging.error(f"❌ An error occurred during vgmstream-cli processing for {os.path.basename(wem_file_path)}: {e}")
        duration = "N/A (Processing Error)"

    return duration


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
    (This function is now largely redundant with find_ps4_wem_duplicates but kept for completeness)
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
                logging.debug(f"Found: {relative_path}") # Changed to debug for less clutter


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
    Outputs relative paths, file size, duration, and lists all categories the file appears in.
    Calculates duration using vgmstream-cli.
    Includes cleanup for .wav files in the input directory.
    """
    file_info_by_filename = defaultdict(lambda: {"paths": [], "all_categories": set(), "size": 0, "duration": "N/A (Processing)"}) # Add size and duration processing status
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
    wem_files_to_process = []
    for root, _, files in os.walk(ps4_wem_dir):
        for filename in files:
            if filename.lower().endswith(".wem"):
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, ps4_wem_dir)

                # Get file size
                try:
                    file_size = os.path.getsize(full_path)
                except Exception as e:
                    logging.warning(f"⚠️ Could not get size for {full_path}: {e}")
                    file_size = 0 # Default to 0 if size cannot be obtained

                # Store info keyed by filename
                file_info_by_filename[filename]["paths"].append(relative_path)
                file_info_by_filename[filename]["size"] = file_size # Store size (assuming size is same for all instances, or take one)

                # Determine category for this specific path
                parent_dir = os.path.basename(os.path.dirname(full_path))
                matched_category = other_category
                for prefix in folder_types:
                    if parent_dir.lower().startswith(prefix.lower()):
                        matched_category = prefix
                        break
                file_info_by_filename[filename]["all_categories"].add(matched_category)

                wem_files_to_process.append(full_path) # Add file to list for duration processing

                logging.debug(f"Scanning: {full_path} (Size: {file_size} bytes)")

    # --- Process WEM files for duration using vgmstream-cli via ThreadPoolExecutor ---
    logging.info(f"Starting WEM duration calculation using vgmstream-cli for {len(wem_files_to_process)} files...")
    duration_results = {} # Store results {full_path: duration_string}

    # Check if vgmstream-cli is available before starting the pool
    if os.path.exists(VGMSTREAM_PATH):
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_wem = {executor.submit(get_wem_duration_vgmstream, wem_path): wem_path for wem_path in wem_files_to_process}

            for future in as_completed(future_to_task):
                wem_path = future_to_wem[future]
                try:
                    duration = future.result()
                    duration_results[wem_path] = duration
                    # logging.debug(f"Processed {os.path.basename(wem_path)}: Duration {duration}") # Moved to get_wem_duration_vgmstream
                except Exception as e:
                    logging.error(f"❌ Exception processing {os.path.basename(wem_path)} for duration: {e}")
                    duration_results[wem_path] = "N/A (Processing Error)"
    else:
        logging.warning("⚠️ Skipping WEM duration calculation due to missing vgmstream-cli.exe at expected location.")
        for wem_path in wem_files_to_process:
             duration_results[wem_path] = "N/A (vgmstream-cli Missing)"
    # ---------------------------------------------------------------------------------


    # Populate the categorized_files structure with aggregated info and actual duration
    all_filenames = list(file_info_by_filename.keys())
    logging.debug("Populating categorized_files structure with duration...")

    for filename in all_filenames:
        info = file_info_by_filename[filename]
        all_categories_list = sorted(list(info["all_categories"])) # Get sorted list of all categories

        # Find the duration for this filename (assuming all instances have the same duration)
        # We can take the duration from the first path found for this filename
        duration_for_filename = "N/A"
        if info["paths"]:
            # Need to find the full path from the relative path to look up in duration_results
            first_relative_path = info["paths"][0]
            first_full_path = os.path.join(ps4_wem_dir, first_relative_path)
            duration_for_filename = duration_results.get(first_full_path, "N/A (Lookup Error)")


        # For each category this filename belongs to, add an entry
        for category in all_categories_list:
             # Ensure the category exists in the output structure
             if filename not in categorized_files[category]:
                 categorized_files[category][filename] = {
                     "paths": sorted(info["paths"]), # Store sorted paths
                     "all_categories": all_categories_list,
                     "size": info["size"], # Include size
                     "duration": duration_for_filename # Include calculated duration
                 }
             # Note: If a file is in multiple categories, its entry (with all paths, size, duration)
             # will appear under each relevant category key in categorized_files.

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
    logging.info(f"✅ PS4 WEM file analysis generated and saved to: {output_path} ({total_files_found} unique filenames categorized across {len(categorized_files)} categories).")
    logging.info("Note: Duration calculation attempted using vgmstream-cli.")

    # --- Cleanup: Delete .wav files in the input directory ---
    logging.info(f"Starting cleanup: Searching for and deleting .wav files in {ps4_wem_dir}...")
    deleted_count = 0
    try:
        for root, _, files in os.walk(ps4_wem_dir):
            for filename in files:
                if filename.lower().endswith(".wav"):
                    wav_file_path = os.path.join(root, filename)
                    try:
                        os.remove(wav_file_path)
                        logging.debug(f"Deleted: {wav_file_path}")
                        deleted_count += 1
                    except OSError as e:
                        logging.warning(f"⚠️ Failed to delete {wav_file_path}: {e}")
                    except Exception as e:
                        logging.warning(f"⚠️ An unexpected error occurred while deleting {wav_file_path}: {e}")
        logging.info(f"✅ Cleanup finished. Deleted {deleted_count} .wav file(s).")
    except Exception as e:
        logging.error(f"❌ An error occurred during .wav file cleanup: {e}")
    # --------------------------------------------------------


