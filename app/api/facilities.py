from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from region_codes import get_region_name
from database import get_db
from models import PerformanceFacilityDB
from schemas import PerformanceFacility
from utils import fetch_facilities_from_kopis, update_facilities_database

router = APIRouter()

@router.post("/update-facilities")
async def update_facilities(
    signgucode: Optional[str] = Query(None, description="지역(시도)코드"),
    db: Session = Depends(get_db)
):
    """
        ## 사용금지!!
        ## 공연시설 DB 업데이트
    """
    try:
        facilities = fetch_facilities_from_kopis(signgucode)
        update_facilities_database(db, facilities)
        return {"message": f"데이터 업데이트가 완료되었습니다. 업데이트된 시설 수: {len(facilities)}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 업데이트 중 오류 발생: {str(e)}")

# 데이터 조회를 위한 엔드포인트
@router.get("/performance-facilities", response_model=List[PerformanceFacility])
async def get_performance_facilities(
    signgucode: Optional[str] = Query(None, description="지역(시도)코드"),
    signgucodesub: Optional[str] = Query(None, description="지역(구군)코드"),
    fcltychartr: Optional[str] = Query(None, description="공연시설특성코드"),
    shprfnmfct: Optional[str] = Query(None, description="공연시설명"),
    cpage: int = Query(1, description="현재페이지"),
    rows: int = Query(5, description="페이지당 목록 수"),
    db: Session = Depends(get_db)
):
    """
        공연시설 조회 API
    """
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