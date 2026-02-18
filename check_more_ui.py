import flet as ft
import inspect

print("ElevatedButton:", list(inspect.signature(ft.ElevatedButton.__init__).parameters.keys()))
print("Checkbox:", list(inspect.signature(ft.Checkbox.__init__).parameters.keys()))
print("Switch:", list(inspect.signature(ft.Switch.__init__).parameters.keys()))
