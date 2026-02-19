from model.cv_data import CVData
from view_flet.main_view import FletMainWindow
import flet as ft
import json
import os
# Will import other modules as we implement them

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
        # Capture current index to restore it later
        current_index = 0
        if hasattr(self.view, "get_current_tab_index"):
            current_index = self.view.get_current_tab_index()

        self.view.clear_tabs()
        
        # Add Config Tab
        self.view.add_config_tab(self.cv_data)
        
        # Add Section Tabs
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
        
        # Restore index
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
        from model.modules import ExperienceModule, ImageModule, PersonalInfoModule, AvatarModule, TextModule
        
        new_module = None
        if section.type == "experience":
            new_module = ExperienceModule(title="New Job", company="Available")
        elif section.type == "software" or section.type == "language":
            new_module = ImageModule(name="New Tool")
        elif section.type == "personal":
            # Simple dialog choice? For now default to Text if personal
            # Or simplified: Alternating? 
            # Im implementing a simple choice here
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
            # Use show_dialog if available
            if hasattr(self.page, "show_dialog"):
                self.page.show_dialog(dlg)
            else:
                self.page.dialog = dlg
                dlg.open = True
                self.page.update()
            return
            
        elif section.type == "generic" or section.type == "education":
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
            
            # Gather tags if experience
            tags = []
            if section.type == "experience":
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
                
            form = ModuleForm(self.page, module, available_tags=tags, on_save=on_save_callback, file_picker=self.file_picker)
            form.show()
        except Exception as e:
            # Avoid printing to console to prevent encoding errors
            # Show error in a dialog which forces attention
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
            
            # Refresh to show changes
            self.refresh_view_section(section)

    def refresh_view_section(self, section):
        # Re-render the specific section view
        # We need to find the SectionView instance.
        self.refresh_view()

    # File Operations
    def new_template(self):
        self.cv_data = CVData()
        self.refresh_view()

    async def load_template(self):
        result = await self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["json"])
        if result and result:
            path = result[0].path
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.cv_data = CVData.from_json(f.read())
                self.refresh_view()
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Template loaded successfully")))
            except Exception as ex:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Error loading: {ex}")))

    async def save_template(self):
        path = await self.file_picker.save_file(allowed_extensions=["json"], file_name="resume.json")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.cv_data.to_json())
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Template saved successfully")))
            except Exception as ex:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Error saving: {ex}")))

    async def export_pdf(self):
        path = await self.file_picker.save_file(allowed_extensions=["pdf"], file_name="resume.pdf")
        if path:
            from utils.pdf_generator import PDFGenerator
            try:
                gen = PDFGenerator(self.cv_data)
                gen.generate(path)
                # Auto-translations might have happened, save them
                self.save_autosave()
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("PDF exported successfully")))
            except Exception as ex:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Error exporting PDF: {ex}")))

    def preview_pdf(self):
        # Preview stays sync for now as it uses tempfile and os.startfile
        import tempfile
        import os
        from utils.pdf_generator import PDFGenerator
        
        try:
            fd, path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            
            gen = PDFGenerator(self.cv_data)
            gen.generate(path)
            
            os.startfile(path)
        except Exception as ex:
            self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Error previewing PDF: {ex}")))

