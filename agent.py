# Load Lib
import pandas as pd
import pdfplumber
import argparse
import subprocess
import sys
import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Load environment variables from .env file
dotenv_path = Path(r"D:\07-SANKET\Assignment\.env")
load_dotenv(dotenv_path=dotenv_path)

# LLM

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


@dataclass
class AgentState:
    target_bank: str
    sample_pdf_path: str
    sample_csv_path: str
    generated_code: str = ""
    test_results: str = ""
    error_feedback: str = ""
    iteration_count: int = 0
    max_iterations: int = 3
    parser_ready: bool = False


class LLMClient:
    def __init__(self, provider: str = "gemini"):
        self.provider = provider
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        if self.provider == "gemini" and HAS_GEMINI:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel("gemini-1.5-flash")
        elif self.provider == "groq" and HAS_GROQ:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            self.client = Groq(api_key=api_key)
        else:
            raise ValueError(
                f"Provider {self.provider} not supported or library not installed"
            )

    def generate(self, prompt: str) -> str:
        try:
            if self.provider == "gemini":
                response = self.client.generate_content(prompt)
                return response.text
            elif self.provider == "groq":
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                    temperature=0.1,
                    max_tokens=4000
                )
                return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"LLM generation error: {e}")
            return ""

# PDF Analyzer


class PDFAnalyzer:
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                analysis = {
                    "num_pages": len(pdf.pages),
                    "page_samples": [],
                    "tables_found": [],
                }
                for i, page in enumerate(pdf.pages[:2]):
                    page_data = {
                        "page_num": i + 1,
                        "text": page.extract_text()[:1000] if page.extract_text() else "",
                        "tables": page.extract_tables(),
                        "width": page.width,
                        "height": page.height
                    }
                    analysis["page_samples"].append(page_data)
                    if page_data["tables"]:
                        analysis["tables_found"].extend(
                            page_data["tables"][:2])
                return analysis
        except Exception as e:
            return {"error": f"PDF analysis failed: {e}"}

# Parser Generator


class ParserGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate_parser(self, state: AgentState) -> str:
        try:
            expected_df = pd.read_csv(state.sample_csv_path)
            expected_columns = list(expected_df.columns)
            sample_data = expected_df.head(3).to_string()
        except Exception:
            expected_columns = ["Date", "Description",
                                "Debit", "Credit", "Balance"]
            sample_data = "Unable to load CSV sample"

        pdf_analyzer = PDFAnalyzer()
        pdf_analysis = pdf_analyzer.analyze_pdf(state.sample_pdf_path)

        iteration_context = ""
        if state.iteration_count > 0 and state.error_feedback:
            iteration_context = f"""
PREVIOUS ATTEMPT FAILED. Error feedback:
{state.error_feedback}
Please fix the issues mentioned above and try a different approach.
"""

        pdf_context = ""
        if "page_samples" in pdf_analysis:
            sample_text = pdf_analysis["page_samples"][0]["text"] if pdf_analysis["page_samples"] else ""
            pdf_context = f"""
PDF Analysis:
- Pages: {pdf_analysis.get('num_pages', 'unknown')}
- Sample text from first page:
{sample_text[:800]}
Tables found: {len(pdf_analysis.get('tables_found', []))}
"""

        prompt = f"""You are a Python coding expert. Generate a complete, working PDF parser for {state.target_bank.upper()} bank statements.
{iteration_context}
REQUIREMENTS:
1. Function signature: parse(pdf_path: str) -> pd.DataFrame
2. Return DataFrame with exactly these columns: {expected_columns}
3. Handle errors gracefully with try/except
4. Use pdfplumber as primary library (import pdfplumber)
5. Include type hints and docstrings
6. Extract transaction data from the PDF including Debit and Credit columns
{pdf_context}
Expected CSV structure:
{sample_data}
CRITICAL: The returned DataFrame MUST match the expected CSV schema exactly.
Use pd.DataFrame.equals() for comparison in tests.
Generate ONLY the Python code for the parser file. Include all necessary imports.
Start with imports, then define the parse function.
Generate the complete working code now:"""

        generated_code = self.llm.generate(prompt)
        code = self._extract_python_code(generated_code)
        return code

    def _extract_python_code(self, response: str) -> str:
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        return '\n'.join(code_lines) if code_lines else response.strip()

# Test Runner


class TestRunner:
    def run_parser_test(self, state: AgentState) -> tuple[bool, str]:
        parser_dir = Path("custom_parsers")
        parser_dir.mkdir(exist_ok=True)
        parser_file = parser_dir / f"{state.target_bank.lower()}_parser.py"

        try:
            with open(parser_file, 'w') as f:
                f.write(state.generated_code)
        except Exception as e:
            return False, f"Failed to write parser file: {e}"

        test_content = self._create_test_content(state)
        test_file = Path("test_parser.py")

        try:
            with open(test_file, 'w') as f:
                f.write(test_content)
        except Exception as e:
            return False, f"Failed to write test file: {e}"

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest",
                    str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path.cwd()
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            test_file.unlink(missing_ok=True)
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out"
        except Exception as e:
            return False, f"Test execution failed: {e}"

    def _create_test_content(self, state: AgentState) -> str:
        return f"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "custom_parsers"))

def test_parser_exists():
    try:
        import {state.target_bank.lower()}_parser
        assert hasattr({state.target_bank.lower()}_parser, 'parse')
    except ImportError as e:
        pytest.fail(f"Failed to import parser: {{e}}")

def test_parser_output():
    pdf_path = r"{state.sample_pdf_path}"
    csv_path = r"{state.sample_csv_path}"

    if not os.path.exists(pdf_path):
        pytest.skip(f"PDF file not found: {{pdf_path}}")
    if not os.path.exists(csv_path):
        pytest.skip(f"CSV file not found: {{csv_path}}")

    import {state.target_bank.lower()}_parser
    result = {state.target_bank.lower()}_parser.parse(pdf_path)
    expected = pd.read_csv(csv_path)

    # Convert Debit/Credit to Amount if needed
    if 'Debit' in expected.columns and 'Credit' in expected.columns:
        expected['Amount'] = expected['Credit'].fillna(0) - expected['Debit'].fillna(0)
        expected = expected[['Date','Description','Debit','Credit','Balance']]

    if 'Debit' in result.columns and 'Credit' in result.columns:
        result['Amount'] = result['Credit'].fillna(0) - result['Debit'].fillna(0)
        result = result[['Date','Description','Debit','Credit','Balance']]

    pd.testing.assert_frame_equal(result, expected, check_dtype=False)
"""

# Feedback Analyzer


class FeedbackAnalyzer:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def analyze_failure(self, state: AgentState, test_output: str) -> str:
        prompt = f"""You are a debugging expert. Analyze this test failure and provide specific, actionable feedback.
BANK: {state.target_bank}
ITERATION: {state.iteration_count}
GENERATED PARSER CODE:
{state.generated_code}

TEST OUTPUT:
{test_output}

Please provide actionable steps to fix the parser code so it passes the tests.
"""
        return self.llm.generate(prompt)

# Main


def main():
    parser = argparse.ArgumentParser(
        description="Bank Statement Parser Generator")
    parser.add_argument("--target", required=True,
                        help="Target bank name (e.g. icici)")
    parser.add_argument("--pdf", required=True,
                        help="Path to sample PDF statement")
    parser.add_argument("--csv", required=True,
                        help="Path to sample CSV with expected output")
    parser.add_argument("--provider", default="gemini",
                        choices=["gemini", "groq"], help="LLM provider to use")
    args = parser.parse_args()

    state = AgentState(target_bank=args.target,
                       sample_pdf_path=args.pdf, sample_csv_path=args.csv)
    llm_client = LLMClient(provider=args.provider)
    parser_generator = ParserGenerator(llm_client)
    test_runner = TestRunner()
    feedback_analyzer = FeedbackAnalyzer(llm_client)

    while state.iteration_count < state.max_iterations and not state.parser_ready:
        print(f"\n=== Iteration {state.iteration_count+1} ===")
        state.generated_code = parser_generator.generate_parser(state)
        success, output = test_runner.run_parser_test(state)
        state.test_results = output

        if success:
            print("\n Parser Passed All Tests")
            state.parser_ready = True
            break
        else:
            print("\n Test failed Analyzing Feedback")
            state.error_feedback = feedback_analyzer.analyze_failure(
                state, output)
            print(state.error_feedback)
            state.iteration_count += 1

    if not state.parser_ready:
        print("\n Could Not Generate A Working Parser After Max Iterations")


if __name__ == "__main__":
    main()
