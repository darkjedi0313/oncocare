from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    role: str
    scope: str
    assigned_region: str
    label: str

# 페르소나 매핑 사전 (영문 및 한글 아이디 양쪽 다 동일한 패스워드로 허용)
PERSONAS = {
    "healthcenter": {
        "role": "healthcenter",
        "scope": "sgg",
        "assigned_region": "서울특별시|양천구",
        "label": "양천구보건소 담당자"
    },
    "보건소": {
        "role": "healthcenter",
        "scope": "sgg",
        "assigned_region": "서울특별시|양천구",
        "label": "양천구보건소 담당자"
    },
    "mohw": {
        "role": "mohw",
        "scope": "all",
        "assigned_region": "all",
        "label": "보건복지부 관리자"
    },
    "보건복지부": {
        "role": "mohw",
        "scope": "all",
        "assigned_region": "all",
        "label": "보건복지부 관리자"
    },
    "ncc": {
        "role": "ncc",
        "scope": "all",
        "assigned_region": "all",
        "label": "국립암센터 연구원"
    },
    "국립암센터": {
        "role": "ncc",
        "scope": "all",
        "assigned_region": "all",
        "label": "국립암센터 연구원"
    },
    "rcc": {
        "role": "rcc",
        "scope": "sido",
        "assigned_region": "서울특별시",
        "label": "지역암센터 담당자"
    },
    "지역암센터": {
        "role": "rcc",
        "scope": "sido",
        "assigned_region": "서울특별시",
        "label": "지역암센터 담당자"
    }
}

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    username_clean = req.username.strip()
    password_clean = req.password.strip()
    
    # ⚠️ 보안 경고 (Security Warning):
    # 본 코드는 시연용 프로토타입으로, 비밀번호 평문 비교 방식을 임시 사용합니다.
    # 실서비스 배포 시에는 반드시 bcrypt 해시 비교와 JWT 토큰 세션 인증 체계로 전환하십시오.
    if username_clean in PERSONAS and password_clean == username_clean:
        p_info = PERSONAS[username_clean]
        return LoginResponse(
            username=username_clean,
            role=p_info["role"],
            scope=p_info["scope"],
            assigned_region=p_info["assigned_region"],
            label=p_info["label"]
        )
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="아이디 또는 비밀번호가 올바르지 않습니다."
    )
