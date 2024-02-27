import os
import pdfplumber
import csv
import json

def clean_text(text):
    # Define replacements here
    replacements = {
        'ÔÇ∑': '<li>',  # Replace with a hyphen or appropriate bullet point
        '': '<li>'
        # Add more replacements as needed
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def extract_and_save_all_tables(pdf_path, output_csv_path, output_json_path, start_page=None, end_page=None):
    """
    Extracts tables from specified range of pages in a PDF, cleans the text,
    and appends them into a single CSV file and a single JSON file.
    
    Parameters:
    - pdf_path: Path to the PDF file.
    - output_csv_path: Path where the extracted tables will be saved as a CSV file.
    - output_json_path: Path where the extracted tables will be saved as a JSON file.
    - start_page: The first page to extract tables from (1-indexed). If None, extraction starts from the first page.
    - end_page: The last page to extract tables from (1-indexed). If None, extraction goes through the last page.
    """
    all_tables = []  # List to hold all rows for JSON output
    if os.path.exists(output_csv_path):
        os.remove(output_csv_path)
    if os.path.exists(output_json_path):
        os.remove(output_json_path)
    with pdfplumber.open(pdf_path) as pdf, open(output_csv_path, 'w', newline='') as csvfile:

        writer = csv.writer(csvfile)
        # Adjust the page range based on provided parameters
        pages = pdf.pages[start_page-1:end_page] if start_page and end_page else pdf.pages
        for page in pages:
            tables = page.extract_tables()
            for table in tables:
                cleaned_table = []
                for row in table:
                    cleaned_row = [clean_text(cell) if cell else cell for cell in row]
                    cleaned_table.append(cleaned_row)
                    all_tables.append(cleaned_row)  # Add cleaned row to list for JSON output
                for cleaned_row in cleaned_table:
                    writer.writerow(cleaned_row)
                    
    
    with open(output_json_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(all_tables, jsonfile, ensure_ascii=False, indent=4)

# Example usage
pdf_path = '/home/njui/kn_workspace/curriculum_taxonomy_extractor/data/ALL/ALL_MATH/GRADE 5 CURRICULUM DESIGNS- MATHEMATICS.pdf'
output_csv_path = 'data/ALL/ALL_MATH_CSV/math_grade_5.csv'
output_json_path = 'data/ALL/ALL_MATH_CSV/math_grade_5.json'
extract_and_save_all_tables(pdf_path, output_csv_path, output_json_path)

# Extract and save tables from a specific page range
# extract_and_save_all_tables(pdf_path, output_csv_path)
