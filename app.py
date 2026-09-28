from pathlib import Path
import time
import requests
from flask import Flask, jsonify, render_template, request, Response

try:
    from tools.model_router import (
        select_model, understand_request, detect_task,
        get_next_action, validate_action,
    )

    print("MODEL ROUTER LOADED FROM:", get_next_action.__module__)
    print("MODEL ROUTER FUNCTION:", get_next_action)


except Exception:
    def _missing(*args, **kwargs):
        raise RuntimeError("tools/model_router.py is not available")
    select_model = understand_request = detect_task = _missing
    get_next_action = validate_action = _missing

try:
    from tools.pdf_tool import extract_text_from_pdf
except Exception:
    extract_text_from_pdf = None

try:
    from tools.ocr_tool import extract_text_from_image
except Exception:
    extract_text_from_image = None

try:
    from tools.sandbox_tool import run_code
except Exception:
    run_code = None

app = Flask(__name__)
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MODEL = "qwen2.5:3b"

def ask_llm(prompt, model=MODEL):
    started = time.perf_counter()

    print(">>> ASK_LLM CALLED <<<")
    print("MODEL:", model)

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    elapsed = time.perf_counter() - started
    print(f"LLM ({model}): {elapsed:.2f}s")

    answer = data.get("response", "").strip()

    print("OLLAMA ANSWER:", repr(answer))

    return answer

def stream_llm(prompt, model=MODEL):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True
        },
        stream=True,
        timeout=180
    )

    response.raise_for_status()

    for line in response.iter_lines(decode_unicode=True):

        if not line:
            continue

        try:
            data = requests.models.complexjson.loads(line)
        except Exception:
            continue

        token = data.get("response", "")

        if token:
            yield token

        if data.get("done"):
            break

def _clean_code(code):
    code = code.strip()
    if code.startswith("```"):
        code = code.replace("```python", "", 1).replace("```", "")
    return code.strip()


def process_request(user_request, attached_path=None, messages=None):

    answer = ""
    final_prompt = ""

    if messages is None:
        messages = []

    messages = messages[-10:]

    history = "Nothing has been done yet."

    text = ""
    context = ""

    code = ""
    code_error = ""
    print(
    "FINAL ANSWER:",
    repr(answer)
    )

    # -------------------------
    # DETECT TASK
    # -------------------------

    task = detect_task(
        user_request,
        ask_llm,
        messages,
        attached_path
    )

    # If no file exists, don't allow file-based tasks
    if not attached_path and task in ("document", "image", "ocr"):
        task = "general"

    # -------------------------
    # GOAL
    # -------------------------

    goal = understand_request(
        user_request,
        task,
        ask_llm
    )

    model = select_model(task)

    print("Task:", task)
    print("Goal:", goal)
    print("Model:", model)

    # -------------------------
    # AGENT LOOP
    # -------------------------

    for _ in range(8):

        print("DEBUG BEFORE ACTION")
        print("history =", repr(history))
        print("task =", repr(task))
        print("goal =", repr(goal))

        action = get_next_action(
            user_request,
            task,
            goal,
            history
        )

        print("NEXT ACTION:", action)

        if action == "done":
            break

        if not validate_action(
            action,
            task,
            history
        ):
            print("Invalid action:", action)
            break

        # -------------------------
        # IMAGE OCR
        # -------------------------

        if action == "ocr":

            if not attached_path or not extract_text_from_image:
                history += (
                    "\nAction: ocr"
                    "\nResult: No image available.\n"
                )
                break

            try:
                text = extract_text_from_image(
                    attached_path
                )

                context = text

                history += (
                    "\nAction: ocr\n"
                    f"Result:\n{text}\n"
                )

                print("OCR TEXT:", text)

            except Exception as exc:
                print("OCR ERROR:", exc)

                history += (
                    "\nAction: ocr\n"
                    f"Result: {exc}\n"
                )

                break

            continue

        # -------------------------
        # DOCUMENT EXTRACTION
        # -------------------------

        if action in ("extract_file", "extract_pdf"):

            if not attached_path:
                history += (
                    "\nAction: extract_file"
                    "\nResult: No file attached.\n"
                )
                break

            path = Path(attached_path)

            try:

                if (
                    path.suffix.lower() == ".pdf"
                    and extract_text_from_pdf
                ):
                    text = extract_text_from_pdf(
                        str(path)
                    )
                else:
                    text = path.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )

                context = text

                history += (
                    "\nAction: extract_file\n"
                    f"Result:\n{text}\n"
                )

            except Exception as exc:

                print("FILE ERROR:", exc)

                history += (
                    "\nAction: extract_file\n"
                    f"Result: {exc}\n"
                )

                break

            continue

        # -------------------------
        # SEARCH
        # -------------------------

        if action == "search":

            context = text or context

            history += (
                "\nAction: search\n"
                f"Result:\n{context}\n"
            )

            continue

        # -------------------------
        # CODING
        # -------------------------

        if action == "run_code":

            code = _clean_code(
                ask_llm(
                    f"""
Write a complete Python program for this request.

Request:
{user_request}

Rules:
- Return only Python code.
- Do not execute it.
- Do not use markdown fences.
- Keep it simple and correct.
""",
                    model
                )
            )

            print("GENERATED CODE:", code)

            final_prompt = f"""
You are a private local Python programming assistant.

User request:
{user_request}

Generated Python code:
{code}

Give the user:

1. The complete Python code.
2. A simple explanation of how it works.

Rules:
- Keep the explanation simple.
- Do not mention internal routing.
- Do not mention prompts.
- Do not mention RAG.
- Do not mention OCR.
- Do not mention the model.
- Return only the final answer.
"""

            history += (
            "\nAction: generate_code\n"
            f"Code:\n{code}\n"
            )

            break

        # -------------------------
        # FIX CODE
        # -------------------------

        if action == "fix_code":

            code = _clean_code(
                ask_llm(
                    f"""
Fix this Python code.

CODE:
{code}

ERROR:
{code_error}

REQUEST:
{user_request}

Return only corrected Python code.
"""
                )
            )

            history += (
                "\nAction: fix_code\n"
                f"Fixed code:\n{code}\n"
            )

            continue

        # -------------------------
        # FINAL ANSWER
        # -------------------------

        if action == "answer":

            if task == "general":

                prompt = (
                    "You are a private local AI assistant.\n\n"
                    "Answer the user's question directly "
                    "and accurately.\n\n"
                    f"User question:\n{user_request}\n\n"
                    "Return only the answer."
                )

            elif task == "image":

                prompt = (
                    "You are a private local AI assistant.\n\n"
                    "The user has attached an image.\n"
                    "OCR text from the image is provided below.\n\n"
                    f"OCR TEXT:\n{context or text}\n\n"
                    f"USER QUESTION:\n{user_request}\n\n"
                    "Explain the image or its meaning clearly "
                    "and simply when asked.\n"
                    "Do not say the image is missing.\n"
                    "Do not invent information.\n"
                    "Return only the answer."
                )

            elif task == "document":

                prompt = (
                    "You are a private local AI assistant.\n\n"
                    "Answer the user's question using the "
                    "provided document context.\n\n"
                    f"DOCUMENT:\n{context or text}\n\n"
                    f"USER QUESTION:\n{user_request}\n\n"
                    "Do not invent information.\n"
                    "Return only the answer."
                )

            else:

                prompt = (
                    "You are a private local AI assistant.\n\n"
                    f"User question:\n{user_request}\n\n"
                    "Answer directly.\n"
                    "Return only the answer."
                )

            print(">>> CALLING OLLAMA <<<")
            print("MODEL:", model)

            final_prompt = prompt

            history += (
                "\nAction: answer\n"
            )

            break

        # -------------------------
        # UNKNOWN ACTION
        # -------------------------

        print(
            "UNKNOWN ACTION:",
            action
        )

        break

    print(
        "FINAL ANSWER:",
        repr(answer)
    )

    return {
        "prompt": final_prompt if "final_prompt" in locals() else "",
        "task": task,
        "goal": goal,
        "model": model,
    }

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/upload")
def upload_file():

    if "file" not in request.files:
        return jsonify({
            "error": "No file provided"
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "error": "No filename"
        }), 400

    try:
        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = file.filename
        save_path = UPLOAD_DIR / filename

        file.save(save_path)

        print("FILE UPLOADED:", save_path)

        return jsonify({
            "success": True,
            "name": filename
        })

    except Exception as exc:

        print(
            "UPLOAD ERROR:",
            repr(exc)
        )

        return jsonify({
            "error": str(exc)
        }), 500


@app.post("/api/chat")
def chat():

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    messages = data.get(
        "messages",
        []
    )

    if not isinstance(messages, list):
        messages = []

    messages = messages[-10:]

    attached_name = data.get(
        "attached_file"
    )

    attached_path = (
        str(UPLOAD_DIR / attached_name)
        if attached_name
        else None
    )

    if not message:
        return jsonify({
            "error": "message is required"
        }), 400

    try:

        result = process_request(
            message,
            attached_path,
            messages
        )

        prompt = result.get(
            "prompt",
            ""
        )

        task = result.get(
            "task",
            "general"
        )

        model = result.get(
            "model",
            MODEL
        )

        if not prompt:
            return jsonify({
                "error": "No final prompt returned."
            }), 500

        def generate():

            try:

                for token in stream_llm(
                    prompt,
                    model
                ):
                    yield token

            except Exception as exc:

                print(
                    "STREAM ERROR:",
                    repr(exc)
                )

                yield (
                    "\n\n[Error: "
                    + str(exc)
                    + "]"
                )

        response = Response(
            generate(),
            mimetype="text/plain"
        )

        response.headers[
            "X-Task"
        ] = task

        response.headers[
            "X-Model"
        ] = model

        response.headers[
            "Cache-Control"
        ] = "no-cache"

        return response

    except requests.RequestException as exc:

        return jsonify({
            "error":
            f"Ollama error: {exc}"
        }), 502

    except Exception as exc:

        import traceback

        print("\n========== SERVER ERROR ==========")
        print(repr(exc))
        traceback.print_exc()
        print("==================================\n")

        return jsonify({
            "error": str(exc)
        }), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
