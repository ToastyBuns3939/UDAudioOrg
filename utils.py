import os
import shutil
import logging
from tkinter import filedialog, messagebox

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
            messagebox.showerror("Error", f"Error copying {source_path}: {e}")
            return False
    else:
        logging.warning(f"Source file not found: {source_path}")
        messagebox.showwarning("Warning", f"Source file not found: {source_path}")
        return False

def select_directory(title, initialdir=None):
    """Opens a directory selection dialog."""
    directory = filedialog.askdirectory(title=title, initialdir=initialdir)
    return directory

def show_message(title, message, level="info"):
    """Shows a message box."""
    if level == "info":
        messagebox.showinfo(title, message)
        logging.info(message)
    elif level == "warning":
        messagebox.showwarning(title, message)
        logging.warning(message)
    elif level == "error":
        messagebox.showerror(title, message)
        logging.error(message)

def configure_logger(log_file_name, level=logging.DEBUG):
    """Configures the logging to write to a file."""
    logging.basicConfig(filename=log_file_name, level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def close_and_remove_handlers():
    """Closes and removes all logging handlers."""
    handlers = logging.getLogger().handlers[:]
    for handler in handlers:
        handler.close()
        logging.getLogger().removeHandler(handler)