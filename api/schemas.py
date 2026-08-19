from pydantic import BaseModel
from typing import List, Optional

class CancerStat(BaseModel):
    암종: str
    수검률: float
    전국_평균: float
    대상자: int
    수검자: int

class PrioritySegment(BaseModel):
    성별: str
    연령: str
    암종: str
    대상자: int
    수검률: float
    기대치: float
    잔차: float
    회복여지: int

class SummaryResponse(BaseModel):
    지역명: str
    연도: int
    통합_수검률: float
    전국_순위: int
    전체_시군구수: int
    미수검_인원: int
    암종별_현황: List[CancerStat]
    우선_대상_top3: List[PrioritySegment]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class PriorityItem(BaseModel):
    시도: str
    시군구: str
    성별: str
    연령: str
    암종: str
    대상자: int
    수검자: int
    수검률: float
    기대치: float
    잔차: float
    회복여지: int
    유사_평균: float
    전국_평균: float

class PriorityResponse(BaseModel):
    연도: int
    총_세그먼트수: int
    목록: List[PriorityItem]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class CompareResponse(BaseModel):
    연도: int
    지역명: str
    성별: str
    연령: str
    암종: str
    실제_수검률: float
    기대치: float
    잔차: float
    유사_평균: float
    유사_최소: float
    유사_최대: float
    유사_SE: float
    전국_평균: float
    유사_지역목록: List[str]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class FactorSegment(BaseModel):
    region: str
    sex: str
    age: str
    cancer: str

class ChangeableFactor(BaseModel):
    factor: str
    effect: float
    source: str
    detail_url: Optional[str] = None

class FixedFactor(BaseModel):
    factor: str
    effect: float
    note: Optional[str] = None

class StrataRow(BaseModel):
    stratum: str
    absent: float
    present: float
    diff: float
    absent_target: int

class FactorsResponse(BaseModel):
    segment: FactorSegment
    changeable: List[ChangeableFactor]
    fixed: List[FixedFactor]
    strata_table: List[StrataRow]
    cautions: List[str]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class ActionItem(BaseModel):
    title: str
    why: str
    evidence: str
    expected: Optional[str] = None
    caution: Optional[str] = None

class ActionResponse(BaseModel):
    segment: FactorSegment
    rate: float
    rule_applied: str
    actions: List[ActionItem]
    survey_questions: List[str]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class SampleRequest(BaseModel):
    region: str
    sex: str
    age: str
    cancer: str
    n: int
    seed: int

class SampleResponse(BaseModel):
    campaign_id: int
    segment: FactorSegment
    total_unscreened: int
    contact_n: int
    control_n: int
    assignment_method: str
    note: str
    download: str
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class MessageRequest(BaseModel):
    region: str
    sex: str
    age: str
    cancer: str
    tone: str

class FactUsed(BaseModel):
    label: str
    value: str

class MessageResponse(BaseModel):
    text: str
    facts_used: List[FactUsed]
    reflected: List[str]
    warning: str = "발신 기관명은 보건소입니다. 온코케어를 노출하지 않습니다."
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class ReportRequest(BaseModel):
    region: str
    year: int
    format: str

class ReportResponse(BaseModel):
    text: str
    sections: List[str]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class CampaignReasons(BaseModel):
    안내문_미수신: int
    이유있음: int
    비용우려: int

class CampaignRecordUpdateRequest(BaseModel):
    campaign_id: int
    contacted: int
    reached: int
    reasons: CampaignReasons
    sms_sent: int
    sms_date: str

class CampaignRecordItem(BaseModel):
    id: int
    segment: FactorSegment
    created: str
    contact_n: int
    control_n: int
    contacted: Optional[int] = None
    reached: Optional[int] = None
    reasons: Optional[CampaignReasons] = None
    sms_sent: Optional[int] = None
    sms_date: Optional[str] = None

class RecordsResponse(BaseModel):
    region: str
    year: int
    campaigns: List[CampaignRecordItem]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    segment: FactorSegment
    year: int
    history: List[ChatMessage]

class ChatResponse(BaseModel):
    reply: str
    facts_used: List[FactUsed]
    안내문구: str = "이 값은 평가가 아니라 검토 시작점입니다"

