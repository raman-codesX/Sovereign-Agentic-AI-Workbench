import requests
import time
from tools.file_router import extract_file
from tools.text_tool import chunk_text
from tools.embedding_tool import embedding
from tools.vector_store_tool import vector_store
from tools.retrieval_tool import search
from tools.model_router import (
    select_model,
    understand_request,
    detect_task,
    get_next_action,
    validate_action
)
from tools.sandbox_tool import run_code
from tools.ocr_tool import extract_text_from_image


# LOCAL LLM

print("🔥 THIS AGENT.PY IS LOADED 🔥")

def ask_llm(prompt, model):
    start = time.perf_counter()

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    elapsed = time.perf_counter() - start

    print(f"LLM ({model}): {elapsed:.2f}s")

    if response.status_code != 200:
        print("OLLAMA ERROR:", response.text)
        return ""

    return response.json()["response"]

# CLEAN CODE FUNCTION

def _clean_code(code):

    code = code.strip()

    if code.startswith("```python"):
        code = code[len("```python"):]

    elif code.startswith("```"):
        code = code[len("```"):]

    if code.endswith("```"):
        code = code[:-3]

    return code.strip()

# AVAILABLE TOOLS

tools = {
    "extract_file": extract_file,
    "search": search,
    "run_code": run_code,
    "ocr": extract_text_from_image
}


# USER REQUEST

request = f"""
give me a puzzle question with storie
"""

# TASK DETECTION
start = time.perf_counter()
task = detect_task(
    request,
    ask_llm
)
print(
    f"Task detection: "
    f"{time.perf_counter() - start:.2f}s"
)
print("Task Detect:", task)

#GOAL

goal = understand_request(
    request,
    task,
    ask_llm
)

print("GOAL: ",goal)

# MODEL SELECTION

start = time.perf_counter()
model = select_model(task)
print(
    f"Model selection: "
    f"{time.perf_counter() - start:.2f}s"
)

print("Selected model:", model)


# AGENT STATE

history = "Nothing has been done yet."

file_path = r"C:\Users\hp\Downloads\cybersecurity_private_ai_systems.txt"

image_path = r"C:\Users\hp\Downloads\images.jpeg"

text = ""
context = ""

code = ""
code_error = ""
code_output = ""


# AGENT LOOP

while True:

    action = get_next_action(
        request,
        task,
        goal,
        history,
        ask_llm
    )

    print("\nNEXT ACTION:", action)

    if not validate_action(
        action,
        task,
        history
    ):
        print("Invalid action:", action)
        break


    # DONE

    if action == "done":

        print("\nAgent Finished")
        break


    # EXTRACT PDF

    elif action == "extract_file":

        start = time.perf_counter()
        text = extract_file(file_path)
        print(
            f"file extraction: "
            f"{time.perf_counter() - start:.2f}s"
        )

        if not text.strip():

            print("file extraction failed: No text found.")
            break

        print("\nFile extracted successfully.")
        print(text)

        history += f"""
Action: extract_file

Result:
{text}
"""


    # RUN CODE


    elif action == "run_code":

        if not code:

            code = _clean_code(
                ask_llm(
                    f"""
Write a complete Python program for this request.

Request:
{request}

Rules:
- Return only Python code.
- Do not use markdown fences.
- Keep the code simple and correct.
""",
                    model
                )
            )

        print("GENERATED CODE:")
        print(code)

        final_prompt = f"""
You are a local Python programming assistant.

User request:
{request}

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



    # FIX CODE

    elif action == "fix_code":

        fix_prompt = f"""
You are a coding debugging agent.

Fix the following Python code.

CODE:
{code}

ERROR:
{code_error}

User request:
{request}

Rules:
- Fix the actual error shown in the traceback.
- Do not randomly change variable names.
- Do not rewrite working parts of the code.
- Keep the original user request.
- Return complete corrected Python code.
- The corrected code must be executable.
- Return ONLY the Python code.
"""

        fixed_code = ask_llm(
            fix_prompt,
            "qwen2.5:3b"
        ).strip()

        if fixed_code.startswith("```"):

            fixed_code = fixed_code.replace(
                "```python",
                ""
            )

            fixed_code = fixed_code.replace(
                "```",
                ""
            )

            fixed_code = fixed_code.strip()

        code = fixed_code

        print("\nFIXED CODE:")
        print(code)

        history += f"""
Action: fix_code

Fixed code:
{code}
"""


    # RAG SEARCH

    elif action == "search":

        if not text.strip():

            print(
                "Search failed: "
                "No document text available."
            )
            break
        start = time.perf_counter()
        chunks = chunk_text(text)

        embeddings = embedding(chunks)

        index = vector_store(embeddings)

        query_embedding = embedding([request])

        results = search(
            index,
            query_embedding,
            chunks,
            k=min(2, len(chunks))
        )

        context = "\n\n".join(results)
        print(
            f"RAG: "
            f"{time.perf_counter() - start:.2f}s"
        )
        print("\nRAG SEARCH COMPLETE")
        print(context)

        history += f"""
Action: search

Result:
{context}
"""


    # OCR

    elif action == "ocr":

        text = extract_text_from_image(image_path)

        if not text.strip():
            print("OCR failed: No text detected.")
            break

        print("\nOCR TEXT:")
        print(text)

        # Store OCR result
        context = text

        history += f"""
Action: ocr

Result:
{text}
"""

# ANSWER

    elif action == "answer":

        if task == "image":

            answer_prompt = f"""
You are a local AI assistant.

The image has already been processed using OCR.

OCR TEXT:
{text}

User question:
{request}

Explain the image in simple English.

Do not mention internal processing.
Do not invent information.

Return only the answer.
"""

    elif task == "document":

        answer_prompt = f"""
You are a local AI assistant.

Answer the user's question using the provided document context.

Context:
{context or text}

User question:
{request}

Rules:
- Answer directly.
- Do not invent information.
- Keep it concise.

Return only the answer.
"""

    else:

        answer_prompt = f"""
You are a private local AI assistant.

Answer the user's question directly.

User question:
{request}

Return only the answer.
"""

    final_prompt = answer_prompt

    history += (
        "\nAction: answer\n"
    )

    break
