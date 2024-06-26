#!/usr/bin/env python3
# %%
"""
Este script Python realiza pesquisas na web com base em um texto de consulta fornecido.
Ele gera perguntas relacionadas, consultas de pesquisa, busca resultados de pesquisa,
carrega documentos, divide documentos em pedaços, gera uma resposta e imprime a resposta formatada.

Para usar o script, execute-o com o texto de consulta como argumento:
    python web_search.py "Seu texto de consulta aqui"

O script gerará perguntas relacionadas, consultas de pesquisa, buscará resultados de pesquisa,
carregará documentos, dividirá documentos, gerará uma resposta e imprimirá a resposta formatada.
"""
import argparse
import logging
import os
import requests
from dotenv import load_dotenv
from helpers import load_prompt
from langchain_community.document_loaders import ToMarkdownLoader, FireCrawlLoader
from langchain_community.utilities import SearxSearchWrapper
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv("./.env")
TWO_MARKDOWN_KEY = os.environ["TWO_MARKDOWN"]
FIRECRAWL_API_KEY = os.environ["FIRECRAWL_API_KEY"]
SEARXNG_HOST = os.environ.get("SEARXNG_HOST", "http://localhost:8080/")

# Modelos de prompt
PROMPT_TEMPLATE = load_prompt("rag-completo.prompt")
PERSPECTIVES_TEMPLATE = load_prompt("perspectives.prompt")
WEBSEARCH_TEMPLATE = load_prompt("websearch2.prompt")

class WebSearchProcessor:
    """
    Classe responsável por processar pesquisas na web.
    """
    def __init__(self):
        # Inicializa o modelo, o mecanismo de pesquisa e os templates de prompt
        self.model = ChatGroq(model="llama3-70b-8192", temperature=0)
        self.searchX = SearxSearchWrapper(searx_host=SEARXNG_HOST)
        self.prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        self.perspectives_template = ChatPromptTemplate.from_template(PERSPECTIVES_TEMPLATE)
        self.websearch_template = ChatPromptTemplate.from_template(WEBSEARCH_TEMPLATE)

    def generate_questions(self, question):
        """
        Gera perguntas relacionadas à pergunta inicial para obter diferentes perspectivas.
        """
        queries = (
            self.perspectives_template
            | self.model
            | StrOutputParser()
            | (lambda x: x.split("\n"))
        ).invoke({"question": question})
        return queries

    def generate_queries(self, questions):
        """
        Gera consultas de pesquisa com base nas perguntas geradas.
        """
        list_questions = ",".join(questions)
        queries = (
            self.websearch_template
            | self.model
            | StrOutputParser()
            | (lambda x: x.split(","))
        ).invoke({"questions": list_questions})
        return queries

    def fetch_search_results(self, queries):
        """
        Busca resultados de pesquisa na web com base nas consultas geradas.
        """
        results = []
        for query in queries:
            logger.info(f"Searching for: {query}.")
            results += self.searchX.results(query, num_results=3)
        logger.info(f"Search results: {len(results)} results.")
        return self.remove_duplicates(results)

    def remove_duplicates(self, list_of_dicts):
        """
        Remove resultados duplicados da lista de resultados de pesquisa.
        """
        seen = set()
        unique_list = []
        for d in list_of_dicts:
            d_tuple = tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in sorted(d.items()))
            if d_tuple not in seen:
                seen.add(d_tuple)
                unique_list.append(d)
        logger.info(f"Unique search results: {len(unique_list)} results.")
        return unique_list

    def load_documents(self, results):
        """
        Carrega documentos a partir dos resultados de pesquisa.
        Esta função percorre cada resultado de pesquisa, extrai a URL e tenta carregar o conteúdo da URL como um documento.
        Se a URL estiver acessível, o conteúdo é convertido em um documento usando o ToMarkdownLoader e adicionado à lista de documentos.
        Se ocorrer um erro ao acessar a URL, uma mensagem de erro é registrada no log.
        """
        documents = []
        for result in results:
            url = result["link"]
            try:
                logger.info(f"Fetching data from {url}.")
                response = requests.head(url, allow_redirects=True)
                response.raise_for_status()
                # loader = ToMarkdownLoader(url, TWO_MARKDOWN_KEY)
                loader = FireCrawlLoader(url, api_key=FIRECRAWL_API_KEY,mode="scrape")
                doc = loader.load()[0]
                documents.append(doc)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error verifying or fetching data from {url}: {e}")        
        logger.info(f"Loaded {len(documents)} documents.")
        return documents

    def split_documents(self, documents):
        """
        Divide os documentos em pedaços menores.
        Esta função usa o RecursiveCharacterTextSplitter para dividir os documentos em pedaços menores de 1000 caracteres, com uma sobreposição de 80 caracteres.
        Isso é útil para processar documentos grandes que podem exceder o limite de tamanho do contexto do modelo.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=80,
            length_function=len,
            add_start_index=True,
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks
    
    def get_similar_docs(self, chunks, query_text, num_results=3):
        """
        Esta função cria um vectorstore a partir dos pedaços de documentos usando embeddings OpenAIEmbeddings.
        Em seguida, configura um retriever para o vectorstore que realiza uma busca de similaridade.
        A função invoca o retriever com a consulta de texto e retorna os documentos similares encontrados.
        """
        # Filter complex metadata from each chunk
        logger.info("Getting similar documents.")
        chunks = filter_complex_metadata(chunks)
        
        logger.info("Getting similar documents.")
        vectorstore = Chroma.from_documents(documents=chunks, embedding=OpenAIEmbeddings())
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": num_results})
        docs = retriever.invoke(query_text)
        logger.info(f"Found {len(docs)} similar documents.")
        return docs

    def generate_response(self, results, query_text):
        """
        Gera uma resposta com base nos resultados da pesquisa e na pergunta.
        Esta função concatena o conteúdo de cada documento em um único texto de contexto, formata o prompt com o contexto e a pergunta,
        e invoca o modelo para gerar uma resposta. Em seguida, extrai as fontes dos documentos e formata a resposta final.
        """
        context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
        prompt = self.prompt_template.format(context=context_text, question=query_text)
        response_text = self.model.invoke(prompt)
        sources = list(set([doc.metadata.get("link", None) for doc in results]))
        formatted_response = f"Response: {response_text.content}\nSources: {sources}"
        return formatted_response
    
    def query(self, query_text):
        """
        Função que processa a consulta e gera uma resposta.
        """
        processor = self
        # Generate related questions and search results
        questions = processor.generate_questions(query_text)
        questions.append(query_text)
        queries = processor.generate_queries(questions)
        search_results = processor.fetch_search_results(queries)
        
        #filter the search results
        search_filter = processor.get_similar_docs(
            chunks=[Document(result['snippet'], metadata={"link": result["link"]}) for result in search_results],
            query_text=query_text,
            num_results=5
        )
        
        documents = processor.load_documents(
            self.remove_duplicates([{"link": doc.metadata.get("link")} for doc in search_filter])
        )
        
        chunks = processor.split_documents(documents)

        docs = processor.get_similar_docs(chunks, query_text)

        formatted_response = processor.generate_response(docs, query_text)
        return formatted_response
    
# %%
def main():
    """
    Função principal que processa a consulta.
    Esta função analisa os argumentos da linha de comando, gera perguntas relacionadas, gera consultas de pesquisa,
    busca resultados de pesquisa, carrega documentos, divide documentos, gera uma resposta e imprime a resposta formatada.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text

    processor = WebSearchProcessor()

    try:
        formatted_response = processor.query(query_text)
        print(formatted_response)
    except Exception as e:
        logger.error(f"Error processing the query: {e}")

if __name__ == "__main__":
   main()
