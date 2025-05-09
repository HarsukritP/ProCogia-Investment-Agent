from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class MarketIndexBase(BaseModel):
    symbol: str
    name: str
    current_value: float
    prev_close: float
    change_pct: float

class MarketIndex(MarketIndexBase):
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EconomicIndicatorBase(BaseModel):
    name: str
    value: float
    previous_value: float
    change: float
    category: str

class EconomicIndicator(EconomicIndicatorBase):
    id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NewsItem(BaseModel):
    title: str
    source: str
    summary: str
    url: Optional[str] = None
    published_at: datetime
    sentiment: Optional[str] = None
    impact: Optional[str] = None

class MarketData(BaseModel):
    timestamp: datetime
    indices: Dict[str, Dict[str, Any]]
    sectors: Optional[Dict[str, Dict[str, Any]]] = None
    economic_indicators: Dict[str, Any]
    news: Optional[List[NewsItem]] = None