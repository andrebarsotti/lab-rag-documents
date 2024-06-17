# Laboratório para o estudo de Retrieval-Augmented Generation

Este projeto demonstra a implementação de Retrieval Augmented Generation (RAG) usando LangChain e OpenAI. O RAG é uma técnica que melhora o desempenho de Modelos de Linguagem Grande (LLMs) recuperando informações relevantes de uma fonte externa e usando-as para gerar respostas mais precisas e contextualmente adequadas.

## Estrutura do Projeto

O projeto consiste em dois principais scripts Python:

1. `create_database.py`: Este script é responsável por carregar, dividir e salvar documentos PDF em um banco de dados vetorial Chroma. Os documentos são divididos em pedaços de 1000 caracteres com uma sobreposição de 80 caracteres. Em seguida, os pedaços são incorporados usando os embeddings da OpenAI e armazenados no banco de dados Chroma.

2. `query_database.py`: Este script permite que você consulte o banco de dados Chroma usando uma interface de linha de comando. Ele procura pelos documentos mais relevantes com base no texto da consulta e gera uma resposta usando um modelo de prompt LangChain e o modelo Chat da OpenAI. A resposta inclui a resposta gerada e as fontes usadas para gerar a resposta.

## Pré-requisitos

Antes de executar os scripts, certifique-se de ter o seguinte:

- Python 3.11 ou superior
- Uma chave de API da OpenAI (você pode se inscrever em https://openai.com/)
- Um arquivo `.env` no diretório raiz do projeto com as seguintes variáveis:
  - `OPENAI_API_KEY`: Sua chave de API da OpenAI
  - `CHROMA_PATH` (opcional): O caminho para o diretório do banco de dados Chroma (padrão é "chroma")
  - `DATA_PATH` (opcional): O caminho para o diretório contendo os documentos PDF (padrão é "../data")

## Uso

1. Instale os pacotes Python necessários:

    ```bash
    pip install -r requirements.txt
    ```
    
    Se estiver usando conda ou mini-conda:

    ```bash
    conda env create -f environment.yml -n rag-documents
    conda activate rag-documents
    ```

2. Execute o script `create_database.py` para carregar, dividir e salvar os documentos PDF no banco de dados Chroma:

    ```bash
    python src/create_database.py
    ```

3. Execute o script `query_database.py` para consultar o banco de dados e gerar uma resposta:

    ```bash
    python src/query_database.py "Seu texto de consulta aqui"
    ```

Substitua `"Seu texto de consulta aqui"` pelo seu texto de consulta real.

## Exemplo

Aqui está um exemplo de como usar o projeto:

1. Carregue e divida os documentos PDF no banco de dados Chroma:

    ```bash
    python src/create_database.py
    ```

2. Consulte o banco de dados e gere uma resposta:

    ```bash
    python src/query_database.py "O que é um Large Language Model?"
    ```

    Saída:

    ```
    Response: Um Large Language Model (LLM) é um modelo de linguagem neural que se diferencia de outros modelos pré-treinados devido à sua enorme quantidade de parâmetros, seu enquadramento na categoria de métodos de IA gerativa e suas habilidades emergentes que não são observadas em modelos menores. Eles são utilizados principalmente para a geração de conteúdo, como geração de texto.
    Sources: ['..\\data\\Nunes - 2024 - Processamento de Linguagem Natural Conceitos, Téc.pdf', '..\\data\\Nunes - 2024 - Processamento de Linguagem Natural Conceitos, Téc.pdf', '..\\data\\Nunes - 2024 - Processamento de Linguagem Natural Conceitos, Téc.pdf']
    ```

## Referências

**PYTHON RAG TUTORIAL (WITH LOCAL LLMS): AI FOR YOUR PDFS.** Direção: Pixegami. [S. l.: s. n.], 2024. (21:33). Disponível em: https://www.youtube.com/watch?v=2TJxpyO3ei4. Acesso em: 13 jun. 2024.

**RAG + LANGCHAIN PYTHON PROJECT: EASY AI/CHAT FOR YOUR DOCS.** Direção: Pixegami. [S. l.: s. n.], 2023. (16:42). Disponível em: https://www.youtube.com/watch?v=tcqEUSNCn8I. Acesso em: 13 jun. 2024.

**LEARN RAG FROM SCRATCH – PYTHON AI TUTORIAL FROM A LANGCHAIN ENGINEER.** Direção: freeCodeCamp.org. [S. l.: s. n.], 2024. (153:11). Disponível em: https://www.youtube.com/watch?v=sVcwVQRHIc8. Acesso em: 14 jun. 2024.
