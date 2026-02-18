import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .sections import SectionFrame

class MainWindow(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("ResumeCabinet Editor")
        self.geometry("1200x800")
        
        self.setup_menu()
        self.setup_ui()

    def setup_menu(self):
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Template", command=self.controller.new_template)
        file_menu.add_command(label="Open Template...", command=self.controller.load_template)
        file_menu.add_command(label="Save Template", command=self.controller.save_template)
        file_menu.add_command(label="Save Template As...", command=self.controller.save_template_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        export_menu = tk.Menu(menubar, tearoff=0)
        export_menu.add_command(label="Preview PDF", command=self.controller.preview_pdf)
        export_menu.add_command(label="Export to PDF", command=self.controller.export_pdf)
        menubar.add_cascade(label="Export", menu=export_menu)

        self.config(menu=menubar)

    def setup_ui(self):
        # Main Layout: Left Sidebar (Config), Center (Tabbed Sections)
        
        # We can implement sections as tabs or a scrollable list. 
        # User images suggest "sections" divided.
        # Let's use a Notebook for clean categorization if sections are many, 
        # but user request implies specific order in "Editor".
        # Let's use a vertical notebook or just tabs.
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tabs will be added by controller logic dynamically or here
        pass

    def clear_tabs(self):
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)

    def add_section_tab(self, section_data):
        frame = SectionFrame(self.notebook, section_data, self.controller)
        self.notebook.add(frame, text=section_data.title)

    def add_config_tab(self, cv_data):
        # Special tab for "Configuración del CV"
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Configuración")
        
        # Language Selection
        lbl_lang = ttk.Label(frame, text="Idioma del CV:")
        lbl_lang.pack(pady=10)
        
        languages = ["Español", "Inglés", "Gallego", "Catalán"]
        self.combo_lang = ttk.Combobox(frame, values=languages, state="readonly")
        self.combo_lang.set(cv_data.settings.language)
        self.combo_lang.pack(pady=5)
        self.combo_lang.bind("<<ComboboxSelected>>", lambda e: self.controller.update_setting("language", self.combo_lang.get()))
        
        # Other global configs could go here
