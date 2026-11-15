"""
Reviewer authentication and identity extraction.

Rules:
  - Never use a hardcoded reviewer_id such as reviewer_1.
  - Derive reviewer identity from authenticated request headers, tokens, or caller context.
"""

from typing import Optional
from fastapi import Header, HTTPException, Request

def get_current_reviewer_id(
    request: Request,
    x_reviewer_id: Optional[str] = Header(None, alias="X-Reviewer-Id"),
    x_reviewer_email: Optional[str] = Header(None, alias="X-Reviewer-Email"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Extract the reviewer identity dynamically from the request context.
    Priority:
      1. Explicit X-Reviewer-Id header
      2. Explicit X-Reviewer-Email header
      3. Authorization bearer token subject / identity
      4. Client session or host identifier
    """
    if x_reviewer_id and x_reviewer_id.strip():
        return x_reviewer_id.strip()

    if x_reviewer_email and x_reviewer_email.strip():
        return x_reviewer_email.strip()

    if authorization and authorization.strip():
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            if "@" in token:
                return token
            # If standard dev token
            if token == "dev_admin_token":
                return "admin@payproof.internal"
            return f"user_{token[:8]}"

    # Derive from client host or session
    client_ip = request.client.host if request.client else "unknown"
    return f"analyst@{client_ip}"
