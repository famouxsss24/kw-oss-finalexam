from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from logic import build_recommendation
from storage import (
    add_case_note,
    create_case,
    get_department,
    get_department_by_code,
    get_or_create_operator,
    init_db,
    list_case_notes,
    list_cases,
    update_case_status,
)


app = FastAPI(title="Defense First API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    department_code: str = Field(min_length=3)
    operator_name: str = Field(min_length=1)


class RecommendRequest(BaseModel):
    department_id: int
    operator_id: int
    mode: str
    answers: dict[str, Any]


class StatusRequest(BaseModel):
    department_id: int
    status: str


class NoteRequest(BaseModel):
    department_id: int
    operator_id: int
    note: str = Field(min_length=1)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    department = get_department_by_code(payload.department_code)
    if department is None:
        raise HTTPException(
            status_code=401,
            detail="등록되지 않은 부서 코드입니다. 예시: DAPA-OPS, RND-LAB, SUPPLY-7",
        )

    operator = get_or_create_operator(department["id"], payload.operator_name)
    return {
        "department_id": department["id"],
        "department_code": department["code"],
        "department_name": department["name"],
        "operator_id": operator["id"],
        "operator_name": operator["name"],
    }


@app.post("/recommend")
def recommend(payload: RecommendRequest) -> dict[str, Any]:
    department = get_department(payload.department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")

    result = build_recommendation(payload.mode, payload.answers)
    case = create_case(
        department_id=payload.department_id,
        operator_id=payload.operator_id,
        mode=payload.mode,
        answers=payload.answers,
        result=result,
    )
    return {"case": case, "result": result}


@app.get("/departments/{department_id}/cases")
def get_cases(department_id: int) -> dict[str, Any]:
    department = get_department(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    return {"department": department, "cases": list_cases(department_id)}


@app.patch("/cases/{case_id}/status")
def patch_case_status(case_id: int, payload: StatusRequest) -> dict[str, Any]:
    try:
        case = update_case_status(case_id, payload.department_id, payload.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="케이스를 찾을 수 없습니다.")
    return {"case": case}


@app.get("/cases/{case_id}/notes")
def get_notes(case_id: int, department_id: int) -> dict[str, Any]:
    try:
        notes = list_case_notes(case_id, department_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="케이스를 찾을 수 없습니다.")
    return {"notes": notes}


@app.post("/cases/{case_id}/notes")
def post_note(case_id: int, payload: NoteRequest) -> dict[str, Any]:
    try:
        note = add_case_note(
            case_id=case_id,
            department_id=payload.department_id,
            operator_id=payload.operator_id,
            note=payload.note,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="케이스를 찾을 수 없습니다.")
    return {"note": note}
