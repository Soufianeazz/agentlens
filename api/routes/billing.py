"""
Stripe billing — checkout sessions for Starter and Growth plans.
"""
import os
import stripe
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/billing")

stripe.api_key = (os.getenv("STRIPE_SECRET_KEY") or os.getenv("stripe_secret_key", "")).strip()

PLANS = {
    "starter": {
        "name": "AgentLens Starter",
        "description": "Managed hosting, up to 500k calls/month, 1 project, email support",
        "amount": 19900,
    },
    "growth": {
        "name": "AgentLens Growth",
        "description": "Up to 5M calls/month, 3 projects, Slack support, priority features",
        "amount": 49900,
    },
}


@router.get("/checkout/{plan}")
async def checkout(plan: str):
    if plan not in PLANS:
        raise HTTPException(status_code=404, detail="Plan not found")

    p = PLANS[plan]
    base_url = os.getenv("BASE_URL", "https://llm-evaltrack-production.up.railway.app")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {
                    "name": p["name"],
                    "description": p["description"],
                },
                "unit_amount": p["amount"],
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }],
        success_url=f"{base_url}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/landing.html",
        allow_promotion_codes=True,
    )
    return RedirectResponse(session.url, status_code=303)
