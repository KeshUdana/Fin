from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_community.vectorstores import FAISS

import pandas as pd

model_id = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")



df = pd.read_csv("data\\financial_summaries\\combined_financial_summary.csv")
df.dropna(inplace=True)

# Turn each row into a document chunk for the LLM
documents = []
for _, row in df.iterrows():
    documents.append(
        f"In {row['period']}, {row['company']} had a {row['metric']} of {row['value']}."
    )

from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Convert documents into LangChain Document objects
docs = [Document(page_content=doc) for doc in documents]

# Create the vector store
vector_store = FAISS.from_documents(docs, embedding_model)

from langchain.llms import HuggingFacePipeline
from transformers import pipeline

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=256,
    do_sample=False,
    temperature=0.2
)

llm = HuggingFacePipeline(pipeline=pipe)

from langchain.chains import RetrievalQA

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True
)

# Sample query
query = "What was REXP’s net income in 2023?"
result = qa_chain(query)

print("Answer:", result['result'])
