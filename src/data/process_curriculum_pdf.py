#!/usr/bin/env python3
import argparse
import os
import pdfplumber
import json

# Function to extract strands and sub-strands with page numbers in smaller segments
def extract_strands_sub_strands_with_page_segmented(pdf_path, start_page, end_page):
    extracted_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number in range(start_page, min(end_page, len(pdf.pages))):
            page = pdf.pages[page_number]
            tables = page.extract_tables()
            for table in tables:
                if "Strand" in table[0] and "Sub Strand" in table[0]:
                    for row in table[1:]:
                        if row[0] and row[1]:
                            extracted_data.append({
                                "page_number": page_number + 1,
                                "strand": row[0],
                                "sub_strand": row[1]
                            })
    return extracted_data

def find_rubric_start_pages(pdf_path, all_strands_sub_strands, rubric_headers):
    with pdfplumber.open(pdf_path) as pdf:
        for strand_info in all_strands_sub_strands:
            start_page = strand_info.get("page_number", 0)
            found_rubric = False

            for page_number in range(start_page, len(pdf.pages)):
                page = pdf.pages[page_number]
                tables = page.extract_tables()

                for table in tables:
                    first_row_text = ' '.join(filter(None, table[0]))
                    if any(header in first_row_text for header in rubric_headers):
                        strand_info["rubric_start_page"] = page_number + 1
                        found_rubric = True
                        break

                if found_rubric:
                    break

            if not found_rubric:
                strand_info["rubric_start_page"] = None

    return all_strands_sub_strands

def extract_rubric_data_complete(pdf_path, complete_data, rubric_headers):
    with pdfplumber.open(pdf_path) as pdf:
        for index, strand_info in enumerate(complete_data):
            rubric_start_page = strand_info.get("rubric_start_page")
            next_strand_start_page = complete_data[index + 1]["page_number"] if index + 1 < len(complete_data) else len(pdf.pages) + 1
            
            if rubric_start_page:
                rubrics = []
                rubric_continues = False

                for page_number in range(rubric_start_page, next_strand_start_page):
                    page = pdf.pages[page_number - 1]
                    tables = page.extract_tables()

                    for table in tables:
                        if rubric_continues or any(header in table[0] for header in rubric_headers):
                            rubric_continues = False
                            for row in table[1:] if any(header in table[0] for header in rubric_headers) else table:
                                if len(row) >= 5:
                                    rubric_entry = {
                                        "indicator_name": row[0].replace('\n', ' ').strip(),
                                        "rubrics": [
                                            {"level": "Exceeds Expectations", "statement": row[1].replace('\n', ' ').strip()},
                                            {"level": "Meets Expectations", "statement": row[2].replace('\n', ' ').strip()},
                                            {"level": "Approaches Expectations", "statement": row[3].replace('\n', ' ').strip()},
                                            {"level": "Below Expectations", "statement": row[4].replace('\n', ' ').strip()}
                                        ]
                                    }
                                    rubrics.append(rubric_entry)
                            if any(header in table[0] for header in rubric_headers):
                                rubric_continues = True

                strand_info["assessment_rubrics"] = rubrics

    return complete_data

def process_file(pdf_path):
    segment_size = 10
    all_strands_sub_strands = []

    for start_page in range(0, 100, segment_size):
        extracted_data = extract_strands_sub_strands_with_page_segmented(pdf_path, start_page, start_page + segment_size)
        all_strands_sub_strands.extend(extracted_data)

    rubric_headers = ["Indicators", "Exceeds Expectations", "Meets Expectations", "Approaches Expectations", "Below Expectations"]
    updated_strands_sub_strands = find_rubric_start_pages(pdf_path, all_strands_sub_strands, rubric_headers)
    complete_data = extract_rubric_data_complete(pdf_path, updated_strands_sub_strands, rubric_headers)
    
    return complete_data

def main(directory_path):
    for file_name in os.listdir(directory_path):
        if file_name.lower().endswith('.pdf'):
            pdf_path = os.path.join(directory_path, file_name)
            print(f"Processing {pdf_path}...")
            complete_data = process_file(pdf_path)
            
            # Define the path for the processed JSON file
            processed_pdf_path = f'{file_name.replace(".pdf", "")}_processed.json'
            with open(processed_pdf_path, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, ensure_ascii=False, indent=4)
            
            print(f"Processed data written to {processed_pdf_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process curriculum PDF files into JSON format.")
    parser.add_argument('directory', help="The directory containing the PDF files")
    args = parser.parse_args()
    main(args.directory)
