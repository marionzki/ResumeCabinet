import sys
from functools import wraps

# Parche para el error de Windows y Python 3.13 con asyncio al cerrar la app
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        def silence_winerror_10054(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except ConnectionResetError as e:
                    if getattr(e, 'winerror', None) == 10054:
                        pass
                    else:
                        raise
            return wrapper
        _ProactorBasePipeTransport._call_connection_lost = silence_winerror_10054(_ProactorBasePipeTransport._call_connection_lost)
    except Exception:
        pass

import flet as ft
from controller.flet_controller import FletController

def main(page: ft.Page):
    app = FletController(page)

if __name__ == "__main__":
    ft.run(main)
