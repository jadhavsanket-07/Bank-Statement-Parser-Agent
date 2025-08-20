# 🤖 Agent-as-Coder: Bank Statement PDF Parser Generator

**An autonomous AI agent that generates custom PDF parsers for bank statements using LLM-powered code generation and self-correction loops.**

## 🎯 Overview

This project implements an intelligent coding agent that automatically generates custom parsers for bank statement PDFs. The agent uses a **plan → generate → test → self-fix** loop to create robust parsers without manual intervention, making it adaptable to different bank statement formats.

### Key Features

🔄 **Autonomous Self-Debugging** - Iterative improvement with LLM-powered error analysis  
🏦 **Multi-Bank Support** - Generate parsers for any bank statement format  
📊 **Schema Validation** - Ensures output matches expected CSV structure  
🧪 **Automated Testing** - Built-in pytest validation for generated parsers  
⚡ **Fast Execution** - Complete parser generation in under 60 seconds  

## 🏗️ Architecture

The agent follows a **modular node-based design** with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF Analyzer  │───▶│ Parser Generator│───▶│   Test Runner   │
│   (Structure)   │    │   (LLM Agent)   │    │   (Validation)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       │
┌─────────────────┐    ┌─────────────────┐              │
│ Feedback Loop   │◀───│ Self-Correction │◀─────────────┘
│  (≤3 attempts)  │    │    (Debug AI)   │
└─────────────────┘    └─────────────────┘
```

The agent orchestrates these components in a feedback loop: it analyzes the PDF structure, generates Python parsing code using LLMs, runs automated tests, and self-corrects based on test failures until a working parser is produced.

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/your-username/ai-agent-challenge.git
cd ai-agent-challenge
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

**Free API Keys Available:**
- 🔑 [Google Gemini API](https://makersuite.google.com/app/apikey) - Free tier available
- 🔑 [Groq API](https://groq.com) - Fast inference with free credits

### 3. Prepare Your Data
Organize your bank statement data:
```
data/
└── icici/
    ├── icici_sample.pdf    # Sample bank statement
    └── icici_sample.csv    # Expected output format
```

### 4. Run the Agent
```bash
python agent.py --target icici --pdf data/icici/icici_sample.pdf --csv data/icici/icici_sample.csv
```

### 5. Verify Results
The agent will generate `custom_parsers/icici_parser.py` and run automated tests. Check for the success message:
```
✅ Parser Passed All Tests!
```

## 📁 Project Structure

```
ai-agent-challenge/
├── agent.py                 # Main agent orchestrator
├── custom_parsers/          # Generated parsers output directory
│   └── icici_parser.py      # Auto-generated ICICI parser
├── data/                    # Sample data directory
│   └── icici/
│       ├── icici_sample.pdf
│       └── icici_sample.csv
├── requirements.txt         # Python dependencies
├── .env                     # API keys (create this)
└── README.md                # This file
```

## 🔧 Advanced Usage

### Custom Bank Support
Generate parsers for any bank by providing sample data:

```bash
# Example: SBI Bank
python agent.py --target sbi --pdf data/sbi/sbi_sample.pdf --csv data/sbi/sbi_sample.csv

# Example: HDFC Bank  
python agent.py --target hdfc --pdf data/hdfc/hdfc_sample.pdf --csv data/hdfc/hdfc_sample.csv
```

### Provider Selection
Choose your preferred LLM provider:

```bash
# Use Google Gemini (default)
python agent.py --target icici --pdf data/icici/icici_sample.pdf --csv data/icici/icici_sample.csv --provider gemini

# Use Groq (faster inference)
python agent.py --target icici --pdf data/icici/icici_sample.pdf --csv data/icici/icici_sample.csv --provider groq
```

### Iteration Control
Adjust maximum retry attempts:

```bash
python agent.py --target icici --pdf data/icici/icici_sample.pdf --csv data/icici/icici_sample.csv --max-attempts 5
```

## 🧪 Testing Your Parser

### Manual Testing
```python
from custom_parsers.icici_parser import parse
import pandas as pd

# Test your generated parser
df = parse("data/icici/icici_sample.pdf")
print(f"Extracted {len(df)} transactions")
print(df.head())
```

### Automated Testing
```bash
# Run pytest on generated parser
pytest custom_parsers/ -v
```

## 📋 Parser Contract

All generated parsers follow a standardized interface:

```python
def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parse bank statement PDF and return structured data.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        DataFrame with columns matching the expected CSV schema
    """
```

**Expected DataFrame Schema:**
- Columns must exactly match the provided CSV sample
- Numeric columns (amounts, balances) as float64
- Date columns as datetime64 or object
- Text columns (descriptions) as object

## 🛠️ Dependencies

```
pdfplumber             # PDF table extraction
pandas                 # Data manipulation  
python-dotenv          # Environment variables
google-generativeai    # Google Gemini API
groq                   # Groq API client
pytest                 # Testing framework
```

## 🎭 How It Works

### 1. **PDF Analysis**
The agent analyzes the input PDF structure:
- Extracts sample text and tables
- Identifies page layout and format
- Determines parsing strategy

### 2. **Code Generation**
Using the sample CSV schema and PDF analysis:
- Generates Python parsing code with pdfplumber
- Includes proper error handling and data cleaning
- Adds type hints and documentation

### 3. **Automated Testing**
Runs pytest to validate the generated parser:
- Tests parser imports and function existence
- Compares output DataFrame with expected CSV
- Validates column names, types, and data structure

### 4. **Self-Correction**
On test failures, the agent:
- Analyzes error messages with LLM feedback
- Identifies specific issues in the generated code
- Generates improved parser code
- Repeats until success or max attempts reached

## 🏆 Features & Benefits

### ✅ **Autonomous Operation**
- Zero manual code writing required
- Self-debugging and error correction
- Handles edge cases automatically

### ✅ **Bank Format Flexibility**  
- Adapts to different PDF layouts
- Supports various table structures
- Handles multi-page statements

### ✅ **Production Ready**
- Comprehensive error handling
- Type hints and documentation
- Automated test validation

### ✅ **Developer Friendly**
- Clear CLI interface
- Detailed logging and feedback
- Modular, extensible architecture

## 🙏 Acknowledgments

- Built for the **Agent-as-Coder Challenge**
- Inspired by [mini-swe-agent](https://github.com/pufanyi/mini-swe-agent) architecture
- Powered by Google Gemini and Groq APIs
- PDF parsing with pdfplumber library

---

**🎯 Challenge Completed:** This agent successfully demonstrates autonomous code generation, self-debugging loops, and production-ready parser creation for bank statement PDFs.

---
