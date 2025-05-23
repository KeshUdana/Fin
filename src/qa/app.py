import streamlit as st
import pandas as pd
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN") or "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"

if not HUGGINGFACE_TOKEN:
    st.error("HUGGINGFACE_TOKEN not found! Please set it in your .env file or environment variables.")
    st.stop()


# --- Load the LLM model ---
@st.cache_resource(show_spinner=False)
def load_llm():
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=HUGGINGFACE_TOKEN)
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        token=HUGGINGFACE_TOKEN,
    )

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        do_sample=False,
        temperature=0.2,
        device=0 if torch.cuda.is_available() else -1,
    )

    return HuggingFacePipeline(pipeline=pipe)


@st.cache_resource(show_spinner=False)
def prepare_qa_chain():
    df = pd.read_csv("data/financial_summaries/financial_summary_all.csv").dropna()
    df.columns = df.columns.str.strip()

    # Convert wide format to long format
    long_df = pd.melt(
        df,
        id_vars=["company", "period"],
        value_vars=["Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Income", "Net Income"],
        var_name="metric",
        value_name="value"
    )

    # Create documents for vector store
    docs = [
        Document(page_content=f"In {row['period']}, {row['company']} had {row['metric']} of {row['value']}.")
        for _, row in long_df.iterrows()
    ]

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(docs, embeddings)

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    llm = load_llm()

    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=False)
    return qa_chain


import streamlit as st

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title="Financial Q&A Chat", layout="wide")
st.title("Financial Assistant (LLM-powered)")
st.markdown("Ask any question about the financial dataset. Powered by **Mistral + LangChain**.")

qa_chain = prepare_qa_chain()

def add_message(user_msg, bot_msg):
    st.session_state.chat_history.append({"user": user_msg, "bot": bot_msg})
for chat in st.session_state.chat_history:
    st.markdown(f"**You:** {chat['user']}")
    st.markdown(f"**Assistant:** {chat['bot']}")

user_question = st.text_input("Ask a financial question:", key="input")

if st.button("Send") and user_question:
    with st.spinner("Thinking..."):
        answer = qa_chain.run(user_question)
        add_message(user_question, answer)
        st.experimental_rerun()  


