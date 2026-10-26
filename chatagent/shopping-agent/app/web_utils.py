from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementNotVisibleException,
    ElementNotInteractableException
)
import time
import os
import subprocess
import socket
import sys
import base64
from datetime import datetime
from PIL import Image  # Requires Pillow: pip install pillow
# Server settings
SERVER_HOST = os.getenv("SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 8501))

# Doubao model settings
MIDSCENE_MODEL_NAME = os.getenv("MIDSCENE_MODEL_NAME", "doubao-seed-1-6-vision-250815")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "c87d16de-85a4-4ea1-8cf1-a47a3dd64634")

# Paths
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")
EXCELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "excels")

# Browser settings
CHROME_PATH = os.getenv("CHROME_PATH", "")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH", "")
# Cap page navigation so a slow/unresponsive page raises TimeoutException
# instead of hanging the request forever.
PAGE_LOAD_TIMEOUT = float(os.getenv("PAGE_LOAD_TIMEOUT", "30"))


class WebUtils:
    def __init__(self):
        self.driver = None
        self.current_url = None
        self.chrome_driver_path = self.find_chrome_driver()
        self.debug_port = self.find_available_port()
        self.initialize_driver()
    
    def find_available_port(self):
        """Find a free local port to avoid port conflicts"""
        for _ in range(5):  # Try up to 5 times to get a port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', 0))  # Binding to 0 picks a free port automatically
                    port = s.getsockname()[1]
                    # Make sure the port really is free
                    if self.is_port_available(port):
                        return port
                except:
                    continue
        raise Exception("Could not find a free port; check which ports are in use on this system")
    
    def is_port_available(self, port):
        """Check whether the port really is free"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0
    
    def find_chrome_driver(self):
        """Find the local chromedriver path"""
        if CHROME_DRIVER_PATH and os.path.exists(CHROME_DRIVER_PATH):
            return CHROME_DRIVER_PATH
            
        common_paths = [
            "C:/chromedriver/chromedriver.exe",
            "C:/Program Files/Google/Chrome/Driver/chromedriver.exe",
            "C:/Program Files (x86)/Google/Chrome/Driver/chromedriver.exe",
            os.path.join(os.path.expanduser("~"), "chromedriver/chromedriver.exe")
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.path.isfile(path):
                return path
        
        raise Exception(f"""
        chromedriver was not found. To fix this:
        1. Check your Chrome version: open chrome://version/ in Chrome
        2. Download the matching driver: https://sites.google.com/chromium.org/driver/
           or the China mirror: https://npm.taobao.org/mirrors/chromedriver/
        3. Unzip it and put chromedriver.exe in one of these places:
           - C:/chromedriver/
           - or set it in the .env file: CHROME_DRIVER_PATH=<full path to the driver>
        """)
    
    def initialize_driver(self):
        """Initialize the browser driver"""
        # Clean up any leftover Chrome processes
        self.cleanup_chrome_processes()
        
        # Find the Chrome browser path
        chrome_path = self.find_chrome_path()
        
        # Disable Selenium's automatic driver management
        os.environ["SE_MANAGER_DOWNLOAD"] = "0"
        
        try:
            # Build the Chrome launch command
            chrome_profile_dir = os.path.abspath("./chrome_profile")
            os.makedirs(chrome_profile_dir, exist_ok=True)  # Make sure the directory exists
            
            command = [
                chrome_path,
                f"--remote-debugging-port={self.debug_port}",
                f"--user-data-dir={chrome_profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                "--disable-gpu",
                "--no-sandbox"
            ]
            
            # Launch Chrome
            subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True  # Windows needs shell=True to handle spaces in the path
            )
            
            # Wait for Chrome to start and listen on the port
            max_attempts = 20
            attempts = 0
            while attempts < max_attempts:
                if not self.is_port_available(self.debug_port):
                    print(f"Chrome started on port {self.debug_port}")
                    break
                attempts += 1
                time.sleep(1)
            
            if attempts >= max_attempts:
                raise Exception(f"Chrome failed to start; could not connect to port {self.debug_port}")
            
            # Connect to Chrome
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"localhost:{self.debug_port}")
            self.driver = webdriver.Chrome(
                service=Service(self.chrome_driver_path),
                options=chrome_options
            )
        
        except Exception as e:
            raise Exception(f"Could not start or connect to Chrome: {str(e)}")
        
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        self.driver.set_script_timeout(PAGE_LOAD_TIMEOUT)
        self.driver.set_window_size(1920, 1080)
    
    def find_chrome_path(self):
        """Find the Chrome installation path"""
        # Prefer the Chrome path from the config file
        chrome_paths = []
        if CHROME_PATH and os.path.exists(CHROME_PATH):
            chrome_paths.append(CHROME_PATH)
        
        # Add the default Chrome paths
        chrome_paths.extend([
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            f"C:/Users/{os.getlogin()}/AppData/Local/Google/Chrome/Application/chrome.exe",
            "/usr/bin/google-chrome",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ])
        
        # Find a valid Chrome path
        for path in chrome_paths:
            if os.path.exists(path) and os.path.isfile(path):
                return path
        
        raise Exception("""
        Chrome was not found. To fix this:
        1. Make sure Chrome is installed
        2. Set the path manually in the .env file: CHROME_PATH=<Chrome install path>
           Example: CHROME_PATH=C:/Program Files/Google/Chrome/Application/chrome.exe
        """)
    
    def cleanup_chrome_processes(self):
        """Clean up any leftover Chrome processes"""
        try:
            if sys.platform.startswith('win'):
                # Windows
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif sys.platform.startswith('linux'):
                # Linux
                subprocess.run(["pkill", "chrome"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif sys.platform.startswith('darwin'):
                # macOS
                subprocess.run(["pkill", "Google Chrome"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
        except Exception as e:
            print(f"Error while cleaning up Chrome processes: {str(e)}")
    
    def open_url(self, url):
        """Open the given URL"""
        try:
            if not self.driver:
                self.initialize_driver()
                
            self.driver.get(url)
            self.current_url = url
            # Wait for the page to finish loading
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return True, f"Opened page: {url}"
        except Exception as e:
            return False, f"Failed to open page: {str(e)}"
    
    def take_screenshot(self, element_selector=None, max_attempts=3):
        """
        Take a screenshot of the current page or a specific element, with retries
        element_selector: CSS selector, e.g. "#order-container"
        max_attempts: maximum number of attempts
        """
        # Make sure the screenshot directory exists
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        
        # Build a unique screenshot file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"screenshot_{timestamp}.png")
        
        for attempt in range(max_attempts):
            try:
                # Check that the browser is still available
                if not self.driver:
                    return False, "The browser is not initialized or has been closed"
                
                # Try refreshing the page (after the first failure)
                if attempt > 0:
                    self.driver.refresh()
                    time.sleep(2)  # Wait for the page to refresh
                
                if element_selector:
                    # Screenshot the given element
                    try:
                        # Scroll to the element first
                        element = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, element_selector))
                        )
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(1)  # Wait for scrolling to finish
                        
                        # Try an element screenshot
                        if element.screenshot(screenshot_path):
                            return True, screenshot_path
                            
                        # Element screenshot failed; take a full screenshot and crop it
                        full_screenshot_path = screenshot_path.replace(".png", "_full.png")
                        self.driver.save_screenshot(full_screenshot_path)
                        
                        # Get the element's position and size
                        location = element.location
                        size = element.size
                        
                        # Handle possible display scaling
                        dpr = self.driver.execute_script("return window.devicePixelRatio;")
                        left = location['x'] * dpr
                        top = location['y'] * dpr
                        right = (location['x'] + size['width']) * dpr
                        bottom = (location['y'] + size['height']) * dpr
                        
                        # Crop the image
                        img = Image.open(full_screenshot_path)
                        img = img.crop((left, top, right, bottom))
                        img.save(screenshot_path)
                        os.remove(full_screenshot_path)  # Remove the temporary file
                        return True, screenshot_path
                        
                    except NoSuchElementException:
                        return False, f"No element found for selector {element_selector}"
                    except TimeoutException:
                        return False, f"Timed out waiting for element {element_selector}"
                    except (ElementNotVisibleException, ElementNotInteractableException):
                        return False, f"Element {element_selector} is not visible or not interactable"
                else:
                    # Screenshot the whole page
                    if self.driver.save_screenshot(screenshot_path):
                        return True, screenshot_path
                    else:
                        # Fall back to a JavaScript screenshot
                        screenshot_data = self.driver.execute_script("""
                            var canvas = document.createElement('canvas');
                            var ctx = canvas.getContext('2d');
                            canvas.width = window.innerWidth;
                            canvas.height = window.innerHeight;
                            ctx.drawWindow(window, 0, 0, window.innerWidth, window.innerHeight, 'rgb(255, 255, 255)');
                            return canvas.toDataURL('image/png');
                        """)
                        
                        # Save the screenshot data returned by JavaScript
                        img_data = screenshot_data.replace('data:image/png;base64,', '')
                        with open(screenshot_path, 'wb') as f:
                            f.write(base64.b64decode(img_data))
                        return True, screenshot_path
                
            except WebDriverException as e:
                if attempt < max_attempts - 1:
                    # Close and re-initialize the driver before retrying
                    self.close_browser()
                    time.sleep(2)
                    self.initialize_driver()
                    if self.current_url:
                        self.driver.get(self.current_url)
                        time.sleep(2)
                    continue
                return False, f"Screenshot failed (attempt {attempt+1}/{max_attempts}): {str(e)}"
            except Exception as e:
                return False, f"Screenshot processing failed: {str(e)}"
        
        return False, f"Could not take the screenshot after {max_attempts} attempts"
    
    def close_browser(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error while closing the browser: {str(e)}")
            finally:
                self.driver = None
                self.cleanup_chrome_processes()
                return True, "Browser closed"
        return False, "No browser is running"
    
    def execute_script(self, script, *args):
        """Run JavaScript code"""
        try:
            if not self.driver:
                return False, "The browser is not initialized or has been closed"
                
            result = self.driver.execute_script(script, *args)
            return True, result
        except Exception as e:
            return False, f"Failed to run script: {str(e)}"
    
    def get_page_title(self):
        """Get the current page title"""
        try:
            if not self.driver:
                return False, "The browser is not initialized or has been closed"
                
            return True, self.driver.title
        except Exception as e:
            return False, f"Failed to get the title: {str(e)}"
    
    def find_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Find a single element"""
        try:
            if not self.driver:
                return False, "The browser is not initialized or has been closed"
                
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return True, element
        except TimeoutException:
            return False, f"Timed out finding element: {selector}"
        except NoSuchElementException:
            return False, f"Element not found: {selector}"
        except Exception as e:
            return False, f"Failed to find element: {str(e)}"
    
    def click_element(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Click the given element"""
        try:
            success, element = self.find_element(selector, by, timeout)
            if not success:
                return False, element  # Pass the error message through
                
            # Make sure the element is visible, then click it
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            ).click()
            return True, f"Clicked element: {selector}"
        except Exception as e:
            return False, f"Failed to click element: {str(e)}"
    
    def input_text(self, selector, text, by=By.CSS_SELECTOR, timeout=10):
        """Type text into an input field"""
        try:
            success, element = self.find_element(selector, by, timeout)
            if not success:
                return False, element  # Pass the error message through
                
            # Clear the existing content and type the new text
            element.clear()
            element.send_keys(text)
            return True, f"Typed text into element {selector}"
        except Exception as e:
            return False, f"Failed to type text: {str(e)}"
    
    def get_element_text(self, selector, by=By.CSS_SELECTOR, timeout=10):
        """Get the text content of an element"""
        try:
            success, element = self.find_element(selector, by, timeout)
            if not success:
                return False, element  # Pass the error message through
                
            return True, element.text
        except Exception as e:
            return False, f"Failed to get element text: {str(e)}"
    
    def scroll_to_bottom(self):
        """Scroll to the bottom of the page"""
        try:
            if not self.driver:
                return False, "The browser is not initialized or has been closed"
                
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            return True, "Scrolled to the bottom of the page"
        except Exception as e:
            return False, f"Scroll failed: {str(e)}"
    
    def wait_for_page_load(self, timeout=30):
        """Wait for the page to fully load"""
        try:
            if not self.driver:
                return False, "The browser is not initialized or has been closed"
                
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            return True, "Page fully loaded"
        except TimeoutException:
            return False, "Timed out waiting for the page to load"
        except Exception as e:
            return False, f"Failed waiting for the page to load: {str(e)}"
