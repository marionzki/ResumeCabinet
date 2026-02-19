
# Link Text Processing Test
import re

def process_custom_links(text):
    # User Syntax: *url*-**text**
    # Regex: \*([^*]+)\*-\*\*([^*]+)\*\*
    # Replacement: <a href="\1"><font color="blue">\2</font></a>
    
    pattern = r'\*(https?://[^*]+)\*-\*\*([^*]+)\*\*'
    
    def replace_match(match):
        url = match.group(1)
        text = match.group(2)
        return f'<a href="{url}"><font color="blue">{text}</font></a>'
        
    return re.sub(pattern, replace_match, text)

def process_markdown_links(text):
    # Standard Markdown: [text](url)
    # Regex: \[([^\]]+)\]\(([^)]+)\)
    
    pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
    
    def replace_match(match):
        text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}"><font color="blue">{text}</font></a>'
        
    return re.sub(pattern, replace_match, text)

# Test
sample = "Aquí está mi *https://linkedin.com*-**PERFIL LINKEDIN** y mi web."
sample_md = "Aquí está mi [PERFIL LINKEDIN](https://linkedin.com) y mi web."

print(f"Original: {sample}")
print(f"Processed: {process_custom_links(sample)}")
print("-" * 20)
print(f"Markdown: {sample_md}")
print(f"Processed MD: {process_markdown_links(sample_md)}")
