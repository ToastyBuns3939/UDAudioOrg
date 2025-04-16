import json
import os
import logging
from utils import copy_file_with_logging

def generate_mapping_from_json(json_dir, specific_folder=None):
    mapping = {}
    total_files = 0
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

                        for event in data:
                            if "EventCookedData" in event and "EventLanguageMap" in event["EventCookedData"]:
                                for lang_map in event["EventCookedData"]["EventLanguageMap"]:
                                    if "Value" in lang_map and "Media" in lang_map["Value"]:
                                        for media in lang_map["Value"]["Media"]:
                                            media_path = media.get("MediaPathName")
                                            debug_name = media.get("DebugName")
                                            if media_path and debug_name:
                                                if media_path in mapping and mapping[media_path] != debug_name:
                                                    logging.warning(f"⚠ Duplicate mapping for {media_path}, skipping {debug_name}")
                                                else:
                                                    mapping[media_path] = debug_name
                    except Exception as e:
                        logging.error(f"❌ Failed to process {json_path}: {e}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "wem_mapping.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    logging.info(f"\n✅ Mapping generated and saved to: {map_path}")
    logging.info(f"🔢 Total JSON files processed: {total_files}")
    logging.info(f"🎯 Unique mappings created: {len(mapping)}\n")


def unobfuscate_from_mapping(wem_dir, output_dir):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "wem_mapping.json")

    if not os.path.exists(map_path):
        logging.error("❌ wem_mapping.json not found. Please generate it first.")
        return

    with open(map_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    success_count = 0
    error_list = []

    for media_path, debug_name in mapping.items():
        source_path = os.path.normpath(os.path.join(wem_dir, media_path))
        debug_base = os.path.basename(debug_name)
        ext = os.path.splitext(media_path)[1]
        output_filename = f"{os.path.splitext(debug_base)[0]}{ext}"
        dest_path = os.path.normpath(os.path.join(output_dir, os.path.dirname(debug_name), output_filename))

        if copy_file_with_logging(source_path, dest_path):
            success_count += 1
        else:
            error_list.append(f"File not found: {source_path}")

    logging.info(f"\n✅ Unobfuscation completed. Files copied: {success_count}")
    if error_list:
        log_path = os.path.join(script_dir, "error_log.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for line in error_list:
                f.write(f"{line}\n")
        logging.warning(f"⚠ Some files could not be found. See: {log_path} ({len(error_list)} missing)")
    else:
        logging.info("🎉 All files copied successfully.\n")


def obfuscate_from_mapping(wem_dir, output_dir):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(script_dir, "wem_mapping.json")

    if not os.path.exists(map_path):
        logging.error("❌ wem_mapping.json not found. Please generate it first.")
        return

    with open(map_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    success_count = 0
    error_list = []

    for media_path, debug_name in mapping.items():
        wem_path_from_debug = debug_name.replace(".wav", ".wem")
        source_path = os.path.normpath(os.path.join(wem_dir, wem_path_from_debug))
        dest_path = os.path.normpath(os.path.join(output_dir, media_path))

        if copy_file_with_logging(source_path, dest_path):
            success_count += 1
        else:
            error_list.append(f"File not found: {source_path}")

    logging.info(f"\n✅ Obfuscation completed. Files copied: {success_count}")
    if error_list:
        log_path = os.path.join(script_dir, "error_log.log")
        with open(log_path, "w", encoding="utf-8") as f:
            for line in error_list:
                f.write(f"{line}\n")
        logging.warning(f"⚠ Some files could not be found. See: {log_path} ({len(error_list)} missing)")
    else:
        logging.info("🎉 All files copied successfully.\n")
