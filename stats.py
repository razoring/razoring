import os
import urllib.request
import urllib.error
import urllib.parse
import json
import re

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

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
            repositories(first: 50, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER], isFork: false{after_clause}) {{
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
                packageJson: object(expression: "HEAD:package.json") {{
                  ... on Blob {{ text }}
                }}
                reqTxt: object(expression: "HEAD:requirements.txt") {{
                  ... on Blob {{ text }}
                }}
                pyproject: object(expression: "HEAD:pyproject.toml") {{
                  ... on Blob {{ text }}
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
frameworks_found = set()

for repo in fetch_repos():
    # Process languages
    if repo["languages"]["edges"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            color = edge["node"]["color"] or "#cccccc"
            size = edge["size"]
            if name not in languages:
                languages[name] = {"size": 0, "color": color}
            languages[name]["size"] += size

    # Process JS Frameworks
    pkg_json = repo.get("packageJson")
    if pkg_json and pkg_json.get("text"):
        try:
            data = json.loads(pkg_json["text"])
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if "react" in deps or "react-dom" in deps: frameworks_found.add("React")
            if "next" in deps: frameworks_found.add("Next.js")
            if "vue" in deps: frameworks_found.add("Vue")
            if "express" in deps: frameworks_found.add("Express")
            if "tailwindcss" in deps: frameworks_found.add("Tailwind CSS")
            if "svelte" in deps: frameworks_found.add("Svelte")
        except:
            pass

    # Process Python Frameworks
    python_deps = ""
    if repo.get("reqTxt") and repo["reqTxt"].get("text"):
        python_deps += repo["reqTxt"]["text"].lower()
    if repo.get("pyproject") and repo["pyproject"].get("text"):
        python_deps += repo["pyproject"]["text"].lower()
        
    if python_deps:
        if "django" in python_deps: frameworks_found.add("Django")
        if "flask" in python_deps: frameworks_found.add("Flask")
        if "fastapi" in python_deps: frameworks_found.add("FastAPI")
        if "streamlit" in python_deps: frameworks_found.add("Streamlit")
        if "pandas" in python_deps: frameworks_found.add("Pandas")
        if "numpy" in python_deps: frameworks_found.add("NumPy")
        if "scikit-learn" in python_deps or "sklearn" in python_deps: frameworks_found.add("Scikit-learn")
        if "tensorflow" in python_deps: frameworks_found.add("TensorFlow")
        if "torch" in python_deps: frameworks_found.add("PyTorch")
        if "keras" in python_deps: frameworks_found.add("Keras")
        if "matplotlib" in python_deps: frameworks_found.add("Matplotlib")
        if "scipy" in python_deps: frameworks_found.add("SciPy")

size = sum(lang["size"] for lang in languages.values())

if size == 0:
    print("No languages found.")
    exit(0)

sorted_langs = sorted(languages.items(), key=lambda x: x[1]["size"], reverse=True)

print("Languages found:")
for name, info in sorted_langs:
    print(f" - {name}: {(info['size']/size)*100:.2f}%")

print("Frameworks found:")
for fw in frameworks_found:
    print(f" - {fw}")

# Generate Language Badges
badges = []
for name, info in sorted_langs:
    percent = (info["size"]/size) * 100
    if percent < 0.05:
        continue
    
    raw_name = name.lower().strip()
    icon_map = {
        "html": "html5",
        "css": "css",
        "jupyter notebook": "jupyter",
        "shell": "gnubash",
        "dockerfile": "docker",
        "tex": "latex",
        "objective-c": "apple",
        "java": "openjdk",
        "c++": "cplusplus",
        "c#": "csharp",
    }
    logo_name = icon_map.get(raw_name, raw_name.replace(" ", "-"))
    logo = urllib.parse.quote(logo_name)
    url_name = urllib.parse.quote(name.replace("-", " "))
    colour = info["color"].replace("#", "")
    
    badges.append(
        f'<img src="https://img.shields.io/badge/{url_name}-{percent:.1f}%25-{colour}?style=for-the-badge&logo={logo}&logoColor=white" alt="{name}" />'
    )

lang_html = "\n".join(badges)

# Generate Framework Badges
FW_CONFIG = {
    "React": {"color": "61DAFB", "logo": "react"},
    "Next.js": {"color": "000000", "logo": "nextdotjs"},
    "Vue": {"color": "4FC08D", "logo": "vuedotjs"},
    "Express": {"color": "000000", "logo": "express"},
    "Tailwind CSS": {"color": "06B6D4", "logo": "tailwindcss"},
    "Svelte": {"color": "FF3E00", "logo": "svelte"},
    "Django": {"color": "092E20", "logo": "django"},
    "Flask": {"color": "000000", "logo": "flask"},
    "FastAPI": {"color": "009688", "logo": "fastapi"},
    "Streamlit": {"color": "FF4B4B", "logo": "streamlit"},
    "Pandas": {"color": "150458", "logo": "pandas"},
    "NumPy": {"color": "013243", "logo": "numpy"},
    "Scikit-learn": {"color": "F7931E", "logo": "scikitlearn"},
    "TensorFlow": {"color": "FF6F00", "logo": "tensorflow"},
    "PyTorch": {"color": "EE4C2C", "logo": "pytorch"},
    "Keras": {"color": "D00000", "logo": "keras"},
    "Matplotlib": {"color": "11557c", "logo": "python"},
    "SciPy": {"color": "8CAAE6", "logo": "scipy"},
}

fw_badges = []
for fw in sorted(list(frameworks_found)):
    conf = FW_CONFIG[fw]
    safe_name = urllib.parse.quote(fw)
    fw_badges.append(
        f'<img src="https://img.shields.io/badge/{safe_name}-{conf["color"]}?style=for-the-badge&logo={conf["logo"]}&logoColor=white" alt="{fw}" />'
    )

fw_html = "\n".join(fw_badges)

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

# Replace Languages
readme = re.sub(
    r'<!-- LANGUAGES_START -->.*?<!-- LANGUAGES_END -->',
    f'<!-- LANGUAGES_START -->\n{lang_html}\n<!-- LANGUAGES_END -->',
    readme,
    flags=re.DOTALL
)

# Replace Frameworks
readme = re.sub(
    r'<!-- FRAMEWORKS_START -->.*?<!-- FRAMEWORKS_END -->',
    f'<!-- FRAMEWORKS_START -->\n{fw_html}\n<!-- FRAMEWORKS_END -->',
    readme,
    flags=re.DOTALL
)

with open("README.md", "w", encoding="utf-8") as f: 
    f.write(readme)

print("Updated README.md with language and framework stats.")
