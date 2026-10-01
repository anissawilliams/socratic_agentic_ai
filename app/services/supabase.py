from functools import lru_cache
from supabase import Client, create_client
from app.config import SUPABASE_SECRET_KEY, SUPABASE_URL
import threading
from supabase import Client, create_client
from app.config import SUPABASE_SECRET_KEY, SUPABASE_URL

_thread_local = threading.local()


def get_supabase_client() -> Client:
    """One client per thread: HTTP/2 connections must not be shared across threads."""
    client = getattr(_thread_local, "client", None)
    if client is None:
        if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be configured.")
        client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
        _thread_local.client = client
    return client

import inspect
import time

import httpx
from postgrest._sync import request_builder as _request_builder
from postgrest.exceptions import APIError

_RETRYABLE_API_CODES = {"PGRST303"}  # auth rejected before any query ran


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, (httpx.ConnectTimeout, httpx.ConnectError)):
        return True  # the request never reached the database
    return isinstance(exc, APIError) and getattr(exc, "code", None) in _RETRYABLE_API_CODES


def _with_safe_retry(original_execute):
    def execute_with_retry(self, *args, **kwargs):
        for attempt in range(1, 4):
            try:
                return original_execute(self, *args, **kwargs)
            except Exception as exc:
                if attempt == 3 or not _is_retryable(exc):
                    raise
                time.sleep(0.5 * attempt)

    execute_with_retry._safe_retry = True
    return execute_with_retry


def _install_safe_retry() -> list[str]:
    """Wrap execute() on every postgrest sync builder that defines it."""
    patched = []
    for name, cls in inspect.getmembers(_request_builder, inspect.isclass):
        execute = cls.__dict__.get("execute")
        if execute is None or getattr(execute, "_safe_retry", False):
            continue
        setattr(cls, "execute", _with_safe_retry(execute))
        patched.append(name)
    return patched


_PATCHED_BUILDERS = _install_safe_retry()