import subprocess

def run_code(run):
    with open("temp_code.py", "w", encoding="utf-8") as file:
        file.write(run)

    result = subprocess.run(
        ["python", "temp_code.py"],
        capture_output=True,
        text=True
    )

    return {
        "output" : result.stdout,
        "error" : result.stderr
    }