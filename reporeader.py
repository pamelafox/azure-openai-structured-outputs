import logging
import os
import base64

import azure.identity
import openai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import requests
import rich
from enum import Enum

load_dotenv()
# Change to logging.DEBUG for more verbose logging from Azure and OpenAI SDKs
logging.basicConfig(level=logging.WARNING)


if not os.getenv("AZURE_OPENAI_SERVICE") or not os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"):
    logging.warning("AZURE_OPENAI_SERVICE and AZURE_OPENAI_GPT_DEPLOYMENT environment variables are empty. See README.")
    exit(1)


credential = azure.identity.DefaultAzureCredential()
token_provider = azure.identity.get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

client = openai.AzureOpenAI(
    api_version="2024-08-01-preview",
    azure_endpoint=f"https://{os.getenv('AZURE_OPENAI_SERVICE')}.openai.azure.com",
    azure_ad_token_provider=token_provider,
)

class Language(str, Enum):
    JAVASCRIPT = "JavaScript"
    PYTHON = "Python"
    DOTNET = ".NET"

class AzureService(str, Enum):
    AISTUDIO = "AI Studio"
    AISEARCH = "AI Search"
    POSTGRESQL = "PostgreSQL"
    COSMOSDB = "CosmosDB"
    AZURESQL = "Azure SQL"

class Framework(str, Enum):
    LANGCHAIN = "Langchain"
    SEMANTICKERNEL = "Semantic Kernel"
    LLAMAINDEX = "Llamaindex"
    AUTOGEN = "Autogen"
    SPRINGBOOT = "Spring Boot"
    PROMPTY = "Prompty"

class RepoOverview(BaseModel):
    name: str
    description: str = Field(..., description="A 1-2 sentence description of the project")
    languages: list[Language]
    azure_services: list[AzureService]
    frameworks: list[Framework]

url = 'https://api.github.com/repos/shank250/CareerCanvas-msft-raghack/contents/README.md'

response = requests.get(url)

if response.status_code != 200:
    print(f'Failed to fetch issue: {response.status_code}')

content = response.json()
readme_content = base64.b64decode(content['content']).decode('utf-8')

completion = client.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Extract the information from the GitHub issue markdown about this hack submission."},
        {"role": "user", "content": readme_content},
    ],
    response_format=RepoOverview,
)

output = completion.choices[0].message.parsed

output = RepoOverview.model_validate(output)
rich.print(output)

