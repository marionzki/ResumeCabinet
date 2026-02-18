import flet as ft

def main(page: ft.Page):
    print(f"Page attributes: {dir(page)}")
    
    def open_dlg(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Hello"),
            content=ft.Text("This is a test dialog"),
            actions=[ft.TextButton("Close", on_click=lambda e: close_dlg(dlg))]
        )
        if hasattr(page, "open"):
            print("Using page.open()")
            page.open(dlg)
        else:
            print("Using page.dialog = ...")
            page.dialog = dlg
            dlg.open = True
        page.update()
        print("Dialog opened")

    def close_dlg(dlg):
        if hasattr(page, "close"):
             page.close(dlg)
        else:
            dlg.open = False
        page.update()
        print("Dialog closed")

    page.add(ft.ElevatedButton("Open Dialog", on_click=open_dlg))

ft.run(main)
