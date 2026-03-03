import os
import time
import textwrap

BASE = "../workspace/projects"

def code(plan):
    ts = str(int(time.time()))
    path = f"{BASE}/{plan['project']}_{ts}"
    os.makedirs(path, exist_ok=True)

    with open(os.path.join(path, "requirements.txt"), "w") as f:
        f.write("fastapi\nuvicorn\n")

    with open(os.path.join(path, "main.py"), "w") as f:
        f.write(textwrap.dedent("""
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/")
        def root():
            return {"status": "running", "by": "Nova"}

        if __name__ == "__main__":
            import uvicorn
            uvicorn.run(app, host="127.0.0.1", port=9000)
        """))

    return path
