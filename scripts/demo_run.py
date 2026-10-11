import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.rag.pipeline import answer
from app.services.hidden_cost_service import HiddenCostService

QUESTIONS = [
    "How much did I spend on software subscriptions in 2024?",
    "Is any of it deductible, and which § applies?",
    "Did I double-pay anything?",
]


async def main() -> None:
    print("=== Hidden costs ===")
    for hc in await HiddenCostService().find_all():
        print(f"- {hc['kind']}: {hc['amount']:.2f} € ({hc['vendor']})")
        print(f"  {hc['suggestion']}")
        print(f"  evidence: {', '.join(hc['evidence'])}")

    print("\n=== Chat ===")
    for q in QUESTIONS:
        print(f"\nQ: {q}")
        res = await answer(q)
        print(f"A: {res['answer']}")
        print(f"   citations: {[c['cite'] for c in res['citations']]}")


if __name__ == "__main__":
    asyncio.run(main())