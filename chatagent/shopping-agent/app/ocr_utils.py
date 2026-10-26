import base64
import requests
import json
from .config import (
    MIDSCENE_MODEL_NAME, OPENAI_BASE_URL, OPENAI_API_KEY,
    LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT
)

class OCRUtils:
    def __init__(self):
        self.model_name = MIDSCENE_MODEL_NAME
        self.api_base = OPENAI_BASE_URL
        self.api_key = OPENAI_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def encode_image(self, image_path):
        """Encode an image as base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_order_screenshot(self, image_path):
        """
        Analyze an order screenshot and extract every order in it.
        Returns the list of parsed orders.
        """
        try:
            # Encode the image
            base64_image = self.encode_image(image_path)
            
            # Build the prompt - extract all orders
            prompt = """
            Carefully analyze this shopping order screenshot, extract the information of every order in it and return it as JSON.
            If the screenshot contains several orders, return an array of order objects. Each order must use exactly these keys:
            - "Order ID"
            - "Order Date"
            - "Items" (an array; each item has "Name", "Quantity", "Unit Price", "Subtotal")
            - "Total Amount"
            - "Payment Method"
            - "Shipping Address"
            - "Recipient"
            - "Phone"
            
            If a piece of information is missing, set that field to null.
            Return a pure JSON array with no other text. Even if there is only one order, return an array with one element.
            Write all values in English where possible.
            """
        
            # Build the request payload
            data = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                "temperature": 0.0
            }
            
            # Send the request
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=self.headers,
                data=json.dumps(data),
                timeout=(LLM_CONNECT_TIMEOUT, LLM_READ_TIMEOUT)
            )

            if response.status_code != 200:
                return False, f"API request failed: {response.text}"
            
            # Parse the response
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse the JSON
            try:
                # The reply is an array of orders
                order_data = json.loads(content)
                return True, order_data
            except json.JSONDecodeError:
                return False, f"Failed to parse the model output: {content}"
                
        except Exception as e:
            return False, f"Error while analyzing the image: {str(e)}"
