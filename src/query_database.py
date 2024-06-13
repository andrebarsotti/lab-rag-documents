import argparse
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI, chat_models
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path="./.env", verbose=True)
CHROMA_PATH = os.environ.get("CHROMA_PATH", "chroma")

PROMPT_TEMPLATE = """
You are a helpful assistant. Use the following pieces of context to answer the question at the end.
If the answer is not in context then just say that you don't know, don't try to make up an answer. 
Be concise and specific, and use a formal language.
Don't say mention the word context in the response.

{context}

---

Question: {question}
Helpful Answer:"""

class QueryProcessor:
    def __init__(self):
        self.embedding_function = OpenAIEmbeddings()
        self.db = Chroma(persist_directory=CHROMA_PATH, embedding_function=self.embedding_function)
        self.prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
    def search_db(self, query_text):
        results = self.db.similarity_search_with_relevance_scores(query_text, k=7)
        if len(results) == 0 or results[0][1] < 0.75:
            print("Unable to find matching results.")
            return None
        return results

    def generate_response(self, results, query_text):
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt = self.prompt_template.format(context=context_text, question=query_text)
        #print(prompt)

        response_text = self.model.invoke(prompt)
        sources = [doc.metadata.get("source", None) for doc, _score in results]
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
    results = processor.search_db(query_text)
    if results is None:
        return

    # Generate response.
    formatted_response = processor.generate_response(results, query_text)

    # Print the result.
    print(formatted_response)

if __name__ == "__main__":
    main()

