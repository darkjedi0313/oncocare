from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.schemas import ChatRequest, ChatResponse, FactUsed
from api.llm import generate_with_numeric_validation
from api.routers.query import get_db
import numpy as np

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def post_chat(req: ChatRequest):
    db = get_db()
    df_exp = db.expectation
    df_sim = db.similar_rates
    
    # 1. 대상 세그먼트 조회
    region = req.segment.region
    sex = req.segment.sex
    age = req.segment.age
    cancer = req.segment.cancer
    year = req.year
    
    seg_row = df_exp[
        (df_exp['키'] == region) & 
        (df_exp['성별'] == sex) & 
        (df_exp['연령'] == age) & 
        (df_exp['암종'] == cancer) & 
        (df_exp['연도'] == year)
    ]
    
    if seg_row.empty:
        raise HTTPException(status_code=404, detail="해당 조건의 세그먼트 데이터를 찾을 수 없습니다.")
        
    row = seg_row.iloc[0]
    rate = float(row['수검률'])
    expected = float(row['기대치'])
    residual = float(row['잔차'])
    recovery = int(np.round(row['회복여지']))
    
    # 2. 유사지역 평균 조회
    sim_row = df_sim[
        (df_sim['시도'] == row['시도']) & 
        (df_sim['시군구'] == row['시군구']) & 
        (df_sim['성별'] == sex) & 
        (df_sim['연령'] == age) & 
        (df_sim['암종'] == cancer) & 
        (df_sim['연도'] == year)
    ]
    similar_rate = float(sim_row.iloc[0]['유사_평균']) if not sim_row.empty else rate
    
    # 3. 데이터 컨텍스트 팩트 정의
    facts = [
        f"조회 지역: {row['시도']} {row['시군구']}",
        f"대상 세그먼트: {sex} {age}세 · {cancer}",
        f"실제 수검률: {rate:.1f}%",
        f"모델 기대치: {expected:.1f}%",
        f"기대치 대비 격차(잔차): {residual:.1f}%p",
        f"유사지역 20곳 평균 수검률: {similar_rate:.1f}%",
        f"유사지역 평균 대비 격차: {(rate - similar_rate):.1f}%p",
        f"수검 독려 시 기대 회복 인원 (회복여지 상한): {recovery:,}명"
    ]
    
    facts_text = "\n".join([f"- {f}" for f in facts])
    
    # 4. 프롬프트 작성 (컨텍스트 팩트 주입)
    history_str = ""
    for msg in req.history:
        role_label = "질문" if msg.role == "user" else "답변"
        history_str += f"{role_label}: {msg.content}\n"
        
    user_msg = req.history[-1].content if req.history else "안녕하세요."
    
    prompt = (
        f"## [데이터 팩트 정보]\n"
        f"{facts_text}\n\n"
        f"## [이전 대화 내역]\n"
        f"{history_str}\n"
        f"## [담당자의 현재 질문]\n"
        f"{user_msg}\n"
    )
    
    system_instruction = (
        "당신은 공공보건 6대암 국가검진 분석 대시보드의 대화형 AI 어시스턴트 '온코(Onco)'입니다.\n"
        "제시된 [데이터 팩트 정보] 안의 숫자와 정보만을 진실로 인용하여 질문에 대답하십시오.\n"
        "임의로 지역 수검률이나 순위 등의 수치를 날조하거나 다른 숫자를 지어내 말하지 마십시오.\n"
        "답변은 정중하고 신뢰감을 주는 존댓말로 마크다운 서식을 활용해 알기 쉽게 설명해야 합니다."
    )
    
    # LLM 호출 및 가드레일 수치 대조
    reply = generate_with_numeric_validation(
        prompt=prompt,
        system_instruction=system_instruction,
        max_retries=2
    )
    
    # facts_used 목록 구성
    facts_used = [
        FactUsed(label="실제 수검률", value=f"{rate:.1f}%"),
        FactUsed(label="모델 기대치", value=f"{expected:.1f}%"),
        FactUsed(label="유사지역 평균", value=f"{similar_rate:.1f}%"),
        FactUsed(label="격차", value=f"{(rate - similar_rate):.1f}%p"),
        FactUsed(label="기대 회복 인원", value=f"{recovery:,}명")
    ]
    
    return ChatResponse(
        reply=reply,
        facts_used=facts_used
    )
