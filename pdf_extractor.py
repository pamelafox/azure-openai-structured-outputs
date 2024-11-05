import logging
import os

import azure.identity
import openai
from pydantic import BaseModel
from dotenv import load_dotenv

import pymupdf4llm

import rich

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

class Item(BaseModel):
    product: str
    price: float
    quantity: int

class Receipt(BaseModel):
   total: float
   shipping: float
   payment_method: str
   items: list[Item]
   order_number: int

md_text = pymupdf4llm.to_markdown("receipt.pdf")

completion = client.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Extract the information from the blog post"},
        {"role": "user", "content": md_text},
    ],
    response_format=Receipt,
)

output = completion.choices[0].message.parsed

output = Receipt.model_validate(output)
rich.print(output)

