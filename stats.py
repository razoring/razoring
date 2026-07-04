import os
import urllib.request
import urllib.error
import urllib.parse
import json
import re
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get("GH_TOKEN") or os.getenv("GH_TOKEN")

if not TOKEN:
    print("GH_TOKEN is not set. Skipping stats generation.")
    exit(0)

def fetch_repos():
    has_next_page = True
    end_cursor = None
    all_repos = []
    
    while has_next_page:
        after_clause = f', after: "{end_cursor}"' if end_cursor else ""
        query = f"""
        {{
          viewer {{
            repositories(first: 100, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]{after_clause}) {{
              pageInfo {{
                hasNextPage
                endCursor
              }}
              nodes {{
                name
                languages(first: 50, orderBy: {{field: SIZE, direction: DESC}}) {{
                  edges {{
                    size
                    node {{
                      name
                      color
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """

        req = urllib.request.Request(
            "https://api.github.com/graphql",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json"
            },
            data=json.dumps({"query": query}).encode("utf-8")
        )

        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode("utf-8"))
            if "errors" in data:
                print("GraphQL Errors:")
                print(json.dumps(data["errors"], indent=2))
        except urllib.error.URLError as e:
            print(f"Failed to fetch data: {e}")
            exit(1)
            
        repos = data["data"]["viewer"]["repositories"]
        for r in repos["nodes"]:
            print(f"Fetched repo: {r['name']}")
        all_repos.extend(repos["nodes"])
        has_next_page = repos["pageInfo"]["hasNextPage"]
        end_cursor = repos["pageInfo"]["endCursor"]
        
    return all_repos

languages = {}
for repo in fetch_repos():
    if not repo["languages"]["edges"]:
        continue
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        color = edge["node"]["color"] or "#cccccc"
        size = edge["size"]
        if name not in languages:
            languages[name] = {"size": 0, "color": color}
        languages[name]["size"] += size

size = sum(lang["size"] for lang in languages.values())

if size == 0:
    print("No languages found.")
    exit(0)

sorted_langs = sorted(languages.items(), key=lambda x: x[1]["size"], reverse=True)

print("Languages found:")
for name, info in sorted_langs:
    print(f" - {name}: {(info['size']/size)*100:.2f}%")

badges = []
for name, info in sorted_langs:
    percent = (info["size"]/size) * 100
    if percent < 0.05:
        continue
    
    logo = urllib.parse.quote(name.lower().replace(" ", "-"))
    url_name = urllib.parse.quote(name.replace("-", " "))
    colour = info["color"].replace("#", "")
    
    badges.append(
        f'<img src="https://img.shields.io/badge/{url_name}-{percent:.1f}%25-{colour}?style=flat&logo={logo}&logoColor=white" alt="{name}" />'
    )

html = "<br>\n".join(badges)

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

new_readme = re.sub(
    r'<!-- LANGUAGES_START -->.*?<!-- LANGUAGES_END -->',
    f'<!-- LANGUAGES_START -->\n{html}\n<!-- LANGUAGES_END -->',
    readme,
    flags=re.DOTALL
)

with open("README.md", "w", encoding="utf-8") as f: f.write(new_readme)

print("Updated README.md with language stats.")
