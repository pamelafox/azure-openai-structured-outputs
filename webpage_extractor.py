import logging
import os

import azure.identity
import openai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup

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

class BlogPost(BaseModel):
    title: str
    summary: str = Field(..., description="A 1-2 sentence summary of the blog post")
    tags: list[str] = Field(..., description="A list of tags for the blog post, like 'python' or 'openai'")


# Replace 'url' with the URL of the Blogger page you want to parse
url = 'https://blog.pamelafox.org/2024/09/integrating-vision-into-rag-applications.html'

response = requests.get(url)

if response.status_code !=  200:
    print(f'Failed to fetch the page: {response.status_code}')
    exit(1)
    

soup = BeautifulSoup(response.content, 'html.parser')
    
# Example: Extract all post titles
post_title = soup.find('h3', class_='post-title')
post_contents = soup.find('div', class_='post-body').get_text(strip=True)

completion = client.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Extract the information from the blog post"},
        {"role": "user", "content": f"{post_title}\n{post_contents}"},
    ],
    response_format=BlogPost,
)

output = completion.choices[0].message.parsed

output = BlogPost.model_validate(output)
rich.print(output)

