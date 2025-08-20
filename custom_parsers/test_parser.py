import pandas as pd
from icici_parser import parse

# Path to PDF file
pdf_file = r"D:\07-SANKET\Assignment\icici\icici_sample.pdf"

# Run parser
df = parse(pdf_file)

# Show first 5 transactions
print("\n First 5 Transactions:\n")
print(df.head())

# Check if extraction succeeded
if df.empty:
    print("\n No transactions extracted! Please check the PDF or parser.")
else:
    print(f"\n Successfully extracted {len(df)} transactions")

    print("\n DataFrame Info:")
    print(df.info())
