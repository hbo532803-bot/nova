import time


class ToolSandbox:
    """
    Isolates external tools / APIs.
    """

    def __init__(self, timeout_sec: int = 5):
        self.timeout_sec = timeout_sec

    def run(self, tool_fn, *args, **kwargs):
        start = time.time()
        try:
            result = tool_fn(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Tool crashed: {e}")

        duration = time.time() - start
        if duration > self.timeout_sec:
            raise RuntimeError("Tool timeout exceeded")

        return result
