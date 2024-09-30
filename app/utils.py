import json
import os
import re
from typing import Optional
import requests
import xmltodict
from datetime import datetime
from models import PerformanceDB, PerformanceDetailDB, PerformanceFacilityDB
from config import KOPIS_API_KEY, KOPIS_BASE_URL
from sqlalchemy.orm import sessionmaker, Session
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException


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

def get_example_value(schema):
    if 'example' in schema:
        return schema['example']
    if schema.get('type') == 'string':
        return "string"
    elif schema.get('type') == 'integer':
        return 0
    elif schema.get('type') == 'number':
        return 0.0
    elif schema.get('type') == 'boolean':
        return False
    elif schema.get('type') == 'array':
        return [get_example_value(schema.get('items', {}))]
    elif schema.get('type') == 'object':
        return {k: get_example_value(v) for k, v in schema.get('properties', {}).items()}
    return None

def schema_to_markdown(schema, level=0):
    markdown = ""
    indent = "  " * level
    if 'type' in schema:
        markdown += f"{indent}- Type: `{schema['type']}`\n"
        if schema['type'] == 'object' and 'properties' in schema:
            for prop, prop_schema in schema['properties'].items():
                markdown += f"{indent}- `{prop}`:\n"
                markdown += schema_to_markdown(prop_schema, level + 1)
        elif schema['type'] == 'array' and 'items' in schema:
            markdown += f"{indent}- Items:\n"
            markdown += schema_to_markdown(schema['items'], level + 1)
    if 'enum' in schema:
        markdown += f"{indent}- Enum: {', '.join([f'`{e}`' for e in schema['enum']])}\n"
    example = get_example_value(schema)
    if example is not None:
        markdown += f"{indent}- Example: `{json.dumps(example)}`\n"
    return markdown



SECRET_KEY = os.getenv("TOKEN_KEY")
ALGORITHM = "HS256"

def create_token():
    payload = {
        "exp": datetime.utcnow() + timedelta(days=30)  # 토큰 유효기간 30일
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")