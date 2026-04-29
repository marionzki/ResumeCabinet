import flet as ft

class FletMainWindow:
    def __init__(self, page: ft.Page, controller):
        self.page = page
        self.controller = controller
        self.page.title = "ResumeCabinet Flet"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # App Bar
        self.page.appbar = ft.AppBar(
            title=ft.Text("ResumeCabinet"),
            center_title=False,
            bgcolor=ft.Colors.GREY_200,
            actions=[
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(content=ft.Text("Preview PDF"), on_click=lambda _: controller.preview_pdf()),
                        ft.PopupMenuItem(content=ft.Text("Export to PDF"), on_click=controller.export_pdf),
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
            ft.Text("Save and load complete profiles. Templates include texts, images, settings and module activation."),
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
            ft.TextField(
                label="Nombre Completo",
                value=cv_data.header_info.name,
                on_blur=lambda e: self.controller.update_header_info("name", e.control.value),
                on_submit=lambda e: self.controller.update_header_info("name", e.control.value)
            ),
            ft.TextField(label="Puesto", value=cv_data.header_info.job_position, on_change=lambda e: self.controller.update_header_info("job_position", e.control.value)),
            ft.TextField(label="Certificaciones", value=getattr(cv_data.header_info, "certifications", ""), multiline=True, min_lines=2, on_change=lambda e: self.controller.update_header_info("certifications", e.control.value)),
            ft.TextField(label="Ciudad", value=cv_data.header_info.city, on_change=lambda e: self.controller.update_header_info("city", e.control.value)),
            ft.TextField(label="País", value=cv_data.header_info.country, on_change=lambda e: self.controller.update_header_info("country", e.control.value)),
            ft.TextField(label="Email", value=cv_data.header_info.email, on_change=lambda e: self.controller.update_header_info("email", e.control.value)),
            ft.TextField(label="Teléfono", value=cv_data.header_info.phone, on_change=lambda e: self.controller.update_header_info("phone", e.control.value)),
            ft.TextField(label="Otros", value=cv_data.header_info.others, on_change=lambda e: self.controller.update_header_info("others", e.control.value)),
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

    def add_design_tab(self, cv_data):
        design = cv_data.settings.design
        rainbow_colors = ["#F44336", "#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#2196F3", "#03A9F4", "#00BCD4", "#009688", "#4CAF50", "#8BC34A", "#CDDC39", "#FFEB3B", "#FFC107", "#FF9800", "#FF5722", "#795548", "#9E9E9E", "#607D8B", "#000000", "#FFFFFF"]
        
        def create_color_picker(label_text, current_val, update_callback):
            def on_hex_change(e): update_callback(e.control.value)
            
            hex_field = ft.TextField(value=current_val, width=100, on_change=on_hex_change, content_padding=5, text_size=12)
            
            def create_swatch(color_hex):
                return ft.Container(
                    width=20, height=20, bgcolor=color_hex, border_radius=10,
                    border=ft.border.all(1, ft.Colors.GREY_300) if color_hex == "#FFFFFF" else None,
                    on_click=lambda e, c=color_hex: select_color(c)
                )
            
            def select_color(c_hex):
                hex_field.value = c_hex
                hex_field.update()
                update_callback(c_hex)
            
            swatches_row1 = ft.Row([create_swatch(c) for c in rainbow_colors[:11]], spacing=5, wrap=True)
            swatches_row2 = ft.Row([create_swatch(c) for c in rainbow_colors[11:]], spacing=5, wrap=True)
            
            return ft.Column([
                ft.Row([ft.Text(label_text, weight=ft.FontWeight.BOLD), hex_field]),
                swatches_row1, swatches_row2
            ], spacing=5)

        def create_font_settings_panel(label_text, font_obj, path_prefix):
            def family_changed(e): self.controller.update_design(f"{path_prefix}.family", e.control.value)
            def size_changed(e): 
                try: self.controller.update_design(f"{path_prefix}.size", float(e.control.value))
                except: pass
            def color_changed(val): self.controller.update_design(f"{path_prefix}.color", val)
            
            return ft.Column([
                ft.Text(label_text, weight=ft.FontWeight.W_600, size=14),
                ft.Row([
                    ft.Dropdown(
                        value=font_obj.family, 
                        options=[ft.dropdown.Option("Helvetica-Bold"), ft.dropdown.Option("Helvetica-Oblique"), ft.dropdown.Option("Helvetica"), ft.dropdown.Option("Times-Bold"), ft.dropdown.Option("Times-Roman"), ft.dropdown.Option("Courier")], 
                        on_select=family_changed,
                        expand=2,
                        text_size=12,
                        content_padding=5
                    ),
                    ft.TextField(value=str(font_obj.size), on_change=size_changed, expand=1, label="Tamaño", text_size=12)
                ]),
                create_color_picker("Color del texto", font_obj.color, color_changed),
                ft.Divider()
            ])

        global_text_col = ft.Column([
             create_font_settings_panel("1.1) Título", design.global_text.title, "global_text.title"),
             create_font_settings_panel("1.2) Subtítulo", design.global_text.subtitle, "global_text.subtitle"),
             create_font_settings_panel("1.3) Cuerpo de texto", design.global_text.body, "global_text.body")
        ])
        
        header_col = ft.Column([
             create_font_settings_panel("2.1) Nombre", design.header.name, "header.name"),
             create_font_settings_panel("2.2) Puesto", design.header.job, "header.job"),
             create_font_settings_panel("2.3) Certificación", design.header.certification, "header.certification")
        ])

        left_col_col = ft.Column([
             create_color_picker("3.1) Color de fondo", design.left_col.bg_color, lambda val: self.controller.update_design("left_col.bg_color", val)),
             ft.Divider(),
             create_font_settings_panel("3.2) Cuerpo de texto", design.left_col.body, "left_col.body"),
             create_font_settings_panel("3.3) Títulos secciones", design.left_col.title, "left_col.title")
        ])

        right_col_col = ft.Column([
             create_color_picker("4.1) Color fondo separadores", design.right_col.separator_bg_color, lambda val: self.controller.update_design("right_col.separator_bg_color", val)),
             ft.Divider(),
             create_font_settings_panel("4.2) Títulos secciones", design.right_col.title, "right_col.title")
        ])

        tags_col = ft.Column([
             create_font_settings_panel("Tipografía y Color Texto", design.tags.font, "tags.font"),
             create_color_picker("5.4) Color relleno", design.tags.bg_color, lambda val: self.controller.update_design("tags.bg_color", val))
        ])

        accordion = ft.Column([
             ft.ExpansionTile(title=ft.Text("1) Texto Global", weight=ft.FontWeight.BOLD), controls=[ft.Container(global_text_col, padding=10)]),
             ft.ExpansionTile(title=ft.Text("2) Cabecera", weight=ft.FontWeight.BOLD), controls=[ft.Container(header_col, padding=10)]),
             ft.ExpansionTile(title=ft.Text("3) Columna Izquierda", weight=ft.FontWeight.BOLD), controls=[ft.Container(left_col_col, padding=10)]),
             ft.ExpansionTile(title=ft.Text("4) Columna Derecha", weight=ft.FontWeight.BOLD), controls=[ft.Container(right_col_col, padding=10)]),
             ft.ExpansionTile(title=ft.Text("5) Tags Competencias", weight=ft.FontWeight.BOLD), controls=[ft.Container(tags_col, padding=10)])
        ], spacing=0)

        controls = ft.Column([
            accordion,
            ft.Divider(),
            ft.ElevatedButton("Actualizar Previsualización", on_click=lambda _: self.controller.update_preview_image())
        ], scroll=ft.ScrollMode.AUTO, expand=1)

        # A valid 1x1 base64 transparent PNG
        dummy_src = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        self.preview_image = ft.Image(src=dummy_src, expand=2, fit="contain")

        content = ft.Row([
            controls,
            ft.VerticalDivider(),
            self.preview_image
        ], expand=True)

        index = len(self.views)
        btn = ft.TextButton(content=ft.Text("Diseño"), on_click=lambda _: self.set_tab(index))
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
