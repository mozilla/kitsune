"""
The few things we ask GitHub for: the latest commit of a branch, one file, the
list of files in a folder, and a download of a whole repository.
"""

import requests
from django.conf import settings

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
CODELOAD = "https://codeload.github.com"


def get_latest_commit(repo: str, ref: str) -> str:
    return _get(
        f"{API}/repos/{repo}/commits/{ref}",
        headers={"Accept": "application/vnd.github.sha"},
    ).text.strip()


def get_file_text(repo: str, ref: str, path: str) -> str:
    return _get(f"{RAW}/{repo}/{ref}/{path}").text


def get_paths(repo: str, ref: str, folder: str) -> list[str]:
    """Return the path of every file and folder under a folder, relative to it."""
    tree = _get(f"{API}/repos/{repo}/git/trees/{ref}:{folder}", params={"recursive": 1}).json()
    if tree["truncated"]:
        raise ValueError(f"GitHub listed only part of {folder} in {repo}.")
    return [entry["path"] for entry in tree["tree"]]


def get_tarball(repo: str, commit: str) -> requests.Response:
    """Return an open download of the repository at a commit. Close it when done."""
    return _get(f"{CODELOAD}/{repo}/tar.gz/{commit}", stream=True)


def _get(url: str, headers: dict[str, str] | None = None, **kwargs) -> requests.Response:
    headers = dict(headers or {})
    if settings.UI_LABELS_GITHUB_TOKEN and url.startswith(f"{API}/"):
        headers["Authorization"] = f"Bearer {settings.UI_LABELS_GITHUB_TOKEN}"
    response = requests.get(
        url, headers=headers, timeout=settings.UI_LABELS_GITHUB_TIMEOUT, **kwargs
    )
    if not response.ok:
        response.close()
    response.raise_for_status()
    return response
