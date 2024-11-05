import logging
import os

import azure.identity
import openai
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rich import print

logging.basicConfig(level=logging.WARNING)
load_dotenv()

# Configure Azure OpenAI
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
model_name = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT")

# Define models for Structured Outputs
class BlogPost(BaseModel):
    title: str
    summary: str = Field(..., description="A 1-2 sentence summary of the blog post")
    tags: list[str] = Field(..., description="A list of tags for the blog post, like 'python' or 'openai'")

# Fetch blog post and extract title/content
url = 'https://blog.pamelafox.org/2024/09/integrating-vision-into-rag-applications.html'
response = requests.get(url)
if response.status_code !=  200:
    print(f'Failed to fetch the page: {response.status_code}')
    exit(1)
soup = BeautifulSoup(response.content, 'html.parser')
post_title = soup.find('h3', class_='post-title')
post_contents = soup.find('div', class_='post-body').get_text(strip=True)


# Send request to GPT model to extract using Structured Outputs
completion = client.beta.chat.completions.parse(
    model=os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT"),
    messages=[
        {"role": "system", "content": "Extract the information from the blog post"},
        {"role": "user", "content": f"{post_title}\n{post_contents}"},
    ],
    response_format=BlogPost,
)

output = completion.choices[0].message.parsed
blog_post = BlogPost.model_validate(output)
print(blog_post)

