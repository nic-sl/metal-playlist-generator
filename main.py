import asyncio
import json
import os
import secrets
import spotipy

from typing import Optional
from dotenv import load_dotenv

from logging_stream import set_main_loop
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.concurrency import run_in_threadpool
from starlette.middleware.sessions import SessionMiddleware
from spotipy.oauth2 import SpotifyOAuth
from starlette.responses import StreamingResponse

from generator import generate
from logging_stream import log_queue, log
from spotify_session.spotify_app_user import SpotifyAppUser
from spotify_session.spotify_token_manager import SpotifyTokenManager

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_SCOPES = os.getenv("SPOTIFY_SCOPES", "playlist-modify-private playlist-modify-public")

app = FastAPI(title="Spotify Playlist Agent")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    set_main_loop(loop)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    spotify_configured = bool(SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "spotify_configured": spotify_configured,
        },
    )


@app.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        return RedirectResponse(url="/?error=spotify_not_configured")

    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        open_browser=False,
    )
    auth_url = sp_oauth.get_authorize_url(state=state)
    return RedirectResponse(url=auth_url)


@app.get("/callback")
async def callback(request: Request, code: Optional[str] = None, state: Optional[str] = None,
                   error: Optional[str] = None):
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        return RedirectResponse(url="/generator")

    if error:
        return RedirectResponse(url=f"/generator?error={error}")

    saved_state = request.session.get("oauth_state")
    if not state or state != saved_state:
        return RedirectResponse(url="/?error=state_mismatch")

    if not code:
        return RedirectResponse(url="/?error=missing_code")

    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=SPOTIFY_SCOPES,
        open_browser=False,
    )
    try:
        token_info = sp_oauth.get_access_token(code)
    except RuntimeError:
        return RedirectResponse(url="/?error=token_exchange_failed")

    me = None
    access_token = token_info.get("access_token")
    if access_token:
        sp = spotipy.Spotify(auth=access_token)
        try:
            me = sp.me()
        except RuntimeError:
            me = None

    request.session["tokens"] = token_info
    request.session["user"] = {
        "display_name": (me or {}).get("display_name") or (me or {}).get("id") or "Spotify User",
        "country": (me or {}).get("country"),
    }
    SpotifyTokenManager.from_token_info(token_info)
    if me:
        SpotifyAppUser.from_json(me)
    return RedirectResponse(url="/generator")


@app.get("/generator", response_class=HTMLResponse)
async def generator(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("generator.html", {"request": request, "user": user})


@app.post("/api/create")
async def create(
        genres: Optional[str] = Form(None),
        artist_count: int = Form(...),
        track_count: int = Form(...)
):
    # Parse genres JSON safely
    if not genres:
        selected_genres = []
    else:
        try:
            selected_genres = json.loads(genres)
        except json.JSONDecodeError:
            selected_genres = []

    log(f"Selected genres: {selected_genres}")
    log(f"Artist count: {artist_count}")
    log(f"Track count: {track_count}")

    # 🔥 Run generate() in a background thread
    await run_in_threadpool(
        generate,
        genres=selected_genres,
        artist_count=artist_count,
        track_count=track_count
    )


@app.get("/api/logs")
async def stream_logs(request: Request):
    async def event_generator():
        while True:
            # Stop if the client disconnects
            if await request.is_disconnected():
                break

            try:
                # Wait for the next log line with heartbeat timeout
                msg = await asyncio.wait_for(log_queue.get(), timeout=15)
                yield f"data: {msg}\n\n"
            except asyncio.TimeoutError:
                # Send a comment ping to keep the SSE connection alive
                yield ": ping\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
