import json
import pandas as pd
import os
import logging

def convert_duplicates_json_to_excel(json_path="ps4_wem_analysis.json", excel_path="ps4_wem_analysis.xlsx"):
    """
    Converts the ps4_wem_analysis.json file into an Excel (.xlsx) file,
    with each category of files in a separate worksheet.
    Includes a column listing all categories the file appears in.

    Args:
        json_path (str): The path to the input JSON file.
                         Defaults to 'ps4_wem_analysis.json'.
        excel_path (str): The path for the output Excel file.
                          Defaults to 'ps4_wem_analysis.xlsx'.
    """
    if not os.path.exists(json_path):
        logging.error(f"❌ Error: Input JSON file not found at {json_path}")
        print(f"Error: Input JSON file not found at {json_path}")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"❌ Error decoding JSON from {json_path}: {e}")
        print(f"Error decoding JSON from {json_path}: {e}")
        return
    except Exception as e:
        logging.error(f"❌ An error occurred while reading {json_path}: {e}")
        print(f"An error occurred while reading {json_path}: {e}")
        return

    if not data:
        logging.info("✅ No file data found in JSON to write to Excel.")
        print("No file data found in JSON to write to Excel.")
        return

    try:
        # Use ExcelWriter to write to multiple sheets
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for category, filenames_data in data.items():
                # Prepare data for pandas DataFrame for the current category
                excel_data_category = []
                for filename, file_info in filenames_data.items():
                    # Extract paths and all_categories from the file_info dictionary
                    paths = file_info.get("paths", [])
                    all_categories = file_info.get("all_categories", []) # Get the list of all categories

                    # Convert the list of all categories to a comma-separated string for the Excel cell
                    all_categories_str = ", ".join(all_categories)

                    for path in paths:
                        excel_data_category.append({
                            "Filename": filename,
                            "Relative Path": path,
                            "All Categories": all_categories_str # Add the new column
                        })

                if excel_data_category:
                    # Create a pandas DataFrame for the current category
                    df_category = pd.DataFrame(excel_data_category)

                    # Write DataFrame to a sheet named after the category
                    # Sanitize category name for sheet name (Excel sheet names have limits)
                    sheet_name = category.replace(":", "_").replace("/", "_").replace("\\", "_")[:31] # Limit to 31 chars
                    df_category.to_excel(writer, index=False, sheet_name=sheet_name)
                    logging.info(f"  - Wrote category '{category}' to sheet '{sheet_name}'")
                else:
                     logging.info(f"  - No data for category '{category}', skipping sheet.")


        logging.info(f"✅ Successfully converted {json_path} to {excel_path} with categories as sheets.")
        print(f"Successfully converted {json_path} to {excel_path} with categories as sheets.")

    except ImportError:
        logging.error("❌ Error: 'openpyxl' library not found. Please install it (`pip install openpyxl`) to write .xlsx files.")
        print("Error: 'openpyxl' library not found. Please install it (`pip install openpyxl`) to write .xlsx files.")
    except Exception as e:
        logging.error(f"❌ An error occurred while writing to Excel file {excel_path}: {e}")
        print(f"An error occurred while writing to Excel file {excel_path}: {e}")


if __name__ == "__main__":
    # Basic logging setup for the script
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # You can specify the input JSON and output Excel paths here
    # or run with defaults ('ps4_wem_analysis.json', 'ps4_wem_analysis.xlsx')
    # Example:
    # convert_duplicates_json_to_excel("my_analysis.json", "my_output.xlsx")

    convert_duplicates_json_to_excel()
