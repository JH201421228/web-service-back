"""
Firebase Realtime Database helper for Reaper game.
Writes game state via Firebase Admin SDK or REST API fallback.
"""
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_firebase_app = None
_db_ref = None
_rest_only = False
_init_attempted = False


def _init_firebase():
    global _firebase_app, _db_ref, _rest_only, _init_attempted
    if _db_ref is not None:
        return True
    if _rest_only or _init_attempted:
        return False

    _init_attempted = True

    try:
        from app.Reaper.core.config import get_reaper_firebase_credentials, REAPER_FIREBASE_DATABASE_URL

        cred_data = get_reaper_firebase_credentials()
        if cred_data is None:
            _rest_only = True
            logger.debug("[ReaperFirebase] Admin SDK credentials not configured; using REST API")
            return False

        import firebase_admin
        from firebase_admin import credentials, db as firebase_db

        try:
            _firebase_app = firebase_admin.get_app("reaper")
        except ValueError:
            cred = credentials.Certificate(cred_data)
            _firebase_app = firebase_admin.initialize_app(
                cred,
                {"databaseURL": REAPER_FIREBASE_DATABASE_URL},
                name="reaper"
            )

        _db_ref = firebase_db.reference("/reaper", app=_firebase_app)
        logger.info("[ReaperFirebase] Admin SDK initialized")
        return True
    except Exception as e:
        _rest_only = True
        logger.debug("[ReaperFirebase] Admin SDK skipped, using REST API: %s", e)
        return False


def _get_db_url() -> str:
    from app.Reaper.core.config import REAPER_FIREBASE_DATABASE_URL
    url = REAPER_FIREBASE_DATABASE_URL.rstrip("/")
    return url


def set_path(path: str, data: Any) -> bool:
    """Write data to a Firebase path."""
    path = path.strip("/")

    if _init_firebase() and _db_ref:
        try:
            _db_ref.child(path).set(data)
            return True
        except Exception as e:
            logger.warning("[ReaperFirebase] SDK write failed, falling back to REST: %s", e)

    # REST API fallback
    try:
        url = f"{_get_db_url()}/reaper/{path}.json"
        with httpx.Client(timeout=5.0) as client:
            resp = client.put(url, content=json.dumps(data))
            return resp.status_code == 200
    except Exception as e:
        logger.error("[ReaperFirebase] REST write failed: %s", e)
        return False


def update_path(path: str, data: dict) -> bool:
    """Update (merge) data at a Firebase path."""
    path = path.strip("/")

    if _init_firebase() and _db_ref:
        try:
            _db_ref.child(path).update(data)
            return True
        except Exception as e:
            logger.warning("[ReaperFirebase] SDK update failed, falling back to REST: %s", e)

    try:
        url = f"{_get_db_url()}/reaper/{path}.json"
        with httpx.Client(timeout=5.0) as client:
            resp = client.patch(url, content=json.dumps(data))
            return resp.status_code == 200
    except Exception as e:
        logger.error("[ReaperFirebase] REST update failed: %s", e)
        return False


def delete_path(path: str) -> bool:
    """Delete data at a Firebase path."""
    path = path.strip("/")

    if _init_firebase() and _db_ref:
        try:
            _db_ref.child(path).delete()
            return True
        except Exception as e:
            logger.warning("[ReaperFirebase] SDK delete failed: %s", e)

    try:
        url = f"{_get_db_url()}/reaper/{path}.json"
        with httpx.Client(timeout=5.0) as client:
            resp = client.delete(url)
            return resp.status_code == 200
    except Exception as e:
        logger.error("[ReaperFirebase] REST delete failed: %s", e)
        return False


def get_path(path: str) -> Any:
    """Get data from a Firebase path."""
    path = path.strip("/")

    if _init_firebase() and _db_ref:
        try:
            return _db_ref.child(path).get()
        except Exception as e:
            logger.warning("[ReaperFirebase] SDK get failed: %s", e)

    try:
        url = f"{_get_db_url()}/reaper/{path}.json"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error("[ReaperFirebase] REST get failed: %s", e)
    return None
