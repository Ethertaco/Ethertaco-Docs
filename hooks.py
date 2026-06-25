PRODUCT_REPOS = {
    "scavlib": {
        "repo_url": "https://github.com/Ethertaco/ScavLib-API",
        "repo_name": "Ethertaco/ScavLib-API",
    },
    "thunder": {
        "repo_url": "https://github.com/Ethertaco/Thunder",
        "repo_name": "Ethertaco/Thunder",
    },
}

DOCS_REPO_URL = "https://github.com/Ethertaco/Ethertaco-Docs"
DOCS_REPO_BRANCH = "main"


def on_page_markdown(markdown, page, config, files):
    src_uri = page.file.src_uri  # 例如 "scavlib/index.zh.md"
    top_folder = src_uri.split("/")[0] if "/" in src_uri else None

    if top_folder in PRODUCT_REPOS:
        page.meta.setdefault("repo_url", PRODUCT_REPOS[top_folder]["repo_url"])
        page.meta.setdefault("repo_name", PRODUCT_REPOS[top_folder]["repo_name"])

    edit_url = page.meta.get("edit_url")
    if edit_url:
        page.edit_url = edit_url
    else:
        page.edit_url = f"{DOCS_REPO_URL}/edit/{DOCS_REPO_BRANCH}/docs/{src_uri}"

    return markdown