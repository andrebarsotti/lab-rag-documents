#!/usr/bin/env python3
# %%
from langchain_community.utilities import SearxSearchWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from helpers import load_prompt
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv("./.env")

prompt_template = ChatPromptTemplate.from_template(load_prompt("rag-completo.prompt"))
perspectives_template = ChatPromptTemplate.from_template(load_prompt("perspectives.prompt"))
websearch_template = ChatPromptTemplate.from_template(load_prompt("websearch.prompt"))

model = ChatGroq(model="llama3-70b-8192", temperature=0.5)
query = "what is a large language model?"

def generate_questions(question):
    queries = (
        perspectives_template
        | model
        | StrOutputParser()
        | (lambda x: x.split("\n"))
    ).invoke({"question": question})
    return queries

def generate_queries(questions):
    list_questions = ",".join(questions)
    queries = (
        websearch_template
        | model
        | StrOutputParser()
        | (lambda x: x.split(","))
    ).invoke({"questions": list_questions})
    return queries

queries = generate_queries(generate_questions(query))

results: List[Dict] = []

searchX = SearxSearchWrapper(searx_host="https://salvadeonetlink.asuscomm.com:8380/")

for query in queries:
    results += searchX.results(query, num_results=3)

# Remove duplicates from results
def remove_duplicates(list_of_dicts):
    seen = set()
    unique_list = []
    for d in list_of_dicts:
        # Convert the dictionary to a tuple of its items, ensuring all values are tuples
        d_tuple = tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in sorted(d.items()))
        if d_tuple not in seen:
            seen.add(d_tuple)
            unique_list.append(d)
    return unique_list


results = remove_duplicates(results)

results
# %%
import os
from langchain_core.documents import Document
from langchain_community.document_loaders import ToMarkdownLoader
import requests
from typing import List

api_key = os.environ.get("TWO_MARKDOWN")
documents: List[Document] = []

for result in results:
    url = result["link"]
    print(f"Verifying URL: {url}")
    
    try:
        # Use a HEAD request to check if the URL is accessible
        response = requests.head(url, allow_redirects=True)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # If the URL is accessible, proceed with loading the document
        print(f"Loading document from URL: {url}")
        loader = ToMarkdownLoader(url, api_key)
        
        try:
            doc = loader.load()[0]
            documents.append(doc)
        except KeyError as e:
            print(f"KeyError: The key '{e}' was not found in the API response for {url}")
    except requests.exceptions.RequestException as e:
        print(f"Error verifying or fetching data from {url}: {e}")

documents
# %%
from langchain_text_splitters import RecursiveCharacterTextSplitter

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

chunks = split_documents(documents)
chunks
# %%
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Embed
vectorstore = Chroma.from_documents(documents=chunks,
                                    embedding=OpenAIEmbeddings())

retriever = vectorstore.as_retriever()