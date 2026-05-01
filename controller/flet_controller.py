import asyncio
from copy import deepcopy
from model.cv_data import CVData, Section, Settings
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
        self.app_root_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.legacy_user_data_dir = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "ResumeCabinet")
        self.legacy_autosave_path = os.path.join(self.legacy_user_data_dir, "user_data.json")
        self.legacy_templates_dir = os.path.join(self.legacy_user_data_dir, "templates")
        self.project_legacy_autosave_path = os.path.abspath("user_data.json")
        self.project_legacy_templates_dir = os.path.abspath("templates")
        self.storage_root_dir = self._resolve_storage_root_dir()
        os.environ["RESUMECABINET_DATA_ROOT"] = self.storage_root_dir
        self.global_root_dir = os.path.join(self.storage_root_dir, "global")
        self.users_root_dir = os.path.join(self.storage_root_dir, "users")
        self.defaults_root_dir = os.path.join(self.storage_root_dir, "defaults")
        self.global_library_path = os.path.join(self.global_root_dir, "library.json")
        self.defaults_profile_path = os.path.join(self.defaults_root_dir, "initial_profile.json")
        self.defaults_library_path = os.path.join(self.defaults_root_dir, "initial_library.json")
        self.active_user_key = ""
        self.user_templates_dir = ""
        self.user_profile_meta_path = ""
        self.bundled_templates_dir = os.path.join(self.base_dir, "templates")
        self.autosave_path = ""
        self._pending_profile_name = ""
        self._pending_name_control = None
        self._pn_blur_generation = 0

        os.makedirs(self.global_root_dir, exist_ok=True)
        os.makedirs(self.users_root_dir, exist_ok=True)
        os.makedirs(self.defaults_root_dir, exist_ok=True)
        self._ensure_default_seed_files()
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

    def _resolve_storage_root_dir(self):
        portable_root = os.path.join(self.app_root_dir, "data")
        try:
            os.makedirs(portable_root, exist_ok=True)
            return portable_root
        except Exception:
            fallback = self.legacy_user_data_dir
            os.makedirs(fallback, exist_ok=True)
            return fallback

    def _sanitize_user_key(self, raw_name):
        name = (raw_name or "").strip()
        if not name:
            name = "usuario_sin_nombre"
        safe = re.sub(r"\s+", "_", name.lower())
        safe = re.sub(r"[^a-z0-9_\-]", "", safe)
        return safe or "usuario_sin_nombre"

    def _atomic_write_json(self, path, data):
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, path)

    def _read_json_file(self, path):
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _profile_payload_from_cv(self, cv):
        return {
            "settings": cv.settings.to_dict(),
            "header_info": cv.header_info.to_dict(),
            "sections": {
                "personal_info": cv.personal_info.to_dict(),
                "experience": cv.experience.to_dict(),
                "education": cv.education.to_dict(),
            },
        }

    def _get_seed_cvdata(self):
        template_candidates = [
            os.path.join(self.bundled_templates_dir, "Python_Developer.json"),
            os.path.join(self.bundled_templates_dir, "Data_Analyst.json"),
        ]
        for candidate in template_candidates:
            if not os.path.exists(candidate):
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return CVData.from_json(f.read())
            except Exception:
                continue
        return CVData()

    def _library_payload_from_cv(self, cv):
        return {
            "sections": {
                "knowledge": cv.knowledge.to_dict(),
                "software": cv.software.to_dict(),
                "languages": cv.languages.to_dict(),
            }
        }

    def _compose_cv_from_profile_and_library(self, profile_payload, library_payload):
        profile = profile_payload or self._profile_payload_from_cv(CVData())
        library = library_payload or self._library_payload_from_cv(CVData())
        merged = {
            "settings": profile.get("settings", {}),
            "header_info": profile.get("header_info", {}),
            "sections": {},
        }
        merged["sections"].update(profile.get("sections", {}))
        merged["sections"].update(library.get("sections", {}))
        return CVData.from_json(json.dumps(merged, ensure_ascii=False))

    def _ensure_default_seed_files(self):
        seed_cv = self._get_seed_cvdata()
        if not os.path.exists(self.defaults_profile_path):
            self._atomic_write_json(self.defaults_profile_path, self._profile_payload_from_cv(seed_cv))
        if not os.path.exists(self.defaults_library_path):
            self._atomic_write_json(self.defaults_library_path, self._library_payload_from_cv(seed_cv))
        if not os.path.exists(self.global_library_path):
            seed_lib = self._read_json_file(self.defaults_library_path) or self._library_payload_from_cv(seed_cv)
            self._atomic_write_json(self.global_library_path, seed_lib)

    def _create_empty_profile(self, display_name):
        profile_seed = deepcopy(self._read_json_file(self.defaults_profile_path) or self._profile_payload_from_cv(CVData()))
        header = profile_seed.setdefault("header_info", {})
        header["name"] = display_name
        self._set_active_user_paths(display_name)
        self._atomic_write_json(self.autosave_path, profile_seed)
        self._atomic_write_json(
            self.user_profile_meta_path,
            {"display_name": display_name, "user_key": self.active_user_key},
        )

    def _list_profile_keys(self):
        if not os.path.exists(self.users_root_dir):
            return []
        return sorted([d for d in os.listdir(self.users_root_dir) if os.path.isdir(os.path.join(self.users_root_dir, d))])

    def get_profile_display_names(self):
        names = []
        for key in self._list_profile_keys():
            meta_path = os.path.join(self.users_root_dir, key, "profile_meta.json")
            meta = self._read_json_file(meta_path) or {}
            names.append(meta.get("display_name", key))
        return sorted(set([n for n in names if n]))

    def _merge_sections_additive(self, current, incoming):
        signatures = set()
        for module in current.modules:
            signatures.add(self._module_signature(module))
        for module in incoming.modules:
            sig = self._module_signature(module)
            if sig in signatures:
                continue
            current.modules.append(module)
            signatures.add(sig)

    def _canonical_library_item_key(self, section, module):
        sec_type = getattr(section, "type", "") or ""
        sec_id = getattr(section, "id", "") or ""
        cls = type(module).__name__

        # Competencias: TextModule keyed by visible title (case-insensitive trim)
        if sec_id == "knowledge" or sec_type == "generic":
            if cls == "TextModule":
                t = (getattr(module, "title", "") or "").strip().lower()
                return ("knowledge_title", t) if t else ("knowledge_fallback", getattr(module, "id", "") or "")
        # Software / lenguajes: ImageModule keyed by name
        if sec_type in ("software", "language") and cls == "ImageModule":
            n = (getattr(module, "name", "") or "").strip().lower()
            return ("image_name", n) if n else ("image_fallback", getattr(module, "id", "") or "")
        # Otros tipos dentro de estas secciones: no agrupamos (evitar colisión)
        return ("other", cls, getattr(module, "id", "") or "")

    def _extend_library_section_without_dupes(self, target_section, incoming_section):
        keys_seen = set()
        for m in target_section.modules:
            keys_seen.add(self._canonical_library_item_key(target_section, m))
        for m in incoming_section.modules:
            k = self._canonical_library_item_key(target_section, m)
            if k in keys_seen:
                continue
            target_section.modules.append(m)
            keys_seen.add(k)

    def _dedupe_global_library_on_cv(self, cv):
        for sec in (cv.knowledge, cv.software, cv.languages):
            seen = set()
            kept = []
            for m in sec.modules:
                k = self._canonical_library_item_key(sec, m)
                if k in seen:
                    continue
                seen.add(k)
                kept.append(m)
            sec.modules = kept

    def _merge_library_payload_additive(self, base_payload, incoming_payload):
        base_cv = self._compose_cv_from_profile_and_library({}, base_payload or {})
        incoming_cv = self._compose_cv_from_profile_and_library({}, incoming_payload or {})
        self._extend_library_section_without_dupes(base_cv.knowledge, incoming_cv.knowledge)
        self._extend_library_section_without_dupes(base_cv.software, incoming_cv.software)
        self._extend_library_section_without_dupes(base_cv.languages, incoming_cv.languages)
        self._dedupe_global_library_on_cv(base_cv)
        return self._library_payload_from_cv(base_cv)

    def _module_signature(self, module):
        m_type = type(module).__name__
        title = (getattr(module, "title", "") or "").strip().lower()
        name = (getattr(module, "name", "") or "").strip().lower()
        company = (getattr(module, "company", "") or "").strip().lower()
        date_range = (getattr(module, "date_range", "") or "").strip().lower()
        text_extended = (getattr(module, "text_extended", "") or "").strip().lower()
        image_path = (getattr(module, "image_path", "") or "").strip().lower()
        return f"{m_type}|{title}|{name}|{company}|{date_range}|{text_extended[:80]}|{image_path}"

    def _set_active_user_paths(self, user_name):
        self.active_user_key = self._sanitize_user_key(user_name)
        user_root = os.path.join(self.users_root_dir, self.active_user_key)
        self.autosave_path = os.path.join(user_root, "user_data.json")
        self.user_templates_dir = os.path.join(user_root, "templates")
        self.user_profile_meta_path = os.path.join(user_root, "profile_meta.json")
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
        if has_user_profiles:
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
                self._atomic_write_json(self.autosave_path, self._profile_payload_from_cv(self.cv_data))
                self._atomic_write_json(self.global_library_path, self._library_payload_from_cv(self.cv_data))
                self._atomic_write_json(
                    self.user_profile_meta_path,
                    {"display_name": self.cv_data.header_info.name, "user_key": self.active_user_key},
                )
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
        self.save_autosave()
        self._set_active_user_paths(new_name)
        if old_key == self.active_user_key:
            return
        if os.path.exists(self.autosave_path):
            self.load_autosave()
            self.show_snackbar(f"Perfil cargado: {new_name}")
        else:
            self._create_empty_profile(new_name)
            self.load_autosave()
            self.show_snackbar(f"Nuevo perfil creado: {new_name}")

    def load_autosave(self):
        try:
            if not os.path.exists(self.autosave_path):
                self._create_empty_profile(self.cv_data.header_info.name or "usuario_sin_nombre")
            profile_payload = self._read_json_file(self.autosave_path) or self._profile_payload_from_cv(CVData())
            library_payload = self._read_json_file(self.global_library_path) or {}
            seed_library = self._read_json_file(self.defaults_library_path) or self._library_payload_from_cv(self._get_seed_cvdata())
            library_payload = self._merge_library_payload_additive(seed_library, library_payload)
            self._atomic_write_json(self.global_library_path, library_payload)
            self.cv_data = self._compose_cv_from_profile_and_library(profile_payload, library_payload)
            self._dedupe_global_library_on_cv(self.cv_data)
            self._normalize_cv_image_paths()
            print("Autosave loaded")
            self.save_autosave()
            self.refresh_view()
        except Exception as e:
            print(f"Error loading autosave: {e}")

    def save_autosave(self):
        try:
            self._normalize_cv_image_paths()
            self._dedupe_global_library_on_cv(self.cv_data)
            self._atomic_write_json(self.autosave_path, self._profile_payload_from_cv(self.cv_data))
            current_global = self._read_json_file(self.global_library_path) or {}
            merged_global = self._merge_library_payload_additive(current_global, self._library_payload_from_cv(self.cv_data))
            self._atomic_write_json(self.global_library_path, merged_global)
            self._atomic_write_json(
                self.user_profile_meta_path,
                {"display_name": self.cv_data.header_info.name, "user_key": self.active_user_key},
            )
            print("Autosave updated")
        except Exception as e:
            print(f"Error saving autosave: {e}")

    def request_profile_name_change(self, new_name, name_control=None):
        requested = (new_name or "").strip()
        current = (self.cv_data.header_info.name or "").strip()
        if not requested or requested == current:
            if name_control and name_control.value != current:
                name_control.value = current
                name_control.update()
            return
        self._pending_profile_name = requested
        self._pending_name_control = name_control

        warning = (
            "Se creará/cargará un perfil para ese nombre.\n\n"
            "Si es nuevo, se resetearán estas pestañas del perfil:\n"
            "- Configuración\n- Información personal\n- Experiencia\n- Formación\n- Templates\n\n"
            "La librería global (Competencias, Software y Lenguajes) se mantiene compartida."
        )
        dlg = ft.AlertDialog(
            title=ft.Text("¿Crear/cambiar perfil?"),
            content=ft.Text(warning),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._cancel_profile_name_change(dlg)),
                ft.TextButton("Aceptar", on_click=lambda e: self._confirm_profile_name_change(dlg)),
            ],
        )
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dlg)
        else:
            self.page.dialog = dlg
            dlg.open = True
            self.page.update()

    def _cancel_profile_name_change(self, dialog):
        dialog.open = False
        prev = self.cv_data.header_info.name
        if self._pending_name_control is not None:
            self._pending_name_control.value = prev
            self._pending_name_control.update()
        self._pending_profile_name = ""
        self._pending_name_control = None
        self.page.update()

    def _confirm_profile_name_change(self, dialog):
        dialog.open = False
        requested = self._pending_profile_name.strip()
        self._pending_profile_name = ""
        self._pending_name_control = None
        if requested:
            self._switch_user_storage(requested)
        self.page.update()

    def cancel_profile_name_scheduled_blur(self):
        """Invalida cualquier blur/submit aplazado (p. ej. al elegir autocompletado)."""
        self._pn_blur_generation += 1

    def schedule_profile_name_prompt(self, control):
        """
        Espera antes de procesar nombre: el clic en autocompletado suele producir blur
        con texto parcial antes de que el campo tome el nombre completo.
        """
        self._pn_blur_generation += 1
        gen = self._pn_blur_generation

        async def deferred():
            await asyncio.sleep(0.22)
            if gen != self._pn_blur_generation:
                return
            val = ""
            try:
                val = (control.value or "").strip()
            except Exception:
                pass
            self.request_profile_name_change(val, control)

        try:
            asyncio.get_running_loop().create_task(deferred())
        except RuntimeError:
            self.request_profile_name_change((control.value or "").strip(), control)

    def import_tabs_from_profile(self, source_name, tabs):
        if not source_name:
            self.show_snackbar("Selecciona un perfil origen.")
            return
        source_key = self._sanitize_user_key(source_name)
        if source_key == self.active_user_key:
            self.show_snackbar("Selecciona un perfil distinto al actual.")
            return
        source_path = os.path.join(self.users_root_dir, source_key, "user_data.json")
        if not os.path.exists(source_path):
            self.show_snackbar("No se encontró el perfil origen.")
            return
        payload = self._read_json_file(source_path)
        if not payload:
            self.show_snackbar("No se pudieron leer los datos del perfil origen.")
            return
        source_cv = self._compose_cv_from_profile_and_library(payload, self._read_json_file(self.global_library_path))
        tab_set = set(tabs or [])

        if "Configuración" in tab_set:
            cur_header = self.cv_data.header_info
            src_header = source_cv.header_info
            for field in ["job_position", "certifications", "city", "country", "email", "phone", "others", "linkedin"]:
                if not (getattr(cur_header, field, "") or "").strip():
                    setattr(cur_header, field, getattr(src_header, field, ""))
            if self.cv_data.settings.language == "Español" and source_cv.settings.language != "Español":
                self.cv_data.settings.language = source_cv.settings.language
            if self.cv_data.settings.design == Settings().design:
                self.cv_data.settings.design = source_cv.settings.design
        if "Información personal" in tab_set:
            self._merge_sections_additive(self.cv_data.personal_info, source_cv.personal_info)
        if "Experiencia" in tab_set:
            self._merge_sections_additive(self.cv_data.experience, source_cv.experience)
        if "Formación" in tab_set:
            self._merge_sections_additive(self.cv_data.education, source_cv.education)
        if "Competencias" in tab_set:
            self._extend_library_section_without_dupes(self.cv_data.knowledge, source_cv.knowledge)
        if "Software" in tab_set:
            self._extend_library_section_without_dupes(self.cv_data.software, source_cv.software)
        if "Lenguajes" in tab_set:
            self._extend_library_section_without_dupes(self.cv_data.languages, source_cv.languages)

        self.save_autosave()
        self.refresh_view()
        self.show_snackbar("Pestañas importadas (sin Templates).")

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
            if key == "name":
                self.request_profile_name_change(value)
                return
            setattr(self.cv_data.header_info, key, value)
            print(f"Header info {key} updated to {value}")
            self.save_autosave()

    def open_import_tabs_dialog(self):
        profile_names = [n for n in self.get_profile_display_names() if self._sanitize_user_key(n) != self.active_user_key]
        source_field = ft.Dropdown(
            label="Perfil origen",
            options=[ft.dropdown.Option(n) for n in profile_names],
            value=profile_names[0] if profile_names else None,
        )
        tab_names = ["Configuración", "Información personal", "Experiencia", "Formación", "Competencias", "Software", "Lenguajes"]
        checks = [(name, ft.Checkbox(label=name, value=name in ["Experiencia", "Formación"])) for name in tab_names]
        dialog = ft.AlertDialog(
            title=ft.Text("Importar pestañas desde otro perfil"),
            content=ft.Column([source_field, ft.Divider()] + [chk for _, chk in checks], tight=True, scroll=ft.ScrollMode.AUTO, height=350),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._close_dialog(dialog)),
                ft.TextButton(
                    "Importar",
                    on_click=lambda e: self._import_from_dialog(dialog, source_field.value, [n for n, c in checks if c.value]),
                ),
            ],
        )
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def _import_from_dialog(self, dialog, source_name, tabs):
        dialog.open = False
        self.page.update()
        self.import_tabs_from_profile(source_name, tabs)


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
            if section.type in ("generic", "software", "language"):
                new_key = self._canonical_library_item_key(section, new_module)
                for m in section.modules:
                    if self._canonical_library_item_key(section, m) == new_key:
                        self.show_snackbar("Ya existe un elemento con el mismo nombre en esta sección.")
                        return
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
