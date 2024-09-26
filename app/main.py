import os
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import Float, create_engine, Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import requests
import xmltodict
from urllib.parse import unquote
import json
import re

from region_codes import get_region_name

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
    relates = Column(Text)
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
    relates: Optional[str] = None

class PerformanceFacilityDB(Base):
    __tablename__ = "performance_facilities"

    id = Column(Integer, primary_key=True, index=True)
    fcltynm = Column(String)  # 공연시설명
    mt10id = Column(String, unique=True, index=True)  # 공연시설ID
    mt13cnt = Column(Integer)  # 공연장 수
    fcltychartr = Column(String)  # 시설특성
    sidonm = Column(String)  # 지역(시도)
    gugunnm = Column(String)  # 지역(구군)
    opende = Column(String)  # 개관연도
    seatscale = Column(Integer)  # 객석 수
    telno = Column(String)  # 전화번호
    relateurl = Column(String)  # 홈페이지
    adres = Column(String)  # 주소
    la = Column(Float)  # 위도
    lo = Column(Float)  # 경도

class PerformanceFacility(BaseModel):
    fcltynm: str
    mt10id: str
    mt13cnt: int
    fcltychartr: str
    sidonm: str
    gugunnm: str
    opende: Optional[str] = None
    seatscale: int
    telno: Optional[str] = None
    relateurl: Optional[str] = None
    adres: str
    la: float
    lo: float

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

KOPIS_API_KEY = os.getenv("KOPIS_API_KEY")
KOPIS_BASE_URL = "http://www.kopis.or.kr/openApi/restful/pblprfr"

def decode_unicode_escape(s):
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)

def process_relates(relates):
    if isinstance(relates, list):
        return [{
            'relatenm': decode_unicode_escape(item['relatenm']),
            'relateurl': item['relateurl']
        } for item in relates]
    elif isinstance(relates, dict):
        return {
            'relatenm': decode_unicode_escape(relates['relatenm']),
            'relateurl': relates['relateurl']
        }
    return relates

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
    
    data = xmltodict.parse(response.content, encoding='utf-8')
    performances = data['dbs']['db']
    
    if not isinstance(performances, list):
        performances = [performances]
    
    return performances

def fetch_facilities_from_kopis(signgucode: Optional[str] = None):
    params = {
        "service": KOPIS_API_KEY,
        "cpage": 1,
        "rows": 1500,
    }
    if signgucode:
        params["signgucode"] = signgucode
    
    response = requests.get("http://kopis.or.kr/openApi/restful/prfplc", params=params)
    response.raise_for_status()
    
    data = xmltodict.parse(response.content, encoding='utf-8')
    facilities = data['dbs']['db']
    
    if not isinstance(facilities, list):
        facilities = [facilities]
    
    return facilities

def fetch_performance_detail(mt20id):
    params = {
        "service": KOPIS_API_KEY,
        "mt20id": mt20id
    }
    
    response = requests.get(f"{KOPIS_BASE_URL}/{mt20id}", params=params)
    response.raise_for_status()
    
    data = xmltodict.parse(response.content, encoding='utf-8')
    return data['dbs']['db']

def fetch_facility_detail_from_kopis(mt10id: str):
    params = {
        "service": KOPIS_API_KEY,
        "mt10id": mt10id
    }
    
    response = requests.get(f"http://kopis.or.kr/openApi/restful/prfplc/{mt10id}", params=params)
    response.raise_for_status()
    
    data = xmltodict.parse(response.content, encoding='utf-8')
    return data['dbs']['db']

def update_database(db: Session, performances):
    for perf in performances:
        db_perf = db.query(PerformanceDB).filter(PerformanceDB.mt20id == perf['mt20id']).first()
        if not db_perf:
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
            else:
                styurls = ''

            if 'relates' in detail and 'relate' in detail['relates']:
                relates = process_relates(detail['relates']['relate'])
                relates_str = json.dumps(relates, ensure_ascii=False)
            else:
                relates_str = ''

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
                relates=relates_str,
                last_updated=datetime.now().date()
            )
            db.add(new_detail)
    
    db.commit()

def update_facilities_database(db: Session, facilities):
    for facility in facilities:
        db_facility = db.query(PerformanceFacilityDB).filter(PerformanceFacilityDB.mt10id == facility['mt10id']).first()
        
        # 상세 정보 가져오기
        detail = fetch_facility_detail_from_kopis(facility['mt10id'])
        
        if not db_facility:
            new_facility = PerformanceFacilityDB(
                fcltynm=facility['fcltynm'],
                mt10id=facility['mt10id'],
                mt13cnt=int(facility['mt13cnt']),
                fcltychartr=facility['fcltychartr'],
                sidonm=facility['sidonm'],
                gugunnm=facility['gugunnm'],
                opende=facility['opende'],
                seatscale=int(detail['seatscale']),
                telno=detail['telno'],
                relateurl=detail['relateurl'],
                adres=detail['adres'],
                la=float(detail['la']),
                lo=float(detail['lo'])
            )
            db.add(new_facility)
        else:
            # 기존 데이터 업데이트
            db_facility.fcltynm = facility['fcltynm']
            db_facility.mt13cnt = int(facility['mt13cnt'])
            db_facility.fcltychartr = facility['fcltychartr']
            db_facility.sidonm = facility['sidonm']
            db_facility.gugunnm = facility['gugunnm']
            db_facility.opende = facility['opende']
            db_facility.seatscale = int(detail['seatscale'])
            db_facility.telno = detail['telno']
            db_facility.relateurl = detail['relateurl']
            db_facility.adres = detail['adres']
            db_facility.la = float(detail['la'])
            db_facility.lo = float(detail['lo'])
    
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
    
    # if db_detail.relates:
    #     relates = json.loads(db_detail.relates)
    #     processed_relates = process_relates(relates)
    #     db_detail.relates = json.dumps(processed_relates, ensure_ascii=False)
    
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
        dtguidance=db_detail.dtguidance,
        relates=db_detail.relates
    )

@app.post("/update-facilities")
async def update_facilities(
    signgucode: Optional[str] = Query(None, description="지역(시도)코드"),
    db: Session = Depends(get_db)
):
    """사용 금지"""
    try:
        facilities = fetch_facilities_from_kopis(signgucode)
        update_facilities_database(db, facilities)
        return {"message": f"데이터 업데이트가 완료되었습니다. 업데이트된 시설 수: {len(facilities)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 업데이트 중 오류 발생: {str(e)}")

# 데이터 조회를 위한 엔드포인트
@app.get("/performance-facilities", response_model=List[PerformanceFacility])
async def get_performance_facilities(
    signgucode: Optional[str] = Query(None, description="지역(시도)코드"),
    signgucodesub: Optional[str] = Query(None, description="지역(구군)코드"),
    fcltychartr: Optional[str] = Query(None, description="공연시설특성코드"),
    shprfnmfct: Optional[str] = Query(None, description="공연시설명"),
    cpage: int = Query(1, description="현재페이지"),
    rows: int = Query(5, description="페이지당 목록 수"),
    db: Session = Depends(get_db)
):
    query = db.query(PerformanceFacilityDB)
    
    region_name = get_region_name(signgucode, signgucodesub)
    if region_name:
        if signgucodesub:
            sido_name = region_name.split()[0]
            gugun_name = ' '.join(region_name.split()[1:])
            print(gugun_name)
            query = query.filter(PerformanceFacilityDB.sidonm == sido_name)
            query = query.filter(PerformanceFacilityDB.gugunnm == gugun_name)
        else:
            query = query.filter(PerformanceFacilityDB.sidonm == region_name)
    
    if fcltychartr:
        query = query.filter(PerformanceFacilityDB.fcltychartr == fcltychartr)
    if shprfnmfct:
        query = query.filter(PerformanceFacilityDB.fcltynm.like(f"%{shprfnmfct}%"))
    
    total_count = query.count()
    facilities = query.offset((cpage - 1) * rows).limit(rows).all()
    
    if not facilities:
        raise HTTPException(status_code=404, detail="시설 정보를 찾을 수 없습니다.")
    
    return [PerformanceFacility(
        fcltynm=facility.fcltynm,
        mt10id=facility.mt10id,
        mt13cnt=facility.mt13cnt,
        fcltychartr=facility.fcltychartr,
        sidonm=facility.sidonm,
        gugunnm=facility.gugunnm,
        opende=facility.opende or None,  
        seatscale=facility.seatscale,
        relateurl=facility.relateurl or None, 
        adres=facility.adres,
        la=facility.la,
        lo=facility.lo
    ) for facility in facilities]


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