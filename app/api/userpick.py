import itertools
import random
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from config import KOPIS_API_KEY
from schemas import Performance, UserPicksInput, RecommendedShows
from utils import create_token, verify_token
from database import get_db
from models import UserPick, PerformanceDB
from typing import List
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime
import models, schemas
from sqlalchemy import func

router = APIRouter()
security = HTTPBearer()

GENRE_CODE_MAP = {
    "AAAA": "연극",
    "BBBC": "무용(서양/한국무용)",
    "BBBE": "대중무용",
    "CCCA": "서양음악(클래식)",
    "CCCC": "한국음악(국악)",
    "CCCD": "대중음악",
    "EEEA": "복합",
    "EEEB": "서커스/마술",
    "GGGA": "뮤지컬"
}

async def fetch_kopis_data(base_url: str, params: dict) -> List[Performance]:
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                xml_string = await response.text()
                return parse_kopis_xml(xml_string)
            else:
                raise HTTPException(status_code=response.status, detail="KOPIS API request failed")

@router.get("/popular-by-genre", response_model=List[Performance])
async def get_popular_by_genre():
    """
        ## 장르별로 공연 1개 반환
        ### stdate / eddate 수정 필요!
    """
    popular_performances = []
    base_url = "http://kopis.or.kr/openApi/restful/pblprfr"
    
    for genre_code, genre_name in GENRE_CODE_MAP.items():
        params = {
            "service": KOPIS_API_KEY,
            "stdate": "20240930",  # 시작일
            "eddate": "20240930",  # 종료일
            "cpage": "1",
            "rows": "1",
            "shcate": genre_code
        }
        
        try:
            performances = await fetch_kopis_data(base_url, params)
            if performances:
                popular_performances.extend(performances)
        except HTTPException as e:
            print(f"Error fetching data for genre {genre_name}: {str(e)}")
    
    return popular_performances

@router.post("/user-picks")
async def save_user_picks(
    input_data: UserPicksInput,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """
        ## Token 기반 사용자 공연 Pick 저장
    """
    

    token = verify_token(credentials.credentials)
    print(token)

    # 기존 선택 삭제
    db.query(UserPick).filter(UserPick.token == token).delete()

    # 새로운 선택 저장
    for perf_id in input_data.performance_ids:
        print(perf_id)
        performance = db.query(PerformanceDB).filter(PerformanceDB.genrenm == perf_id).first()
        if performance:
            new_pick = UserPick(token=token, performance_id=perf_id)
            db.add(new_pick)
    
    db.commit()
    return {"message": "User picks saved successfully"}

@router.get("/user-picks")
async def get_user_picks(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """
        ## Token 기반 사용자 공연 Pick 반환
    """
    token = verify_token(credentials.credentials)

    user_picks = db.query(UserPick).filter(UserPick.token == token).all()
    performance_ids = [pick.performance_id for pick in user_picks]

    return performance_ids

@router.post("/token")
async def generate_token():
    token = create_token()
    return {"token": token}

def parse_kopis_xml(xml_string: str) -> List[Performance]:
    root = ET.fromstring(xml_string)
    performances = []

    for item in root.findall('.//db'):
        performance_data = {}
        for child in item:
            performance_data[child.tag] = child.text

        # 날짜 파싱 및 문자열로 변환
        try:
            prfpdfrom = datetime.strptime(performance_data.get('prfpdfrom', ''), '%Y.%m.%d').strftime('%Y-%m-%d')
        except ValueError:
            prfpdfrom = None

        try:
            prfpdto = datetime.strptime(performance_data.get('prfpdto', ''), '%Y.%m.%d').strftime('%Y-%m-%d')
        except ValueError:
            prfpdto = None

        performance = Performance(
            mt20id=performance_data.get('mt20id', ''),
            prfnm=performance_data.get('prfnm', ''),
            prfpdfrom=prfpdfrom,
            prfpdto=prfpdto,
            fcltynm=performance_data.get('fcltynm', ''),
            poster=performance_data.get('poster', ''),
            genrenm=performance_data.get('genrenm', ''),
            prfstate=performance_data.get('prfstate', ''),
            openrun=performance_data.get('openrun', ''),
            area=performance_data.get('area', '')
        )
        performances.append(performance)

    return performances

# @router.get("/recommended-shows", response_model=List[schemas.Performance])
# def get_recommended_shows(token: str, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.token == token).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     user_genres = db.query(models.UserGenre).filter(models.UserGenre.user_id == user.id).all()
#     genre_names = [ug.genre for ug in user_genres]
    
#     # 사용자의 선호 장르에 해당하는 공연들 중 최근 공연을 추천
#     recommended_shows = db.query(models.Performance).filter(
#         models.Performance.genrenm.in_(genre_names),
#         models.Performance.prfpdfrom >= datetime.now().date()
#     ).order_by(models.Performance.prfpdfrom).limit(10).all()
    
#     return recommended_shows

@router.get("/recommended-shows", response_model=RecommendedShows)
def get_recommended_shows(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
        ## 공연 Pick에 따른 추천 공연 리스트
    """
    # 토큰으로 사용자가 선택한 장르 가져오기
    token = verify_token(credentials.credentials)
    user_picks = db.query(models.UserPick).filter(models.UserPick.token == token).all()
    if not user_picks:
        raise HTTPException(status_code=404, detail="User picks not found")
    
    selected_genres = list(set([pick.performance_id for pick in user_picks]))
    
    recommended_shows = []
    for genre in selected_genres:
        genre_shows = db.query(models.PerformanceDB).filter(
            models.PerformanceDB.genrenm == genre,
            models.PerformanceDB.prfpdfrom >= func.current_date()
        ).order_by(func.random()).limit(10).all()
        
        recommended_shows.extend(genre_shows)

    return RecommendedShows(root={
        genre: [Performance.from_orm(show) for show in shows]
        for genre, shows in itertools.groupby(recommended_shows, key=lambda x: x.genrenm)
    })