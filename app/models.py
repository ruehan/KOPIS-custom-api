from sqlalchemy import Column, ForeignKey, Integer, String, Date, Text, Float
from database import Base
from sqlalchemy.orm import relationship

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

class PerformanceFacilityDB(Base):
    __tablename__ = "performance_facilities"

    id = Column(Integer, primary_key=True, index=True)
    fcltynm = Column(String)
    mt10id = Column(String, unique=True, index=True)
    mt13cnt = Column(Integer)
    fcltychartr = Column(String)
    sidonm = Column(String)
    gugunnm = Column(String)
    opende = Column(String)
    seatscale = Column(Integer)
    telno = Column(String)
    relateurl = Column(String)
    adres = Column(String)
    la = Column(Float)
    lo = Column(Float)

# 삭제 보류
class UserPick(Base):
    __tablename__ = "user_picks"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True)  # 사용자 토큰
    performance_id = Column(String, ForeignKey("performances.mt20id"))

    performance = relationship("PerformanceDB", back_populates="picks")

# PerformanceDB 모델에 관계 추가
PerformanceDB.picks = relationship("UserPick", back_populates="performance")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)

class UserGenre(Base):
    __tablename__ = "user_genres"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    genre = Column(String)

class UpcomingPerformanceDB(Base):
    __tablename__ = "upcoming_performances"

    mt20id = Column(String, primary_key=True, index=True)
    prfnm = Column(String, index=True)
    prfpdfrom = Column(Date)
    prfpdto = Column(Date)
    fcltynm = Column(String)
    poster = Column(String)
    area = Column(String, nullable=True, default="Unknown")  # 필드 추가
    genrenm = Column(String, nullable=True, default="Unknown")
    openrun = Column(String, nullable=True, default="N/A")
    prfstate = Column(String)