"""Pure storage key helpers without bootstrapping FletController (see spec.md)."""

from model.cv_data import Section
from model.modules import ImageModule, TextModule
from controller.flet_controller import FletController


def test_sanitize_user_key_basic():
    # Methods do not reference `self`; any object may be bound arg in Py3 Class.method form.
    assert FletController._sanitize_user_key(FletController, " Mario Noriega! ") == "mario_noriega"
    assert FletController._sanitize_user_key(FletController, "") == "usuario_sin_nombre"


def test_canonical_library_key_knowledge_case_insensitive_title():
    sec = Section(id="knowledge", title="Skills", type="generic", modules=[])
    mod = TextModule(title=" Leadership ")
    key = FletController._canonical_library_item_key(FletController, sec, mod)
    assert key == ("knowledge_title", "leadership")


def test_canonical_library_key_software_by_name_ci():
    sec = Section(id="software", title="Software", type="software", modules=[])
    mod = ImageModule(name=" Cursor ")
    key = FletController._canonical_library_item_key(FletController, sec, mod)
    assert key == ("image_name", "cursor")


def test_canonical_duplicate_name_same_key_language_section():
    sec = Section(id="languages", title="Lang", type="language", modules=[])
    mod1 = ImageModule(name="Python")
    mod2 = ImageModule(name="python")
    k1 = FletController._canonical_library_item_key(FletController, sec, mod1)
    k2 = FletController._canonical_library_item_key(FletController, sec, mod2)
    assert k1 == k2
