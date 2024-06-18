import os

def load_prompt(prompt_name):
    prompt_dir = os.getenv('PROMPT_DIR', '.prompt')
    prompt_path = os.path.join(prompt_dir, prompt_name)
    with open(prompt_path, 'r') as file:
        return file.read()
