from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.schemas import Performance
from app.utils import create_token, verify_token
from database import get_db
from models import UserPick, PerformanceDB
from typing import List

router = APIRouter()
security = HTTPBearer()

@router.post("/user-picks")
async def save_user_picks(
    performance_ids: List[str],
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = verify_token(credentials.credentials)

    # 기존 선택 삭제
    db.query(UserPick).filter(UserPick.token == token).delete()

    # 새로운 선택 저장
    for perf_id in performance_ids:
        performance = db.query(PerformanceDB).filter(PerformanceDB.mt20id == perf_id).first()
        if performance:
            new_pick = UserPick(token=token, performance_id=perf_id)
            db.add(new_pick)
    
    db.commit()
    return {"message": "User picks saved successfully"}

@router.get("/user-picks", response_model=List[Performance])
async def get_user_picks(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    token = verify_token(credentials.credentials)

    user_picks = db.query(UserPick).filter(UserPick.token == token).all()
    performance_ids = [pick.performance_id for pick in user_picks]

    performances = db.query(PerformanceDB).filter(PerformanceDB.mt20id.in_(performance_ids)).all()

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

@router.post("/token")
async def generate_token():
    token = create_token()
    return {"token": token}