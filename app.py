import os
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from llama_cpp import Llama
from functools import lru_cache
from typing import Optional
import asyncio
from dotenv import load_dotenv
from prompt import PromptBuilder
import json
load_dotenv()

app = FastAPI()

# Environment variables
MODEL_DIR = os.getenv("LLAMA_MODEL_DIR", "models")
DEFAULT_MODEL_NAME = os.getenv(
    "LLAMA_DEFAULT_MODEL_NAME", 
    "DeepSeek-R1-Strategy-Qwen-2.5-1.5b-Unstructured-To-Structured.Q6_K.gguf"
)
DEFAULT_CHAT_FORMAT = os.getenv(
    "CHAT_FORMAT", 
    None
)
HMAC_SECRET = os.getenv("HMAC_SECRET")
ROLE_FILE = os.getenv("ROLE_FILE", "./assets/roles/reply.txt") 
PROMPT_BUILDER = PromptBuilder(role=ROLE_FILE)

class PromptRequest(BaseModel):
    prompt: Optional[str] = None
    model: Optional[str] = None
    stop_tokens: Optional[list[str]] = None
    max_tokens: Optional[int] = None
    chat_format: Optional[str] = None
    role: Optional[str] = None
    chat_history: Optional[list[object]] = None
    article: Optional[str] = None

def verify_hmac(request: Request):
    if HMAC_SECRET:
        client_sig = request.headers.get("X-HMAC-SIGNATURE")
        if not client_sig:
            raise HTTPException(status_code=401, detail="Missing HMAC signature")

        body = request.scope.get("_cached_body")
        if body is None:
            raise HTTPException(status_code=400, detail="Internal error caching body")

        sig = hmac.new(
            HMAC_SECRET.encode(), msg=body, digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(sig, client_sig):
            raise HTTPException(status_code=403, detail="Invalid HMAC signature")

@lru_cache(maxsize=4)
def load_model(model_path, chat_format=None):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    llm = Llama(
        model_path=model_path, 
        chat_format=chat_format, 
        n_ctx=int(os.getenv("N_CTX", 2048)),
    )
    return llm

def parse_stop_tokens(raw_value: str) -> list[str]:
    if not raw_value:
        return []
    try:
        # Try parsing as JSON list
        tokens = json.loads(raw_value)
        if isinstance(tokens, list):
            return [str(t) for t in tokens]
    except json.JSONDecodeError:
        pass
    # Fallback: comma-separated
    return [token.strip() for token in raw_value.split(",") if token.strip()]

async def generate_async(llm, prompt, stop_tokens=None, max_tokens=None):
    loop = asyncio.get_running_loop()
    
    # Fallbacks to environment
    stop_tokens = stop_tokens if stop_tokens is not None else parse_stop_tokens(os.getenv("STOP_TOKENS", ""))
    max_tokens = max_tokens if max_tokens is not None else int(os.getenv("MAX_TOKENS", 512))
    print("MAX_TOKENS", max_tokens)

    kwargs = dict(
        max_tokens=max_tokens,
        temperature=float(os.getenv("TEMPERATURE", 0.8)),
        top_k=int(os.getenv("TOP_K", 40)),
        top_p=float(os.getenv("TOP_P", 0.95)),
        repeat_penalty=float(os.getenv("REPEAT_PENALTY", 1.1)),
        frequency_penalty=float(os.getenv("FREQUENCY_PENALTY", 0.0)),
        presence_penalty=float(os.getenv("PRESENCE_PENALTY", 0.0)),
        stop=stop_tokens or ["</s>"],
    )

    response = ""
    while not response:
        def f():
            r = llm(prompt, **kwargs)
            return r["choices"][0]["text"]
        response = await loop.run_in_executor(None, f)
        response = response.strip()
    print(response)
    return response

@app.middleware("http")
async def cache_body(request: Request, call_next):
    body = await request.body()
    request.scope["_cached_body"] = body
    return await call_next(request)

@app.post("/generate")
async def generate(request: Request, payload: PromptRequest, _=Depends(verify_hmac)):
    model_name = payload.model or DEFAULT_MODEL_NAME
    model_path = os.path.join(MODEL_DIR, model_name)
    chat_format = payload.chat_format or DEFAULT_CHAT_FORMAT

    try:
        llm = load_model(model_path, chat_format)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Build prompt dynamically if not given
    prompt = payload.prompt
    if not prompt:
        prompt_builder = PromptBuilder(payload.role) if payload.role else PROMPT_BUILDER
        prompt = prompt_builder.get_qwen_prompt(article=payload.article, chat_history=payload.chat_history)

    output = await generate_async(llm, prompt, payload.stop_tokens, payload.max_tokens)
    return JSONResponse({"response": output.strip()})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
