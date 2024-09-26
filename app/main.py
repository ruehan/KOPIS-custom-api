from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse
from datetime import datetime
import json
from utils import fetch_from_kopis, update_database
from api import performances, facilities
from database import Base, SessionLocal, engine


load_dotenv()

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(performances.router)
app.include_router(facilities.router)

@app.get("/docs/markdown", response_class=PlainTextResponse)
async def get_markdown_docs():
    """API 문서를 Markdown 형식으로 반환합니다."""
    
    def generate_markdown_docs():
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )

        markdown = f"# {openapi_schema['info']['title']}\n\n"
        markdown += f"Version: {openapi_schema['info']['version']}\n\n"

        for path, path_item in openapi_schema['paths'].items():
            for method, operation in path_item.items():
                markdown += f"## {method.upper()} {path}\n\n"
                markdown += f"{operation.get('summary', '')}\n\n"
                markdown += f"{operation.get('description', '')}\n\n"

                if 'parameters' in operation:
                    markdown += "### Parameters\n\n"
                    markdown += "| Name | Located in | Description | Required | Schema |\n"
                    markdown += "| ---- | ---------- | ----------- | -------- | ------ |\n"
                    for param in operation['parameters']:
                        markdown += f"| {param.get('name')} | {param.get('in')} | {param.get('description', '')} | {param.get('required', False)} | {param.get('schema', {}).get('type', '')} |\n"

                if 'requestBody' in operation:
                    markdown += "### Request Body\n\n"
                    content = operation['requestBody']['content']
                    for media_type, media_info in content.items():
                        markdown += f"Content type: {media_type}\n\n"
                        if 'schema' in media_info:
                            markdown += "Schema:\n```json\n"
                            markdown += json.dumps(media_info['schema'], indent=2)
                            markdown += "\n```\n\n"

                if 'responses' in operation:
                    markdown += "### Responses\n\n"
                    for status, response in operation['responses'].items():
                        markdown += f"**{status}**\n\n"
                        markdown += f"{response.get('description', '')}\n\n"
                        if 'content' in response:
                            for media_type, media_info in response['content'].items():
                                markdown += f"Content type: {media_type}\n\n"
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








