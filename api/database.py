import sqlite3
import os
from datetime import datetime

DB_DIR = "data/processed"
DB_PATH = os.path.join(DB_DIR, "records.db")

def get_db_connection():
    """SQLite 데이터베이스 커넥션을 생성하여 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 파일 및 테이블을 초기화합니다. 개인정보 컬럼은 일절 생성하지 않습니다."""
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # campaigns 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            sex TEXT NOT NULL,
            age TEXT NOT NULL,
            cancer TEXT NOT NULL,
            created TEXT NOT NULL,
            contact_n INTEGER NOT NULL,
            control_n INTEGER NOT NULL,
            total_unscreened INTEGER NOT NULL,
            seed INTEGER NOT NULL,
            contacted INTEGER,
            reached INTEGER,
            reason_no_notice INTEGER,
            reason_have_excuse INTEGER,
            reason_cost_concern INTEGER,
            sms_sent INTEGER,
            sms_date TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"SQLite database initialized at {DB_PATH}")

# 모듈 로드 시 데이터베이스 초기화 실행
init_db()
