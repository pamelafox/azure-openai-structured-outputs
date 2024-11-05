import logging
import json
import os

import azure.identity
import openai
from pydantic import BaseModel
from dotenv import load_dotenv
from rich import print


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


class SummarizeDocument(BaseModel):
    filename: str

class SearchDocuments(BaseModel):
    query: str

tools = [openai.pydantic_function_tool(SummarizeDocument), openai.pydantic_function_tool(SearchDocuments)]

completion = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Decide whether to do a search of our documents or whether to summarize a document"},
        {"role": "user", "content": "whats the whistleblower policy for our company"},
    ],
    tools=tools,
)

function_name = completion.choices[0].message.tool_calls[0].function.name
function_args = json.loads(completion.choices[0].message.tool_calls[0].function.arguments)
if function_name == "SummarizeDocument":
    print("Summarizing ", function_args["filename"])
elif function_name == "SearchDocuments":
    print("Searching ", function_args["query"])

