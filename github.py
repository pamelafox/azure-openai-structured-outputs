import requests
import rich

# Replace 'owner' and 'repo' with the repository owner and name
owner = 'microsoft'
repo = 'RAG_Hack'
issue_number = 167

url = f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}'

response = requests.get(url)

if response.status_code == 200:
    issue = response.json()
    rich.print(issue)
else:
    rich.print(f'Failed to fetch issue: {response.status_code}')