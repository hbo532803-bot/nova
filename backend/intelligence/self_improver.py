from backend.tools.diff_engine import propose_change

def suggest_self_improvement():
    """
    Minimal safe demo:
    Nova suggests adding a comment to its own main file.
    """

    path = "backend/main.py"

    with open(path, "r") as f:
        content = f.read()

    if "# Nova Self-Note" in content:
        return None

    new_content = content + "\n# Nova Self-Note: Reviewed and stable\n"

    propose_change(path, new_content)

    return {
        "path": path,
        "new_content": new_content
    }
