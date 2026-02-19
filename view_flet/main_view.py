import flet as ft

class FletMainWindow:
    def __init__(self, page: ft.Page, controller):
        self.page = page
        self.controller = controller
        self.page.title = "ResumeCabinet Flet"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # File Picker for global operations
        self.file_picker = ft.FilePicker()
        # Workaround for "Unknown control" visual glitch: wrap in hidden Row and add to page
        self.file_picker_wrapper = ft.Row([self.file_picker], visible=False)
        self.page.add(self.file_picker_wrapper)
        self.controller.file_picker = self.file_picker # Link back to controller
        
        # App Bar
        self.page.appbar = ft.AppBar(
            title=ft.Text("ResumeCabinet"),
            center_title=False,
            bgcolor=ft.Colors.GREY_200,
            actions=[
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(content=ft.Text("New Template"), on_click=lambda _: controller.new_template()),
                        ft.PopupMenuItem(content=ft.Text("Open Template..."), on_click=lambda _: controller.load_template()),
                        ft.PopupMenuItem(), # Divider
                        ft.PopupMenuItem(content=ft.Text("Preview PDF"), on_click=lambda _: controller.preview_pdf()),
                        ft.PopupMenuItem(content=ft.Text("Export to PDF"), on_click=lambda _: controller.export_pdf()),
                    ]
                )
            ]
        )
        
        self.tab_row = ft.Row(scroll=ft.ScrollMode.AUTO)
        self.body = ft.Container(expand=True, padding=10)
        self.views = [] 
        self.tab_buttons = []
        self.current_tab_index = 0
        
        self.page.add(
            ft.Column([
                ft.Container(self.tab_row, padding=10, bgcolor=ft.Colors.GREY_100),
                self.body
            ], expand=True)
        )

    def clear_tabs(self):
        self.tab_row.controls.clear()
        self.views.clear()
        self.tab_buttons.clear()
        self.body.content = None
        self.page.update()

    def set_tab(self, index, update_ui=True):
        if 0 <= index < len(self.views):
            self.current_tab_index = index
            self.body.content = self.views[index]
            # Update button styles
            for i, btn in enumerate(self.tab_buttons):
                btn.style = ft.ButtonStyle(
                    color=ft.Colors.BLUE if i == index else ft.Colors.BLACK,
                    bgcolor=ft.Colors.BLUE_50 if i == index else None
                )
                if update_ui:
                    btn.update()
            
            if update_ui:
                self.body.update()

    def get_current_tab_index(self):
        return self.current_tab_index

    def add_templates_tab(self, templates_list):
        # Implementation for templates tab
        
        def save_click(e):
            if name_field.value:
                self.controller.save_template_file(name_field.value)
                name_field.value = ""
                self.controller.refresh_view() # Refresh to show new template

        name_field = ft.TextField(label="New Template Name", expand=True)
        
        # List of templates
        template_items = []
        for t_name in templates_list:
            template_items.append(
                ft.Container(
                    ft.Row([
                        ft.Text(t_name, expand=True, size=16),
                        ft.ElevatedButton("Load", on_click=lambda _, n=t_name: self.controller.apply_template_file(n)),
                        ft.IconButton(icon=ft.icons.Icons.DELETE, on_click=lambda _, n=t_name: self.controller.delete_template_file(n))
                    ]),
                    padding=10,
                    border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_300))
                )
            )

        content = ft.Column([
            ft.Text("Manage Templates", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Save current module configuration as a template. Loading a template will only affect which modules are active/inactive."),
            ft.Divider(),
            ft.Row([
                name_field,
                ft.ElevatedButton("Save Current State", on_click=save_click)
            ]),
            ft.Divider(),
            ft.Text("Saved Templates:", size=16, weight=ft.FontWeight.BOLD),
            ft.Column(template_items, scroll=ft.ScrollMode.AUTO, expand=True)
        ], scroll=ft.ScrollMode.AUTO)
        
        index = len(self.views)
        btn = ft.TextButton(
            content=ft.Text("Templates"),
            on_click=lambda _: self.set_tab(index)
        )
        self.tab_buttons.append(btn)
        self.tab_row.controls.append(btn)
        self.views.append(content)
        
        if index == 0:
            self.set_tab(0, update_ui=False)
        
        self.page.update()

    def add_config_tab(self, cv_data):
        # Implementation for config tab
        content = ft.Column([
            ft.Text("Configuración", size=20, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Text("Idioma del CV:", weight=ft.FontWeight.BOLD),
            ft.Dropdown(
                options=[
                    ft.dropdown.Option("Español"),
                    ft.dropdown.Option("Inglés"),
                    ft.dropdown.Option("Gallego"),
                    ft.dropdown.Option("Catalán")
                ],
                value=cv_data.settings.language,
                on_select=lambda e: self.controller.update_setting("language", e.control.value)
            ),
            ft.Divider(),
            ft.Text("Datos de Cabecera (Contacto):", size=16, weight=ft.FontWeight.BOLD),
            ft.TextField(label="Nombre Completo", value=cv_data.header_info.name, on_change=lambda e: self.controller.update_header_info("name", e.control.value)),
            ft.TextField(label="Ciudad", value=cv_data.header_info.city, on_change=lambda e: self.controller.update_header_info("city", e.control.value)),
            ft.TextField(label="País", value=cv_data.header_info.country, on_change=lambda e: self.controller.update_header_info("country", e.control.value)),
            ft.TextField(label="Email", value=cv_data.header_info.email, on_change=lambda e: self.controller.update_header_info("email", e.control.value)),
            ft.TextField(label="Teléfono", value=cv_data.header_info.phone, on_change=lambda e: self.controller.update_header_info("phone", e.control.value)),
            ft.TextField(label="LinkedIn", value=cv_data.header_info.linkedin, on_change=lambda e: self.controller.update_header_info("linkedin", e.control.value)),
        ], scroll=ft.ScrollMode.AUTO)
        
        index = len(self.views)
        btn = ft.TextButton(
            content=ft.Text("Configuración"),
            on_click=lambda _: self.set_tab(index)
        )
        self.tab_buttons.append(btn)
        self.tab_row.controls.append(btn)
        self.views.append(content)
        
        if index == 0:
            self.set_tab(0, update_ui=False)
        
        self.page.update()

    def add_section_tab(self, section_data):
        from .section_view import SectionView
        content = SectionView(section_data, self.controller)
        
        index = len(self.views)
        btn = ft.TextButton(
            content=ft.Text(section_data.title),
            on_click=lambda _: self.set_tab(index)
        )
        self.tab_buttons.append(btn)
        self.tab_row.controls.append(btn)
        self.views.append(content)
        
        if index == 0:  # If it's the first one (and Config wasn't added or verified)
             self.set_tab(0, update_ui=False)

        self.page.update()
