"""
설정 예제 파일
실제 사용 시 이 파일을 config.py로 복사하고 값을 수정하세요.
"""

# Riot API 키 (Riot Developer Portal에서 발급)
RIOT_API_KEY = "YOUR_RIOT_API_KEY_HERE"

# Flask 시크릿 키 (프로덕션 환경에서는 반드시 변경하세요)
SECRET_KEY = "change-this-to-a-random-secret-key-in-production"

# 서버 설정
HOST = "0.0.0.0"  # 모든 네트워크 인터페이스에서 접근 가능
PORT = 5000
DEBUG = False  # 프로덕션 환경에서는 False로 설정
