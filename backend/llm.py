import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI

load_dotenv()

# Initialize the Gemini Models (Free tier API key should be used in .env as GOOGLE_API_KEY)
# We use Pro for reasoning (Orchestrator, Design)
llm_flash = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    temperature=0.2,
    max_tokens=8192,
    timeout=None,
    max_retries=2,
)

# We use Mistral Large for simpler tasks (Asset, Backend, Execution parsing)
# Requires MISTRAL_API_KEY in .env
llm_light = ChatMistralAI(
    model="mistral-large-latest",
    temperature=0.2,
    max_retries=2,
)
