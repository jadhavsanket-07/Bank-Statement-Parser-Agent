import pandas as pd
import pdfplumber
import re


def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses an ICICI bank statement PDF and returns a pandas DataFrame.

    Args:
        pdf_path: The path to the ICICI bank statement PDF file.

    Returns:
        A DataFrame with columns ['S No.', 'Value Date', 'Transaction Date', 'Cheque Number',
        'Transaction Remarks', 'Withdrawal Amount (INR)', 'Deposit Amount (INR)', 'Balance (INR)']
    """
    try:
        transactions = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue
                for table in tables:
                    for row in table:

                        row = [str(x).strip() if x else "" for x in row]

                        header_keys = [
                            'S No.', 'Value Date', 'Transaction Date']
                        if any(hk in row[0] for hk in header_keys) or len(row) < 8:
                            continue

                        if not re.match(r"\d{2}/\d{2}/\d{4}", row[1]):
                            continue

                        transactions.append(row)

        if not transactions:
            print(" No transactions extracted!")
            columns = ['S No.', 'Value Date', 'Transaction Date', 'Cheque Number',
                       'Transaction Remarks', 'Withdrawal Amount (INR)', 'Deposit Amount (INR)', 'Balance (INR)']
            return pd.DataFrame(columns=columns)

        columns = ['S No.', 'Value Date', 'Transaction Date', 'Cheque Number',
                   'Transaction Remarks', 'Withdrawal Amount (INR)', 'Deposit Amount (INR)', 'Balance (INR)']
        df = pd.DataFrame(transactions, columns=columns)

        # Numeric convert to float
        num_cols = ['Withdrawal Amount (INR)',
                    'Deposit Amount (INR)', 'Balance (INR)']
        for col in num_cols:
            df[col] = (df[col]
                       # Remove commas & symbols
                       .replace(r"[^\d.-]", "", regex=True)
                       .replace("", "0")
                       )
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df

    except FileNotFoundError:
        print(f" Error: PDF file not found at {pdf_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f" An error occurred while parsing the PDF: {e}")
        return pd.DataFrame()
