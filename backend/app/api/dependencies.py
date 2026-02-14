from typing import Optional
import os
from uuid import UUID

from fastapi import Header, Query, HTTPException, status
from jose import jwt, JWTError


USE_JWT_AUTH = os.getenv("USE_JWT_AUTH", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "")
JWT_ALGORITHMS = ["HS256"]


async def get_user_id(
    authorization: Optional[str] = Header(None),
    q_user_id: Optional[str] = Query(None, alias="user_id"),
) -> UUID:
    """Resolve `user_id` for endpoints.

    Behavior:
    - If `USE_JWT_AUTH` is true: require `Authorization: Bearer <token>` and decode JWT.
    - If `USE_JWT_AUTH` is false (default): require `user_id` query parameter (backward compat).

    Returns a UUID instance or raises HTTPException.
    """
    if USE_JWT_AUTH:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header"
            )

        try:
            token = authorization.split()[1]
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed Authorization header"
            )

        if not SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server is not configured to validate JWT tokens"
            )

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=JWT_ALGORITHMS)
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

        uid = payload.get("sub") or payload.get("user_id")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identifier"
            )

        try:
            return UUID(uid)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token user identifier is not a valid UUID"
            )

    # Backward-compat mode: require user_id query param
    if q_user_id:
        try:
            return UUID(q_user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="user_id must be a valid UUID"
            )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="user_id query parameter required when JWT auth is disabled"
    )
