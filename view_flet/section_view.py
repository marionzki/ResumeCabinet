import flet as ft

class SectionView(ft.Column):
    def __init__(self, section, controller):
        super().__init__()
        self.section = section
        self.controller = controller
        self.spacing = 10
        self.scroll = ft.ScrollMode.AUTO
        self.expand = True

    def did_mount(self):
        self.refresh_modules()

    def refresh_modules(self):
        self.controls.clear()
        
        # Header
        self.controls.append(
            ft.Row([
                ft.Text(self.section.title, size=24, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.icons.Icons.ADD_CIRCLE, 
                    icon_color=ft.Colors.GREEN,
                    tooltip=f"Add to {self.section.title}",
                    on_click=lambda e: self.controller.add_module(self.section)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
        
        # Modules List
        if not self.section.modules:
            self.controls.append(ft.Text("No items yet.", italic=True, color=ft.Colors.GREY))
        else:
            for module in self.section.modules:
                self.controls.append(self.create_module_card(module))
        
        self.update()

    def create_module_card(self, module):
        # Determine title to show
        title_text = "Untitled"
        subtitle_text = ""
        
        if hasattr(module, 'title') and module.title:
            title_text = module.title
        elif hasattr(module, 'name') and module.name:
            title_text = module.name
        elif hasattr(module, 'image_path') and module.image_path:
            title_text = "Image"
            subtitle_text = module.image_path
            
        if hasattr(module, 'company') and module.company:
            subtitle_text = f"{module.company} | {module.date_range}"
            
        # Is active switch
        is_active = ft.Switch(
            value=module.is_active,
            on_change=lambda e: self.toggle_module(module, e.control.value)
        )
            
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(title_text, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(subtitle_text, size=12, color=ft.Colors.GREY_700) if subtitle_text else ft.Container()
                    ], expand=True),
                    
                    ft.Row([
                        ft.IconButton(
                            icon=ft.icons.Icons.ARROW_UPWARD,
                            tooltip="Subir",
                            on_click=lambda e: self.controller.move_module_up(module, self.section)
                        ),
                        ft.IconButton(
                            icon=ft.icons.Icons.ARROW_DOWNWARD,
                            tooltip="Bajar",
                            on_click=lambda e: self.controller.move_module_down(module, self.section)
                        ),
                        is_active,
                        ft.IconButton(
                            icon=ft.icons.Icons.EDIT, 
                            icon_color=ft.Colors.BLUE,
                            tooltip="Edit",
                            on_click=self.create_edit_handler(module)
                        ),
                        ft.IconButton(
                            icon=ft.icons.Icons.DELETE, 
                            icon_color=ft.Colors.RED,
                            tooltip="Delete",
                            on_click=lambda e: self.controller.delete_module(module, self.section)
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=10
            )
        )

    def create_edit_handler(self, module):
        def handler(e):
            self.controller.edit_module(module, self.section)
        return handler

    def toggle_module(self, module, value):
        module.is_active = value
        # Controller logic might be needed for single-selection enforcement (Personal Info)
        self.controller.toggle_module(module, self.section)
