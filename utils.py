import os
import shutil
import logging
from tkinter import filedialog

def copy_file_with_logging(source_path, dest_path):
    """Copies a file with logging."""
    if os.path.exists(source_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            shutil.copy2(source_path, dest_path)
            logging.info(f"Copied: {source_path} -> {dest_path}")
            return True
        except Exception as e:
            logging.error(f"Error copying {source_path}: {e}")
            return False
    else:
        logging.warning(f"Source file not found: {source_path}")
        return False

def select_directory(title, initialdir=None):
    """Opens a directory selection dialog."""
    directory = filedialog.askdirectory(title=title, initialdir=initialdir)
    return directory

def configure_logger(level=logging.INFO):
    """Configures logging to output to the console only."""
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
