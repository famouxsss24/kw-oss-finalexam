from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


def request(method: str, path: str, **kwargs: Any) -> Any:
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        st.error(f"요청 오류: {detail}")
    except requests.RequestException as exc:
        st.error(f"백엔드 서버에 연결할 수 없습니다 (API_URL={API_URL})\n{exc}")
    return None
