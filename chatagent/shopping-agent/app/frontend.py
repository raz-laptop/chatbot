import streamlit as st
import requests
import pandas as pd
import os
import json
from PIL import Image
from dotenv import load_dotenv
import uuid
import re
import time


# Load environment variables
load_dotenv()

from config import MIDSCENE_MODEL_NAME, SCREENSHOTS_DIR, EXCELS_DIR, OPENAI_BASE_URL,OPENAI_API_KEY,CHROME_DRIVER_PATH,CHROME_PATH

# Load environment variables
load_dotenv()

# Server settings
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 8501))

# Config file path
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "config.py")  # points at app/config.py


# Page settings
st.set_page_config(
    page_title="Shopping Order Agent",
    page_icon="🛒",
    layout="wide"
)

# Custom CSS - button height tweaks and scrolling styles
st.markdown("""
<style>
    .chat-container {
        position: relative;
        width: 100%;
        margin-top: 5px;
        display: flex;
        flex-direction: column;
        flex: 1;
    }
    .chat-input-area {
        display: flex;
        gap: 8px;
        align-items: center;
        width: 100%;
        box-sizing: border-box;
        padding: 10px;
        border-top: 1px solid #e0e0e0;
        background-color: #ffffff;
        border-radius: 0 0 8px 8px;
    }
    .chat-input {
        flex: 1;
        border-radius: 20px;
        padding: 10px 15px;
        border: 1px solid #ddd;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        height: 40px;
        box-sizing: border-box;
        background-color: rgba(255, 255, 255, 0.95);
    }
    .typing-indicator {
        color: #666;
        font-style: italic;
        font-size: 12px;
        margin-top: 5px;
        margin-left: 10px;
    }
    .dataframe-container {
        max-height: 500px;
        overflow-y: auto;
    }
    .left-panel {
        display: flex;
        flex-direction: column;
        height: 100%;
        flex: 1;
        padding-right: 10px;
    }
    .stApp {
        overflow: hidden;
    }
    /* Column container styles - the key change */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        /* Remove fixed heights and default scrolling from all columns */
        padding-top: 0 !important;  /* Tighten the button area height */
        padding-bottom: 0 !important; /* Tighten the button area height */
    }
    /* Only the left chat area scrolls */
    [data-testid="column"]:first-child {
        height: calc(100vh - 120px);
        overflow-y: auto;
    }
    /* Explicitly disable scrolling in the middle and right columns */
    [data-testid="column"]:nth-child(2),
    [data-testid="column"]:nth-child(3) {
        overflow-y: visible;
        height: auto;
    }
    .stSubheader {
        margin-bottom: 0.5rem !important;
    }
    .batch-results {
        margin-top: 20px;
        padding: 15px;
        background-color: #f9f9f9;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .order-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #fff;
    }
    .function-call {
        background-color: #e8f4fd;
        padding: 10px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.9em;
        margin: 10px 0;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    .function-result {
        background-color: #f0fdf4;
        padding: 10px;
        border-radius: 6px;
        margin: 10px 0;
        word-wrap: break-word;
    }
    .function-call-sequence {
        margin-left: 15px;
        padding-left: 10px;
        border-left: 2px solid #93c5fd;
        margin-bottom: 15px;
    }
    .selection-container {
        position: relative;
        width: 100%;
        margin: 10px 0;
    }
    .selection-image {
        width: 100%;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    .selection-box {
        position: absolute;
        border: 2px solid #4CAF50;
        background-color: rgba(76, 175, 80, 0.2);
        display: none;
    }
    .selection-buttons {
        margin-top: 10px;
        display: flex;
        gap: 10px;
    }
    .clear-chat-btn {
        margin-bottom: 10px;
        padding: 4px 8px;
        font-size: 0.8em;
        height: auto;
    }
    .chat-message {
        word-wrap: break-word;
        white-space: normal;
    }
    .step-indicator {
        font-size: 0.9em;
        color: #666;
        margin: 5px 0;
    }
    .config-form {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .config-input {
        margin-bottom: 15px;
    }
    /* Button area height tweaks */
    [data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important; /* Less space between columns */
        margin-bottom: 0.5rem !important; /* Less bottom margin for the whole block */
    }
    
    /* Button container margins */
    .element-container:has(.stButton) {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Button size */
    .stButton > button {
        padding: 0.25rem 0.5rem !important; /* Less button padding */
        height: 2.25rem !important; /* Lower button height */
        min-height: auto !important; /* Remove the minimum height */
    }
    
    /* Button text size and margins */
    .stButton > button [data-testid="stMarkdownContainer"] p {
        margin: 0 !important; /* Remove default paragraph margins */
        font-size: 0.875rem !important; /* Slightly smaller font */
    }
</style>
""", unsafe_allow_html=True)

# Load the Font Awesome icon library
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">', unsafe_allow_html=True)

# Custom JavaScript for area selection and clearing the input
st.markdown("""
<script>
// Global variables holding the selected area
let selection = {
    startX: 0,
    startY: 0,
    endX: 0,
    endY: 0,
    isSelecting: false
};

// Set up area selection
function initSelection() {
    const container = document.getElementById('selection-container');
    const image = document.getElementById('selection-image');
    const selectionBox = document.getElementById('selection-box');
    
    if (!container || !image || !selectionBox) return;
    
    // Click to start selecting
    image.addEventListener('mousedown', function(e) {
        const rect = image.getBoundingClientRect();
        selection.startX = e.clientX - rect.left;
        selection.startY = e.clientY - rect.top;
        selection.isSelecting = true;
        
        // Show the selection box
        selectionBox.style.display = 'block';
        selectionBox.style.left = selection.startX + 'px';
        selectionBox.style.top = selection.startY + 'px';
        selectionBox.style.width = '0px';
        selectionBox.style.height = '0px';
    });
    
    // Resize the selection as the mouse moves
    document.addEventListener('mousemove', function(e) {
        if (!selection.isSelecting) return;
        
        const rect = image.getBoundingClientRect();
        selection.endX = e.clientX - rect.left;
        selection.endY = e.clientY - rect.top;
        
        // Compute the selection box position and size
        const left = Math.min(selection.startX, selection.endX);
        const top = Math.min(selection.startY, selection.endY);
        const width = Math.abs(selection.endX - selection.startX);
        const height = Math.abs(selection.endY - selection.startY);
        
        // Apply to the selection box
        selectionBox.style.left = left + 'px';
        selectionBox.style.top = top + 'px';
        selectionBox.style.width = width + 'px';
        selectionBox.style.height = height + 'px';
    });
    
    // Finish selecting
    document.addEventListener('mouseup', function() {
        if (selection.isSelecting) {
            selection.isSelecting = false;
            
            // Compute the ratio relative to the image
            const imageWidth = image.offsetWidth;
            const imageHeight = image.offsetHeight;
            
            // Make sure the selection is valid
            if (Math.abs(selection.endX - selection.startX) > 10 && 
                Math.abs(selection.endY - selection.startY) > 10) {
                
                // Compute percentages relative to the original image
                const left = Math.min(selection.startX, selection.endX) / imageWidth * 100;
                const top = Math.min(selection.startY, selection.endY) / imageHeight * 100;
                const width = Math.abs(selection.endX - selection.startX) / imageWidth * 100;
                const height = Math.abs(selection.endY - selection.startY) / imageHeight * 100;
                
                // Store the selection in the hidden input
                document.getElementById('selection-coords').value = 
                    `${left},${top},${width},${height}`;
                
                // Show the selection info
                document.getElementById('selection-info').textContent = 
                    `Selected area: top-left (${Math.round(left)}%, ${Math.round(top)}%), size (${Math.round(width)}%, ${Math.round(height)}%)`;
            } else {
                // Selection too small; reset
                selectionBox.style.display = 'none';
                document.getElementById('selection-coords').value = '';
                document.getElementById('selection-info').textContent = 'No area selected';
            }
        }
    });
}

// Initialize once the page has loaded
document.addEventListener('DOMContentLoaded', function() {
    // Send the message on Enter
    setTimeout(function() {
        const chatInput = document.querySelector('input[placeholder="Type a message..."]');
        
        if (chatInput) {
            chatInput.setAttribute('autocomplete', 'off');
            chatInput.setAttribute('autocapitalize', 'off');
            chatInput.setAttribute('spellcheck', 'false');
            
            let isSubmitting = false;
            
            chatInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && this.value.trim() !== '' && !isSubmitting) {
                    e.preventDefault();
                    isSubmitting = true;
                    
                    const event = new Event('input', { bubbles: true });
                    this.dispatchEvent(event);
                    
                    const form = this.closest('form');
                    if (form) {
                        form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                    }
                    
                    // Clear the input
                    this.value = '';
                    
                    setTimeout(() => {
                        isSubmitting = false;
                    }, 1000);
                }
            });
        }
    }, 100);
    
    // Initialize area selection
    initSelection();
});
</script>
""", unsafe_allow_html=True)

# API base URL
API_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Page title
st.title("🛒 Smart Order Analysis Agent")

# Sidebar navigation
st.sidebar.title("Navigation")
selected_tab = st.sidebar.radio(
    "Choose a feature",
    ["Order Recognition", "Settings"]
)

# Initialize session state
if "is_thinking" not in st.session_state:
    st.session_state["is_thinking"] = False
if "screenshots" not in st.session_state:
    st.session_state["screenshots"] = []  # Screenshots taken so far, as [{id, path, timestamp}, ...]
if "batch_analysis_results" not in st.session_state:
    st.session_state["batch_analysis_results"] = []  # All recognized orders
if "order_data" not in st.session_state:
    st.session_state["order_data"] = None
if "current_order_data" not in st.session_state:
    st.session_state["current_order_data"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "submit_triggered" not in st.session_state:
    st.session_state["submit_triggered"] = False
if "last_submitted_message" not in st.session_state:
    st.session_state["last_submitted_message"] = ""
if "full_page_screenshot" not in st.session_state:
    st.session_state["full_page_screenshot"] = None  # Full-page screenshot used for area selection
if "selection_coords" not in st.session_state:
    st.session_state["selection_coords"] = ""  # Selected area coordinates
if "function_results" not in st.session_state:
    st.session_state["function_results"] = []  # Function call results
if "show_analysis_results" not in st.session_state:
    st.session_state["show_analysis_results"] = False  # Whether to show the analysis results
if "function_call_sequence" not in st.session_state:
    st.session_state["function_call_sequence"] = []  # Pending function call sequence
if "current_function_index" not in st.session_state:
    st.session_state["current_function_index"] = 0  # Index of the function being run
# State used to drive the UI from chat commands
if "url_input" not in st.session_state:
    st.session_state["url_input"] = ""  # URL input value
if "element_selector_input" not in st.session_state:
    st.session_state["element_selector_input"] = ""  # Element selector input value
if "trigger_open_url" not in st.session_state:
    st.session_state["trigger_open_url"] = False  # Trigger opening the URL
if "trigger_take_screenshot" not in st.session_state:
    st.session_state["trigger_take_screenshot"] = False  # Trigger a screenshot
if "trigger_batch_analysis" not in st.session_state:
    st.session_state["trigger_batch_analysis"] = False  # Trigger batch analysis
# Settings state
if "show_config_success" not in st.session_state:
    st.session_state["show_config_success"] = False  # Show the settings-saved message

# Helper: generate a unique ID
def generate_unique_id():
    return str(uuid.uuid4())[:8]

# Helper: remove a screenshot
def remove_screenshot(screenshot_id):
    st.session_state["screenshots"] = [
        s for s in st.session_state["screenshots"] 
        if s["id"] != screenshot_id
    ]
    # If the removed screenshot was analyzed, drop its results too
    st.session_state["batch_analysis_results"] = [
        r for r in st.session_state["batch_analysis_results"] 
        if r.get("screenshot_id") != screenshot_id
    ]

# Helper: clear the chat history
def clear_chat_history():
    st.session_state["chat_history"] = []
    st.session_state["function_results"] = []
    st.session_state["function_call_sequence"] = []
    st.session_state["current_function_index"] = 0
    st.success("Chat history cleared")

# Helper: save settings to config.py
def save_config_to_py(configs):
    """Save settings to config.py"""
    try:
        # Make sure config.py exists
        if not os.path.exists(CONFIG_FILE_PATH):
            st.error(f"Config file {CONFIG_FILE_PATH} does not exist")
            return False, f"Config file {CONFIG_FILE_PATH} does not exist"
        
        # Read the current config file
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update the values
        for i, line in enumerate(lines):
            # Skip blank lines and comments
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
                
            # Find the variable definition line
            for key, value in configs.items():
                if stripped_line.startswith(f"{key} ="):
                    # Quote string values
                    if isinstance(value, str) and not (value.startswith('"') and value.endswith('"')) and not (value.startswith("'") and value.endswith("'")):
                        value = f"'{value}'"
                    
                    # Keep comments
                    comment_index = line.find('#')
                    if comment_index != -1:
                        comment = line[comment_index:]
                        lines[i] = f"{key} = {value} {comment}\n"
                    else:
                        lines[i] = f"{key} = {value}\n"
        
        # Write the config file back
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True, "Settings saved"
    except Exception as e:
        return False, f"Save failed: {str(e)}"

# Helper: render the order analysis results
def display_analysis_results():
    """Render all order analysis results"""
    if not st.session_state["batch_analysis_results"]:
        return "No order analysis results to show"
    
    result_html = "<div class='batch-results'>"
    result_html += "<h3>All order analysis results</h3>"
    
    # Show the full information for each order
    for i, order in enumerate(st.session_state["batch_analysis_results"], 1):
        # Make sure order is a dict
        if not isinstance(order, dict):
            result_html += f"<p>Order #{i} has an invalid data format; skipped</p>"
            continue
            
        result_html += "<div class='order-card'>"
        result_html += f"<h4>Order #{i}</h4>"
        
        # Basic order information
        result_html += "<div style='display: flex; gap: 10px; margin-bottom: 10px;'>"
        result_html += "<div style='flex: 1;'>"
        result_html += f"<p><strong>Order ID:</strong> {order.get('Order ID', 'N/A')}</p>"
        result_html += f"<p><strong>Order date:</strong> {order.get('Order Date', 'N/A')}</p>"
        result_html += "</div>"
        result_html += "<div style='flex: 1;'>"
        result_html += f"<p><strong>Screenshot time:</strong> {order.get('screenshot_timestamp', 'N/A')}</p>"
        result_html += f"<p><strong>Total amount:</strong> {order.get('Total Amount', 'N/A')}</p>"
        result_html += "</div>"
        result_html += "</div>"
        
        # Item list
        result_html += "<p><strong>Items:</strong></p>"
        products = order.get('Items', [])
        
        if not isinstance(products, list) or not products:
            result_html += "<p>No valid item list recognized</p>"
        else:
            result_html += "<ul>"
            for product in products:
                if isinstance(product, dict):
                    product_name = product.get("Name", "Unknown name")
                    product_quantity = product.get("Quantity", "N/A")
                    product_price = product.get("Unit Price", "N/A")
                    result_html += f"<li>{product_name} - Quantity: {product_quantity}, Unit price: {product_price}</li>"
                else:
                    result_html += f"<li>{str(product)}</li>"
            result_html += "</ul>"
        
        result_html += "</div>"  # close the order card
    
    result_html += "</div>"  # close batch-results
    return result_html

# Function call handling
def extract_function_calls(response_text):
    """Extract all function calls from the response text"""
    # Find the function call markers
    start_tag = "<function_call>"
    end_tag = "</function_call>"
    
    function_calls = []
    start_idx = 0
    
    # Extract every function call
    while True:
        start_pos = response_text.find(start_tag, start_idx)
        if start_pos == -1:
            break
            
        end_pos = response_text.find(end_tag, start_pos)
        if end_pos == -1:
            break
            
        # Extract and parse the function call
        function_json = response_text[start_pos + len(start_tag):end_pos].strip()
        try:
            function_call = json.loads(function_json)
            function_calls.append(function_call)
        except json.JSONDecodeError:
            st.error(f"Failed to parse function call: {function_json}")
            
        start_idx = end_pos + len(end_tag)
    
    return function_calls if function_calls else None

def execute_function_call(function_call):
    """Run one function call, return its result and update the UI state"""
    if not function_call or "name" not in function_call:
        return {"status": "error", "message": "Invalid function call"}
    
    function_name = function_call["name"]
    parameters = function_call.get("parameters", {})
    result = {"status": "error", "message": f"Function not found: {function_name}"}
    
    # Open a page - drives the UI
    if function_name == "open_url":
        url = parameters.get("url", "")
        if not url:
            return {"status": "error", "message": "Missing URL parameter"}
        
        # Update the UI: fill in the URL and trigger the click
        st.session_state["url_input"] = url
        st.session_state["trigger_open_url"] = True
        
        # Wait briefly for the UI to update
        time.sleep(1)
            
        try:
            response = requests.post(
                f"{API_BASE_URL}/open_url",
                json={"url": url}
            )
            if response.status_code == 200:
                result = {"status": "success", "message": "Page opened", "data": {"url": url}}
            else:
                result = {"status": "error", "message": f"Failed: {response.json().get('detail')}"}
        except Exception as e:
            result = {"status": "error", "message": f"Error: {str(e)}"}
        
        # Reset the trigger
        st.session_state["trigger_open_url"] = False
    
    # Close the browser
    elif function_name == "close_browser":
        try:
            response = requests.post(f"{API_BASE_URL}/close_browser")
            if response.status_code == 200:
                result = {"status": "success", "message": "Browser closed"}
            else:
                result = {"status": "error", "message": f"Failed: {response.json().get('detail')}"}
        except Exception as e:
            result = {"status": "error", "message": f"Error: {str(e)}"}
    
    # Single screenshot - drives the UI
    elif function_name == "take_screenshot":
        element_selector = parameters.get("element_selector", "")
        
        # Update the UI: fill in the selector and trigger the screenshot
        st.session_state["element_selector_input"] = element_selector
        st.session_state["trigger_take_screenshot"] = True
        
        # Wait briefly for the UI to update
        time.sleep(1)
            
        try:
            response = requests.post(
                f"{API_BASE_URL}/take_screenshot",
                json={"element_selector": element_selector}
            )
            if response.status_code == 200:
                screenshot_path = response.json().get("screenshot_path")
                
                # Generate a unique ID and timestamp
                screenshot_id = generate_unique_id()
                timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add to the screenshot list
                st.session_state["screenshots"].append({
                    "id": screenshot_id,
                    "path": screenshot_path,
                    "timestamp": timestamp
                })
                
                result = {
                    "status": "success", 
                    "message": f"Screenshot taken! {len(st.session_state['screenshots'])} screenshot(s) so far",
                    "data": {
                        "screenshot_id": screenshot_id,
                        "path": screenshot_path
                    }
                }
            else:
                result = {"status": "error", "message": f"Failed: {response.json().get('detail')}"}
        except Exception as e:
            result = {"status": "error", "message": f"Error: {str(e)}"}
        
        # Reset the trigger
        st.session_state["trigger_take_screenshot"] = False
    
    # Take a full-page screenshot
    elif function_name == "take_fullpage_screenshot":
        try:
            response = requests.post(
                f"{API_BASE_URL}/take_fullpage_screenshot"
            )
            if response.status_code == 200:
                screenshot_path = response.json().get("screenshot_path")
                st.session_state["full_page_screenshot"] = screenshot_path
                st.session_state["selection_coords"] = ""
                
                result = {
                    "status": "success", 
                    "message": "Full-page screenshot captured",
                    "data": {"path": screenshot_path}
                }
            else:
                result = {"status": "error", "message": f"Failed: {response.json().get('detail')}"}
        except Exception as e:
            result = {"status": "error", "message": f"Error: {str(e)}"}
    
    # Capture the selected area
    elif function_name == "take_selected_screenshot":
        coords = parameters.get("coordinates")
        if not coords or len(coords) != 4:
            return {"status": "error", "message": "Missing or invalid coordinates"}
            
        if not st.session_state["full_page_screenshot"]:
            return {"status": "error", "message": "Take a full-page screenshot first"}
            
        try:
            left, top, width, height = coords
            
            response = requests.post(
                f"{API_BASE_URL}/take_selected_screenshot",
                json={
                    "fullpage_screenshot_path": st.session_state["full_page_screenshot"],
                    "region": {
                        "left": float(left),
                        "top": float(top),
                        "width": float(width),
                        "height": float(height)
                    }
                }
            )
            
            if response.status_code == 200:
                screenshot_path = response.json().get("screenshot_path")
                
                # Generate a unique ID and timestamp
                screenshot_id = generate_unique_id()
                timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Add to the screenshot list
                st.session_state["screenshots"].append({
                    "id": screenshot_id,
                    "path": screenshot_path,
                    "timestamp": timestamp
                })
                
                result = {
                    "status": "success", 
                    "message": f"Screenshot taken! {len(st.session_state['screenshots'])} screenshot(s) so far",
                    "data": {
                        "screenshot_id": screenshot_id,
                        "path": screenshot_path
                    }
                }
            else:
                result = {"status": "error", "message": f"Failed: {response.json().get('detail')}"}
        except Exception as e:
            result = {"status": "error", "message": f"Error: {str(e)}"}
    
    # Batch analyze orders - drives the UI
    elif function_name == "batch_analyze_orders":
        if not st.session_state["screenshots"]:
            return {"status": "error", "message": "Take at least one order screenshot first"}
        
        # Update the UI: trigger batch analysis
        st.session_state["trigger_batch_analysis"] = True
        
        # Wait briefly for the UI to update
        time.sleep(1)
            
        try:
            # Clear the previous analysis results
            st.session_state["batch_analysis_results"] = []
            
            # Analyze each screenshot and keep every order
            success_count = 0
            for idx, screenshot in enumerate(st.session_state["screenshots"], 1):
                response = requests.post(
                    f"{API_BASE_URL}/analyze_screenshot",
                    params={"screenshot_path": screenshot["path"]}
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    # Make sure order_data is a dict
                    if isinstance(result_data.get("order_data"), dict):
                        order_data = result_data.get("order_data")
                        # Attach the screenshot ID for reference
                        order_data["screenshot_id"] = screenshot["id"]
                        order_data["screenshot_timestamp"] = screenshot["timestamp"]
                        st.session_state["batch_analysis_results"].append(order_data)
                        success_count += 1
                    elif isinstance(result_data.get("order_data"), list):
                        # If an array of orders came back, add each one
                        for item in result_data.get("order_data", []):
                            if isinstance(item, dict):
                                item["screenshot_id"] = screenshot["id"]
                                item["screenshot_timestamp"] = screenshot["timestamp"]
                                st.session_state["batch_analysis_results"].append(item)
                                success_count += 1
                    else:
                        st.warning(f"Screenshot {idx} returned an unsupported data format")
                else:
                    error_msg = f"Analysis failed: {response.json().get('detail')}"
                    st.warning(f"Screenshot {idx} analysis failed: {error_msg}")
            
            # Build the results HTML
            results_html = display_analysis_results()
            
            result = {
                "status": "success", 
                "message": f"Batch analysis done! {success_count} screenshot(s) analyzed",
                "data": {
                    "total_analyzed": len(st.session_state["screenshots"]),
                    "success_count": success_count,
                    "results_html": results_html
                }
            }
            
            # Show the results
            st.session_state["show_analysis_results"] = True
            
        except Exception as e:
            result = {"status": "error", "message": f"Error during analysis: {str(e)}"}
        
        # Reset the trigger
        st.session_state["trigger_batch_analysis"] = False
    
    # Clear all data
    elif function_name == "clear_all_data":
        st.session_state["screenshots"] = []
        st.session_state["batch_analysis_results"] = []
        st.session_state["full_page_screenshot"] = None
        st.session_state["selection_coords"] = ""
        st.session_state["show_analysis_results"] = False
        st.session_state["url_input"] = ""
        st.session_state["element_selector_input"] = ""
        result = {"status": "success", "message": "All screenshots and analysis results cleared"}
    
    # Record the function call result
    func_result_entry = {
        "function": function_name,
        "parameters": parameters,
        "result": result,
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state["function_results"].append(func_result_entry)
    
    return result, func_result_entry

def process_function_sequence():
    """Run the function call sequence step by step until it is done"""
    # Nothing to run; return
    if not st.session_state["function_call_sequence"]:
        st.session_state["is_thinking"] = False
        st.session_state["current_function_index"] = 0
        return True
        
    # Get the function to run now
    current_index = st.session_state["current_function_index"]
    if current_index >= len(st.session_state["function_call_sequence"]):
        # All functions done; get the final AI reply
        get_final_ai_response()
        
        # Reset state
        st.session_state["is_thinking"] = False
        st.session_state["current_function_index"] = 0
        st.session_state["function_call_sequence"] = []
        return True
    
    # Show the current step
    st.markdown(f'''
    <div class="step-indicator">
        <i class="fas fa-cog fa-spin"></i> Running step {current_index + 1}/{len(st.session_state["function_call_sequence"])}: 
        {st.session_state["function_call_sequence"][current_index]["name"]}
    </div>
    ''', unsafe_allow_html=True)
    
    # Run the current function
    current_function = st.session_state["function_call_sequence"][current_index]
    function_result, func_result_entry = execute_function_call(current_function)
    
    # Show the current step's result
    status = "succeeded" if function_result["status"] == "success" else "failed"
    status_color = "#10b981" if function_result["status"] == "success" else "#ef4444"
    st.markdown(f'''
    <div style="
        text-align: left;
        margin-bottom: 8px;
        padding-left: 10px;
    ">
        <div class="function-result">
            <strong style="color: {status_color};">Step {current_index + 1}/{len(st.session_state["function_call_sequence"])}: {current_function["name"]} {status}</strong>
            <br>{function_result["message"]}
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Pause between steps
    st.markdown(f'''
    <div class="step-indicator">
        <i class="fas fa-clock"></i> Waiting 3 seconds before the next step...
    </div>
    ''', unsafe_allow_html=True)
    time.sleep(3)  # wait 3 seconds
    
    # Advance the index
    st.session_state["current_function_index"] += 1
    
    # Automatically trigger the next function
    st.experimental_rerun()

def get_final_ai_response():
    """Get the final AI reply after all functions have run"""
    try:
        # Build the request with all function results
        functions = [
            {
                "name": "open_url",
                "description": "Open the given URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL of the page to open"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "close_browser",
                "description": "Close the browser",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "take_screenshot",
                "description": "Take a screenshot of the current page or a specific element",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element_selector": {
                            "type": "string",
                            "description": "CSS selector of the element to capture; leave empty for the full screen"
                        }
                    }
                }
            },
            {
                "name": "take_fullpage_screenshot",
                "description": "Take a full-page screenshot of the current page, for selecting an area manually afterwards",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "take_selected_screenshot",
                "description": "Capture the previously selected area",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coordinates": {
                            "type": "array",
                            "description": "Area coordinates as [left, top, width, height], in percent",
                            "items": {"type": "number"}
                        }
                    },
                    "required": ["coordinates"]
                }
            },
            {
                "name": "batch_analyze_orders",
                "description": "Batch analyze all captured order screenshots and show detailed results",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "clear_all_data",
                "description": "Clear all screenshots and analysis results",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        # Summarize all function results
        execution_summary = {
            "total_steps": len(st.session_state["function_results"]),
            "success_steps": sum(1 for res in st.session_state["function_results"] if res["result"]["status"] == "success"),
            "last_step": st.session_state["function_results"][-1] if st.session_state["function_results"] else None
        }
        
        chat_request = {
            "message": f"All operations are done. Results: {json.dumps(execution_summary, ensure_ascii=False)}",
            "history": st.session_state["chat_history"],
            "functions": functions,
            "function_call": "auto",
            "execution_summary": execution_summary
        }
        
        # Call the API for the final reply
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=chat_request,
            timeout=60  # request timeout
        )
        
        # Handle the response
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                assistant_response = result["response"]
                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": assistant_response
                })
            else:
                error_msg = f"Processing failed: {result.get('detail', 'Unknown error')}"
                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": error_msg
                })
        else:
            error_detail = response.json().get("detail", "Unknown error")
            error_msg = f"API call failed: {error_detail}"
            st.session_state["chat_history"].append({
                "role": "assistant",
                "content": error_msg
            })
        
    except Exception as e:
        error_msg = f"Communication error: {str(e)}"
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": error_msg
        })

def stacked_columns(spec):
    """Stand-in for nested st.columns: streamlit 1.10 cannot nest columns, so stack containers."""
    count = spec if isinstance(spec, int) else len(spec)
    return [st.container() for _ in range(count)]


# Three-column layout proportions
left_col, middle_col, right_col = st.columns([0.8, 1.2, 1.2])

# Left: chat area with message sending and function calls
with left_col:
    st.markdown('<div class="left-panel">', unsafe_allow_html=True)
    
    if selected_tab == "Order Recognition":
        st.subheader("💬 Order Assistant")
        st.caption("Control the order workflow with natural-language commands")
        
        # Clear chat history button
        if st.button("Clear chat history", key="clear_chat"):
            clear_chat_history()
        
        # Show the chat history
        if st.session_state["chat_history"]:
            for msg in st.session_state["chat_history"]:
                if msg["role"] == "user":
                    # User message style - with word wrap
                    st.markdown(f'''
                    <div style="
                        text-align: right;
                        margin-bottom: 8px;
                        padding-right: 10px;
                    ">
                        <div style="
                            display: inline-block;
                            background-color: #4285f4;
                            color: white;
                            padding: 8px 12px;
                            border-radius: 18px 18px 4px 18px;
                            max-width: 80%;
                            text-align: left;
                        " class="chat-message">
                            {msg["content"]}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    # Assistant message style - with word wrap
                    content = msg["content"]
                    
                    # Check for function calls
                    function_calls = extract_function_calls(content)
                    
                    # Format function calls for display
                    if function_calls:
                        # Extract the plain-text part
                        text_part = content
                        for call in function_calls:
                            text_part = text_part.replace(
                                f"<function_call>{json.dumps(call)}</function_call>", 
                                ""
                            ).strip()
                        
                        st.markdown(f'''
                        <div style="
                            text-align: left;
                            margin-bottom: 8px;
                            padding-left: 10px;
                        ">
                            <div style="
                                display: inline-block;
                                background-color: #e0e0e0;
                                color: #333;
                                padding: 8px 12px;
                                border-radius: 18px 18px 18px 4px;
                                max-width: 80%;
                            " class="chat-message">
                                {text_part}
                            </div>
                            <div>
                                <strong>Operation sequence:</strong>
                                <div class="function-call-sequence">
                        ''', unsafe_allow_html=True)
                        
                        # Show each function call
                        for i, call in enumerate(function_calls):
                            st.markdown(f'''
                                <div class="function-call">
                                    <strong>Step {i+1}:</strong> {call["name"]}
                                    <br>
                                    <strong>Parameters:</strong> {json.dumps(call.get("parameters", {}), ensure_ascii=False)}
                                </div>
                            ''', unsafe_allow_html=True)
                        
                        st.markdown(f'''
                                </div>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        # Plain reply - with word wrap
                        st.markdown(f'''
                        <div style="
                            text-align: left;
                            margin-bottom: 8px;
                            padding-left: 10px;
                        ">
                            <div style="
                                display: inline-block;
                                background-color: #e0e0e0;
                                color: #333;
                                padding: 8px 12px;
                                border-radius: 18px 18px 18px 4px;
                                max-width: 80%;
                            " class="chat-message">
                                {content}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
        else:
            # Empty state
            st.markdown('''
            <div style="text-align: center; color: #999; padding: 20px 0;">
                No messages yet. Start a conversation!<br>
                Example: "Open JD.com and capture the order page"
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # close the chat history container
        
        # Message input and send area
        st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
        
        # Input and send button side by side
        input_col, button_col = stacked_columns([8, 2])
        
        with input_col:
            user_input = st.text_input(
                "",
                value="",
                placeholder="Type a message...",
                key="chat_input",
                autocomplete="off"
            )
        
        with button_col:
            send_button = st.button(
                "Send",
                disabled=st.session_state["is_thinking"]  # disabled while thinking
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Loading state
        if st.session_state["is_thinking"]:
            if st.session_state["function_call_sequence"] and st.session_state["current_function_index"] > 0:
                # Show function progress
                total = len(st.session_state["function_call_sequence"])
                current = st.session_state["current_function_index"]
                st.markdown(f'''
                <div class="typing-indicator">
                    <i class="fas fa-circle-notch fa-spin"></i> Running step {current}/{total}...
                </div>
                ''', unsafe_allow_html=True)
            else:
                # Show the thinking state
                st.markdown(f'''
                <div class="typing-indicator">
                    <i class="fas fa-circle-notch fa-spin"></i> Processing...
                </div>
                ''', unsafe_allow_html=True)
        
        # Send logic (button click or Enter)
        if (
            (user_input.strip() and send_button) or  # sent with the button
            (user_input.strip() and not st.session_state["is_thinking"] and 
             user_input.strip() != st.session_state.get("last_submitted_message", ""))  # sent with Enter
        ):
            # Save and clear the input
            st.session_state["last_submitted_message"] = user_input.strip()
            st.session_state["chat_history"].append({
                "role": "user",
                "content": user_input.strip()
            })
            st.session_state["is_thinking"] = True
            st.session_state["function_call_sequence"] = []
            st.session_state["current_function_index"] = 0
            
            # Rerun to show the new message
            st.experimental_rerun()
        
        # Handle the AI reply and function calls
        if st.session_state["is_thinking"]:
            # Check for a pending function sequence
            if st.session_state["function_call_sequence"]:
                # Run the function sequence (triggers the next function)
                process_function_sequence()
            else:
                # First AI reply
                with st.spinner(""):  # hide the default spinner; use the custom style
                    try:
                        # Build the request, including the function definitions
                        functions = [
                            {
                                "name": "open_url",
                                "description": "Open the given URL",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "url": {
                                            "type": "string",
                                            "description": "URL of the page to open"
                                        }
                                    },
                                    "required": ["url"]
                                }
                            },
                            {
                                "name": "close_browser",
                                "description": "Close the browser",
                                "parameters": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "take_screenshot",
                                "description": "Take a screenshot of the current page or a specific element",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "element_selector": {
                                            "type": "string",
                                            "description": "CSS selector of the element to capture; leave empty for the full screen"
                                        }
                                    }
                                }
                            },
                            {
                                "name": "take_fullpage_screenshot",
                                "description": "Take a full-page screenshot of the current page, for selecting an area manually afterwards",
                                "parameters": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "take_selected_screenshot",
                                "description": "Capture the previously selected area",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "coordinates": {
                                            "type": "array",
                                            "description": "Area coordinates as [left, top, width, height], in percent",
                                            "items": {"type": "number"}
                                        }
                                    },
                                    "required": ["coordinates"]
                                }
                            },
                            {
                                "name": "batch_analyze_orders",
                                "description": "Batch analyze all captured order screenshots and show detailed results",
                                "parameters": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "clear_all_data",
                                "description": "Clear all screenshots and analysis results",
                                "parameters": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        ]
                        
                        chat_request = {
                            "message": st.session_state["last_submitted_message"],
                            "history": st.session_state["chat_history"],
                            "functions": functions,
                            "function_call": "auto"
                        }
                        
                        # Call the API
                        response = requests.post(
                            f"{API_BASE_URL}/chat",
                            json=chat_request,
                            timeout=60  # request timeout
                        )
                        
                        # Handle the response
                        if response.status_code == 200:
                            result = response.json()
                            if result["status"] == "success":
                                assistant_response = result["response"]
                                st.session_state["chat_history"].append({
                                    "role": "assistant",
                                    "content": assistant_response
                                })
                                
                                # Check for function calls and run them
                                function_calls = extract_function_calls(assistant_response)
                                if function_calls:
                                    st.session_state["function_call_sequence"] = function_calls
                                    st.session_state["current_function_index"] = 0
                                    st.experimental_rerun()
                                else:
                                    st.session_state["is_thinking"] = False
                            else:
                                error_msg = f"Processing failed: {result.get('detail', 'Unknown error')}"
                                st.session_state["chat_history"].append({
                                    "role": "assistant",
                                    "content": error_msg
                                    })
                                st.session_state["is_thinking"] = False
                        else:
                            error_detail = response.json().get("detail", "Unknown error")
                            error_msg = f"API call failed: {error_detail}"
                            st.session_state["chat_history"].append({
                                "role": "assistant",
                                "content": error_msg
                            })
                            st.session_state["is_thinking"] = False
                        
                    except Exception as e:
                        error_msg = f"Communication error: {str(e)}"
                        st.session_state["chat_history"].append({
                            "role": "assistant",
                            "content": error_msg
                        })
                        st.session_state["is_thinking"] = False
                    finally:
                        if not st.session_state["function_call_sequence"]:
                            st.experimental_rerun()
    else:
        pass
    
    st.markdown('</div>', unsafe_allow_html=True)

# Middle: actions area (compact layout, fixes empty labels)
with middle_col:
    if selected_tab == "Order Recognition":
        st.subheader("Order Recognition")
        
        with st.expander("User guide", expanded=False):
            st.write("""
            1. Enter the order page URL and open the page
            2. Choose a screenshot method:
               - Option 1: automatic screenshot with an element selector
               - Option 2: manually select an area (recommended)
            3. Capture several order areas
            4. Click "Batch analyze orders" to process all screenshots
            5. Review and save all order results below
            
            You can also do all of this by sending commands in the chat on the left, for example:
            - "Open https://example.com/orders for me"
            - "Capture the order area of the current page"
            - "Analyze all order screenshots"
            """)
        
        # URL input, driven by chat commands
        url = st.text_input(
            "Enter the order URL", 
            value=st.session_state["url_input"],
            autocomplete="off",
            key="url_input_field"
        )
        # Sync to session_state
        st.session_state["url_input"] = url
        
        col1, col2 = stacked_columns(2)
        with col1:
            # Open page button, can be triggered automatically
            open_url_clicked = st.button("Open page") or st.session_state["trigger_open_url"]
            if open_url_clicked and url:
                with st.spinner("Opening..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/open_url",
                            json={"url": url}
                        )
                        if response.status_code == 200:
                            st.success("Page opened")
                        else:
                            st.error(f"Failed: {response.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("Close browser"):
                with st.spinner("Closing..."):
                    try:
                        response = requests.post(f"{API_BASE_URL}/close_browser")
                        if response.status_code == 200:
                            st.success("Browser closed")
                        else:
                            st.error(f"Failed: {response.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # Screenshot method
        screenshot_method = st.radio(
            "Order screenshot area",
            ["Full screen (default)", "Select area manually"],
            horizontal=True
        )
        
        # Element selector method
        if screenshot_method == "Full screen (default)":
            # Element selector input, driven by chat commands
            element_selector = st.text_input(
                "CSS element selector",
                value=st.session_state["element_selector_input"],
                autocomplete="off",
                placeholder="Optional: enter a CSS selector (e.g. #order-container)",
                key="element_selector_field"
            )
            # Sync to session_state
            st.session_state["element_selector_input"] = element_selector
            
            # Screenshot button, can be triggered automatically
            take_screenshot_clicked = st.button("Take screenshot") or st.session_state["trigger_take_screenshot"]
            if take_screenshot_clicked:
                with st.spinner("Taking screenshot..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/take_screenshot",
                            json={"element_selector": element_selector}
                        )
                        if response.status_code == 200:
                            screenshot_path = response.json().get("screenshot_path")
                            
                            # Generate a unique ID and timestamp
                            screenshot_id = generate_unique_id()
                            timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Add to the screenshot list
                            st.session_state["screenshots"].append({
                                "id": screenshot_id,
                                "path": screenshot_path,
                                "timestamp": timestamp
                            })
                            
                            st.success(f"Screenshot taken! {len(st.session_state['screenshots'])} screenshot(s) so far")
                            
                            # Show the latest screenshot
                            if os.path.exists(screenshot_path):
                                image = Image.open(screenshot_path)
                                st.image(image, caption="Screenshot", use_column_width=True)
                        else:
                            st.error(f"Failed: {response.json().get('detail')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # Manual area selection method
        else:
            col_a, col_b = stacked_columns(2)
            with col_a:
                if st.button("Take full-page screenshot"):
                    with st.spinner("Taking full-page screenshot..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/take_fullpage_screenshot"
                            )
                            if response.status_code == 200:
                                screenshot_path = response.json().get("screenshot_path")
                                st.session_state["full_page_screenshot"] = screenshot_path
                                st.session_state["selection_coords"] = ""
                                st.success("Full-page screenshot captured. Select an area below")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed: {response.json().get('detail')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            with col_b:
                if st.button("Reset selection"):
                    st.session_state["selection_coords"] = ""
                    st.success("Selection reset")
        
        # Show the full-page screenshot and allow selecting an area
        if st.session_state["full_page_screenshot"] and os.path.exists(st.session_state["full_page_screenshot"]):
            st.markdown("### Select the screenshot area")
            st.write("Click and drag on the image below to select the area to capture")
            
            # Hidden input holding the selected coordinates
            st.markdown(f'''
            <input type="hidden" id="selection-coords" value="{st.session_state['selection_coords']}">
            <div id="selection-container" class="selection-container">
                <img id="selection-image" class="selection-image" src="data:image/png;base64,{st.session_state['full_page_screenshot']}" alt="Full-page screenshot">
                <div id="selection-box" class="selection-box"></div>
            </div>
            <p id="selection-info" class="text-sm text-gray-600">
                { "Area selected" if st.session_state['selection_coords'] else "No area selected" }
            </p>
            ''', unsafe_allow_html=True)
            
            # Confirm the selection and capture it
            if st.button("Capture selected area"):
                if not st.session_state["selection_coords"]:
                    st.warning("Select a screenshot area first")
                else:
                    with st.spinner("Capturing selected area..."):
                        try:
                            # Parse the coordinates
                            left, top, width, height = st.session_state["selection_coords"].split(',')
                            
                            response = requests.post(
                                f"{API_BASE_URL}/take_selected_screenshot",
                                json={
                                    "fullpage_screenshot_path": st.session_state["full_page_screenshot"],
                                    "region": {
                                        "left": float(left),
                                        "top": float(top),
                                        "width": float(width),
                                        "height": float(height)
                                    }
                                }
                            )
                            
                            if response.status_code == 200:
                                screenshot_path = response.json().get("screenshot_path")
                                
                                # Generate a unique ID and timestamp
                                screenshot_id = generate_unique_id()
                                timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                                
                                # Add to the screenshot list
                                st.session_state["screenshots"].append({
                                    "id": screenshot_id,
                                    "path": screenshot_path,
                                    "timestamp": timestamp
                                })
                                
                                st.success(f"Screenshot taken! {len(st.session_state['screenshots'])} screenshot(s) so far")
                                
                                # Show the captured area
                                if os.path.exists(screenshot_path):
                                    image = Image.open(screenshot_path)
                                    st.image(image, caption="Captured area", use_column_width=True)
                            else:
                                st.error(f"Failed: {response.json().get('detail')}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # Batch analyze button, can be triggered automatically
        batch_analyze_clicked = st.button("Batch analyze orders") or st.session_state["trigger_batch_analysis"]
        if batch_analyze_clicked:
            if not st.session_state["screenshots"]:
                st.warning("Take at least one order screenshot first")
            else:
                with st.spinner(f"Analyzing {len(st.session_state['screenshots'])} screenshot(s)..."):
                    try:
                        # Clear the previous analysis results
                        st.session_state["batch_analysis_results"] = []
                        
                        # Analyze each screenshot and keep every order
                        success_count = 0
                        for idx, screenshot in enumerate(st.session_state["screenshots"], 1):
                            with st.spinner(f"Analyzing screenshot {idx}/{len(st.session_state['screenshots'])}..."):
                                response = requests.post(
                                    f"{API_BASE_URL}/analyze_screenshot",
                                    params={"screenshot_path": screenshot["path"]}
                                )
                                
                                if response.status_code == 200:
                                    result_data = response.json()
                                    # Make sure order_data is a dict
                                    if isinstance(result_data.get("order_data"), dict):
                                        order_data = result_data.get("order_data")
                                        # Attach the screenshot ID for reference
                                        order_data["screenshot_id"] = screenshot["id"]
                                        order_data["screenshot_timestamp"] = screenshot["timestamp"]
                                        st.session_state["batch_analysis_results"].append(order_data)
                                        success_count += 1
                                    elif isinstance(result_data.get("order_data"), list):
                                        # If an array of orders came back, add each one
                                        for item in result_data.get("order_data", []):
                                            if isinstance(item, dict):
                                                item["screenshot_id"] = screenshot["id"]
                                                item["screenshot_timestamp"] = screenshot["timestamp"]
                                                st.session_state["batch_analysis_results"].append(item)
                                                success_count += 1
                                    else:
                                        st.warning(f"Screenshot {idx} returned an unsupported data format")
                                else:
                                    error_msg = f"Analysis failed: {response.json().get('detail')}"
                                    st.warning(f"Screenshot {idx} analysis failed: {error_msg}")
                        
                        st.success(f"Batch analysis done! {success_count} screenshot(s) analyzed")
                        st.session_state["show_analysis_results"] = True
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
        
        # Show the analysis results (if any)
        if st.session_state["show_analysis_results"] and st.session_state["batch_analysis_results"]:
            st.markdown('<div class="batch-results">', unsafe_allow_html=True)
            st.subheader("All order analysis results")
            
            # Show the full information for each order
            for i, order in enumerate(st.session_state["batch_analysis_results"], 1):
                # Make sure order is a dict
                if not isinstance(order, dict):
                    st.warning(f"Order #{i} has an invalid data format; skipped")
                    continue
                    
                st.markdown(f'<div class="order-card">', unsafe_allow_html=True)
                st.subheader(f"Order #{i}")
                
                # Basic order information
                col1, col2 = stacked_columns(2)
                with col1:
                    st.write(f"**Order ID:** {order.get('Order ID', 'N/A')}")
                    st.write(f"**Order date:** {order.get('Order Date', 'N/A')}")
                with col2:
                    st.write(f"**Screenshot time:** {order.get('screenshot_timestamp', 'N/A')}")
                    st.write(f"**Total amount:** {order.get('Total Amount', 'N/A')}")
                
                # Item list
                st.write("**Items:**")
                products = order.get('Items', [])
                # Make sure products is a list
                if not isinstance(products, list):
                    st.info("No valid item list recognized")
                elif products:
                    product_data = []
                    for product in products:
                        # Normalize item data to dicts
                        if isinstance(product, dict):
                            product_info = {
                                "Product Name": product.get("Name", "Unknown name"),
                                "Quantity": product.get("Quantity", "N/A"),
                                "Unit Price": product.get("Unit Price", "N/A"),
                                "Total Price": product.get("Subtotal", "N/A")
                            }
                        elif isinstance(product, list):
                            # If it is a list, turn it into a description string
                            product_info = {
                                "Product Name": f"Item info: {', '.join(map(str, product))}",
                                "Quantity": "N/A",
                                "Unit Price": "N/A",
                                "Total Price": "N/A"
                            }
                        else:
                            # Anything else becomes a string
                            product_info = {
                                "Product Name": str(product),
                                "Quantity": "N/A",
                                "Unit Price": "N/A",
                                "Total Price": "N/A"
                            }
                        product_data.append(product_info)
                    
                    df = pd.DataFrame(product_data)
                    st.dataframe(df)
                else:
                    st.info("No item information recognized")
                
                st.markdown('</div>', unsafe_allow_html=True)  # close the order card
            
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif selected_tab == "Settings":
        st.subheader("Settings")
        
        # Settings form
        st.markdown('<div class="config-form">', unsafe_allow_html=True)
        st.subheader("Model settings")
        
        # Inputs prefilled with the current values
        new_server_host = st.text_input(
            "Server address (SERVER_HOST)", 
            value=SERVER_HOST,
            key="server_host_input"
        )
        
        new_server_port = st.text_input(
            "Server port (SERVER_PORT)", 
            value=str(SERVER_PORT),
            key="server_port_input"
        )
        
        new_frontend_port = st.text_input(
            "Frontend port (FRONTEND_PORT)", 
            value=str(FRONTEND_PORT),
            key="frontend_port_input"
        )
        
        new_model_name = st.text_input(
            "Model name (MIDSCENE_MODEL_NAME)", 
            value=MIDSCENE_MODEL_NAME,
            key="model_name_input"
        )
        
        new_openai_base_url = st.text_input(
            "API URL (OPENAI_BASE_URL)", 
            value=OPENAI_BASE_URL,
            key="openai_base_url_input"
        )
        
        # Password field for the API key, masked by default
        new_openai_api_key = st.text_input(
            "API key (OPENAI_API_KEY)", 
            value=OPENAI_API_KEY,
            type="password",
            key="openai_api_key_input"
        )
        
        # Browser settings
        new_chrome_path = st.text_input(
            "Chrome path (CHROME_PATH)", 
            value=CHROME_PATH,
            key="chrome_path_input"
        )
        
        new_chrome_driver_path = st.text_input(
            "chromedriver path (CHROME_DRIVER_PATH)", 
            value=CHROME_DRIVER_PATH,
            key="chrome_driver_path_input"
        )
        
        # Save settings button
        col_save, col_cancel = stacked_columns(2)
        with col_save:
            if st.button("Save settings"):
                # Check that the ports are numeric
                try:
                    if new_server_port:
                        int(new_server_port)
                    if new_frontend_port:
                        int(new_frontend_port)
                except ValueError:
                    st.error("Port numbers must be numeric")
                else:
                    # Prepare the settings to save
                    configs = {
                        "SERVER_HOST": new_server_host,
                        "SERVER_PORT": new_server_port,
                        "FRONTEND_PORT": new_frontend_port,
                        "MIDSCENE_MODEL_NAME": new_model_name,
                        "OPENAI_BASE_URL": new_openai_base_url,
                        "OPENAI_API_KEY": new_openai_api_key,
                        "CHROME_PATH": new_chrome_path,
                        "CHROME_DRIVER_PATH": new_chrome_driver_path
                    }
                    
                    # Save the settings
                    success, message = save_config_to_py(configs)
                    if success:
                        st.session_state["show_config_success"] = True
                        st.success(message + ". Restart the app for the changes to take effect")
                    else:
                        st.error(message)
        
        with col_cancel:
            if st.button("Cancel"):
                st.session_state["show_config_success"] = False
                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.write("**Active settings**")
        st.write("**API server:**", API_BASE_URL)
        st.write("**Screenshot path:**", SCREENSHOTS_DIR.split(os.sep)[-1])
        st.write("**Excel path:**", EXCELS_DIR.split(os.sep)[-1])
        
        st.write("\n**Model settings**")
        st.write("**Current model:**", MIDSCENE_MODEL_NAME)
        st.write("**API URL:**", OPENAI_BASE_URL)
        
        st.markdown("---")
        st.subheader("Environment")
        env_config = {
            "SERVER_HOST": str(SERVER_HOST),
            "SERVER_PORT": str(SERVER_PORT),
            "FRONTEND_PORT": str(FRONTEND_PORT),
            "Model name": MIDSCENE_MODEL_NAME.split("-")[0] + "...",
            "API URL": OPENAI_BASE_URL
        }
        st.dataframe(pd.DataFrame(list(env_config.items()), columns=["Setting", "Current value"]))
        
        st.info("Settings are stored in config.py; restart the app after changing them")

# Right: summary of all order data
with right_col:
    if selected_tab == "Order Recognition":
        st.subheader("Order Summary")
        
        if st.session_state["batch_analysis_results"]:
            # Summary table of all orders
            all_products = []
            for order in st.session_state["batch_analysis_results"]:
                # Make sure order is a dict
                if not isinstance(order, dict):
                    continue
                    
                products = order.get('Items', [])
                # Make sure products is a list
                if not isinstance(products, list):
                    continue
                    
                order_time = order.get('Order Date', 'N/A')
                order_number = order.get('Order ID', f"unknown-{order.get('screenshot_id', 'id')}")
                
                for product in products:
                    # Handle item data safely
                    if isinstance(product, dict):
                        formatted_product = {
                            "Order ID": order_number,
                            "Order Time": order_time,
                            "Product Name": product.get("Name", "Unknown name"),
                            "Quantity": product.get("Quantity", "N/A"),
                            "Unit Price": product.get("Unit Price", "N/A"),
                            "Total Price": product.get("Subtotal", "N/A")
                        }
                    else:
                        formatted_product = {
                            "Order ID": order_number,
                            "Order Time": order_time,
                            "Product Name": str(product),
                            "Quantity": "N/A",
                            "Unit Price": "N/A",
                            "Total Price": "N/A"
                        }
                    all_products.append(formatted_product)
            
            if all_products:
                df = pd.DataFrame(all_products)[["Order ID", "Order Time", "Product Name", "Quantity", "Unit Price", "Total Price"]]
                st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                st.dataframe(df, height=500)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Export
                if st.button("Export to Excel"):
                    try:
                        excel_path = os.path.join(EXCELS_DIR, f"order_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                        df.to_excel(excel_path, index=False)
                        st.success(f"Exported to: {excel_path}")
                        
                        # Offer a download link
                        with open(excel_path, "rb") as file:
                            st.download_button(
                                label="Download Excel file",
                                data=file,
                                file_name=os.path.basename(excel_path),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.error(f"Export failed: {str(e)}")
            else:
                st.info("No item information recognized in the screenshots")
        else:
            st.info("Run an order analysis first")
        
        # Clear-all-data button
        if st.button("Clear all data"):
            st.session_state["screenshots"] = []
            st.session_state["batch_analysis_results"] = []
            st.session_state["full_page_screenshot"] = None
            st.session_state["selection_coords"] = ""
            st.session_state["show_analysis_results"] = False
            st.session_state["url_input"] = ""
            st.session_state["element_selector_input"] = ""
            st.success("All screenshots and analysis results cleared")
            st.experimental_rerun()
    
    elif selected_tab == "Settings":
        st.subheader("About the settings")
        st.write("""
        - **Server address**: IP and port of the backend service
        - **Screenshot path**: folder where order screenshots are saved
        - **Excel path**: folder where order data is saved
        - **Model settings**: Doubao model parameters
        
        Config format:
        ```
        SERVER_HOST=localhost
        SERVER_PORT=8000
        OPENAI_API_KEY=your_key
        ```
        """)
        
        st.subheader("FAQ")
        with st.expander("Cannot connect to the server"):
            st.write("1. Check that the backend is running\n2. Check the server address setting\n3. Check the network connection")
        
        with st.expander("Screenshot failed"):
            st.write("1. Check the browser settings\n2. Check that the page is reachable\n3. Try a different selector or select the area manually")
        
        with st.expander("AI analysis failed"):
            st.write("1. Check the API key\n2. Check the network\n3. Try a clearer screenshot")

if __name__ == "__main__":
    pass
