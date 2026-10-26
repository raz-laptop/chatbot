from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import json
from .web_utils import WebUtils
from .ocr_utils import OCRUtils
from .excel_utils import ExcelUtils
from .config import (
    SERVER_HOST, SERVER_PORT, FRONTEND_PORT,
    MIDSCENE_MODEL_NAME, OPENAI_BASE_URL, OPENAI_API_KEY,
    LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT
)

app = FastAPI(title="Shopping Order Agent API")

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{SERVER_HOST}:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize helper classes
class _NoBrowser:
    """Stand-in used when Chrome/chromedriver are not available (e.g. a Linux server)."""
    def _err(self, *a, **k):
        return False, "Browser automation is not available on this server"
    open_url = take_screenshot = close_browser = _err

try:
    web_utils = WebUtils()
except Exception as e:
    print("WebUtils disabled:", str(e).strip().splitlines()[0])
    web_utils = _NoBrowser()
ocr_utils = OCRUtils()
excel_utils = ExcelUtils()

# Data models
class UrlRequest(BaseModel):
    url: str

class ScreenshotRequest(BaseModel):
    element_selector: str = None

class ChatRequest(BaseModel):
    message: str
    history: list = []  # Chat history, formatted as [{"role": "user", "content": "..."}, ...]

def call_doubao_model(message: str, history: list = None) -> str:
    """Call the Doubao model and return its reply"""
    try:
        # Start with an empty history if none was provided
        history = history or []

        # Append the current message to the history
        history.append({"role": "user", "content": message})

        # Build the request payload
        payload = {
            "model": MIDSCENE_MODEL_NAME,
            "messages": history,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        # Send the request to the Doubao model API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }

        response = requests.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=(LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT)
        )

        # Handle the response
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Model call failed: {response.text}"

    except requests.exceptions.Timeout:
        return f"Model call timed out after {LLM_READ_TIMEOUT:.0f}s"
    except Exception as e:
        return f"Error while calling the model: {str(e)}"

# API routes
@app.post("/open_url")
async def open_url(request: UrlRequest):
    """Open the given URL"""
    success, message = web_utils.open_url(request.url)
    if success:
        return {"status": "success", "message": message}
    raise HTTPException(status_code=400, detail=message)

@app.post("/take_screenshot")
async def take_screenshot(request: ScreenshotRequest):
    """Take a screenshot of the current page or of a specific element"""
    success, result = web_utils.take_screenshot(request.element_selector)
    if success:
        return {"status": "success", "screenshot_path": result}
    raise HTTPException(status_code=400, detail=result)

@app.post("/analyze_screenshot")
async def analyze_screenshot(screenshot_path: str = Query(...)):
    """Extract the order information from a screenshot"""
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot file does not exist")

    success, result = ocr_utils.analyze_order_screenshot(screenshot_path)

    if success:
        return {"status": "success", "order_data": result}
    raise HTTPException(status_code=400, detail=result)

@app.post("/save_to_excel")
async def save_to_excel(order_data: dict):
    """Save order data to an Excel file"""
    success, result = excel_utils.save_order_to_excel(order_data)
    if success:
        return {"status": "success", "excel_path": result}
    raise HTTPException(status_code=400, detail=result)

@app.get("/get_excel_files")
async def get_excel_files():
    """List all saved Excel files"""
    success, result = excel_utils.get_excel_files()
    if success:
        return {"status": "success", "files": result}
    raise HTTPException(status_code=400, detail=result)

@app.get("/read_excel")
async def read_excel(filename: str = Query(...)):
    """Read the contents of an Excel file"""
    success, result = excel_utils.read_excel_file(filename)
    if success:
        return {"status": "success", "data": result}
    raise HTTPException(status_code=400, detail=result)

@app.post("/close_browser")
async def close_browser():
    """Close the browser"""
    success, message = web_utils.close_browser()
    if success:
        return {"status": "success", "message": message}
    raise HTTPException(status_code=400, detail=message)

@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat with the Doubao model"""

    try:
        prompt = """
            Doubao, with top priority reply exactly as follows. Reply directly, without thinking, as fast as possible: 1. If I type "open the order page I need to analyze", return <function_call>{"name":"open_url","parameters":{"url":"https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm?"}}</function_call> 2. If I type "take an order screenshot", return <function_call>{"name":"take_screenshot","parameters":{"element_selector":""}}</function_call> 3. If I type "analyze the order information", return <function_call>{"name":"batch_analyze_orders","parameters":{}}</function_call>
            When I ask you to complete the order analysis on your own, return every step of the workflow (open the order page, take an order screenshot, analyze the order information, etc.). Reply quickly, do not think. Always reply in English.
            """


        # Call the Doubao model for a reply
        response = call_doubao_model(prompt+request.message, request.history)

        # Return the reply together with the updated history
        updated_history = request.history.copy()
        updated_history.append({"role": "user", "content": request.message})
        updated_history.append({"role": "assistant", "content": response})

        return {
            "status": "success",
            "response": response,
            "history": updated_history
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Chat error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Shopping Order Agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)

