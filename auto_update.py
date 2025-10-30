# auto_update.py
from google import genai
from dotenv import load_dotenv
from git import Repo
import os
import re
import shutil
from datetime import datetime

# Load .env if present locally (Render will use env vars set in dashboard)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

def fetch_trending_keywords(topic: str) -> str:
    prompt = f"List 10 trending SEO keywords related to {topic} in comma-separated format."
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        if response.candidates and len(response.candidates) > 0:
            parts = response.candidates[0].content.parts
            if parts and len(parts) > 0:
                return parts[0].text.strip()
        return "No keywords generated"
    except Exception as e:
        print(f"[ERROR] Gemini API: {e}")
        return "Error fetching keywords"

def update_html_with_keywords(keywords: str):
    file_path = "index.html"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_meta = f'<meta name="keywords" content="{keywords}">'
        if re.search(r'<meta name="keywords".*?>', content, flags=re.IGNORECASE):
            content = re.sub(r'<meta name="keywords".*?>', new_meta, content, flags=re.IGNORECASE)
        else:
            content = content.replace("<head>", f"<head>\n    {new_meta}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[INFO] index.html updated with keywords: {keywords}")
    except Exception as e:
        print(f"[ERROR] Updating HTML: {e}")

def push_to_github():
    try:
        repo_dir = "repo"
        authed_repo_url = GITHUB_REPO.replace("https://", f"https://{GITHUB_TOKEN}@")
        if not os.path.exists(repo_dir):
            print("[INFO] Cloning repository...")
            Repo.clone_from(authed_repo_url, repo_dir)
        repo = Repo(repo_dir)
        shutil.copy("index.html", os.path.join(repo_dir, "index.html"))
        repo.git.add("index.html")
        commit_message = f"Auto SEO keyword update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        repo.index.commit(commit_message)
        origin = repo.remote(name="origin")
        origin.set_url(authed_repo_url)
        origin.push()
        print("[SUCCESS] Pushed changes to GitHub.")
    except Exception as e:
        print(f"[ERROR] GitHub push failed: {e}")

def main():
    topic = "E-commerce SEO trends"
    print("\n=== Running daily SEO update ===")
    keywords = fetch_trending_keywords(topic)
    update_html_with_keywords(keywords)
    push_to_github()
    print("=== Done ===\n")

if __name__ == "__main__":
    main()
