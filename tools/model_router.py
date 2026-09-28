# DETECT TASK

def detect_task(request, ask_llm=None, messages=None, attached_path=None):

    if messages is None:
        messages = []

    text = request.lower().strip()


    # CODING — HIGHEST PRIORITY


    coding_words = [
        "python",
        "code",
        "coding",
        "program",
        "script",
        "function",
        "debug",
        "error",
        "bug",
        "leetcode",
        "algorithm",
        "recursion",
        "recursive",
        "write code",
        "write a code",
        "generate code",
    ]

    if any(word in text for word in coding_words):
        return "coding"


    # ATTACHMENT

    if attached_path:

        path = str(attached_path).lower()

        if path.endswith((".jpg", ".jpeg", ".png", ".webp")):
            return "image"

        if path.endswith((".pdf", ".docx", ".txt", ".md")):
            return "document"


    # FOLLOW-UP

    previous_tasks = []

    for message in messages[-6:]:

        content = str(
            message.get("content", "")
        ).lower()

        if "routed: image" in content:
            previous_tasks.append("image")

        if "routed: document" in content:
            previous_tasks.append("document")

    follow_up_words = [
        "explain this",
        "explain it",
        "explain simple",
        "what does this mean",
        "what is this",
        "tell me more",
        "describe this",
    ]

    if any(word in text for word in follow_up_words):

        if "image" in previous_tasks:
            return "image"

        if "document" in previous_tasks:
            return "document"

    # GENERAL

    return "general"


# MODEL SELECTION

SIMPLE_MODEL = "qwen2.5:1.5b"
COMPLEX_MODEL = "qwen2.5:3b"

def select_model(task):
    if task in ("document", "image"):
        return COMPLEX_MODEL

    return SIMPLE_MODEL

# REQUEST UNDERSTANDING

def understand_request(
    user_request,
    task,
    ask_llm
):

    text = user_request.lower().strip()

    # -----------------------------
    # CODING
    # -----------------------------

    if task == "coding":

        explanation_words = [
            "explain",
            "describe",
            "what does",
            "what is",
            "how does",
            "how this works",
            "why",
            "understand"
        ]

        if any(
            word in text
            for word in explanation_words
        ):
            return ["answer"]

        return ["execute_code"]

    # -----------------------------
    # EVERYTHING ELSE
    # -----------------------------

    return ["answer"]


# NEXT ACTION


def get_next_action(
    user_request,
    task,
    goal,
    history
):

    history_lower = history.lower()

    # =========================
    # GENERAL
    # =========================

    if task == "general":

        if "action: answer" not in history_lower:
            return "answer"

        return "done"

    # =========================
    # IMAGE
    # =========================

    if task == "image":

        if "action: ocr" not in history_lower:
            return "ocr"

        if "action: answer" not in history_lower:
            return "answer"

        return "done"

    # =========================
    # DOCUMENT
    # =========================

    if task == "document":

        if "action: extract_file" not in history_lower:
            return "extract_file"

        if "action: search" not in history_lower:
            return "search"

        if "action: answer" not in history_lower:
            return "answer"

        return "done"

    # =========================
    # CODING
    # =========================

    if task == "coding":

        if "execute_code" in goal:

            if "action: run_code" not in history_lower:
                return "run_code"

            return "done"

        if "answer" in goal:

            if "action: answer" not in history_lower:
                return "answer"

            return "done"

    # =========================
    # UNKNOWN
    # =========================

    return "done"


# ACTION VALIDATION

def validate_action(
    action,
    task,
    history
):

    history_lower = history.lower()


    valid_actions = [
        "extract_file",
        "search",
        "answer",
        "ocr",
        "run_code",
        "fix_code",
        "done"
    ]


    if action not in valid_actions:
        return False


    # Extract PDF
    if action == "extract_pdf":

        return (
            "action: extract_pdf"
            not in history_lower
        )


    # OCR
    if action == "ocr":

        return (
            "action: ocr"
            not in history_lower
        )


    # Search
    if action == "search":

        return (
            "action: extract_file"
            in history_lower
            and
            "action: search"
            not in history_lower
        )


    # Answer
    if action == "answer":

        return (
            "action: answer"
            not in history_lower
        )


    # Fix code
    if action == "fix_code":

        return (
            "action: fix_code"
            not in history_lower
        )


    return True