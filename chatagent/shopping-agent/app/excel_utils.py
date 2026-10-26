# Developer: Enjoy
# Function: shop agent
# Creation Date: 2025-09-21
# Version: 1.0
import pandas as pd
import os
from datetime import datetime
from .config import EXCELS_DIR

class ExcelUtils:
    def __init__(self):
        self.excels_dir = EXCELS_DIR
    
    def save_order_to_excel(self, order_data):
        """
        Save order data to an Excel file
        order_data: order data dict produced by the OCR step
        """
        try:
            # Build a unique Excel file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            order_id = order_data.get('Order ID', f'order_{timestamp}')
            excel_filename = f"order_{order_id}_{timestamp}.xlsx"
            excel_path = os.path.join(self.excels_dir, excel_filename)
            
            # Create an ExcelWriter
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Basic order information
                order_info = {
                    'Order ID': [order_data.get('Order ID')],
                    'Order Date': [order_data.get('Order Date')],
                    'Total Amount': [order_data.get('Total Amount')],
                    'Payment Method': [order_data.get('Payment Method')],
                    'Recipient': [order_data.get('Recipient')],
                    'Phone': [order_data.get('Phone')],
                    'Shipping Address': [order_data.get('Shipping Address')]
                }
                pd.DataFrame(order_info).to_excel(writer, sheet_name='Order Info', index=False)
                
                # Item list
                products = order_data.get('Items', [])
                if not isinstance(products, list):
                    products = []
                
                pd.DataFrame(products).to_excel(writer, sheet_name='Items', index=False)
            
            return True, excel_path
            
        except Exception as e:
            return False, f"Failed to save Excel: {str(e)}"
    
    def get_excel_files(self):
        """List all saved Excel files"""
        try:
            excel_files = [f for f in os.listdir(self.excels_dir) if f.endswith('.xlsx')]
            # Sort by modification time, newest first
            excel_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.excels_dir, x)), reverse=True)
            return True, excel_files
        except Exception as e:
            return False, f"Failed to list Excel files: {str(e)}"
    
    def read_excel_file(self, filename):
        """Read the contents of an Excel file"""
        try:
            excel_path = os.path.join(self.excels_dir, filename)
            if not os.path.exists(excel_path):
                return False, "File does not exist"
                
            # Read the order information
            order_info = pd.read_excel(excel_path, sheet_name='Order Info').to_dict('records')
            # Read the item details
            products = pd.read_excel(excel_path, sheet_name='Items').to_dict('records')
            
            return True, {
                'order_info': order_info[0] if order_info else {},
                'products': products
            }
        except Exception as e:
            return False, f"Failed to read Excel file: {str(e)}"
