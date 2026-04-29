import atexit
import threading


_lock = threading.Lock()
_roots = set()


def register_dialog_root(root):
    if root is None:
        return
    with _lock:
        _roots.add(root)


def unregister_dialog_root(root):
    if root is None:
        return
    with _lock:
        _roots.discard(root)


def close_all_dialog_roots():
    with _lock:
        roots = list(_roots)
        _roots.clear()
    for root in roots:
        try:
            root.destroy()
        except Exception:
            pass


atexit.register(close_all_dialog_roots)
