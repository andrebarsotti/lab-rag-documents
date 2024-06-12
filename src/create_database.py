# %%
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import openai 
from dotenv import load_dotenv
import os
import shutil

# Load environment variables
load_dotenv(dotenv_path="./.env", verbose=True)

CHROMA_PATH = os.environ.get("CHROMA_PATH", "chroma")
DATA_PATH = os.environ.get("DATA_PATH", "../data")
openai.api_key = os.environ['OPENAI_API_KEY']

# %%
def load_documents(): 
    print("Loading documents...")
    return PyPDFDirectoryLoader(DATA_PATH, recursive=True, extract_images=True).load()

# %%
def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=80,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    return chunks

# %%
def save_to_chroma(chunks: list[Document]):
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        chunks, OpenAIEmbeddings(), persist_directory=CHROMA_PATH
    )
    #db.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
    
# %%
def main():
    documents = load_documents()
    chunks = split_documents(documents)
    save_to_chroma(chunks)

if __name__ == "__main__":
    main()
# %%
