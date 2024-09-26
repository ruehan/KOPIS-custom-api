import os
from dotenv import load_dotenv

load_dotenv()

KOPIS_API_KEY = os.getenv("KOPIS_API_KEY")
KOPIS_BASE_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"