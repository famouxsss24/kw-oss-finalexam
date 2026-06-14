from __future__ import annotations

from typing import Any


ASSET_WEIGHTS = {
    "무기체계 설계도면": 28,
    "소스코드": 22,
    "인사·계약정보": 16,
    "시험데이터": 20,
    "네트워크 인프라": 22,
    "문서·산출물": 12,
}

THREAT_WEIGHTS = {
    "APT 표적공격": 28,
    "랜섬웨어": 24,
    "공급망 침해": 24,
    "내부자 유출": 22,
    "물리적 침입": 18,
    "피싱": 14,
}

SECURITY_LEVEL_ADJUST = {
    "매우 낮음": 20,
    "낮음": 15,
    "보통": 8,
    "높음": 3,
    "매우 높음": 0,
}

ORG_ADJUST = {
    "중소협력사": 8,
    "연구소": 5,
    "대기업": 2,
}


def build_recommendation(mode: str, answers: dict[str, Any]) -> dict[str, Any]:
    threat = _first_value(answers.get("threat_type")) or _first_value(answers.get("concerns")) or "APT 표적공격"
    asset = _first_value(answers.get("asset")) or "무기체계 설계도면"
    security_level = answers.get("security_level", "보통")
    org_size = answers.get("org_size", "중소협력사")
    damage_flags = answers.get("damage_flags", [])
    regulations = answers.get("regulations", [])

    score = 18
    score += ASSET_WEIGHTS.get(asset, 14)
    score += THREAT_WEIGHTS.get(threat, 18)
    score += SECURITY_LEVEL_ADJUST.get(security_level, 8)
    score += ORG_ADJUST.get(org_size, 4)
    score += min(len(damage_flags) * 6, 18)
    score = max(0, min(score, 100))

    return {
        "risk_score": score,
        "risk_level": _risk_level(score),
        "threat_category": threat,
        "priority": _priority(score),
        "summary": _summary(mode, threat, asset, _priority(score)),
        "recommendations": _recommendations(mode, threat, asset),
        "regulations": _regulations(regulations, asset),
    }


def _first_value(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str) and value:
        return value
    return None


def _risk_level(score: int) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def _priority(score: int) -> str:
    if score >= 75:
        return "긴급"
    if score >= 45:
        return "주의"
    return "관찰"


def _summary(mode: str, threat: str, asset: str, priority: str) -> str:
    if mode == "incident":
        return f"{asset}에 대한 {threat} 정황이 있어 {priority} 대응이 필요합니다."
    return f"{asset} 보호 관점에서 {threat} 대비 수준을 우선 점검해야 합니다."


def _recommendations(mode: str, threat: str, asset: str) -> list[dict[str, str]]:
    if mode == "incident":
        return [
            {
                "type": "기술적",
                "title": "영향 구간 격리 및 침해지표 차단",
                "detail": f"{threat} 의심 구간을 네트워크에서 분리하고 방화벽, EDR, 프록시에 관련 IOC를 차단합니다.",
            },
            {
                "type": "관리적",
                "title": "접근권한 전수 점검 및 자격증명 갱신",
                "detail": f"{asset} 접근 계정을 전수 조사하고 권한 최소화, 비밀번호 변경, MFA 적용을 수행합니다.",
            },
            {
                "type": "물리적",
                "title": "출입·반출 기록 대조",
                "detail": "사고 시점의 출입기록과 자료 반출 이력을 대조하고 보안구역 반출 승인을 임시 강화합니다.",
            },
        ]

    return [
        {
            "type": "기술적",
            "title": "핵심 자산 접근 경로 분리",
            "detail": f"{asset} 저장소를 일반 업무망과 분리하고 접근 로그, EDR, 백업 상태를 주기 점검합니다.",
        },
        {
            "type": "관리적",
            "title": "부서 단위 대응 역할 지정",
            "detail": f"{threat} 발생 시 신고, 격리, 로그 확보 담당자를 지정하고 모의훈련 절차를 문서화합니다.",
        },
        {
            "type": "물리적",
            "title": "보안구역 출입 통제 강화",
            "detail": "핵심 자료 취급 구역의 출입권한을 재검토하고 반출 승인 절차와 보관함 관리 상태를 점검합니다.",
        },
    ]


def _regulations(selected: list[str], asset: str) -> list[str]:
    mapped = list(selected)
    if asset in {"무기체계 설계도면", "시험데이터"} and "방위산업기술보호법" not in mapped:
        mapped.append("방위산업기술보호법")
    if "없음" in mapped and len(mapped) > 1:
        mapped.remove("없음")
    return mapped or ["내부 보안규정"]
