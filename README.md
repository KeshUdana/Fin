# Quarterly Financial Report Scraper and Analyzer

## Overview

This project automates the collection, extraction, and summarization of quarterly financial reports published by companies listed on the Colombo Stock Exchange (CSE). It streamlines the process of extracting financial data from PDF reports, enabling efficient analysis and integration into financial models.

The system uses web scraping and PDF parsing techniques combined with natural language processing (NLP) and a large language model (LLM) to deliver interactive financial insights.

## Features

- Automated scraping and downloading of quarterly financial PDF reports using Selenium.
- Extraction and filtering of relevant financial data from PDFs with pdfplumber.
- Data structuring and summarization into CSV files for analysis.
- Interactive financial summary visualization via a Streamlit dashboard.
- LLM-driven natural language query interface for financial data using Hugging Face and LangChain.
- Handles inconsistent PDF formatting, null values, and complex table structures using custom logic.

## Technologies Used

- Python 3
- Selenium (browser automation and scraping)
- pdfplumber (PDF text extraction)
- spaCy (NLP processing)
- pandas (data manipulation and CSV output)
- requests (PDF downloading)
- re (regular expressions for pattern matching)
- Streamlit (dashboard UI)
- Hugging Face Transformers & LangChain (LLM query system)
- FAISS (vector search for semantic retrieval)

## System Architecture

### 1. Scraping and Downloading
- Headless Chrome browser controlled via Selenium to navigate CSE company pages.
- Targeted extraction of quarterly financial PDF URLs based on URL patterns.
- PDFs are saved into structured directories named by company.

### 2. Text Extraction and Filtering
- pdfplumber extracts text from PDFs.
- Pages are filtered by keywords to isolate income statement data.
- Regex patterns detect reporting periods (e.g., fiscal quarters).
- Lines are cleaned and filtered to identify financial data rows.
- Data saved into intermediate CSV files.

### 3. Financial Data Structuring and Summary
- Financial rows are classified into categories (Revenue, COGS, Gross Profit, etc.) via keyword mapping and NLP.
- Structured summaries are generated for use in reports or forecasting.

### 4. LLM-Based Query System
- Uses TinyLlama-1.1B-Chat-v1.0 model for generating financial insights.
- Data is converted into natural language statements, embedded using sentence-transformers, and indexed with FAISS.
- LangChain RetrievalQA chain combines vector retrieval with LLM generation.
- Users can ask natural language questions about financial performance and receive context-aware answers.

## Usage Instructions

### Setup
1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
Run the scraping and extraction scripts in order to generate cleaned CSV files.

Launch the LLM query system:

bash
Copy
Edit
python ll.py
Start the Streamlit dashboard:

bash
Copy
Edit
streamlit run dashboard/app.py
Notes
The system currently processes data for the following companies:

DIPD (Dipped Products PLC)

REXP (Richard Pieris Exports PLC)

Make sure to have ChromeDriver installed and compatible with your Chrome version for Selenium to work.

Hugging Face authentication token is required to load the TinyLlama model.

The project handles null/missing values using custom imputation and logic to maximize data usability.

The modular pipeline uses intermediate CSV outputs to allow stepwise processing and debugging.