from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .models import IncomingMessage, AgentResponse
from .service import process_message
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

load_dotenv()

app = FastAPI(title="Agentic Honey-Pot API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")
    try:
        body = await request.body()
        logger.info(f"Body: {body.decode('utf-8')}")
    except Exception:
        logger.info("Body: Could not read body")
    
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API Key security
EXPECTED_API_KEY = os.getenv("HONEYPOT_API_KEY", "secret-key-123") 

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.post("/analyze", response_model=AgentResponse)
async def analyze_message(data: IncomingMessage, api_key: str = Depends(verify_api_key)):
    """
    Endpoint to analyze incoming messages, detect scams, and return agent responses.
    """
    try:
        response = process_message(data)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Agentic Honey-Pot is running. POST to /analyze"}

@app.post("/", response_model=AgentResponse)
async def root_analyze(data: IncomingMessage, api_key: str = Depends(verify_api_key)):
    """
    Fallback endpoint for root POST requests.
    """
    return await analyze_message(data, api_key)
