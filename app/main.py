import os
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
import requests
import xmltodict
from urllib.parse import unquote

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
        # Assuming kidstate is stored in the database. If not, you might need to adjust this.
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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)