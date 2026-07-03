import os
import urllib.request
import urllib.error
import urllib.parse
import json
import re

TOKEN = os.environ.get("GH_TOKEN")

if not TOKEN:
    print("GH_TOKEN is not set. Skipping stats generation.")
    exit(0)

query = """
{
  viewer {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      nodes {
        name
        languages(first: 20, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
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
except urllib.error.URLError as e:
    print(f"Failed to fetch data: {e}")
    exit(1)

languages = {}
for repo in data["data"]["viewer"]["repositories"]["nodes"]:
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

badges = []
for name, info in sorted_langs:
    percent = (info["size"]/size) * 100
    if percent < 0.5:
        continue
    
    # Shields.io uses simple-icons, spaces become underscores, etc.
    logo = urllib.parse.quote(name.lower().replace(" ", "-"))
    name = urllib.parse.quote(name.replace("-", " "))
    colour = info["color"].replace("#", "")
    
    badges.append(
        f'<img src="https://img.shields.io/badge/{name}-{percent:.1f}%25-{colour}?style=flat&logo={logo}&logoColor=white" alt="{name}" />'
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
