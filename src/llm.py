from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
import pandas as pd
import torch
import os
import re

# Set Hugging Face token
os.environ["HUGGINGFACE_TOKEN"] = "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"

# Load tokenizer and model
model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
tokenizer = AutoTokenizer.from_pretrained(model_id, token=os.environ["HUGGINGFACE_TOKEN"])
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.float16,
    token=os.environ["HUGGINGFACE_TOKEN"]
)

# Load and preprocess data
df = pd.read_csv("data/financial_summaries/financial_summary_all.csv")
df.dropna(inplace=True)

# Reshape the DataFrame to long format: one row per (company, period, metric)
melted_df = df.melt(
    id_vars=["company", "period"],
    value_vars=["Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Income", "Net Income"],
    var_name="metric",
    value_name="value"
)

# Drop rows with missing values
melted_df.dropna(inplace=True)

# Convert to natural language documents
documents = [
    f"In {row['period']}, {row['company']} had a {row['metric']} of {row['value']}."
    for _, row in melted_df.iterrows()
]

# Convert to LangChain Document objects
docs = [Document(page_content=doc) for doc in documents]

# Embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Vector store
vector_store = FAISS.from_documents(docs, embedding_model)

# HuggingFace text generation pipeline
text_gen_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    do_sample=False,
    temperature=0.2
)

# Wrap LLM for LangChain
llm = HuggingFacePipeline(pipeline=text_gen_pipeline)

# Retriever
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# QA chain setup
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Example query
query = "How much revenue did DIPD make in FY2021?"
result = qa_chain.invoke(query)

# Output
print("Answer:", result['result'])
