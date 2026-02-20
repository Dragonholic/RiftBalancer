# LoL Custom Matchmaker (RiftBalancer)

리그 오브 레전드(LoL) 10인 내전(Custom Game)을 위한 자동 팀 편성 및 레이팅 관리 프로그램입니다.

## 주요 기능

- **자동 팀 편성**: 참가자들의 실력(Rating), 포지션, 폼, 시너지를 바탕으로 예상 승률이 50%에 가장 근접한 팀 조합을 찾아냅니다.
- **Riot API 연동**: 라이엇 공식 API를 통해 플레이어 정보와 경기 데이터를 수집합니다.
- **내전 기록 동기화**: Riot API에서 내전 기록을 자동으로 가져와서 로컬에 저장합니다.
- **레이팅 시스템**: Elo 기반 레이팅 시스템으로 플레이어의 실력을 추적합니다.
- **통계 시스템**: 포지션별, 챔피언별, 플레이어별 상세 통계를 제공합니다.
- **웹 인터페이스**: 라즈베리파이에서 실행 가능한 Flask 기반 웹 애플리케이션입니다.

## 프로젝트 구조

```
RiftBalancer/
├── app.py                  # Flask 웹 애플리케이션
├── riot_api_client.py      # Riot API 클라이언트
├── player.py               # Player 클래스
├── team.py                 # Team 클래스
├── match_manager.py        # 매치메이킹 알고리즘
├── rating_system.py        # 레이팅 업데이트 로직
├── match_storage.py        # 매치 데이터 저장/관리
├── statistics.py            # 통계 계산 모듈
├── test_matchmaker.py      # 테스트 코드
├── requirements.txt        # Python 패키지 의존성
├── players.json            # 플레이어 데이터 (자동 생성)
├── matches.json            # 저장된 매치 데이터 (자동 생성)
├── templates/
│   └── index.html         # 웹 인터페이스 템플릿
└── static/
    ├── css/
    │   └── style.css      # 스타일시트
    └── js/
        └── main.js        # 클라이언트 사이드 JavaScript
```

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Riot API 키 발급

1. [Riot Developer Portal](https://developer.riotgames.com/)에 접속
2. 계정 생성 및 로그인
3. API 키 발급

### 3. 웹 애플리케이션 실행

```bash
python app.py
```

웹 브라우저에서 `http://localhost:5000` 또는 라즈베리파이의 IP 주소로 접속하세요.

### 4. 테스트 실행

더미 데이터를 사용한 테스트를 실행하려면:

```bash
python test_matchmaker.py
```

## 사용 방법

### 플레이어 추가

1. "플레이어 관리" 탭에서 플레이어 정보 입력
   - 이름, Riot ID, Tag Line
   - 주 포지션 및 부 포지션 선택
2. "플레이어 추가" 버튼 클릭

### 매치메이킹

1. "매치메이킹" 탭으로 이동
2. 참가할 10명의 플레이어 선택
3. "매치메이킹 실행" 버튼 클릭
4. 최적의 팀 조합 3가지를 확인

### 경기 결과 입력

1. "경기 결과" 탭으로 이동
2. 각 팀의 플레이어 선택 (각 5명)
3. 승리 팀, 게임 시간, 골드/킬 차이 입력
4. "결과 제출" 버튼 클릭하여 레이팅 업데이트

## 매치메이킹 알고리즘

### Cost Function

매치메이킹 알고리즘은 다음 공식을 사용하여 최적의 팀 조합을 찾습니다:

```
Cost = |팀A MMR 총합 - 팀B MMR 총합| + 포지션 페널티
```

- **MMR 계산**: 각 플레이어의 포지션별 유효 레이팅 합산
  - 주 포지션: 100%
  - 부 포지션: 85%
  - 미숙 포지션: 70%
- **시너지 보너스**: 팀 내 플레이어 간 시너지 점수를 MMR에 반영
- **포지션 페널티**: 부 포지션 +10점, 미숙 포지션 +30점

Cost가 낮을수록 더 균형잡힌 매치입니다.

## 레이팅 시스템

### 업데이트 방식

Elo 레이팅 시스템을 기반으로 하며, 다음 요소를 고려합니다:

- **게임 시간**: 압도적인 짧은 게임(20분 이하)은 높은 가중치, 팽팽한 장기전(40분 이상)은 낮은 가중치
- **점수 차이**: 골드 차이와 킬 차이를 고려하여 매치 중요도 조정
- **K-factor**: 기본값 32, 매치 중요도에 따라 0.5배 ~ 2배 조정

### 레이팅 공식

```
레이팅 변화 = K-factor × (실제 결과 - 예상 승률) × 기여도
```

## 라즈베리파이 배포

상세한 배포 가이드는 [DEPLOYMENT.md](DEPLOYMENT.md)를 참고하세요.

### 빠른 시작

```bash
# 1. 프로젝트 클론 및 설정
cd ~
git clone <repository-url> RiftBalancer
cd RiftBalancer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 방화벽 설정
sudo ufw allow 5000/tcp
sudo ufw enable

# 3. 실행
python3 app.py
```

### 외부 접근 설정

1. **방화벽 포트 열기**: `sudo ufw allow 5000/tcp`
2. **라우터 포트 포워딩**: 외부 포트 → 라즈베리파이 IP:5000
3. **자동 시작 설정**: Systemd 서비스 사용 (DEPLOYMENT.md 참고)

자세한 내용은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참고하세요.

## API Rate Limit

Riot API는 다음 제한이 있습니다:
- 초당 20회 요청
- 2분당 100회 요청

프로그램은 자동으로 Rate Limit을 관리합니다.

## 라이선스

이 프로젝트는 개인 사용을 위한 것입니다. Riot Games의 API 사용 약관을 준수해야 합니다.

## 내전 기록 동기화

### 동작 방식

1. **매치 수집**: Riot API에서 각 플레이어의 최근 매치 히스토리를 가져옵니다.
2. **내전 필터링**: `gameType`이 `CUSTOM_GAME`인 매치만 필터링합니다.
3. **로컬 저장**: 필터링된 매치 데이터를 `matches.json` 파일에 저장합니다.
4. **통계 반영**: 저장된 매치 데이터를 플레이어의 `recent_matches`에 추가하여 통계에 반영합니다.

### 저장되는 데이터

- 매치 ID, 게임 시간, 게임 모드/타입
- 각 플레이어의 KDA, 포지션, 챔피언, 승패
- 팀 정보 및 골드/킬 차이

### 사용 팁

- 처음 동기화 시 시간이 걸릴 수 있습니다 (Rate Limit 고려).
- 정기적으로 동기화하여 최신 통계를 유지하세요.
- 저장된 매치 데이터는 `matches.json`에서 확인할 수 있습니다.

## 참고사항

- Riot API 키는 안전하게 보관하세요.
- 플레이어 데이터는 `players.json` 파일에 저장됩니다.
- 매치 데이터는 `matches.json` 파일에 저장됩니다.
- Rate Limit을 고려하여 동기화는 적절한 간격으로 실행하세요.
- 저장된 매치 데이터는 통계 계산에 자동으로 반영됩니다.
