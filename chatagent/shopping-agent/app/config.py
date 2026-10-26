import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server settings
SERVER_HOST = 'localhost'
SERVER_PORT = '8000'
FRONTEND_PORT = '8501'

# Doubao model settings
MIDSCENE_MODEL_NAME = 'doubao-seed-1-6-250615'
OPENAI_BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3'
OPENAI_API_KEY = ''

# Upstream timeouts (seconds). Without these, a stalled model call or a slow
# page load hangs the request forever -- the socket just sits open until the
# client gives up, which is indistinguishable from a block. Env-overridable.
# LLM_TIMEOUT is (connect, read): fail fast on connect, allow time to generate.
LLM_CONNECT_TIMEOUT = float(os.getenv("LLM_CONNECT_TIMEOUT", "10"))
LLM_READ_TIMEOUT = float(os.getenv("LLM_READ_TIMEOUT", "60"))
PAGE_LOAD_TIMEOUT = float(os.getenv("PAGE_LOAD_TIMEOUT", "30"))

# Paths
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")
EXCELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "excels")

# Browser settings
CHROME_PATH = ''
CHROME_DRIVER_PATH = './dist/resources/chromedriver.exe'

# Make sure the directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(EXCELS_DIR, exist_ok=True)