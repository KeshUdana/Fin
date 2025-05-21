import streamlit as st
import pandas as pd
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# --- Load the model ---
@st.cache_resource
def load_llm():
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        do_sample=False,
        temperature=0.2
    )

    return HuggingFacePipeline(pipeline=pipe)

# --- Load financial data and vector store ---
@st.cache_resource
def prepare_qa_chain():
    df = pd.read_csv("data\\financial_summaries\\combined_financial_summary.csv").dropna()

    # Convert each row to a textual document
    docs = [
        Document(page_content=f"In {row['period']}, {row['company']} had {row['metric']} of {row['value']}.")
        for _, row in df.iterrows()
    ]

    # Embed and index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(docs, embeddings)

    retriever = db.as_retriever(search_kwargs={"k": 5})
    llm = load_llm()

    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=False)
    return qa_chain

# --- Streamlit UI ---
st.set_page_config(page_title="Financial Q&A with Mistral", layout="wide")
st.title("🧠📊 Financial Assistant (LLM-powered)")
st.markdown("Ask any question about the financial dataset. Powered by **Mistral + LangChain**.")

user_question = st.text_input("💬 Ask a financial question:", placeholder="e.g. What was REXP’s revenue in 2022?")
qa_chain = prepare_qa_chain()

if st.button("Get Answer") and user_question:
    with st.spinner("Thinking..."):
        result = qa_chain.run(user_question)
        st.success(result)
