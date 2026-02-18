import flet as ft
from controller.flet_controller import FletController

def main(page: ft.Page):
    app = FletController(page)

if __name__ == "__main__":
    ft.run(main)
