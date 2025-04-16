import os
import shutil
import logging
from tkinter import filedialog

def copy_file_with_logging(source_path, dest_path):
    """Copies a file with basic logging, skipping extra checks."""
    try:
        shutil.copyfile(source_path, dest_path)
        logging.info(f"📦 Copied: {source_path} → {dest_path}")
        return True
    except Exception as e:
        logging.warning(f"⚠️ Failed to copy {source_path} → {dest_path}: {e}")
        return False

def select_directory(title, initialdir=None):
    return filedialog.askdirectory(title=title, initialdir=initialdir)

def configure_logger(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='[%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
