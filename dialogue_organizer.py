# dialogue_organizer.py
import json
import os
import shutil
import logging

def organize_dialogue_json_files(source_base_path, destination_path):
    """
    Organizes dialogue JSON files based on "ObjectPath" values within "PSExternalMediaAsset".

    Args:
        source_base_path (str): The base directory to search for JSON files in.
        destination_path (str): The directory where the organized files will be copied.
    """

    # Walk through the base source directory
    for root, dirs, files in os.walk(source_base_path):
        for file in files:
            if file.endswith(".json") and not file.endswith(".2.json"):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process each object in the JSON array
                    for item in data:
                        if item.get("Type") == "PSExternalMediaAsset":
                            object_path = item.get("Properties", {}).get("ObjectPath", "")
                            if object_path:
                                # Extract the directory from the ObjectPath
                                target_dir = os.path.dirname(object_path)
                                
                                # Create the destination directory
                                dest_dir = os.path.join(destination_path, target_dir)
                                os.makedirs(dest_dir, exist_ok=True)
                                
                                # Construct the destination file path
                                dest_file_path = os.path.join(dest_dir, file)
                                
                                # Copy the file
                                shutil.copy2(file_path, dest_file_path)
                                print(f"Copied '{file_path}' to '{dest_file_path}'")
                
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {file_path}")
                except FileNotFoundError:
                    print(f"File not found: {file_path}")
                except Exception as e:
                    print(f"An error occurred processing {file_path}: {e}")