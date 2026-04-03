from __future__ import annotations

import secrets
import urllib.parse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config import settings

router = APIRouter()


@router.get("/google/start")
def google_start():
    if not settings.google_client_id:
        raise HTTPException(501, "Google OAuth not configured (set GOOGLE_CLIENT_ID)")
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str | None = Query(None)):
    """Backend-side token exchange example — frontend typically exchanges code with secret."""
    if not settings.google_client_secret or not settings.google_client_id:
        raise HTTPException(501, "Google OAuth secrets not set")
    if not code:
        raise HTTPException(400, "Missing code")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if r.status_code != 200:
        raise HTTPException(400, "Token exchange failed")
    return r.json()
