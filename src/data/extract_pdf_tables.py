import os
import pdfplumber
import csv
import camelot
from tqdm import tqdm
import argparse
import pandas as pd 

def extract_tables_with_pdfplumber(pdf_path):
    """
    Extracts tables from a given PDF file using pdfplumber.
    """
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract tables from the current page
            page_tables = page.extract_tables()
            for table in page_tables:
                # Append each table with its page number for later reference
                tables.append(table)
    return tables

def extract_tables_with_camelot(pdf_path):
    """
    Extracts tables from a given PDF file using Camelot and includes page numbers.
    """
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
    extracted_tables = []
    for table in tables:
        data = [row for row in table.df.itertuples(index=False, name=None)]
        # Use the `page` attribute of the table object to get the correct page number
        page_number = table.page
        extracted_tables.append((data, page_number))
    return extracted_tables


def save_tables_as_csv(tables, output_folder, pdf_name):
    """
    Saves extracted tables as CSV files.
    """
    for i, (table, page_number) in enumerate(tables):
        csv_file_name = f"{pdf_name}page{page_number}table{i+1}.csv"
        csv_file_path = os.path.join(output_folder, csv_file_name)
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in table:
                writer.writerow(row)

def save_combined_tables_as_csv(tables, output_folder, pdf_name):
    """
    Saves all extracted tables from a PDF into a single CSV file.
    """
    combined_csv_file_name = f"{pdf_name}_all_tables.csv"
    combined_csv_file_path = os.path.join(output_folder, combined_csv_file_name)

    with open(combined_csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        for i, (table, page_number) in enumerate(tables):
            # Optionally, add a header or separator to indicate a new table
            writer.writerow([f"Table {i+1} from Page {page_number}"])
            for row in table:
                writer.writerow(row)
            # Optionally, add an empty row as a separator between tables
            writer.writerow([])

def save_parsing_report(tables, report_folder, pdf_name):
    """
    Saves the parsing report for all tables in a PDF as a combined CSV file.
    """
    # Initialize a list to hold all report data
    reports = []
    for table in tables:
        # Each table's parsing report is a dictionary
        report = table.parsing_report
        # Add the report data to our list
        reports.append(report)
    
    # Convert the list of reports into a DataFrame
    report_df = pd.DataFrame(reports)
    
    # Define the CSV file path using the PDF name
    report_csv_path = os.path.join(report_folder, f"{pdf_name}_parsing_report.csv")
    
    # Save the DataFrame to CSV
    report_df.to_csv(report_csv_path, index=False)

def process_pdfs_in_folder(input_folder, output_folder, report_folder, use_camelot=False):
    """
    Processes all PDF files in the specified folder.
    """
    for pdf_file in tqdm(os.listdir(input_folder)):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, pdf_file)
            pdf_name = pdf_file[:-4]  # Remove .pdf extension

            # Define pdf_csv_folder here to ensure it's always set before use
            pdf_csv_folder = os.path.join(output_folder, f"{pdf_name}_csvs")
            os.makedirs(pdf_csv_folder, exist_ok=True)

            if use_camelot:
                tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
                extracted_tables = [(table.df.values.tolist(), table.page) for table in tables]
                save_combined_tables_as_csv(extracted_tables, pdf_csv_folder, pdf_name)
                save_parsing_report(tables, report_folder, pdf_name)
            else:
                tables = extract_tables_with_pdfplumber(pdf_path)
                print('running pdfplumber')
                # Adjust the data structure if necessary to match the expected format for save_combined_tables_as_csv
                # For example, you might need to convert pdfplumber table data to a similar tuple format as Camelot's
                adjusted_tables = [(table, "UnknownPage") for table in tables]  # This is a placeholder adjustment
                save_combined_tables_as_csv(adjusted_tables, pdf_csv_folder, pdf_name)
                # Note: No parsing report for pdfplumber, as mentioned earlier

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract tables from PDF.")
    parser.add_argument("input_folder", help="Path to the folder containing PDF files.")
    parser.add_argument("output_folder", help="Path to save the CSV files.")
    parser.add_argument("report_folder", help="Path to save the parsing reports.")
    parser.add_argument("--camelot", action='store_true', help="Use Camelot for extraction.")
    args = parser.parse_args()

    process_pdfs_in_folder(args.input_folder, args.output_folder, args.report_folder, args.camelot)