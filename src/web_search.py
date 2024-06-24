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

model = ChatGroq(model="llama3-70b-8192", temperature=0)
# query = "what is a large language model?"
query = "o que é um llm?"

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

for q in queries:
    results += searchX.results(q, num_results=3)

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

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

docs = retriever.invoke(query)

# %%
def generate_response(results, query_text):
    try:
        context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
        prompt = prompt_template.format(context=context_text, question=query_text)
        response_text = model.invoke(prompt)
        sources = [doc.metadata.get("source", None) for doc in results]
        formatted_response = f"Response: {response_text.content}\nSources: {sources}"
        return formatted_response
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Unable to generate a response at this time."
    
formated_response = generate_response(docs, query)

print(formated_response)

