import flet as ft
import inspect

print("Tabs args:", list(inspect.signature(ft.Tabs.__init__).parameters.keys()))
print("TextField args:", list(inspect.signature(ft.TextField.__init__).parameters.keys()))
