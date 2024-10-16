#!/usr/bin/env python3
import os
import argparse
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.load import dumps, loads
from helpers import load_prompt

# Load environment variables
load_dotenv(dotenv_path="./.env", verbose=True)
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma")

# Prompt template
PROMPT_TEMPLATE = load_prompt("rag-completo.prompt")

# Multi Query prompt template
PERSPECTIVES_TEMPLATE = load_prompt("perspectives.prompt")

class QueryProcessor:
    def __init__(self):
        self.embedding_function = OpenAIEmbeddings()
        self.db = Chroma(persist_directory=CHROMA_PATH, embedding_function=self.embedding_function)
        self.retriever = self.db.as_retriever()
        self.prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        self.perspectives_template = ChatPromptTemplate.from_template(PERSPECTIVES_TEMPLATE)
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        

    def generate_queries(self, question):
        """Generate multiple queries based on the original question."""
        queries = (
            self.perspectives_template
            | self.model
            | StrOutputParser()
            | (lambda x: x.split("\n"))
        ).invoke({"question": question})
        return queries

    def get_unique_union(self, documents):
        """Unique union of retrieved documents."""
        # Flatten list of lists, and convert each Document to string
        flattened_docs = [dumps(doc) for sublist in documents for doc in sublist]
        # Get unique documents
        unique_docs = list(set(flattened_docs))
        # Return
        return [loads(doc) for doc in unique_docs]

    def retrieve_docs(self, question):
        """Retrieve documents based on the original question and generated queries."""
        retrieval_chain = self.generate_queries | self.retriever.map() | self.get_unique_union
        unique_docs = retrieval_chain.invoke({"question": question})
        return unique_docs

    def generate_response(self, results, query_text):
        context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
        prompt = self.prompt_template.format(context=context_text, question=query_text)
        # print(prompt)

        response_text = self.model.invoke(prompt)
        sources = list(set([doc.metadata.get("source", None) for doc in results]))
        formatted_response = f"Response: {response_text.content}\nSources: {sources}"

        return formatted_response

def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    # Process the query.
    processor = QueryProcessor()
    results = processor.retrieve_docs(query_text)
    if not results:
        print("Unable to find matching results.")
        return

    # Generate response.
    formatted_response = processor.generate_response(results, query_text)

    # Print the result.
    print(formatted_response)

if __name__ == "__main__":
    main()



