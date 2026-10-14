# Dev server for citation-chat-ui
$env:LLM_MODE = "mock"
uvicorn backend.main:app --reload --port 8000
