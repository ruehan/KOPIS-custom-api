from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse
from datetime import datetime
import json

from fastapi.templating import Jinja2Templates
from utils import fetch_from_kopis, update_database
from api import performances, facilities
from database import Base, SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

Base.metadata.create_all(bind=engine)

app.include_router(performances.router)
app.include_router(facilities.router)

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/docs/markdown", response_class=PlainTextResponse)
async def get_markdown_docs():
    """API 문서를 ReDoc 스타일의 Markdown 형식으로 반환"""
    
    def generate_markdown_docs():
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )

        markdown = f"# {openapi_schema['info']['title']}\n\n"
        markdown += f"Version: {openapi_schema['info']['version']}\n\n"

        # 태그별로 엔드포인트 그룹화
        tag_groups = {}
        for path, path_item in openapi_schema['paths'].items():
            for method, operation in path_item.items():
                tags = operation.get('tags', ['default'])
                for tag in tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append((path, method, operation))

        # 태그별로 문서 생성
        for tag, operations in tag_groups.items():
            markdown += f"# {tag}\n\n"
            for path, method, operation in operations:
                markdown += f"## {operation.get('summary', path)}\n\n"
                markdown += f"`{method.upper()} {path}`\n\n"
                markdown += f"{operation.get('description', '')}\n\n"

                # Parameters
                if 'parameters' in operation:
                    markdown += "### Parameters\n\n"
                    for param in operation['parameters']:
                        markdown += f"- `{param['name']}` ({param['in']}): {param.get('description', '')}\n"
                        if 'schema' in param:
                            markdown += f"  - Type: `{param['schema'].get('type', '')}`\n"
                        if param.get('required', False):
                            markdown += "  - Required: Yes\n"
                    markdown += "\n"

                # Request Body
                if 'requestBody' in operation:
                    markdown += "### Request Body\n\n"
                    content = operation['requestBody']['content']
                    for media_type, media_info in content.items():
                        markdown += f"Content type: `{media_type}`\n\n"
                        if 'schema' in media_info:
                            markdown += "Schema:\n```json\n"
                            markdown += json.dumps(media_info['schema'], indent=2)
                            markdown += "\n```\n\n"

                # Responses
                if 'responses' in operation:
                    markdown += "### Responses\n\n"
                    for status, response in operation['responses'].items():
                        markdown += f"**{status}**\n\n"
                        markdown += f"{response.get('description', '')}\n\n"
                        if 'content' in response:
                            for media_type, media_info in response['content'].items():
                                markdown += f"Content type: `{media_type}`\n\n"
                                if 'schema' in media_info:
                                    markdown += "Schema:\n```json\n"
                                    markdown += json.dumps(media_info['schema'], indent=2)
                                    markdown += "\n```\n\n"

                markdown += "---\n\n"

        return markdown

    try:
        markdown_docs = generate_markdown_docs()
        return markdown_docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 생성 중 오류 발생: {str(e)}")

@app.on_event("startup")
async def startup_event():
    try:
        db = SessionLocal()
        start_date = datetime.now().date()
        end_date = start_date
        performances = fetch_from_kopis(start_date, end_date)
        update_database(db, performances)
        print(f"Database updated at {datetime.now()}")
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)








