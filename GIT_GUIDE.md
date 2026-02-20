# Git 사용 가이드

## Git에 공유하면 안 되는 파일들

다음 파일들은 **개인정보, 통계 데이터, API 키** 등이 포함되어 있어 Git에 커밋하면 안 됩니다.

### 1. 데이터 파일

- **`players.json`**: 플레이어 개인정보 및 통계 데이터
  - Riot ID, Tag Line, PUUID
  - 레이팅 및 포지션 정보
  - 경기 기록 및 챔피언 승률
  - 시너지 데이터

- **`matches.json`**: 매치 기록 데이터
  - Riot API에서 가져온 내전 기록
  - 플레이어 성적 및 통계
  - 게임 상세 정보

### 2. 환경 변수 및 설정 파일

- **`.env`**: 환경 변수 파일
  - Riot API 키
  - Flask Secret Key
  - 기타 민감한 설정

- **`config.py`**: 설정 파일 (API 키 포함 가능)

### 3. 로그 및 캐시 파일

- **`*.log`**: 로그 파일
- **`logs/`**: 로그 디렉토리
- **`*.cache`**: 캐시 파일
- **`session/`**: 세션 파일

### 4. 백업 파일

- **`*.bak`**, **`*.backup`**: 백업 파일
- **`backup/`**: 백업 디렉토리

## .gitignore 설정 방법

### 1. .gitignore 파일 확인

프로젝트 루트에 `.gitignore` 파일이 있는지 확인:

```bash
ls -la .gitignore
cat .gitignore
```

### 2. .gitignore에 추가

이미 `.gitignore` 파일에 필요한 항목들이 포함되어 있습니다. 
만약 추가해야 할 파일이 있다면:

```bash
# .gitignore 파일 편집
nano .gitignore

# 또는
vim .gitignore
```

다음과 같이 추가:

```
# 예시: 추가로 무시할 파일
my_custom_data.json
local_settings.py
```

### 3. 이미 커밋된 파일 제거

만약 실수로 데이터 파일을 커밋했다면:

```bash
# Git 추적에서 제거 (파일은 로컬에 유지)
git rm --cached players.json
git rm --cached matches.json
git rm --cached .env

# .gitignore에 추가되어 있는지 확인
# (이미 추가되어 있음)

# 변경사항 커밋
git add .gitignore
git commit -m "Remove sensitive data files from git tracking"
```

### 4. .gitignore 적용 확인

```bash
# Git 상태 확인
git status

# 무시되는 파일 목록 확인
git status --ignored
```

## Git 사용 시 주의사항

### ✅ 커밋해도 되는 파일

- 소스 코드 (`.py` 파일)
- 템플릿 파일 (`templates/`)
- 정적 파일 (`static/`)
- 설정 예제 파일 (`*.example`, `*_example.py`)
- 문서 파일 (`README.md`, `DEPLOYMENT.md` 등)
- `requirements.txt`

### ❌ 커밋하면 안 되는 파일

- `players.json` - 플레이어 데이터
- `matches.json` - 매치 데이터
- `.env` - 환경 변수
- `*.log` - 로그 파일
- `venv/` - 가상환경 (이미 .gitignore에 포함됨)
- `__pycache__/` - Python 캐시 (이미 .gitignore에 포함됨)

## 초기 Git 설정

### 1. Git 저장소 초기화

```bash
# Git 저장소 초기화
git init

# .gitignore 확인
cat .gitignore

# 상태 확인
git status
```

### 2. 첫 커밋

```bash
# 모든 파일 추가 (자동으로 .gitignore 적용됨)
git add .

# 상태 확인 (데이터 파일이 제외되었는지 확인)
git status

# 첫 커밋
git commit -m "Initial commit: LoL Custom Matchmaker"
```

### 3. 원격 저장소 연결

```bash
# 원격 저장소 추가
git remote add origin <repository-url>

# 브랜치 이름 설정 (필요시)
git branch -M main

# 푸시
git push -u origin main
```

## 데이터 파일 백업

Git에 커밋하지 않으면서 데이터를 백업하려면:

### 1. 로컬 백업

```bash
# 백업 디렉토리 생성
mkdir -p backups

# 데이터 파일 백업
cp players.json backups/players_$(date +%Y%m%d).json
cp matches.json backups/matches_$(date +%Y%m%d).json
```

### 2. 원격 백업 (선택사항)

- 개인 클라우드 스토리지 (Google Drive, Dropbox 등)
- 별도의 비공개 Git 저장소
- 암호화된 백업 서비스

## 예제: .gitignore 파일 구조

현재 프로젝트의 `.gitignore` 파일 구조:

```
# Python 관련
__pycache__/
*.py[cod]
venv/
...

# Flask 관련
instance/
.webassets-cache

# 내부 통계 및 사용자 데이터 파일
players.json
matches.json

# 환경 변수
.env
.env.local

# 로그 및 캐시
*.log
logs/
*.cache

# 백업
*.bak
backup/
...
```

## 문제 해결

### 이미 커밋된 파일 제거

```bash
# Git 히스토리에서 완전히 제거 (주의: 되돌릴 수 없음)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch players.json matches.json" \
  --prune-empty --tag-name-filter cat -- --all

# 강제 푸시 (협업 시 주의!)
git push origin --force --all
```

### .gitignore가 작동하지 않을 때

```bash
# Git 캐시 클리어
git rm -r --cached .

# 다시 추가
git add .

# 커밋
git commit -m "Update .gitignore"
```

## 보안 체크리스트

커밋 전에 확인:

- [ ] `players.json`이 커밋 목록에 없는가?
- [ ] `matches.json`이 커밋 목록에 없는가?
- [ ] `.env` 파일이 커밋 목록에 없는가?
- [ ] API 키가 코드에 하드코딩되지 않았는가?
- [ ] 개인정보가 주석이나 로그에 포함되지 않았는가?

```bash
# 커밋 전 확인 명령어
git status
git diff --cached
```
