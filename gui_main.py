import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox, scrolledtext
import logging
import threading
from processing import generate_mapping_from_json, unobfuscate_from_mapping, obfuscate_from_mapping

# Super rough GUI freezing workaround. Everything works normally, but now the GUI locks up whenever it's in the middle of a process.


# Centralized theme colors
THEME = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "entry_bg": "#2e2e2e",
    "entry_fg": "#ffffff",
    "button_bg": "#3a3a3a",
    "button_fg": "#ffffff",
    "accent": "#4CAF50",
    "scroll_bg": "#444444"
}

class AudioToolGUI:
    def __init__(self, root):
        self.root = root
        root.title("UD Remake Event Audio Tool")
        root.geometry("1000x1000")
        self.root.config(bg=THEME["bg"])

        self.operation_mode = tk.StringVar(value="none")
        self.json_dir = tk.StringVar()
        self.wem_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.operation_buttons = {}

        self.add_logo("UntilDawnLogo.png")
        self.create_widgets()
        self.configure_logging()

    def add_logo(self, image_path):
        try:
            self.logo_img = tk.PhotoImage(file=image_path)
            logo_label = tk.Label(self.root, image=self.logo_img, bg=THEME["bg"])
            logo_label.pack(pady=(20, 10))
        except Exception as e:
            logging.warning(f"Could not load logo image: {e}")

    def configure_logging(self):
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if logger.hasHandlers():
            logger.handlers.clear()
        text_handler = logging.StreamHandler(self.LogRedirector(self.log_output))
        formatter = logging.Formatter('%(message)s')
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)

    def create_widgets(self):
        tk.Label(self.root, text="Choose an Operation:", bg=THEME["bg"], fg=THEME["fg"], font=("Helvetica", 14, "bold")).pack(anchor='center', pady=(20, 10))
        btn_frame = tk.Frame(self.root, bg=THEME["bg"])
        btn_frame.pack()

        self.operation_buttons["mapping"] = self.create_button_with_tooltip(btn_frame, "📄 Generate Mapping from JSON", self.prepare_mapping_ui, 
                                                 "Generate wem_mapping.json file from Bates\\Content\\WwiseAudio\\Events.", THEME["button_bg"])
        self.operation_buttons["unobfuscate"] = self.create_button_with_tooltip(btn_frame, "🔓 Unobfuscate WEM Files", self.prepare_unobfuscate_ui, 
                                                 "Unobfuscate .wem files from Bates\\Content\\WwiseStaged.", THEME["button_bg"])
        self.operation_buttons["obfuscate"] = self.create_button_with_tooltip(btn_frame, "🔒 Obfuscate WEM Files", self.prepare_obfuscate_ui, 
                                                 "Obfuscate renamed .wem files to their original random ID names.", THEME["button_bg"])
        for btn in self.operation_buttons.values():
            btn.pack(pady=5)

        self.picker_frame = tk.Frame(self.root, bg=THEME["bg"])
        self.picker_frame.pack(pady=20)

        self.run_button = self.make_button(self.root, "Run", self.start_processing, THEME["accent"], width=20)
        self.run_button.pack(pady=20)

        self.log_output = scrolledtext.ScrolledText(self.root, height=10, state='disabled',
                                                    bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                                    insertbackground=THEME["entry_fg"])
        self.log_output.pack(fill="both", expand=True, padx=20, pady=5)

        style_scrollbar = ttk.Style()
        style_scrollbar.theme_use('default')
        style_scrollbar.configure("Vertical.TScrollbar", background=THEME["scroll_bg"], troughcolor=THEME["bg"])

    def create_button_with_tooltip(self, parent, text, command, tooltip_text, bg_color):
        button = tk.Button(parent, text=text, command=command, bg=bg_color, fg=THEME["fg"],
                           activebackground="#5c5c5c", activeforeground=THEME["fg"], width=40, relief="flat")
        self.create_tooltip(button, tooltip_text)
        return button

    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(self.root)
        tooltip.overrideredirect(True)
        tooltip.config(bg="black", bd=1)
        tooltip_label = tk.Label(tooltip, text=text, fg="white", bg="black", font=("Helvetica", 10), padx=5, pady=5)
        tooltip_label.pack()
        tooltip.withdraw()

        def on_enter(event):
            widget_x = widget.winfo_rootx()
            widget_y = widget.winfo_rooty()
            widget_width = widget.winfo_width()
            tooltip_width = tooltip_label.winfo_reqwidth()
            tooltip_height = tooltip_label.winfo_reqheight()
            tooltip.geometry(f"{tooltip_width}x{tooltip_height}+{widget_x + (widget_width // 2) - (tooltip_width // 2)}+{widget_y - tooltip_height - 10}")
            tooltip.deiconify()

        def on_leave(event):
            tooltip.withdraw()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def make_button(self, parent, text, command, bg_color, width=40):
        return tk.Button(parent, text=text, command=command, bg=bg_color, fg=THEME["fg"],
                         activebackground="#5c5c5c", activeforeground=THEME["fg"], width=width, relief="flat")

    def update_button_styles(self):
        for key, button in self.operation_buttons.items():
            if self.operation_mode.get() == key:
                button.config(bg=THEME["accent"])
            else:
                button.config(bg=THEME["button_bg"])

    def prepare_mapping_ui(self):
        self.operation_mode.set("mapping")
        self.update_fields()
        self.update_button_styles()

    def prepare_unobfuscate_ui(self):
        self.operation_mode.set("unobfuscate")
        self.update_fields()
        self.update_button_styles()

    def prepare_obfuscate_ui(self):
        self.operation_mode.set("obfuscate")
        self.update_fields()
        self.update_button_styles()

    def update_fields(self):
        for widget in self.picker_frame.winfo_children():
            widget.pack_forget()
        mode = self.operation_mode.get()
        if mode == "mapping":
            self.json_picker = self.create_folder_picker("JSON Folder", self.json_dir, "Select the folder containing JSON files")
            self.json_picker.pack(pady=10)
        elif mode in ["unobfuscate", "obfuscate"]:
            self.wem_picker = self.create_folder_picker("WEM Folder", self.wem_dir, "Select the folder containing WEM files")
            self.output_picker = self.create_folder_picker("Output Folder", self.output_dir, "Select the folder to save output")
            self.wem_picker.pack(pady=10)
            self.output_picker.pack(pady=10)

    def create_folder_picker(self, label_text, var, tooltip_text):
        outer = tk.Frame(self.picker_frame, bg=THEME["bg"])
        outer.pack(pady=10)
        inner = tk.Frame(outer, bg=THEME["bg"])
        inner.grid(row=0, column=0)
        tk.Label(inner, text=label_text, bg=THEME["bg"], fg=THEME["fg"]).grid(row=0, column=0, padx=5, pady=5)
        entry = tk.Entry(inner, textvariable=var, width=60, bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                         insertbackground=THEME["entry_fg"], relief="flat")
        entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(inner, text="Browse", command=lambda: self.browse_folder(var, tooltip_text),
                  bg=THEME["accent"], fg=THEME["fg"], activebackground="#5c5c5c", relief="flat").grid(row=0, column=2, padx=5, pady=5)
        return outer

    def browse_folder(self, var, tooltip_text):
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
            messagebox.showinfo("Folder Selected", f"You selected: {folder}")
        else:
            messagebox.showwarning("No Folder", "Please select a valid folder.")

    def start_processing(self):
        mode = self.operation_mode.get()

        def task():
            if mode == "mapping":
                if not self.json_dir.get():
                    messagebox.showerror("Missing Input", "Please select the JSON directory.")
                    return
                logging.info("📄 Generating mapping from JSON...")
                generate_mapping_from_json(self.json_dir.get())
            elif mode == "unobfuscate":
                if not self.wem_dir.get() or not self.output_dir.get():
                    messagebox.showerror("Missing Input", "Please select both WEM and output directories.")
                    return
                logging.info("🔓 Unobfuscating WEM files...")
                unobfuscate_from_mapping(self.wem_dir.get(), self.output_dir.get())
            elif mode == "obfuscate":
                if not self.wem_dir.get() or not self.output_dir.get():
                    messagebox.showerror("Missing Input", "Please select both WEM and output directories.")
                    return
                logging.info("🔒 Obfuscating WEM files...")
                obfuscate_from_mapping(self.wem_dir.get(), self.output_dir.get())
            else:
                messagebox.showwarning("No Operation", "Please select an operation first.")
                return
            logging.info("✅ Operation completed.\n")

        threading.Thread(target=task, daemon=True).start()

    class LogRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget
        def write(self, message):
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        def flush(self):
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioToolGUI(root)
    root.mainloop()
