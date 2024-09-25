import os
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import Text, create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import requests
import xmltodict
from urllib.parse import unquote
from fastapi.responses import PlainTextResponse
from fastapi.openapi.utils import get_openapi
import json

load_dotenv()

app = FastAPI()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./kopis_performances.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PerformanceDB(Base):
    __tablename__ = "performances"

    id = Column(Integer, primary_key=True, index=True)
    mt20id = Column(String, unique=True, index=True)
    prfnm = Column(String)
    prfpdfrom = Column(Date)
    prfpdto = Column(Date)
    fcltynm = Column(String)
    poster = Column(String)
    genrenm = Column(String)
    prfstate = Column(String)
    openrun = Column(String)
    area = Column(String)
    last_updated = Column(Date)

class Performance(BaseModel):
    mt20id: str
    prfnm: str
    prfpdfrom: str
    prfpdto: str
    fcltynm: str
    poster: str
    genrenm: str
    prfstate: str
    openrun: Optional[str]
    area: Optional[str]

class PerformanceDetailDB(Base):
    __tablename__ = "performance_details"

    id = Column(Integer, primary_key=True, index=True)
    mt20id = Column(String, unique=True, index=True)
    prfnm = Column(String)
    prfpdfrom = Column(Date)
    prfpdto = Column(Date)
    fcltynm = Column(String)
    prfcast = Column(String)
    prfcrew = Column(String)
    prfruntime = Column(String)
    prfage = Column(String)
    entrpsnm = Column(String)
    pcseguidance = Column(String)
    poster = Column(String)
    sty = Column(Text)
    genrenm = Column(String)
    prfstate = Column(String)
    openrun = Column(String)
    styurls = Column(Text)
    dtguidance = Column(String)
    last_updated = Column(Date)

class PerformanceDetail(BaseModel):
    mt20id: str
    prfnm: str
    prfpdfrom: str
    prfpdto: str
    fcltynm: str
    prfcast: Optional[str] = None
    prfcrew: Optional[str] = None
    prfruntime: Optional[str] = None
    prfage: Optional[str] = None
    entrpsnm: Optional[str] = None
    pcseguidance: Optional[str] = None
    poster: Optional[str] = None
    sty: Optional[str] = None
    genrenm: Optional[str] = None
    prfstate: Optional[str] = None
    openrun: Optional[str] = None
    styurls: Optional[str] = None
    dtguidance: Optional[str] = None

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

KOPIS_API_KEY = os.getenv("KOPIS_API_KEY")
KOPIS_BASE_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"

def fetch_from_kopis(start_date, end_date):
    params = {
        "service": KOPIS_API_KEY,
        "stdate": start_date.strftime("%Y%m%d"),
        "eddate": end_date.strftime("%Y%m%d"),
        "cpage": 1,
        "rows": 1000,
    }
    
    response = requests.get(KOPIS_BASE_URL, params=params)
    response.raise_for_status()
    
    data = xmltodict.parse(response.content)
    performances = data['dbs']['db']
    
    if not isinstance(performances, list):
        performances = [performances]
    
    return performances

def fetch_performance_detail(mt20id):
    params = {
        "service": KOPIS_API_KEY,
        "mt20id": mt20id
    }
    response = requests.get(f"{KOPIS_BASE_URL}/{mt20id}", params=params)
    response.raise_for_status()
    
    data = xmltodict.parse(response.content)
    return data['dbs']['db']

def update_database(db, performances):
    # Delete all existing records
    db.query(PerformanceDB).delete()
    
    # Add new performances
    for perf in performances:
        new_perf = PerformanceDB(
            mt20id=perf['mt20id'],
            prfnm=perf['prfnm'],
            prfpdfrom=datetime.strptime(perf['prfpdfrom'], "%Y.%m.%d").date(),
            prfpdto=datetime.strptime(perf['prfpdto'], "%Y.%m.%d").date(),
            fcltynm=perf['fcltynm'],
            poster=perf['poster'],
            genrenm=perf['genrenm'],
            prfstate=perf['prfstate'],
            openrun=perf.get('openrun'),
            area=perf.get('area'),
            last_updated=datetime.now().date()
        )
        db.add(new_perf)

        db_detail = db.query(PerformanceDetailDB).filter(PerformanceDetailDB.mt20id == perf['mt20id']).first()
        if not db_detail:
            detail = fetch_performance_detail(perf['mt20id'])
            if isinstance(detail['styurls']['styurl'], list):
                styurls = ','.join(detail['styurls']['styurl'])
            elif isinstance(detail['styurls']['styurl'], str):
                styurls = detail['styurls']['styurl']

            new_detail = PerformanceDetailDB(
                mt20id=detail['mt20id'],
                prfnm=detail['prfnm'],
                prfpdfrom=datetime.strptime(detail['prfpdfrom'], "%Y.%m.%d").date(),
                prfpdto=datetime.strptime(detail['prfpdto'], "%Y.%m.%d").date(),
                fcltynm=detail['fcltynm'],
                prfcast=detail['prfcast'],
                prfcrew=detail['prfcrew'],
                prfruntime=detail['prfruntime'],
                prfage=detail['prfage'],
                entrpsnm=detail['entrpsnm'],
                pcseguidance=detail['pcseguidance'],
                poster=detail['poster'],
                sty=detail['sty'],
                genrenm=detail['genrenm'],
                prfstate=detail['prfstate'],
                openrun=detail.get('openrun'),
                styurls=styurls,
                dtguidance=detail['dtguidance'],
                last_updated=datetime.now().date()
            )
            db.add(new_detail)
    
    

    db.commit()

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

@app.get("/performances", response_model=List[Performance])
async def get_performances(
    stdate: str = Query(..., description="공연시작일자"),
    eddate: str = Query(..., description="공연종료일자"),
    cpage: int = Query(1, description="현재페이지"),
    rows: int = Query(10, description="페이지당 목록 수"),
    shprfnm: Optional[str] = Query(None, description="공연명"),
    shprfnmfct: Optional[str] = Query(None, description="공연시설명"),
    shcate: Optional[str] = Query(None, description="장르코드"),
    prfplccd: Optional[str] = Query(None, description="공연장코드"),
    signgucode: Optional[str] = Query(None, description="지역(시도)코드"),
    signgucodesub: Optional[str] = Query(None, description="지역(구군)코드"),
    kidstate: Optional[str] = Query(None, description="아동공연여부"),
    prfstate: Optional[str] = Query(None, description="공연상태코드"),
    openrun: Optional[str] = Query(None, description="오픈런"),
    db: Session = Depends(get_db)
):
    """공연목록 정보를 반환합니다."""
    try:
        start_date = datetime.strptime(stdate, "%Y%m%d").date()
        end_date = datetime.strptime(eddate, "%Y%m%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYYMMDD.")

    query = db.query(PerformanceDB).filter(
        PerformanceDB.prfpdfrom <= end_date,
        PerformanceDB.prfpdto >= start_date
    )

    if shprfnm:
        query = query.filter(PerformanceDB.prfnm.like(f"%{unquote(shprfnm)}%"))
    if shprfnmfct:
        query = query.filter(PerformanceDB.fcltynm.like(f"%{unquote(shprfnmfct)}%"))
    if shcate:
        query = query.filter(PerformanceDB.genrenm == shcate)
    if prfplccd:
        query = query.filter(PerformanceDB.mt20id.like(f"{prfplccd}%"))
    if signgucode:
        query = query.filter(PerformanceDB.area.like(f"{signgucode}%"))
    if signgucodesub:
        query = query.filter(PerformanceDB.area.like(f"{signgucode}{signgucodesub}%"))
    if kidstate:
        query = query.filter(PerformanceDB.kidstate == kidstate)
    if prfstate:
        query = query.filter(PerformanceDB.prfstate == prfstate)
    if openrun:
        query = query.filter(PerformanceDB.openrun == openrun)

    total_count = query.count()
    performances = query.offset((cpage - 1) * rows).limit(rows).all()

    return [Performance(
        mt20id=perf.mt20id,
        prfnm=perf.prfnm,
        prfpdfrom=perf.prfpdfrom.strftime("%Y.%m.%d"),
        prfpdto=perf.prfpdto.strftime("%Y.%m.%d"),
        fcltynm=perf.fcltynm,
        poster=perf.poster,
        genrenm=perf.genrenm,
        prfstate=perf.prfstate,
        openrun=perf.openrun,
        area=perf.area
    ) for perf in performances]

@app.get("/performance/{mt20id}", response_model=PerformanceDetail)
async def get_performance_detail(mt20id: str, db: Session = Depends(get_db)):
    db_detail = db.query(PerformanceDetailDB).filter(PerformanceDetailDB.mt20id == mt20id).first()
    if db_detail is None:
        raise HTTPException(status_code=404, detail="Performance not found")
    
    return PerformanceDetail(
        mt20id=db_detail.mt20id,
        prfnm=db_detail.prfnm,
        prfpdfrom=db_detail.prfpdfrom.strftime("%Y.%m.%d") if db_detail.prfpdfrom else None,
        prfpdto=db_detail.prfpdto.strftime("%Y.%m.%d") if db_detail.prfpdto else None,
        fcltynm=db_detail.fcltynm,
        prfcast=db_detail.prfcast,
        prfcrew=db_detail.prfcrew,
        prfruntime=db_detail.prfruntime,
        prfage=db_detail.prfage,
        entrpsnm=db_detail.entrpsnm or "",
        pcseguidance=db_detail.pcseguidance,
        poster=db_detail.poster,
        sty=db_detail.sty or "",
        genrenm=db_detail.genrenm,
        prfstate=db_detail.prfstate,
        openrun=db_detail.openrun,
        styurls=db_detail.styurls,
        dtguidance=db_detail.dtguidance
    )

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)