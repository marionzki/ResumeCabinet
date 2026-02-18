from model.cv_data import CVData, Section, Settings
from model.modules import TextModule, ExperienceModule, ImageModule, PersonalInfoModule, AvatarModule
from view.main_window import MainWindow
from view.forms import ModuleForm
from utils.pdf_generator import PDFGenerator
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os

class MasterController:
    def __init__(self):
        self.cv_data = CVData()
        self.view = MainWindow(self)
        
        self.refresh_view()
        self.view.mainloop()

    def refresh_view(self):
        self.view.clear_tabs()
        
        # Add Config Tab
        self.view.add_config_tab(self.cv_data)
        
        # Add Section Tabs
        # Order: Personal, Experience, Education, Knowledge, Software, Languages
        sections = [
            self.cv_data.personal_info,
            self.cv_data.experience,
            self.cv_data.education,
            self.cv_data.knowledge,
            self.cv_data.software,
            self.cv_data.languages
        ]
        
        for sec in sections:
            self.view.add_section_tab(sec)

    def add_module(self, section):
        # Factory logic based on section type
        new_module = None
        if section.type == "experience":
            new_module = ExperienceModule(title="New Job", company="Available")
        elif section.type == "software" or section.type == "language":
            new_module = ImageModule(name="New Tool")
        elif section.type == "personal":
            # Simplified: Check if we have an avatar? 
            # Let's ask user or just add text default, and have a separate 'Add Avatar' check?
            # Or simplified: Alternating? 
            # Let's make it so it defaults to Text, but if they want Avatar we might need a dialog.
            # For now, let's just add a TextModule (Bio) by default.
            # To add Avatar, user might need a specific action.
            # Hack: Add a simple prompt or just add both for testing?
            # Better: Ask context.
            # Since I can't use popups easily here without blocking, I'll just add a Text (Bio) by default.
            # Functionality to add specific types might be improved later.
            # Let's add a "Add Avatar" button in the view? 
            # Or just prompt:
            from tkinter import simpledialog
            choice = simpledialog.askstring("Type", "Type 'avatar' for image, 'bio' for text")
            if choice and choice.lower() == 'avatar':
                new_module = AvatarModule(image_path="path/to/image.jpg")
            else:
                new_module = PersonalInfoModule(title="Bio", text_extended="...")
        elif section.type == "generic" or section.type == "education":
            new_module = TextModule(title="New Item")
            
        if new_module:
            section.modules.append(new_module)
            # Trigger edit immediately?
            self.edit_module(new_module, section)
            
    def edit_module(self, module, section):
        # Gather tags if experience
        tags = []
        if isinstance(module, ExperienceModule):
            # Collect from Knowledge, Software, Languages
            for m in self.cv_data.knowledge.modules:
                if m.title: tags.append(m.title)
            for m in self.cv_data.software.modules:
                if m.name: tags.append(m.name)
            for m in self.cv_data.languages.modules:
                if m.name: tags.append(m.name)
        
        def on_save_callback(mod):
            # View refreshes automatically via its own logic/call? 
            # No, View calls controller.edit, controller opens form. 
            # Form calls callback on save.
            # We need to tell view to refresh.
            # But we don't have direct ref to specific section frame here easily without passing it.
            # actually we can just refresh the whole view or better, the specific section if we stored it.
            # For now, let's just re-render or let the View handle the refresh after this returns?
            # MainWindow.notebook -> tabs -> frames...
            pass 

        form = ModuleForm(self.view, module, available_tags=tags, on_save=on_save_callback)
        # Note: The view reloads form on button click. The widget updates are handled by form updating the module object IN PLACE.
        # The SectionFrame.refresh_modules() reads from the modules list.
        # So we just need to ensure the SectionFrame refreshes.
        # But `edit_module` in SectionFrame calls this. 
        # We need to make sure SectionFrame refreshes after the form closes.
        # Form is Toplevel. We can wait_window?
        self.view.wait_window(form)

    def toggle_module(self, module, section):
        # Enforce single selection for Personal Info
        if section.type == "personal" and module.is_active:
            # Check type of module (AvatarModule vs PersonalInfoModule)
            is_avatar = isinstance(module, AvatarModule)
            
            for m in section.modules:
                if m != module and m.is_active:
                    # If same type, deactivate it
                    if isinstance(m, AvatarModule) == is_avatar:
                         m.is_active = False

    def delete_module(self, module, section):
        if module in section.modules:
            section.modules.remove(module)

    def update_setting(self, key, value):
        if key == "language":
            self.cv_data.settings.language = value

    def new_template(self):
        self.cv_data = CVData()
        self.refresh_view()

    def save_template(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.cv_data.to_json())

    def save_template_as(self):
        self.save_template()

    def load_template(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filename:
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    self.cv_data = CVData.from_json(f.read())
                    self.refresh_view()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load: {e}")

    def preview_pdf(self):
        # Generate temp PDF and open
        import tempfile
        import os
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        gen = PDFGenerator(self.cv_data)
        gen.generate(path)
        
        os.startfile(path) # Windows logic

    def export_pdf(self):
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if filename:
            gen = PDFGenerator(self.cv_data)
            gen.generate(filename)
            messagebox.showinfo("Success", "PDF Exported Successfully")

if __name__ == "__main__":
    app = MasterController()
