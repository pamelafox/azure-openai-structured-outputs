import logging
import os

import azure.identity
import openai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import base64
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

class Graph(BaseModel): # Pydantic model
    title: str
    description: str = Field(..., description="1 sentence description of the graph")
    x_axis: str
    y_axis: str
    legend: list[str]

def open_image_as_base64(filename):
    with open(filename, "rb") as image_file:
        image_data = image_file.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")
    return f"data:image/png;base64,{image_base64}"

completion = client.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Extract the information from the blog post"},
        {
            "role": "user",
            "content": [
                {"text": "extract information about this graph", "type": "text"},
                {"image_url": {"url": open_image_as_base64("graph_treecover.png")}, "type": "image_url"},
            ],
        }
    ],
    response_format=Graph,
)

output = completion.choices[0].message.parsed

output = Graph.model_validate(output)
rich.print(output)

