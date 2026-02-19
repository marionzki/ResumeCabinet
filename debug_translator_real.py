from utils.translator import TranslationService

ts = TranslationService()
text = "Ingeniero de Software"
print(f"Translating '{text}'...")
res = ts.translate_text(text, "Inglés")
print(f"Result: '{res}'")

text2 = "Desarrollador [Web](https://example.com)"
print(f"Translating '{text2}'...")
res2 = ts.translate_text(text2, "Inglés")
print(f"Result: '{res2}'")
