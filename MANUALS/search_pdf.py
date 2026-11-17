import PyPDF2
import os

keywords = ['VPA', 'VPA2', 'TPS', 'THROTTLE', 'VOLTAGE']

for file in os.listdir('.'):
    if file.lower().endswith('.pdf'):
        print(f"--- Searching in {file} ---")
        try:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        if any(kw in line.upper() for kw in keywords):
                            if 'VPA' in line.upper() or 'THROTTLE' in line.upper() or 'TPS' in line.upper():
                                print(f"Page {page_num + 1}: {line.strip()}")
        except Exception as e:
            print(f"Error reading {file}: {e}")
