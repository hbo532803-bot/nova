LOW_RISK_PATHS = [
    "backend/",
]

LOW_RISK_KINDS = {
    "comment_only",
}


def classify_change(path: str, diff_lines: list[str]) -> str:

    if not any(path.startswith(p) for p in LOW_RISK_PATHS):
        return "HIGH"

    added = [
        l for l in diff_lines
        if l.startswith("+") and not l.startswith("+++")
    ]

    non_comment = [
        l for l in added
        if not l.lstrip("+").strip().startswith("#")
    ]

    if not non_comment:
        return "LOW"

    return "HIGH"