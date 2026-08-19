import sqlite3
import os
from api.database import DB_PATH, get_db_connection

def test_sqlite_records_schema_no_personal_info():
    """
    SQLite campaigns 테이블에 개인 식별 정보 컬럼이 존재하지 않는지 검증합니다.
    """
    # database.py 로드 시 자동 생성되므로 DB 파일이 무조건 존재해야 함
    assert os.path.exists(DB_PATH), f"Database file not found at {DB_PATH}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(campaigns)")
    columns = cursor.fetchall()
    conn.close()
    
    assert len(columns) > 0, "campaigns 테이블이 비어있거나 생성되지 않았습니다."
    
    # 금지된 개인 식별 정보 관련 키워드 (대소문자 구분 없이 매칭)
    forbidden_keywords = [
        "이름", "성명", "주민", "전화", "주소", "연락처", "이메일", "폰", "모바일", "고객", "주민번호",
        "name", "jumin", "phone", "address", "email", "ssn", "mobile", "personal", "user", "patient"
    ]
    
    detected_personal_info = []
    for col in columns:
        col_name = col['name'].lower()
        for kw in forbidden_keywords:
            if kw in col_name:
                detected_personal_info.append((col['name'], kw))
                
    # 개인정보 컬럼이 0개여야 패스
    assert len(detected_personal_info) == 0, f"개인 식별 우려 컬럼이 발견되었습니다: {detected_personal_info}"
