import logging
import os

import azure.identity
import openai
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

import requests
import rich
from enum import Enum

load_dotenv()
# Change to logging.DEBUG for more verbose logging from Azure and OpenAI SDKs
logging.basicConfig(level=logging.INFO)


if not os.getenv("AZURE_OPENAI_SERVICE") or not os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"):
    logging.warning("AZURE_OPENAI_SERVICE and AZURE_OPENAI_GPT_DEPLOYMENT environment variables are empty. See README.")
    exit(1)

openai_host = "github"
if openai_host == "azure":
    logging.info("Using an Azure-hosted model")
    credential = azure.identity.DefaultAzureCredential()
    token_provider = azure.identity.get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
    client = openai.AzureOpenAI(
        api_version="2024-08-01-preview",
        azure_endpoint=f"https://{os.getenv('AZURE_OPENAI_SERVICE')}.openai.azure.com",
        azure_ad_token_provider=token_provider,
    )
    model_name = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")
elif openai_host == "github":
    logging.info("Using a GitHub-hosted model")
    client = openai.OpenAI(
        api_version="2024-08-01-preview",
        base_url="https://models.inference.ai.azure.com",
        api_key=os.getenv("GITHUB_TOKEN")
    )
    model_name = "gpt-4o"

    endpoint = "https://models.inference.ai.azure.com"
    token = os.environ["GITHUB_TOKEN"]

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

class Technology(str, Enum):
    JAVASCRIPT = "JavaScript"
    PYTHON = "Python"
    DOTNET = ".NET"
    AISTUDIO = "AI Studio"
    AISEARCH = "AI Search"
    POSTGRESQL = "PostgreSQL"
    COSMOSDB = "CosmosDB"
    AZURESQL = "Azure SQL"

class HackSubmission(BaseModel):
    name: str
    description: str = Field(..., description="A 1-2 sentence description of the project")
    technologies: list[Technology]
    repository_url: str
    video_url: str
    team_members: list[str]

# Replace 'owner' and 'repo' with the repository owner and name
owner = 'microsoft'
repo = 'RAG_Hack'
issue_number = 159

url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'

response = requests.get(url)

if response.status_code != 200:
    print(f'Failed to fetch issue: {response.status_code}')

issue_body = response.json()['body']

completion = client.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Extract the information from the GitHub issue markdown about this hack submission."},
        {"role": "user", "content": issue_body},
    ],
    response_format=HackSubmission,
)

output = completion.choices[0].message.parsed

output = HackSubmission.model_validate(output)
rich.print(output)

