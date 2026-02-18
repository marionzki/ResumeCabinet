import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ModuleForm(tk.Toplevel):
    def __init__(self, parent, module, available_tags=None, on_save=None):
        super().__init__(parent)
        self.module = module
        self.available_tags = available_tags or []
        self.on_save = on_save
        self.title("Edit Module")
        self.geometry("600x600")
        
        self.setup_ui()

    def setup_ui(self):
        # Determine fields based on module type
        m_type = self.module.__class__.__name__
        
        row = 0
        
        # Common: Title/Name
        if hasattr(self.module, 'title'):
            ttk.Label(self, text="Title:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            self.entry_title = ttk.Entry(self, width=50)
            self.entry_title.insert(0, self.module.title)
            self.entry_title.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1
        
        if hasattr(self.module, 'name'):
            ttk.Label(self, text="Name:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            self.entry_name = ttk.Entry(self, width=50)
            self.entry_name.insert(0, self.module.name)
            self.entry_name.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1

        # ImageModule / AvatarModule
        if hasattr(self.module, 'image_path'):
            ttk.Label(self, text="Image Path:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            self.entry_img = ttk.Entry(self, width=40)
            self.entry_img.insert(0, self.module.image_path)
            self.entry_img.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            
            btn_browse = ttk.Button(self, text="Browse...", command=self.browse_image)
            btn_browse.grid(row=row, column=2, padx=5)
            row += 1

        # Experience Specific
        if hasattr(self.module, 'company'):
            ttk.Label(self, text="Company:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            self.entry_company = ttk.Entry(self, width=50)
            self.entry_company.insert(0, self.module.company)
            self.entry_company.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1
            
            ttk.Label(self, text="Date Range:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            self.entry_date = ttk.Entry(self, width=50)
            self.entry_date.insert(0, self.module.date_range)
            self.entry_date.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1

        # TextModule (Extended/Summary)
        if hasattr(self.module, 'text_extended'):
            ttk.Label(self, text="Extended Text:").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
            self.text_ext = tk.Text(self, height=8, width=50)
            self.text_ext.insert("1.0", self.module.text_extended)
            self.text_ext.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1
            
            ttk.Label(self, text="Summary Text:").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
            self.text_sum = tk.Text(self, height=4, width=50)
            self.text_sum.insert("1.0", self.module.text_summary)
            self.text_sum.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1
            
            # Hyperlink explanation (simple implementation)
            lbl_help = ttk.Label(self, text="Use HTML-like tags for links: <a href='url'>text</a>")
            lbl_help.grid(row=row, column=1, sticky="w")
            row += 1

        # Tags (Experience only)
        if hasattr(self.module, 'tags'):
            ttk.Label(self, text="Tags:").grid(row=row, column=0, sticky="nw", padx=10, pady=5)
            self.list_tags = tk.Listbox(self, selectmode=tk.MULTIPLE, height=6)
            for tag in self.available_tags:
                self.list_tags.insert(tk.END, tag)
                if tag in self.module.tags:
                     self.list_tags.selection_set(tk.END) # Select last inserted
                # Re-check selection logic based on value matching.
                # Actually, keys are names.
                if tag in self.module.tags:
                     idx = self.list_tags.size() - 1
                     self.list_tags.selection_set(idx)

            self.list_tags.grid(row=row, column=1, sticky="w", padx=10, pady=5)
            row += 1

        # Save Button
        btn_save = ttk.Button(self, text="Save", command=self.save_module)
        btn_save.grid(row=row, column=1, pady=20)

    def browse_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if filename:
            self.entry_img.delete(0, tk.END)
            self.entry_img.insert(0, filename)

    def save_module(self):
        # Update module object
        if hasattr(self.module, 'title'):
            self.module.title = self.entry_title.get()
        if hasattr(self.module, 'name'):
            self.module.name = self.entry_name.get()
        if hasattr(self.module, 'image_path'):
            self.module.image_path = self.entry_img.get()
        if hasattr(self.module, 'company'):
            self.module.company = self.entry_company.get()
        if hasattr(self.module, 'date_range'):
            self.module.date_range = self.entry_date.get()
        if hasattr(self.module, 'text_extended'):
            self.module.text_extended = self.text_ext.get("1.0", tk.END).strip()
            self.module.text_summary = self.text_sum.get("1.0", tk.END).strip()
        if hasattr(self.module, 'tags'):
            selected_indices = self.list_tags.curselection()
            self.module.tags = [self.list_tags.get(i) for i in selected_indices]
            
        if self.on_save:
            self.on_save(self.module)
        
        self.destroy()
