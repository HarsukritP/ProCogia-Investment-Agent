from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ...database.postgres import get_db
from ...models.portfolio import Portfolio, Asset, Trade
from ...schemas.portfolio import (
    Portfolio as PortfolioSchema,
    PortfolioCreate,
    PortfolioSummary,
    Asset as AssetSchema,
    AssetCreate,
    Trade as TradeSchema,
    TradeCreate
)
from ...services.get.portfolio_data import portfolio_data_service
from ...services.analyze.risk_analyzer import risk_analyzer
from ...services.analyze.portfolio_optimizer import portfolio_optimizer

router = APIRouter()

@router.get("/", response_model=List[PortfolioSchema])
def get_portfolios(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get all portfolios.
    """
    portfolios = db.query(Portfolio).offset(skip).limit(limit).all()
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioSchema)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Get a specific portfolio by ID.
    """
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio

@router.post("/", response_model=PortfolioSchema)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    """
    Create a new portfolio.
    """
    db_portfolio = Portfolio(**portfolio.dict())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.get("/{portfolio_id}/summary")
def get_portfolio_summary(portfolio_id: int, db: Session = Depends(get_db)):
    """
    Get a summary of the portfolio.
    """
    return portfolio_data_service.get_portfolio_summary(db, portfolio_id)

@router.get("/{portfolio_id}/history")
def get_portfolio_history(
    portfolio_id: int, 
    days: int = Query(30, ge=1, le=365), 
    db: Session = Depends(get_db)
):
    """
    Get historical portfolio data.
    """
    return portfolio_data_service.get_portfolio_history(db, portfolio_id, days)

@router.get("/{portfolio_id}/risk")
def analyze_portfolio_risk(
    portfolio_id: int, 
    risk_threshold: float = Query(0.5, ge=0, le=1), 
    db: Session = Depends(get_db)
):
    """
    Analyze portfolio risk.
    """
    # Get portfolio data first
    portfolio_data = portfolio_data_service.get_portfolio_summary(db, portfolio_id)
    
    # Then analyze risk
    return risk_analyzer.analyze_portfolio_risk(portfolio_data, risk_threshold)

@router.get("/{portfolio_id}/optimize")
def optimize_portfolio(
    portfolio_id: int, 
    target_risk: float = Query(0.5, ge=0, le=1),
    max_allocation_per_asset: Optional[float] = Query(0.2, ge=0, le=1),
    min_bonds_allocation: Optional[float] = Query(0.15, ge=0, le=1),
    max_alternatives_allocation: Optional[float] = Query(0.1, ge=0, le=1),
    liquidity_requirement: Optional[float] = Query(0.3, ge=0, le=1),
    db: Session = Depends(get_db)
):
    """
    Generate portfolio optimization recommendations.
    """
    # Get portfolio data first
    portfolio_data = portfolio_data_service.get_portfolio_summary(db, portfolio_id)
    
    # Create constraints dictionary
    constraints = {
        "max_allocation_per_asset": max_allocation_per_asset,
        "min_bonds_allocation": min_bonds_allocation,
        "max_alternatives_allocation": max_alternatives_allocation,
        "liquidity_requirement": liquidity_requirement
    }
    
    # Generate optimization recommendations
    return portfolio_optimizer.optimize_portfolio(portfolio_data, target_risk, constraints)

@router.post("/{portfolio_id}/assets", response_model=AssetSchema)
def add_asset(
    portfolio_id: int, 
    asset: AssetCreate, 
    db: Session = Depends(get_db)
):
    """
    Add an asset to the portfolio.
    """
    # Check if portfolio exists
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Create the asset
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.post("/{portfolio_id}/trades", response_model=TradeSchema)
def execute_trade(
    portfolio_id: int, 
    trade: TradeCreate, 
    db: Session = Depends(get_db)
):
    """
    Execute a trade in the portfolio.
    """
    # Check if portfolio exists
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if asset exists
    asset = db.query(Asset).filter(Asset.id == trade.asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Create the trade
    db_trade = Trade(**trade.dict(), status="executed")
    db.add(db_trade)
    
    # Update asset quantity
    if trade.trade_type == "buy":
        asset.quantity += trade.quantity
    elif trade.trade_type == "sell":
        if asset.quantity < trade.quantity:
            raise HTTPException(status_code=400, detail="Not enough shares to sell")
        asset.quantity -= trade.quantity
    
    db.commit()
    db.refresh(db_trade)
    return db_trade