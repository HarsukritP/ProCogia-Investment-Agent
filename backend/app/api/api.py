from fastapi import APIRouter


from .endpoints import portfolio, market, trade, auth, chat

# Create main API router
api_router = APIRouter()

# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(trade.router, prefix="/trade", tags=["trade"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])