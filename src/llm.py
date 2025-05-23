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

# Load and clean data
df = pd.read_csv("data/financial_summaries/combined_financial_summary.csv")
df.dropna(inplace=True)

# Normalize period column to extract FY and FQ
def extract_fy_fq(period):
    fy_match = re.search(r"FY\s*(\d{2,4})", period, re.IGNORECASE)
    fq_match = re.search(r"Q([1-4])", period, re.IGNORECASE)
    fy = None
    fq = None
    if fy_match:
        fy = fy_match.group(1)
        fy = "20" + fy[-2:] if len(fy) == 2 else fy
    if fq_match:
        fq = f"Q{fq_match.group(1)}"
    return pd.Series([fy, fq])

df[['fy', 'fq']] = df['period'].apply(extract_fy_fq)

# Melt the dataframe into long format
melted_df = df.melt(
    id_vars=["company", "period", "fy", "fq"],
    value_vars=["Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Income", "Net Income"],
    var_name="metric",
    value_name="value"
)
melted_df.dropna(inplace=True)

# Create documents for vector store
documents = [
    f"In fiscal year {row['fy']} {row['fq'] or ''}, {row['company']} had a {row['metric']} of {row['value']}."
    for _, row in melted_df.iterrows()
]
docs = [Document(page_content=doc) for doc in documents]

# Build vector store using BAAI embeddings
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
vector_store = FAISS.from_documents(docs, embedding_model)

# Build text generation pipeline
text_gen_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    do_sample=False,
    temperature=0.2
)

llm = HuggingFacePipeline(pipeline=text_gen_pipeline)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# Create QA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Example query
query = "How much revenue did DIPD make in FY2021?"
result = qa_chain.invoke(query)

print("Answer:", result['result'])
