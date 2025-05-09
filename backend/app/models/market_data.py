from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database.postgres import Base

class MarketIndex(Base):
    __tablename__ = "market_indices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    current_value = Column(Float)
    prev_close = Column(Float)
    change_pct = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    value = Column(Float)
    previous_value = Column(Float)
    change = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)
    category = Column(String)  # inflation, interest_rate, employment, etc.