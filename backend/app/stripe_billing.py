from __future__ import annotations

import json
import os

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings

router = APIRouter()


@router.post("/checkout-session")
def checkout_session():
    """Demo checkout — set STRIPE_SECRET_KEY + STRIPE_PRICE_ID for live Stripe Checkout."""
    price_id = os.environ.get("STRIPE_PRICE_ID", "").strip()
    if settings.stripe_secret_key and price_id:
        try:
            import stripe

            stripe.api_key = settings.stripe_secret_key
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=f"{settings.frontend_origin}/app?paid=1",
                cancel_url=f"{settings.frontend_origin}/app",
            )
            return {"url": session.url, "id": session.id}
        except Exception as e:
            raise HTTPException(500, str(e))
    return {
        "url": f"{settings.frontend_origin}/app?demo_checkout=1",
        "id": "demo_session",
        "note": "Set STRIPE_SECRET_KEY and STRIPE_PRICE_ID for live billing.",
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(None)):
    payload = await request.body()
    if settings.stripe_webhook_secret and stripe_signature:
        try:
            import stripe

            stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=settings.stripe_webhook_secret,
            )
        except Exception as e:
            raise HTTPException(400, str(e))
    else:
        try:
            json.loads(payload.decode() or "{}")
        except json.JSONDecodeError:
            pass
    return {"received": True}
