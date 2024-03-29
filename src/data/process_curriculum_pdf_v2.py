#!/usr/bin/env python3
import argparse
import os
import pdfplumber
import json
import pandas as pd
import re

def extract_grade(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        # Assuming the grade is formatted as "Grade 6" or "6th Grade"
        match = re.search(r"Grade (\d+)", text)
        if match:
            return match.group(1)
        # Fallback for different format
        match = re.search(r"(\d+)(?:th|nd|rd|st) Grade", text)
        if match:
            return match.group(1)
    return "Unknown"  # Default if not found



def contains_keywords(strands_data, keywords=["Strand", "Sub Strand"]):
    # Convert keywords to lowercase for case-insensitive comparison
    lower_keywords = [keyword.lower() for keyword in keywords]

    for strand in strands_data:
        for row in strand['table']:
            for cell in row:
                if cell and any(lower_keyword in cell.lower() for lower_keyword in lower_keywords):
                    keywords_str = "' or '".join(keywords)
                    print(f"The strands data contains '{keywords_str}'.")
                    return True
    keywords_str = "' or '".join(keywords)
    print(f"The strands data does not contain '{keywords_str}'.")
    return False


def find_keyword_columns(strands_data, keywords):
    column_indexes = {keyword: -1 for keyword in keywords}
    for strand in strands_data:
        for row in strand['table']:
            for index, cell in enumerate(row):
                if cell:
                    processed_cell = cell.replace('\n', ' ').lower()
                    for keyword in keywords:
                        processed_keyword = keyword.replace('\n', ' ').lower()
                        if processed_keyword in processed_cell and column_indexes[keyword] == -1:
                            column_indexes[keyword] = index
    return column_indexes

def merge_strand_and_indicator(tables, column_positions):
    
    # Split where "table".first contains "Indicators"
    tables = [table for table in tables if table['number_of_columns'] >= 4]
    split_index = next((i for i, table in enumerate(tables) if "Indicators" in ' '.join(str(cell) for cell in table['table'][0] if cell is not None)), len(tables))
    tables_before_indicator = tables[:split_index]
    tables_after_indicator = tables[split_index:]
    
    # Define strands mapping as a dictionary
    strands_mapping = {
        'strand': ['Strand', 'strand', 'Strands'],
        'sub_strand': ['Sub Strand', 'Sub strand'],
        'specific_learning_outcomes': ['Specific Learning Outcomes','Specific Learning\nOutcomes', 'Specific Learning\nOutcomes', 'Specific Learning Outcomes'],
        'suggested_learning_experiences': ['Suggested Learning Experiences'],
        'key_inquiry_questions': ['Key Inquiry\nQuestion(s)']
    }

    # Initialize DataFrame for strands with the final column names
    df_substrand = pd.DataFrame(columns=strands_mapping.keys())

    # Create a dictionary for column mapping
    column_mapping = {}
    for col in tables_before_indicator[0]['table'][0]:
        col_lower = col.lower()  # Convert column name to lowercase
        for final_name, original_names in strands_mapping.items():
            # Check if the lowercase column name matches any of the lowercase original names
            if any(col_lower == original_name.lower() for original_name in original_names):
                column_mapping[col] = final_name
                break

    # Only process the table if at least one column was successfully mapped
    if column_mapping:
        # Create temporary DataFrame and rename columns

        temp_df = pd.DataFrame(tables_before_indicator['table'][0:], columns=tables_before_indicator[0]['table'][0])  # Assuming the first row is the header
        temp_df.rename(columns=column_mapping, inplace=True)

        # Retain only the columns that are in df_substrand
        temp_df = temp_df[df_substrand.columns.intersection(temp_df.columns)]

        # Append processed DataFrame to df_substrand
        df_substrand = df_substrand.append(temp_df, ignore_index=True)



    # Define rubrics mapping as a dictionary
    rubrics_mapping = {
        'indicator': ['Indicators', 'Indicator','indicators', 'indicator'],
        'exceeds_expectations': ['Exceeds Expectations','Exceeds expectations','Exceeds'],
        'meets_expectations': ['Meets Expectations', 'Meets\nExpectations', 'Meets\nexpectations', 'Meets expectations'],
        'approaches_expectations': ['Approaches Expectations', 'Approaches\nExpectations', 'Approaches\nexpectations', 'Approaches expectations'],
        'below_expectations': ['Below Expectations', 'Below\nExpectations', 'Below\nexpectations', 'Below expectations']
    }

    # Initialize DataFrame for rubrics
    df_rubrics = pd.DataFrame(columns=rubrics_mapping.keys())

    column_mapping = {}
    for col in tables_after_indicator[0]['table'][0]:
        col_lower = col.lower()  # Convert column name to lowercase
        for final_name, original_names in rubrics_mapping.items():
            # Check if the lowercase column name matches any of the lowercase original names
            if any(col_lower == original_name.lower() for original_name in original_names):
                column_mapping[col] = final_name
                break

        # Only process the table if at least one column was successfully mapped
        if column_mapping:
            # Create temporary DataFrame and rename columns
            temp_df = pd.DataFrame(table['table'][0:], columns=table['table'][0])  # Assuming the first row is the header
            temp_df.rename(columns=column_mapping, inplace=True)

            # Retain only the columns that are in df_rubrics
            temp_df = temp_df[df_rubrics.columns.intersection(temp_df.columns)]

            # Append processed DataFrame to df_rubrics
            df_rubrics = df_rubrics.append(temp_df, ignore_index=True)

    
    print(df_substrand)
    print(df_rubrics)
    ## Remove 1st row in df_substrand and df_rubrics
    df_substrand = df_substrand.iloc[1:]
    df_rubrics = df_rubrics.iloc[1:]


    strand_data = {
        "strand": df_substrand.iloc[0]["strand"],
        "sub_strand": df_substrand.iloc[0]["sub_strand"],
        "specific_learning_outcomes": [],
        "suggested_learning_experiences": [],
        "key_inquiry_questions": [],
        "assessment_rubrics": []
    }

    for index, row in df_substrand.iterrows():
        specific_learning_outcome = row['specific_learning_outcomes']
        suggested_learning_experience = row['suggested_learning_experiences']
        key_inquiry_question = row['key_inquiry_questions']
        
        if specific_learning_outcome and specific_learning_outcome.strip():
            strand_data["specific_learning_outcomes"].append(specific_learning_outcome.strip())

        if suggested_learning_experience and suggested_learning_experience.strip():
            strand_data["suggested_learning_experiences"].append(suggested_learning_experience.strip())

        if key_inquiry_question and key_inquiry_question.strip():
            strand_data["key_inquiry_questions"].append(key_inquiry_question.strip())



    # Extracting rubrics
    for index, row in df_rubrics.iterrows():
        indicator = row['indicator'].replace('\n', ' ').strip() #if 'indicator' in row else ''
        exceeds = row['exceeds_expectations'].replace('\n', ' ').strip()# if 'exceeds_expectations' in row else ''
        meets = row['meets_expectations'].replace('\n', ' ').strip()# if 'meets_expectations' in row else ''
        approaches = row['approaches_expectations'].replace('\n', ' ').strip() #if 'approaches_expectations' in row else ''
        below = row['below_expectations'].replace('\n', ' ').strip()#if 'below_expectations' in row else ''
        # Further processing for each rubric...


        strand_data["assessment_rubrics"].append({
            "indicator_name": indicator,
            "rubrics": [
                {"level": "Exceeds Expectations", "statement": exceeds},
                {"level": "Meets Expectations", "statement": meets},
                {"level": "Approaches Expectations", "statement": approaches},
                {"level": "Below Expectations", "statement": below}
            ]
        })
    print(strand_data)

    return strand_data


def extract_tables_grouped_by_strand(pdf_path):
    grade = extract_grade(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        all_tables = []
        for i in range(0, len(pdf.pages)):
            page = pdf.pages[i]
            tables = page.extract_tables()
            for table in tables:
                all_tables.append({
                    "page_number": i + 1,
                    "grade": grade,
                    "number_of_columns": len(table[0]),
                    "table": table
                })

        all_strands = []
        current_strand = []
        strand_counter = 1

        for table_info in all_tables:
            page_number = table_info["page_number"]
            table = table_info["table"]
            
            if "Strand" in ' '.join(filter(None, table[0])):  # Check if "Strand" is in the first row of the table
                if current_strand:  # If current strand is not empty
                    all_strands.append({"strand_" + str(strand_counter): current_strand})
                    strand_counter += 1
                    current_strand = []

            current_strand.append({
                "page_number": page_number,
                "number_of_columns": len(table[0]),
                "table": table
            })

        # Append the last strand if not empty
        if current_strand:
            all_strands.append({"strand_" + str(strand_counter): current_strand})

        return all_strands


def save_grouped_tables_as_json(pdf_path):
    # Extract tables grouped by strand from the PDF
    grouped_tables = extract_tables_grouped_by_strand(pdf_path)

    # Create the file name for the JSON file
    file_name = f'{os.path.splitext(os.path.basename(pdf_path))[0]}_grouped_tables.json'

    # Create the path for the GROUPED_TABLES_JSON directory in the same directory as the PDF file
    base_folder = os.path.dirname(pdf_path)
    grouped_tables_dir = os.path.join(base_folder, 'GROUPED_TABLES_JSON')
    grouped_tables_path = os.path.join(grouped_tables_dir, file_name)

    # Ensure the GROUPED_TABLES_JSON directory exists
    os.makedirs(grouped_tables_dir, exist_ok=True)

    # Write grouped_tables to JSON file
    with open(grouped_tables_path, 'w', encoding='utf-8') as f:
        json.dump(grouped_tables, f, ensure_ascii=False, indent=4)

    return grouped_tables_path

def process_grouped_tables(json_path):
    # Load the grouped tables from JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        grouped_tables = json.load(f)

    # Process each strand
    strands = []
    for strand in grouped_tables:
        strand_key = list(strand.keys())[0]
        keywords = [
            "Strand", "Sub strand", "Specific Learning Outcomes",
            "Suggested Learning Experiences", "Key Inquiry Question(s)", "Indicators",
            "Exceeds Expectations", "Meets Expectations", "Approaches Expectations",
            "Below Expectations"
        ]
        # Check if the strand contains any of the keywords
        if contains_keywords(strand[strand_key], keywords):
            column_positions = find_keyword_columns(strand[strand_key], keywords)
            strand_data = merge_strand_and_indicator(strand[strand_key], column_positions)
            strands.append({strand_key: strand_data})
    
    return strands

def main(directory_path):
    for file_name in os.listdir(directory_path):
        if file_name.lower().endswith('.pdf'):
            pdf_path = os.path.join(directory_path, file_name)
            print(f"Processing {pdf_path}...")

            # Stage 1: Save the grouped tables as JSON
            grouped_json_path = save_grouped_tables_as_json(pdf_path)
            print(f"Downloaded {grouped_json_path}...")

            # # Stage 2: Process the grouped tables and save the result
            # complete_data = process_grouped_tables(grouped_json_path)
            # processed_pdf_path = os.path.join(directory_path, f'{os.path.splitext(file_name)[0]}_processed.json')
            # with open(processed_pdf_path, 'w', encoding='utf-8') as f:
            #     json.dump(complete_data, f, ensure_ascii=False, indent=4)
            
            # print(f"Processed data written to {processed_pdf_path}")

if __name__ == '__main__':
    directory_path = "/home/dataiku/kn_workspace/currilculum_taxonomy_extractor/data/ALL"
    main(directory_path)
