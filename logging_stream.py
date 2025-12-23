import asyncio
from typing import Optional

# A single asyncio.Queue used to stream log lines to connected clients
log_queue: asyncio.Queue[str] = asyncio.Queue()

# Event loop captured from FastAPI on startup; needed to schedule from threads
main_loop: Optional[asyncio.AbstractEventLoop] = None

def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global main_loop
    main_loop = loop

def log(msg: str) -> None:
    """Thread-safe log function that enqueues messages for SSE clients.

    Always prints to stdout for local visibility, and if the FastAPI event loop
    is available, schedules a non-blocking put into the shared log_queue in a
    thread-safe way. This works even when called from worker threads.
    """
    # Always print to stdout as a fallback
    print(msg, flush=True)

    # Schedule put on the main event loop so it's safe from any thread
    if main_loop and not main_loop.is_closed():
        try:
            main_loop.call_soon_threadsafe(log_queue.put_nowait, msg)
        except RuntimeError:
            # If the loop is closed or unavailable, ignore the enqueue
            pass
    else:
        # If we don't have a main loop yet, try best-effort enqueue if in an event loop
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(log_queue.put_nowait, msg)
        except RuntimeError:
            # No running loop in this thread yet — nothing more to do
            pass
