from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from ..database.postgres import Base

asset_tag_association = Table(
    'asset_tag',
    Base.metadata,
    Column('asset_id', Integer, ForeignKey('assets.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    portfolios = relationship("Portfolio", back_populates="user")
    
class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="portfolios")
    assets = relationship("Asset", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")
    
class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    name = Column(String)
    asset_type = Column(String)  # equity, bond, alternative, cash
    quantity = Column(Float)
    purchase_price = Column(Float)
    current_price = Column(Float)
    allocation = Column(Float)  # Percentage of portfolio
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="assets")
    trades = relationship("Trade", back_populates="asset")
    tags = relationship("Tag", secondary=asset_tag_association, back_populates="assets")
    
class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"))
    trade_type = Column(String)  # buy, sell
    quantity = Column(Float)
    price = Column(Float)
    commission = Column(Float, default=0.0)
    execution_time = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # executed, pending, failed
    
    portfolio = relationship("Portfolio", back_populates="trades")
    asset = relationship("Asset", back_populates="trades")
    
class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    assets = relationship("Asset", secondary=asset_tag_association, back_populates="tags")