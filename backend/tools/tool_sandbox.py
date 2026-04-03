import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


class ToolSandbox:
    """
    Isolates external tools / APIs.
    """

    def __init__(self, timeout_sec: int = 5):
        self.timeout_sec = timeout_sec

    def run(self, tool_fn, *args, **kwargs):
        start = time.time()
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(tool_fn, *args, **kwargs)
                result = fut.result(timeout=self.timeout_sec)
        except FuturesTimeoutError:
            raise RuntimeError("Tool timeout exceeded")
        except Exception as e:
            raise RuntimeError(f"Tool crashed: {e}")
        finally:
            _ = time.time() - start

        return result
