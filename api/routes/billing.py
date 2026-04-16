"""
Stripe billing — checkout sessions for Starter and Growth plans.
"""
import os
import stripe
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

router = APIRouter(prefix="/billing")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICES = {
    "starter": "price_1TMmZuKFKgqAaSVJfm3jFtmN",
    "growth":  "price_1TMmZvKFKgqAaSVJ0j6qBtZb",
}


@router.get("/checkout/{plan}")
async def checkout(plan: str):
    if plan not in PRICES:
        raise HTTPException(status_code=404, detail="Plan not found")

    base_url = os.getenv("BASE_URL", "https://llm-evaltrack-production.up.railway.app")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": PRICES[plan], "quantity": 1}],
        success_url=f"{base_url}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/landing.html",
        allow_promotion_codes=True,
    )
    return RedirectResponse(session.url, status_code=303)
