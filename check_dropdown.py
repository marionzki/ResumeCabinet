import flet as ft
import inspect

print("Dropdown:", list(inspect.signature(ft.Dropdown.__init__).parameters.keys()))
print("TextButton:", list(inspect.signature(ft.TextButton.__init__).parameters.keys()))
