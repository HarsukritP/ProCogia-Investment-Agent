from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AssetBase(BaseModel):
    symbol: str
    name: str
    asset_type: str
    quantity: float
    current_price: float
    allocation: float

class AssetCreate(AssetBase):
    purchase_price: float
    portfolio_id: int

class Asset(AssetBase):
    id: int
    purchase_price: float
    portfolio_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TradeBase(BaseModel):
    portfolio_id: int
    asset_id: int
    trade_type: str
    quantity: float
    price: float
    commission: Optional[float] = 0.0

class TradeCreate(TradeBase):
    pass

class Trade(TradeBase):
    id: int
    execution_time: datetime
    status: str
    
    class Config:
        from_attributes = True

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    user_id: int

class Portfolio(PortfolioBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    assets: List[Asset] = []
    
    class Config:
        from_attributes = True

class PortfolioSummary(BaseModel):
    id: int
    name: str
    total_value: float
    asset_allocation: Dict[str, float]
    performance: Dict[str, float]
    risk_metrics: Dict[str, float]
    top_holdings: List[Dict[str, Any]]