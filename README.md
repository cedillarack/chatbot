# Chatbot

A minimal chatbot that answers questions about **Nishitha Degree College**
(Nizamabad) using only the content of a Markdown knowledge base file scraped
from [nishitha.org](https://nishitha.org). Built with FastAPI, LangChain, and
OpenRouter, deployed on Vercel.

Presented by Vaishnavi, Sri Gowrika, Rajasri, and Shivaraj.

## Project & team

- **Project name:** Chatbot
- **Team members:**
  - Vaishnavi
  - Sri Gowrika
  - Rajasri
  - Shivaraj
- **Purpose:** A web chatbot that answers questions about Nishitha Degree
  College (Nizamabad) from a curated knowledge base, so users get instant,
  accurate answers without browsing the college website.
- **Tech stack:** HTML/CSS/JS frontend, Python + FastAPI + LangChain backend,
  OpenRouter LLM API, Vercel hosting.

## UI features

- Dark / light theme toggle (persisted in `localStorage`, follows system preference by default)
- Responsive layout for desktop and mobile (`100dvh`, safe-area insets)
- Info dialog with project and team credits
- Conversation history capped at the last 20 entries (10 exchanges) to keep
  token usage and latency flat across long sessions

## Why Markdown for the knowledge base

`knowledge/data.md` is the single source of truth. It was extracted from
[nishitha.org](https://nishitha.org) and distilled into a compact fact file
(~5.7 KB) so the whole file fits in the model's context on every request —
no retrieval step, no vector database, fastest possible responses.

Markdown was chosen over text/PDF because:

- **No parsing dependencies.** PDF requires `pypdf`/`unstructured` and loses
  layout during extraction; Markdown is read as plain text in one line.
- **Small payload.** A few KB of Markdown fits directly in the system prompt —
  no vector database or embedding step needed.
- **Structure for free.** Headings and lists make content easy to organize and
  easy for the model to navigate.

Edit `knowledge/data.md` and redeploy to update the chatbot's answers.

## Project structure

```
chatbot/
├── api/index.py        # FastAPI app: /api/chat, /api/health
├── public/             # Static frontend (HTML/CSS/JS)
├── knowledge/data.md   # Knowledge base (edit this to change answers)
├── requirements.txt
├── vercel.json
├── .env.example
└── README.md
```

## How it works

1. The browser UI (`public/`) sends `POST /api/chat` with the user's message
   and conversation history.
2. The FastAPI backend loads `knowledge/data.md`, injects it into a LangChain
   system prompt, and calls the LLM through OpenRouter's OpenAI-compatible
   endpoint (`https://openrouter.ai/api/v1`).
3. The chain is `prompt | llm | StrOutputParser()`; the model is instructed to
   answer **only** from the knowledge base.
4. The reply is returned as JSON and rendered in the chat UI.

## Local development

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env            # then put your OpenRouter key in .env
uvicorn api.index:app --reload
```

Open http://127.0.0.1:8000

## Deploy to Vercel

1. Push the repo to GitHub.
2. On [vercel.com](https://vercel.com), import the repo (Vercel auto-detects
   `api/index.py` as a serverless function and `public/` as static files).
3. Add the environment variable `OPENROUTER_API_KEY` (from
   [openrouter.ai/keys](https://openrouter.ai/keys)) in **Settings → Environment
   Variables**.
4. Deploy.

Or use the CLI:

```bash
npm i -g vercel
vercel            # first deploy, link the project
vercel env add OPENROUTER_API_KEY
vercel --prod
```

## Configuration

| Variable              | Required | Default                | Description            |
| --------------------- | -------- | ---------------------- | ---------------------- |
| `OPENROUTER_API_KEY`  | yes      | —                      | OpenRouter API key     |
| `OPENROUTER_MODEL`    | no       | `z-ai/glm-4.5-flash`   | Any OpenRouter model ID |

## Endpoints

| Method | Path          | Body                                                        | Returns        |
| ------ | ------------- | ----------------------------------------------------------- | -------------- |
| GET    | `/api/health` | —                                                           | `{"status":"ok"}` |
| POST   | `/api/chat`   | `{"message": "string", "history": [{"role","content"}]}`    | `{"reply": "string"}` |

## Scaling notes

The knowledge base is injected whole into the prompt, which is the cheapest and
simplest approach for files up to roughly the model's context window. If
`data.md` grows large, switch to chunking + retrieval (e.g. LangChain
`RecursiveCharacterTextSplitter` with a vector store and
`ConversationalRetrievalChain`-style RAG).
