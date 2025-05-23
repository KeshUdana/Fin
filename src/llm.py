from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
import pandas as pd
import torch
import os
from dotenv import load_dotenv

load_dotenv()

# Hugging Face token
hf_token = os.getenv("HUGGINGFACE_TOKEN") or "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"
os.environ["HUGGINGFACE_TOKEN"] = hf_token

model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=hf_token)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    use_auth_token=hf_token,
    device_map="auto",
    torch_dtype=torch.float16
)

# Load and preprocess data
df = pd.read_csv("data/financial_summaries/combined_financial_summary.csv")
df.dropna(inplace=True)

# Melt wide format to long format so 'metric' and 'value' columns exist
melted_df = df.melt(
    id_vars=["company", "period"],
    value_vars=["Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Income", "Net Income"],
    var_name="metric",
    value_name="value"
)
melted_df.dropna(inplace=True)

# Create text documents for each row
documents = [
    f"In {row['period']}, {row['company']} had a {row['metric']} of {row['value']}."
    for _, row in melted_df.iterrows()
]
docs = [Document(page_content=doc) for doc in documents]

# Load embeddings
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
)

vector_store = FAISS.from_documents(docs, embedding_model)

# Setup text generation pipeline
text_gen_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    do_sample=False,
    temperature=0.2,
    device=0 if torch.cuda.is_available() else -1
)

llm = HuggingFacePipeline(pipeline=text_gen_pipeline)
retriever = vector_store.as_retriever(search_kwargs={"k": 5})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Example query
query = "How much revenue did DIPD make in FY2000?"
result = qa_chain.run(query)

print("Answer:", result)
