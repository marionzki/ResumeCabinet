import flet as ft
from model.modules import ExperienceModule, ImageModule, PersonalInfoModule, AvatarModule, TextModule

class ModuleForm:
    def __init__(self, page: ft.Page, module, available_tags=None, on_save=None, file_picker=None):
        self.page = page
        self.module = module
        self.available_tags = available_tags or []
        self.on_save = on_save
        
        self.dialog = None
        self.file_picker = file_picker
        
        # Controls references

        # Controls references
        self.title_field = None
        self.name_field = None
        self.img_field = None
        self.company_field = None
        self.date_field = None
        self.text_ext_field = None
        self.text_sum_field = None
        self.tags_checks = []

    def show(self):
        content_controls = self.build_form_fields()
        
        self.dialog = ft.AlertDialog(
            title=ft.Text("Edit Module"),
            content=ft.Container(
                content=ft.Column(content_controls, scroll=ft.ScrollMode.AUTO, height=400),
                width=500
            ),
            actions=[
                ft.TextButton(content=ft.Text("Cancel"), on_click=self.close),
                ft.ElevatedButton(content=ft.Text("Save"), on_click=self.save)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        # Try page.show_dialog() as seen in dir(page)
        if hasattr(self.page, "show_dialog"):
            self.page.show_dialog(self.dialog)
        else:
            self.page.dialog = self.dialog
            self.dialog.open = True
            self.page.update()

    def close(self, e=None):
        self.dialog.open = False
        self.page.update()

    def build_form_fields(self):
        controls = []
        
        # Common: Title/Name
        if hasattr(self.module, 'title'):
            self.title_field = ft.TextField(label="Title", value=self.module.title)
            controls.append(self.title_field)
            
        if hasattr(self.module, 'name'):
            self.name_field = ft.TextField(label="Name", value=self.module.name)
            controls.append(self.name_field)
            
        # Image Path
        if hasattr(self.module, 'image_path'):
            self.img_field = ft.TextField(label="Image Path", value=self.module.image_path, expand=True)
            controls.append(ft.Row([
                self.img_field,
                ft.IconButton(icon=ft.icons.Icons.FOLDER_OPEN, on_click=self.pick_image)
            ]))
            
        # Experience
        if hasattr(self.module, 'company'):
            self.company_field = ft.TextField(label="Company", value=self.module.company)
            controls.append(self.company_field)
            
            self.date_field = ft.TextField(label="Date Range", value=self.module.date_range)
            controls.append(self.date_field)

        # Text
        if hasattr(self.module, 'text_extended'):
            self.text_ext_field = ft.TextField(label="Extended Text", value=self.module.text_extended, multiline=True, min_lines=3)
            controls.append(self.text_ext_field)
            
            self.text_sum_field = ft.TextField(label="Summary Text", value=self.module.text_summary, multiline=True, min_lines=2)
            controls.append(self.text_sum_field)
            
        # Tags
        if hasattr(self.module, 'tags'):
            controls.append(ft.Text("Tags:", weight=ft.FontWeight.BOLD))
            self.tags_checks = []
            for tag in self.available_tags:
                is_checked = tag in self.module.tags
                chk = ft.Checkbox(label=tag, value=is_checked)
                self.tags_checks.append((tag, chk))
                controls.append(chk)

        return controls

    async def pick_image(self, e):
        result = await self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["jpg", "png", "jpeg"])
        if result:
            if self.img_field:
                self.img_field.value = result[0].path
                self.img_field.update()

    def save(self, e):
        # Update module
        if self.title_field: self.module.title = self.title_field.value
        if self.name_field: self.module.name = self.name_field.value
        if self.img_field: self.module.image_path = self.img_field.value
        if self.company_field: self.module.company = self.company_field.value
        if self.date_field: self.module.date_range = self.date_field.value
        if self.text_ext_field: 
            self.module.text_extended = self.text_ext_field.value
            self.module.text_summary = self.text_sum_field.value
        
        if hasattr(self.module, 'tags'):
            new_tags = [tag for tag, chk in self.tags_checks if chk.value]
            self.module.tags = new_tags

        if self.on_save:
            self.on_save(self.module)
            
        self.close()
