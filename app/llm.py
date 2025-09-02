import os
import ollama
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def _build_prompt(finding_details: dict) -> str:
    return f"""
    Explain the following security finding in simple terms for a developer.
    Focus on the risk and suggest a clear, actionable remediation.

    Vulnerability Type: {finding_details.get('check_id')}
    File Path: {finding_details.get('path')}
    Code Snippet:
    ```
    {finding_details.get('code_snippet')}
    ```
    """

def explain_ollama(finding_details: dict) -> str:
    prompt = _build_prompt(finding_details)
    model = os.getenv("OLLAMA_MODEL", "llama3")
    response = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['message']['content']

def explain_openai(finding_details: dict) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = _build_prompt(finding_details)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def explain_stub(finding_details: dict) -> str:
    return f"This is a stub explanation for a finding of type '{finding_details.get('check_id')}' in file '{finding_details.get('path')}'."

def get_explanation_from_llm(finding_details: dict) -> str:
    provider = os.getenv("LLM_PROVIDER", "stub").lower()
    try:
        if provider == "ollama":
            return explain_ollama(finding_details)
        elif provider == "openai":
            return explain_openai(finding_details)
        else:
            return explain_stub(finding_details)
    except Exception as e:
        return f"Failed to get explanation from LLM provider '{provider}'. Error: {e}"
