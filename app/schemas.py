from typing import List, Dict
from pydantic import BaseModel
from typing import Optional
from datetime import date

def date_to_string(v):
    return v.strftime('%Y-%m-%d') if isinstance(v, date) else v

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

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            **{
                k: date_to_string(v) for k, v in obj.__dict__.items()
            }
        )

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

class PerformanceName(BaseModel):
    prfnm: str

class UserPicksInput(BaseModel):
    performance_ids: List[str]

class RecommendedShows(BaseModel):
    root: Dict[str, List[Performance]]

    class Config:
        from_attributes = True 