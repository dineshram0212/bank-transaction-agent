import re

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\b(\w+)(?:\W+\1\b)+', r'\1', text)
    return text