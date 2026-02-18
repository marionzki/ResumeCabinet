import flet as ft
try:
    print("ft.Colors.RED:", ft.Colors.RED)
except Exception as e:
    print("ft.Colors.RED error:", e)

try:
    import flet.icons as icons
    print("icons.ADD:", icons.ADD)
except ImportError:
    print("import flet.icons failed")

try:
    print("ft.icons.ADD:", ft.icons.ADD)
except Exception as e:
    print("ft.icons.ADD error:", e)
