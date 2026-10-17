from fastapi import APIRouter

from app.api.v1 import (
    banking,
    chat,
    documents,
    health,
    hidden_costs,
    invoices,
    law,
    tax_tips,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(banking.router, prefix="/banking", tags=["banking"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(hidden_costs.router, prefix="/hidden-costs", tags=["hidden-costs"])
api_router.include_router(tax_tips.router, prefix="/tax-tips", tags=["tax-tips"])
api_router.include_router(law.router, prefix="/law", tags=["law"])