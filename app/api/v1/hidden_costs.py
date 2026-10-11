from fastapi import APIRouter

from app.services.hidden_cost_service import HiddenCostService

router = APIRouter()


@router.get("")
async def hidden_costs():
    return {"items": await HiddenCostService().find_all()}