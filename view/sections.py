import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

class ModuleWidget(ttk.Frame):
    def __init__(self, parent, module, on_edit, on_delete, on_toggle, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.module = module
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_toggle = on_toggle

        self.setup_ui()

    def setup_ui(self):
        # Checkbox for active state
        self.var_active = tk.BooleanVar(value=self.module.is_active)
        self.chk_active = ttk.Checkbutton(self, variable=self.var_active, command=self._on_toggle_internal)
        self.chk_active.pack(side=tk.LEFT, padx=5)

        # Content info (Title or Brief)
        # Different display based on module type
        display_text = "Module"
        if hasattr(self.module, 'title'):
            display_text = self.module.title or "(No Title)"
        elif hasattr(self.module, 'name'):
            display_text = self.module.name or "(No Name)"
        elif hasattr(self.module, 'company'):
            display_text = f"{self.module.company} - {self.module.role}"
        
        self.lbl_info = ttk.Label(self, text=display_text, font=("Arial", 10, "bold"))
        self.lbl_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Edit Button
        self.btn_edit = ttk.Button(self, text="✎", width=3, command=lambda: self.on_edit(self.module))
        self.btn_edit.pack(side=tk.RIGHT, padx=2)

        # Delete Button
        self.btn_delete = ttk.Button(self, text="🗑", width=3, command=lambda: self.on_delete(self.module))
        self.btn_delete.pack(side=tk.RIGHT, padx=2)
        
        # Extended/Summary Toggle (if TextModule)
        if hasattr(self.module, 'use_summary'):
             self.var_summary = tk.BooleanVar(value=self.module.use_summary)
             # Use a robust command wrapper
             def toggle_summary():
                 self.module.use_summary = self.var_summary.get()
             
             self.rad_ext = ttk.Radiobutton(self, text="Ext", variable=self.var_summary, value=False, command=toggle_summary)
             self.rad_sum = ttk.Radiobutton(self, text="Sum", variable=self.var_summary, value=True, command=toggle_summary)
             self.rad_sum.pack(side=tk.RIGHT, padx=2)
             self.rad_ext.pack(side=tk.RIGHT, padx=2)


    def _on_toggle_internal(self):
        self.module.is_active = self.var_active.get()
        if self.on_toggle:
            self.on_toggle(self.module)

    def update_display(self):
        # Refresh label text in case it changed
        display_text = "Module"
        if hasattr(self.module, 'title'):
             display_text = self.module.title
        elif hasattr(self.module, 'name'):
             display_text = self.module.name
        
        # Specific for Experience
        if hasattr(self.module, 'company'):
             display_text = f"{self.module.company}"
        
        self.lbl_info.config(text=display_text)


class SectionFrame(ttk.LabelFrame):
    def __init__(self, parent, section_data, controller, *args, **kwargs):
        super().__init__(parent, text=section_data.title, padding=10, *args, **kwargs)
        self.section_data = section_data
        self.controller = controller
        
        self.module_widgets = []
        
        self.setup_ui()

    def setup_ui(self):
        # Toolbar (Select All / Add)
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        if self.section_data.type != "personal": # Select all doesn't make sense for single-choice personal info usually, but User asked for it generic? 
            # User said: "Opción "Seleccionar todo"/"Deseleccionar todo": permitirá seleccionar/deseleccionar todas las checkboxes de la sección **siempre que ésta lo permita**."
            # Personal Info (Avatar/Bio) is Single Choice usually.
            
            self.btn_sel_all = ttk.Button(toolbar, text="Select All", command=lambda: self.toggle_all(True))
            self.btn_sel_all.pack(side=tk.RIGHT, padx=5)
            self.btn_desel_all = ttk.Button(toolbar, text="Deselect All", command=lambda: self.toggle_all(False))
            self.btn_desel_all.pack(side=tk.RIGHT, padx=5)

        self.btn_add = ttk.Button(toolbar, text="+ Add New", command=self.add_module)
        self.btn_add.pack(side=tk.LEFT)

        # Scrollable Container for modules
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.refresh_modules()

    def add_module(self):
        self.controller.add_module(self.section_data)
        self.refresh_modules()

    def edit_module(self, module):
        self.controller.edit_module(module, self.section_data)
        self.refresh_modules()

    def delete_module(self, module):
        if messagebox.askyesno("Confirm", "Delete this module?"):
            self.controller.delete_module(module, self.section_data)
            self.refresh_modules()

    def toggle_module(self, module):
        if self.controller and hasattr(self.controller, 'toggle_module'):
            self.controller.toggle_module(module, self.section_data)
            # Refresh to show changes (e.g. unchecking others)
            # Optimization: could just update widgets, but full refresh is safer for now
            self.refresh_modules()

    def toggle_all(self, state):
        for mod in self.section_data.modules:
            mod.is_active = state
        self.refresh_modules()

    def refresh_modules(self):
        # Clear existing
        for widget in self.module_widgets:
            widget.destroy()
        self.module_widgets.clear()

        for mod in self.section_data.modules:
            mw = ModuleWidget(self.scrollable_frame, mod, 
                              on_edit=self.edit_module, 
                              on_delete=self.delete_module,
                              on_toggle=self.toggle_module)
            mw.pack(fill=tk.X, pady=2, anchor="n")
            self.module_widgets.append(mw)
