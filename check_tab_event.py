import flet as ft
import inspect

print("Tab args:", list(inspect.signature(ft.Tab.__init__).parameters.keys()))
print("TabBar dir:", dir(ft.TabBar))
