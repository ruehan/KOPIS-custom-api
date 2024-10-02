from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import PerformanceDB, PerformanceDetailDB, UpcomingPerformanceDB
from schemas import Performance, PerformanceDetail, PerformanceName
from urllib.parse import unquote

router = APIRouter()

@router.get("/performances", response_model=List[Performance])
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
    """
        ## 공연목록 조회 API
    """
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

@router.get("/upcoming-performances", response_model=List[Performance])
async def get_upcoming_performances(db: Session = Depends(get_db)):
    today = datetime.now().date()

    performances = db.query(UpcomingPerformanceDB).filter(
        UpcomingPerformanceDB.prfpdfrom > today
    ).order_by(UpcomingPerformanceDB.prfpdfrom).all()

    result = [
        {
            "mt20id": perf.mt20id,
            "prfnm": perf.prfnm,
            "prfpdfrom": perf.prfpdfrom.strftime('%Y-%m-%d'),
            "prfpdto": perf.prfpdto.strftime('%Y-%m-%d'),
            "fcltynm": perf.fcltynm,
            "poster": perf.poster,
            "area": perf.area if perf.area else "Unknown",  # 기본값 설정
            "genrenm": perf.genrenm if perf.genrenm else "Unknown",  # 기본값 설정
            "openrun": perf.openrun if perf.openrun else "N/A",  # 기본값 설정
            "prfstate": perf.prfstate
        }
        for perf in performances
    ]

    return result



@router.get("/performance/{mt20id}", response_model=PerformanceDetail)
async def get_performance_detail(mt20id: str, db: Session = Depends(get_db)):
    """
        ## 공연상세정보 조회 API
    """
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
        dtguidance=db_detail.dtguidance,
        relates=db_detail.relates
    )

@router.get("/auto-fill", response_model=List[PerformanceName])
async def get_auto_fill(
    stdate: str = Query(..., description="공연시작일자"),
    eddate: str = Query(..., description="공연종료일자"),
    cpage: int = Query(1, description="현재페이지"),
    rows: int = Query(10, description="페이지당 목록 수"),
    shprfnm: str = Query(... , description="공연명"),
    db: Session = Depends(get_db)
):
    """
        ## 자동완성 API
    """

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

    total_count = query.count()
    performance_names = query.offset((cpage - 1) * rows).limit(rows).all()

    return [PerformanceName(prfnm=name.prfnm) for name in performance_names]