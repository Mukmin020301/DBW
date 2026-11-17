import fitz
import os

keywords = ['VPA', 'VPA2', 'TPS', 'THROTTLE', 'VOLTAGE']

with open('output_utf8.txt', 'w', encoding='utf-8') as f:
    for file in os.listdir('.'):
        if file.lower().endswith('.pdf'):
            f.write(f"--- Searching in {file} ---\n")
            print(f"Searching in {file}")
            try:
                doc = fitz.open(file)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            line_upper = line.upper()
                            if any(kw in line_upper for kw in keywords):
                                if 'VPA' in line_upper or 'THROTTLE' in line_upper or 'TPS' in line_upper:
                                    f.write(f"Page {page_num + 1}: {line.strip()}\n")
            except Exception as e:
                f.write(f"Error reading {file}: {e}\n")
