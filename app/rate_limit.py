
import time
from collections import defaultdict

RATE_LIMIT = 5
WINDOW_SECONDS = 60

# Store request timestamps for each client IP.
request_history = defaultdict(list)


def is_rate_limited(client_ip: str) -> tuple[bool, int]:
    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Keep only requests made within the current time window.
    recent_requests = [
        timestamp
        for timestamp in request_history[client_ip]
        if timestamp > window_start
    ]

    request_history[client_ip] = recent_requests

    # Reject the request if the client has reached the limit.
    if len(recent_requests) >= RATE_LIMIT:
        retry_after = int(
            WINDOW_SECONDS - (now - recent_requests[0])
        ) + 1
        return True, retry_after

    # Record this request.
    request_history[client_ip].append(now)

    return False, 0
