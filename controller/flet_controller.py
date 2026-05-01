from model.cv_data import CVData, Section
from view_flet.main_view import FletMainWindow
import flet as ft
import json
import os
import re
import sys
from utils.asset_paths import materialize_user_media_path, normalize_asset_reference
from utils.dialog_cleanup import register_dialog_root, unregister_dialog_root, close_all_dialog_roots

class FletController:
    def __init__(self, page: ft.Page):
        self.page = page
        self.cv_data = CVData()
        self.base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.user_data_dir = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "ResumeCabinet")
        self.users_root_dir = os.path.join(self.user_data_dir, "users")
        self.legacy_autosave_path = os.path.join(self.user_data_dir, "user_data.json")
        self.legacy_templates_dir = os.path.join(self.user_data_dir, "templates")
        self.project_legacy_autosave_path = os.path.abspath("user_data.json")
        self.project_legacy_templates_dir = os.path.abspath("templates")
        self.active_user_key = ""
        self.user_templates_dir = ""
        self.bundled_templates_dir = os.path.join(self.base_dir, "templates")
        self.autosave_path = ""

        os.makedirs(self.users_root_dir, exist_ok=True)
        self._set_active_user_paths(self.cv_data.header_info.name)
        self._migrate_legacy_data_if_needed()

        self.view = FletMainWindow(page, self)
        self.current_action = None
        self._bind_app_shutdown_hooks()
        self.load_autosave()
        self.refresh_view()

    def _bind_app_shutdown_hooks(self):
        if hasattr(self.page, "on_disconnect"):
            self.page.on_disconnect = lambda e: self.cleanup_before_exit()
        if hasattr(self.page, "window") and hasattr(self.page.window, "on_event"):
            self.page.window.on_event = self._on_window_event

    def _on_window_event(self, e):
        if getattr(e, "data", "") == "close":
            self.cleanup_before_exit()

    def cleanup_before_exit(self):
        close_all_dialog_roots()

    def _sanitize_user_key(self, raw_name):
        name = (raw_name or "").strip()
        if not name:
            name = "usuario_sin_nombre"
        safe = re.sub(r"\s+", "_", name.lower())
        safe = re.sub(r"[^a-z0-9_\-]", "", safe)
        return safe or "usuario_sin_nombre"

    def _set_active_user_paths(self, user_name):
        self.active_user_key = self._sanitize_user_key(user_name)
        user_root = os.path.join(self.users_root_dir, self.active_user_key)
        self.autosave_path = os.path.join(user_root, "user_data.json")
        self.user_templates_dir = os.path.join(user_root, "templates")
        os.makedirs(self.user_templates_dir, exist_ok=True)

    def _copy_json_templates(self, src_dir, dst_dir):
        if not os.path.exists(src_dir):
            return
        os.makedirs(dst_dir, exist_ok=True)
        for file_name in os.listdir(src_dir):
            if not file_name.endswith(".json"):
                continue
            src = os.path.join(src_dir, file_name)
            dst = os.path.join(dst_dir, file_name)
            if os.path.isfile(src) and not os.path.exists(dst):
                try:
                    with open(src, "r", encoding="utf-8") as f:
                        content = f.read()
                    with open(dst, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception as ex:
                    print(f"Template migration warning for '{file_name}': {ex}")

    def _migrate_legacy_data_if_needed(self):
        has_user_profiles = os.path.exists(self.users_root_dir) and any(
            os.path.isdir(os.path.join(self.users_root_dir, d))
            for d in os.listdir(self.users_root_dir)
        )
        if has_user_profiles and os.path.exists(self.autosave_path):
            return

        legacy_candidates = [self.legacy_autosave_path, self.project_legacy_autosave_path]
        migrated = False
        for candidate in legacy_candidates:
            if not os.path.exists(candidate):
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    loaded = CVData.from_json(f.read())
                self.cv_data = loaded
                self._set_active_user_paths(self.cv_data.header_info.name)
                if not os.path.exists(self.autosave_path):
                    with open(self.autosave_path, "w", encoding="utf-8") as f:
                        f.write(self.cv_data.to_json())
                migrated = True
                break
            except Exception as ex:
                print(f"Legacy autosave migration warning for '{candidate}': {ex}")

        # Migrate legacy templates into currently active user workspace
        self._copy_json_templates(self.legacy_templates_dir, self.user_templates_dir)
        self._copy_json_templates(self.project_legacy_templates_dir, self.user_templates_dir)

        if migrated:
            print("Legacy data migrated to per-user storage.")

    def _switch_user_storage(self, new_name):
        old_key = self.active_user_key
        self._set_active_user_paths(new_name)
        if old_key == self.active_user_key:
            return
        if os.path.exists(self.autosave_path):
            self.load_autosave()
            self.show_snackbar(f"Perfil cargado: {new_name}")
        else:
            self.save_autosave()
            self.show_snackbar(f"Nuevo perfil creado: {new_name}")

    def load_autosave(self):
        if os.path.exists(self.autosave_path):
            try:
                with open(self.autosave_path, "r", encoding="utf-8") as f:
                    self.cv_data = CVData.from_json(f.read())
                self._normalize_cv_image_paths()
                print("Autosave loaded")
                self.save_autosave()
                self.refresh_view()
            except Exception as e:
                print(f"Error loading autosave: {e}")

    def save_autosave(self):
        try:
            self._normalize_cv_image_paths()
            with open(self.autosave_path, "w", encoding="utf-8") as f:
                f.write(self.cv_data.to_json())
            print("Autosave updated")
        except Exception as e:
            print(f"Error saving autosave: {e}")

    def _keep_current_personal_info_on_loaded_cv(self, loaded_cv: CVData) -> None:
        """Preserve edited personal section when replacing cv_data from a template file."""
        kept = self.cv_data.personal_info.to_dict()
        loaded_cv.personal_info = Section.from_dict(kept)

    def _normalize_cv_image_paths(self):
        sections = [
            self.cv_data.personal_info,
            self.cv_data.experience,
            self.cv_data.education,
            self.cv_data.knowledge,
            self.cv_data.software,
            self.cv_data.languages,
        ]
        for section in sections:
            for module in section.modules:
                if hasattr(module, "image_path"):
                    module.image_path = materialize_user_media_path(
                        normalize_asset_reference(module.image_path)
                    )

    def refresh_view(self):
        current_index = 0
        if hasattr(self.view, "get_current_tab_index"):
            current_index = self.view.get_current_tab_index()

        self.view.clear_tabs()
        self.view.add_config_tab(self.cv_data)
        self.view.add_design_tab(self.cv_data)
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

    def update_design(self, key, value):
        target = self.cv_data.settings.design
        parts = key.split(".")
        try:
            for part in parts[:-1]:
                target = getattr(target, part)
            setattr(target, parts[-1], value)
            self.save_autosave()
        except AttributeError as e:
            print(f"Error updating design key '{key}': {e}")

    def update_preview_image(self):
        import fitz
        import tempfile
        import base64
        import os
        from utils.pdf_generator import PDFGenerator

        if not hasattr(self.view, 'preview_image'):
            return

        try:
            self.show_snackbar("Generando previsualización...")
            self._normalize_cv_image_paths()
            pdf_path = os.path.abspath("temp_preview.pdf")
            gen = PDFGenerator(self.cv_data)
            gen.generate(pdf_path)

            doc = fitz.open(pdf_path)
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=150)
            
            img_path = os.path.abspath("temp_preview.png")
            pix.save(img_path)
            doc.close()
            
            try:
                os.remove(pdf_path)
            except:
                pass

            with open(img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
            self.view.preview_image.src_base64 = None
            self.view.preview_image.src = f"data:image/png;base64,{encoded_string}"
            self.view.preview_image.update()
            
            self.show_snackbar("Previsualización actualizada")
        except Exception as e:
            self.show_snackbar(f"Error generando preview: {e}")

    def update_header_info(self, key, value):
        if hasattr(self.cv_data.header_info, key):
            setattr(self.cv_data.header_info, key, value)
            print(f"Header info {key} updated to {value}")
            if key == "name":
                self._switch_user_storage(value)
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

    def _create_foreground_dialog_root(self):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        register_dialog_root(root)
        return root

    # --- File Operations ---
    def new_template(self):
        self.cv_data = CVData()
        self.refresh_view()

    def load_template(self):
        from tkinter import filedialog
        root = self._create_foreground_dialog_root()
        try:
            path = filedialog.askopenfilename(parent=root, title="Open Template", filetypes=[("JSON Files", "*.json")])
        finally:
            unregister_dialog_root(root)
            root.destroy()
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    loaded_cv = CVData.from_json(f.read())
                self._keep_current_personal_info_on_loaded_cv(loaded_cv)
                self.cv_data = loaded_cv
                self._normalize_cv_image_paths()
                self._set_active_user_paths(self.cv_data.header_info.name)
                self.save_autosave()
                self.refresh_view()
                self.show_snackbar("Template loaded successfully")
            except Exception as ex:
                self.show_snackbar(f"Error loading: {ex}")

    def save_template(self):
        from tkinter import filedialog
        root = self._create_foreground_dialog_root()
        try:
            path = filedialog.asksaveasfilename(
                parent=root,
                title="Save Template",
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json")],
                initialfile="resume.json"
            )
        finally:
            unregister_dialog_root(root)
            root.destroy()
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.cv_data.to_json())
                self.show_snackbar("Template saved successfully")
            except Exception as ex:
                self.show_snackbar(f"Error saving: {ex}")

    def export_pdf(self, e=None):
        from tkinter import filedialog
        root = self._create_foreground_dialog_root()
        try:
            path = filedialog.asksaveasfilename(
                parent=root,
                title="Export to PDF",
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                initialfile="resume.pdf"
            )
        finally:
            unregister_dialog_root(root)
            root.destroy()
        if path:
            from utils.pdf_generator import PDFGenerator
            try:
                self._normalize_cv_image_paths()
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
            self._normalize_cv_image_paths()
            gen = PDFGenerator(self.cv_data)
            gen.generate(path)
            os.startfile(path)
        except Exception as ex:
            self.show_snackbar(f"Error previewing PDF: {ex}")


    def save_template_file(self, name):
        if not name: return
        file_name = f"{name}.json"
        file_name = re.sub(r'[<>:"/\\|?*]', '', file_name)

        path = os.path.join(self.user_templates_dir, file_name)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.cv_data.to_json())
            self.show_snackbar(f"Template '{name}' saved.")
            self.refresh_view() # Refresh to show new template in list
        except Exception as ex:
             self.show_snackbar(f"Error saving template: {ex}")

    def apply_template_file(self, name):
        """Load a full template (sections, texts, images, settings, and header)."""
        path = os.path.join(self.user_templates_dir, name)
        if not os.path.exists(path):
            path = os.path.join(self.bundled_templates_dir, name)
            if not os.path.exists(path):
                self.show_snackbar("Template file not found.")
                return

        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded_cv = CVData.from_json(f.read())
            self._keep_current_personal_info_on_loaded_cv(loaded_cv)
            self.cv_data = loaded_cv
            self._normalize_cv_image_paths()
            self._set_active_user_paths(self.cv_data.header_info.name)
            self.save_autosave()
            self.refresh_view()
            self.show_snackbar(f"Template '{name}' cargado con toda la información.")

        except Exception as ex:
            self.show_snackbar(f"Error applying template: {ex}")

    def delete_template_file(self, name):
        path = os.path.join(self.user_templates_dir, name)
        if os.path.exists(path):
            try:
                os.remove(path)
                self.refresh_view()
                self.show_snackbar(f"Template '{name}' deleted.")
            except Exception as ex:
                self.show_snackbar(f"Error deleting: {ex}")
        else:
            self.show_snackbar("Only user templates can be deleted.")

    def get_templates(self):
        template_names = set()
        for folder in [self.bundled_templates_dir, self.user_templates_dir]:
            if os.path.exists(folder):
                template_names.update([f for f in os.listdir(folder) if f.endswith(".json")])
        return sorted(template_names)
