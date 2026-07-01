import requests
import base64
from urllib.parse import urlparse


def parse_github_url(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip("/").split("/")

    if len(path_segments) >= 2:
        owner, repo = path_segments[0], path_segments[1]
        return owner, repo
    else:
        raise ValueError("Invalid GitHub URL provided!")


def fetch_repo_content(owner, repo, path="", token=None):
    base_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    headers = {
        "Accept": "application/vnd.github.v3+json"
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_file_content(file_info):
    if file_info.get("encoding") == "base64":
        return base64.b64decode(file_info["content"]).decode("utf-8", errors="ignore")
    return file_info.get("content", "")


def build_directory_tree(owner, repo, path="", token=None, indent=0, file_paths=None):
    if file_paths is None:
        file_paths = []

    items = fetch_repo_content(owner, repo, path, token)

    tree_str = ""

    for item in items:
        if ".github" in item["path"].split("/"):
            continue

        if item["type"] == "dir":
            tree_str += "   " * indent + f"[{item['name']}/]\n"

            sub_tree, file_paths = build_directory_tree(
                owner,
                repo,
                item["path"],
                token,
                indent + 1,
                file_paths
            )

            tree_str += sub_tree

        else:
            tree_str += "   " * indent + f"{item['name']}\n"

            if item["name"].endswith((".py", ".html", ".css", ".js", ".jsx", ".rst", ".md")):
                file_paths.append((indent, item["path"]))

    return tree_str, file_paths


def retrieve_github_repo_info(url, token=None):
    owner, repo = parse_github_url(url)

    formatted_string = ""

    try:
        readme_info = fetch_repo_content(owner, repo, "README.md", token)
        readme_content = get_file_content(readme_info)

        formatted_string += f"README.md:\n```\n{readme_content}\n```\n\n"

    except Exception:
        formatted_string += "README.md: Not found or error fetching README\n\n"

    directory_tree, file_paths = build_directory_tree(owner, repo, token=token)

    formatted_string += f"Directory Structure:\n{directory_tree}\n"

    for indent, file_path in file_paths:
        try:
            file_info = fetch_repo_content(owner, repo, file_path, token)
            file_content = get_file_content(file_info)

            formatted_string += f"{'   ' * indent}{file_path}:\n```\n{file_content}\n```\n\n"

        except Exception:
            formatted_string += f"{'   ' * indent}{file_path}: Error fetching file content\n\n"

    return formatted_string