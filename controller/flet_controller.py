from model.cv_data import CVData
from view_flet.main_view import FletMainWindow
import flet as ft
import json
import os
import re

class FletController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.cv_data = CVData()
        self.view = FletMainWindow(page, self)
        self.current_action = None
        
        self.refresh_view()
        self.load_autosave()

    def load_autosave(self):
        autosave_path = "user_data.json"
        if os.path.exists(autosave_path):
            try:
                with open(autosave_path, "r", encoding="utf-8") as f:
                    self.cv_data = CVData.from_json(f.read())
                print("Autosave loaded")
                self.refresh_view()
            except Exception as e:
                print(f"Error loading autosave: {e}")

    def save_autosave(self):
        try:
            with open("user_data.json", "w", encoding="utf-8") as f:
                f.write(self.cv_data.to_json())
            print("Autosave updated")
        except Exception as e:
            print(f"Error saving autosave: {e}")

    def refresh_view(self):
        current_index = 0
        if hasattr(self.view, "get_current_tab_index"):
            current_index = self.view.get_current_tab_index()

        self.view.clear_tabs()
        self.view.add_config_tab(self.cv_data)
        self.view.add_templates_tab(self.get_templates())

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

        self.view.set_tab(current_index, update_ui=False)
        self.page.update()

    def update_setting(self, key, value):
        if key == "language":
            self.cv_data.settings.language = value
            print(f"Language updated to {value}")
            self.save_autosave()

    def update_header_info(self, key, value):
        if hasattr(self.cv_data.header_info, key):
            setattr(self.cv_data.header_info, key, value)
            print(f"Header info {key} updated to {value}")
            self.save_autosave()


    def add_module(self, section):
        from model.modules import ExperienceModule, ImageModule, PersonalInfoModule, AvatarModule, TextModule, EducationModule
        
        new_module = None
        if section.type == "experience":
            new_module = ExperienceModule(title="New Job", company="Available")
        elif section.type == "software" or section.type == "language":
            new_module = ImageModule(name="New Tool")
        elif section.type == "personal":
            def on_type_chosen(type_name):
                nonlocal new_module
                if type_name == "Avatar":
                    new_module = AvatarModule(image_path="path/to/image.jpg")
                else:
                    new_module = PersonalInfoModule(title="Bio", text_extended="...")
                
                dlg.open = False
                self.page.update()
                
                if new_module:
                    section.modules.append(new_module)
                    self.save_autosave()
                    self.edit_module(new_module, section)

            dlg = ft.AlertDialog(
                title=ft.Text("Choose Type"),
                actions=[
                    ft.TextButton("Avatar", on_click=lambda _: on_type_chosen("Avatar")),
                    ft.TextButton("Bio", on_click=lambda _: on_type_chosen("Bio"))
                ]
            )
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(dlg)
            else:
                self.page.dialog = dlg
                dlg.open = True
                self.page.update()
            return
            
        elif section.type == "education":
            new_module = EducationModule(title="New Degree", company="Institution")
        elif section.type == "generic":
            new_module = TextModule(title="New Item")
            
        if new_module:
            section.modules.append(new_module)
            self.save_autosave()
            self.edit_module(new_module, section)

    def edit_module(self, module, section):
        try:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Opening editor..."), duration=1000)
            self.page.snack_bar.open = True
            self.page.update()
            
            from view_flet.forms import ModuleForm
            
            # Gather tags if experience or education
            tags = []
            if section.type in ["experience", "education"]:
                # Collect from Knowledge, Software, Languages
                for m in self.cv_data.knowledge.modules:
                    if m.title: tags.append(m.title)
                for m in self.cv_data.software.modules:
                    if m.name: tags.append(m.name)
                for m in self.cv_data.languages.modules:
                    if m.name: tags.append(m.name)
            
            def on_save_callback(mod):
                self.save_autosave()
                self.refresh_view_section(section)
                
            form = ModuleForm(self.page, module, available_tags=tags, on_save=on_save_callback)
            form.show()
        except Exception as e:
            error_dlg = ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text(f"Could not open editor:\n{str(e)}"),
                actions=[ft.TextButton("OK", on_click=lambda _: setattr(error_dlg, 'open', False) or self.page.update())],
            )
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(error_dlg)
            else:
                self.page.dialog = error_dlg
                error_dlg.open = True
                self.page.update()

    def delete_module(self, module, section):
        if module in section.modules:
            section.modules.remove(module)
            self.save_autosave()
            self.refresh_view_section(section)

    def move_module_up(self, module, section):
        if module in section.modules:
            index = section.modules.index(module)
            if index > 0:
                section.modules[index], section.modules[index - 1] = section.modules[index - 1], section.modules[index]
                self.save_autosave()
                self.refresh_view_section(section)

    def move_module_down(self, module, section):
        if module in section.modules:
            index = section.modules.index(module)
            if index < len(section.modules) - 1:
                section.modules[index], section.modules[index + 1] = section.modules[index + 1], section.modules[index]
                self.save_autosave()
                self.refresh_view_section(section)

    def toggle_module(self, module, section):
        from model.modules import AvatarModule
        if section.type == "personal" and module.is_active:
            is_avatar = isinstance(module, AvatarModule)
            for m in section.modules:
                if m != module and m.is_active:
                    if isinstance(m, AvatarModule) == is_avatar:
                        m.is_active = False
            self.refresh_view_section(section)

    def refresh_view_section(self, section):
        self.refresh_view()

    def show_snackbar(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.snack_bar.open = True
        self.page.update()

    # --- File Operations ---
    def new_template(self):
        self.cv_data = CVData()
        self.refresh_view()

    def load_template(self):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Open Template",
            filetypes=[("JSON Files", "*.json")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.cv_data = CVData.from_json(f.read())
                self.refresh_view()
                self.show_snackbar("Template loaded successfully")
            except Exception as ex:
                self.show_snackbar(f"Error loading: {ex}")

    def save_template(self):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            title="Save Template",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="resume.json"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.cv_data.to_json())
                self.show_snackbar("Template saved successfully")
            except Exception as ex:
                self.show_snackbar(f"Error saving: {ex}")

    def export_pdf(self, e=None):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            title="Export to PDF",
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="resume.pdf"
        )
        if path:
            from utils.pdf_generator import PDFGenerator
            try:
                gen = PDFGenerator(self.cv_data)
                gen.generate(path)
                self.save_autosave()
                self.show_snackbar("PDF exported successfully")
            except Exception as ex:
                self.show_snackbar(f"Error exporting PDF: {ex}")

    def preview_pdf(self):
        import tempfile
        from utils.pdf_generator import PDFGenerator
        try:
            fd, path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            gen = PDFGenerator(self.cv_data)
            gen.generate(path)
            os.startfile(path)
        except Exception as ex:
            self.show_snackbar(f"Error previewing PDF: {ex}")


    def save_template_file(self, name):
        if not name: return
        file_name = f"{name}.json"
        file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)
        
        path = os.path.join("templates", file_name)
        if not os.path.exists("templates"):
            os.makedirs("templates")
            
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.cv_data.to_json())
            self.show_snackbar(f"Template '{name}' saved.")
            self.refresh_view() # Refresh to show new template in list
        except Exception as ex:
             self.show_snackbar(f"Error saving template: {ex}")

    def apply_template_file(self, name):
        """Apply only the active/inactive states from a saved template to the current data."""
        path = os.path.join("templates", name)
        if not os.path.exists(path):
             self.show_snackbar("Template file not found.")
             return

        try:
            with open(path, "r", encoding="utf-8") as f:
                template_data = json.loads(f.read())
            
            def map_modules(section_data):
                return {m["id"]: m.get("is_active", True) for m in section_data.get("modules", [])}

            template_sections = template_data.get("sections", {})
            current_sections = {
                "personal_info": self.cv_data.personal_info,
                "experience": self.cv_data.experience,
                "education": self.cv_data.education,
                "knowledge": self.cv_data.knowledge,
                "software": self.cv_data.software,
                "languages": self.cv_data.languages
            }
            
            count = 0
            for sec_key, sec_obj in current_sections.items():
                if sec_key in template_sections:
                    t_mod_states = map_modules(template_sections[sec_key])
                    for m in sec_obj.modules:
                        if m.id in t_mod_states:
                            m.is_active = t_mod_states[m.id]
                            count += 1
                        else:
                            m.is_active = False
                else:
                    for m in sec_obj.modules:
                        m.is_active = False
            
            self.save_autosave()
            self.refresh_view()
            self.show_snackbar(f"Template applied. Updated {count} modules.")
            
        except Exception as ex:
            self.show_snackbar(f"Error applying template: {ex}")

    def delete_template_file(self, name):
        path = os.path.join("templates", name)
        if os.path.exists(path):
            try:
                os.remove(path)
                self.refresh_view()
                self.show_snackbar(f"Template '{name}' deleted.")
            except Exception as ex:
                self.show_snackbar(f"Error deleting: {ex}")

    def get_templates(self):
        if not os.path.exists("templates"):
            return []
        files = [f for f in os.listdir("templates") if f.endswith(".json")]
        return files
