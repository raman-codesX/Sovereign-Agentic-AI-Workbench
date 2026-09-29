1| # ASK — Sovereign Agentic AI Workbench
2| 
3| A private, local-first agentic AI workbench that handles general questions, documents, code, and images through a single interface.
4| 
5| ![Python](https://img.shields.io/badge/python-3.13.5-blue)
6| ![Flask](https://img.shields.io/badge/backend-Flask-black)
7| ![Ollama](https://img.shields.io/badge/LLM%20runtime-Ollama-informational)
8| 
9| ## Overview
10| 
11| **ASK (Agentic Sovereign Knowledge)** is a local AI workbench. It classifies each request and routes it to the right workflow: general Q&A, document analysis, Python coding, or image understanding.
12| 
13| ## Table of Contents
14| 
15| - [Features](#features)
16| - [Demo / Screenshots](#demo--screenshots)
17| - [Architecture](#architecture)
18| - [Tech Stack](#tech-stack)
19| - [Getting Started](#getting-started)
20| - [Usage](#usage)
21| - [Project Structure](#project-structure)
22| - [Privacy and Security](#privacy-and-security)
23| - [Roadmap](#roadmap)
24| - [Contributing](#contributing)
25| - [Contact](#contact)
26| 
27| ## Features
28| 
29| - **Automatic task routing:** Classifies each request as General, Document, Coding, or Image. You use one agent instead of switching tools.
30| - **Local LLM inference:** Runs Qwen 2.5 models (`qwen2.5:1.5b` and `qwen2.5:3b`) through Ollama. No remote LLM API is required.
31| - **Document understanding:** Extracts text from PDF, DOCX and TXT files, retrieves relevant passages, and answers questions locally.
32| - **Image understanding via OCR:** Extracts text from images with Tesseract and passes it to the local model.
33| - **Coding assistant:** Generates Python code and supports a local execution workflow through a sandbox tool.
34| - **Modular design:** Tools live in separate modules, so you can add new tools and routes.
35| 
36| ## Demo / Screenshots
37| 
38| Add screenshots to the `docs/screenshots/` folder and reference them here.
39| 
40| ![ASK Dashboard](docs/screenshots/dashboard.png)
41| *Main ASK workbench interface*
42| 
43| ![Document Workflow](docs/screenshots/document-workflow.png)
44| *Upload a file and ask questions about it locally*
45| 
46| ![Coding Workflow](docs/screenshots/coding-workflow.png)
47| *Generate and run Python code from the app interface*
48| 
49| > Example: save your screenshot files in `docs/screenshots/` as `.png` files, then update the paths above to match your filenames.
50| 
51| ## Architecture
52| 
53| ```text
54|                     ┌─────────────────────┐
55|                     │       Web UI        │
56|                     │    Local Browser    │
57|                     └──────────┬──────────┘
58|                                │
59|                                ▼
60|                     ┌─────────────────────┐
61|                     │      Flask API      │
62|                     │      ASK Agent      │
63|                     └──────────┬──────────┘
64|                                │
65|                                ▼
66|                     ┌─────────────────────┐
67|                     │     Task Router     │
68|                     │  General | Document │
69|                     │  Coding  | Image    │
70|                     └──────────┬──────────┘
71|                                │
72|               ┌────────────────┼────────────────┐
73|               │                │                │
74|               ▼                ▼                ▼
75|         ┌──────────┐     ┌──────────┐    ┌──────────┐
76|         │ Document │     │  Coding  │    │   OCR    │
77|         │  Tools   │     │ Sandbox  │    │  Tools   │
78|         └────┬─────┘     └──────────┘    └────┬─────┘
79|              │                                │
80|              └────────────────┬───────────────┘
81|                               ▼
82|                     ┌─────────────────────┐
83|                     │       Ollama        │
84|                     │  Local Qwen Models  │
85|                     └─────────────────────┘
86| ```
87| 
88| ### Routing
89| 
90| | Request type | Route |
91| |---|---|
92| | General questions | General |
93| | PDF / document questions | Document |
94| | Python programming requests | Coding |
95| | Image-based questions | Image |
96| 
97| ## Tech Stack
98| 
99| | Component | Technology |
100| |---|---|
101| | Backend | Flask |
102| | Local LLM runtime | Ollama |
103| | LLMs | Qwen 2.5 |
104| | Language | Python 3.13.5 |
105| | Document processing | PyPDF, python-docx |
106| | OCR | Tesseract, pytesseract |
107| | Image processing | Pillow |
108| | Embeddings | Sentence Transformers |
109| | Vector search | FAISS |
110| | Code execution | Python sandbox |
111| | Frontend | HTML, CSS, JavaScript |
112| 
113| ## Getting Started
114| 
115| ### Prerequisites
116| 
117| - Python 3.13.5
118| - [Ollama](https://ollama.com) installed and running
119| - At least one supported local model (see installation step 5)
120| - Tesseract OCR engine installed on your system (required by `pytesseract` for the image workflow)
121| - `git`
122| 
123| ### Installation
124| 
125| 1. Clone the repository.
126| 
127| ```bash
128|    git clone https://github.com/raman-codesX/Sovereign-Agentic-AI-Workbench.git
129|    cd Sovereign-Agentic-AI-Workbench
130| ```
131| 
132| 2. Create a virtual environment.
133| 
134| ```bash
135|    python -m venv venv
136| ```
137| 
138| 3. Activate it.
139| 
140|    Windows:
141| 
142| ```bash
143|    venv\Scripts\activate
144| ```
145| 
146|    macOS / Linux:
147| 
148| ```bash
149|    source venv/bin/activate
150| ```
151| 
152| 4. Install dependencies.
153| 
154| ```bash
155|    pip install -r requirements.txt
156| ```
157| 
158| 5. Pull the local models.
159| 
160| ```bash
161|    ollama pull qwen2.5:3b
162|    ollama pull qwen2.5:1.5b
163| ```
164| 
165| ### Run
166| 
167| Make sure Ollama is running, then start the app:
168| 
169| ```bash
170| python app.py
171| ```
172| 
173| Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.
174| 
175| ## Usage
176| 
177| ### General
178| 
179| ```text
180| User:  What is artificial intelligence?
181| ASK:   General route → local Qwen model → answer
182| ```
183| 
184| ### Document
185| 
186| ```text
187| User:  [Attach PDF] What is this document about?
188| ASK:   Document route → extract text → retrieve relevant content → generate answer locally
189| ```
190| 
191| ### Coding
192| 
193| ```text
194| User:  Write Python code to check whether a number is prime.
195| ASK:   Coding route → generate Python code → coding workflow → return answer
196| ```
197| 
198| ### Image
199| 
200| ```text
201| User:  [Attach image] What does this image mean?
202| ASK:   Image route → OCR → local AI processing → answer
203| ```
204| 
205| ## Project Structure
206| 
207| ```text
208| Sovereign-Agentic-AI-Workbench/
209| ├── agent.py                  # ASK agent and routing logic
210| ├── app.py                    # Flask application entry point
211| ├── requirements.txt          # Python dependencies
212| ├── templates/
213| │   └── index.html            # Web UI
214| └── tools/
215|     ├── document_tool.py      # Document workflow
216|     ├── docx_tool.py          # DOCX text extraction
217|     ├── embedding_tool.py     # Embeddings
218|     ├── file_router.py        # File handling and routing
219|     ├── file_tool.py          # File utilities
220|     ├── model_router.py       # Model selection (qwen2.5:3b / qwen2.5:1.5b)
221|     ├── ocr_tool.py           # OCR for images
222|     ├── pdf_tool.py           # PDF text extraction
223|     ├── retrieval_tool.py     # Content retrieval
224|     ├── sandbox_tool.py       # Python code execution sandbox
225|     ├── text_tool.py          # Text processing
226|     └── vector_store_tool.py  # Vector storage and search
227| ```
228| 
229| ## Privacy and Security
230| 
231| ASK sends inference requests to the locally running Ollama service instead of a remote LLM API. Sensitive files can stay within your local environment.
232| 
233| > **Note:** Local software alone does not guarantee zero network traffic. For a fully air-gapped deployment, you must also control the operating environment, dependencies, and models.
234| 
235| For production or sensitive deployments:
236| 
237| - Run the system on an isolated or controlled network.
238| - Keep sensitive documents outside the Git repository.
239| - Do not commit API keys, credentials, private documents, or user uploads.
240| - Restrict access to the local application.
241| - Review the code execution sandbox before running untrusted code.
242| - Download local models and dependencies before operating offline.
243| 
244| ## Roadmap
245| 
246| - Multimodal open-weight model support
247| - More document formats
248| - Improved retrieval and reranking
249| - Tool permission controls
250| - Better code sandbox isolation
251| - Enterprise authentication
252| - Audit logging
253| - Role-based access control
254| - Hardware-aware model routing
255| - Fully air-gapped deployment support
256| 
257| ## Contributing
258| 
259| Contributions are welcome.
260| 
261| 1. Fork the repository.
262| 2. Create a feature branch: `git checkout -b feature/your-feature`.
263| 3. Commit your changes with clear messages.
264| 4. Push the branch and open a pull request describing what you changed and why.
265| 
266| For large changes, open an issue first to discuss the approach. Never commit credentials, private documents, or user uploads.
267| 
268| ## Contact
269| 
270| - Author: Raman
271| - GitHub: [raman-codesX](https://github.com/raman-codesX)
272| - LinkedIn: [raman-x](https://www.linkedin.com/in/raman-x/)
273| - Email: [namansingh982150@gmail.com](mailto:namansingh982150@gmail.com)
274| 
275| ### Acknowledgments
276| 
277| - [Ollama](https://ollama.com)
278| - [Qwen 2.5](https://github.com/QwenLM/Qwen2.5)
279| 