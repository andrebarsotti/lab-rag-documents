# %%
import openai
import subprocess
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env", verbose=True)

def executar_codigo(codigo):
    # Escreva o código em um arquivo temporário
    with open("temp_code.py", "w") as f:
        f.write(codigo)
    
    # Execute o código e capture a saída
    result = subprocess.run(['python', 'temp_code.py'], capture_output=True, text=True)
    
    # Delete o arquivo temporário
    os.remove("temp_code.py")
    
    return result.stdout

def agente_executar_codigo(prompt):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    
    codigo = response.choices[0].message.content.strip()
    resultado = executar_codigo(codigo)
    return resultado

# Exemplo de uso
prompt = "You are an expert programmer. Write a Python code snippet that calculates the sum of numbers from 1 to 10. Your responses should only be code, without explanation or formatting."
resultado = agente_executar_codigo(prompt)
print("Resultado da execução do código:\n", resultado)
