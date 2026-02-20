# 라즈베리파이 설치 가이드

## 필수 패키지 설치

### 1. 시스템 패키지 설치

```bash
# 시스템 업데이트
sudo apt update
sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install python3 python3-pip python3-venv git ufw -y
```

### 2. Python 가상환경 생성

```bash
# 프로젝트 디렉토리로 이동
cd ~/RiftBalancer

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate
```

### 3. pip 업그레이드

```bash
pip install --upgrade pip
```

### 4. Python 패키지 설치

```bash
# requirements.txt에서 모든 패키지 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install Flask==3.0.0
pip install requests==2.31.0
pip install Werkzeug==3.0.1
```

### 5. 설치 확인

```bash
# 설치된 패키지 확인
pip list

# Flask 버전 확인
python3 -c "import flask; print(flask.__version__)"
```

## 설치된 패키지 목록

프로젝트에서 사용하는 Python 패키지:

- **Flask==3.0.0**: 웹 프레임워크
- **requests==2.31.0**: HTTP 라이브러리 (Riot API 호출용)
- **Werkzeug==3.0.1**: WSGI 유틸리티 라이브러리 (Flask 의존성)

## 빠른 설치 (원라인)

```bash
cd ~/RiftBalancer && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
```

## 문제 해결

### pip 설치 오류 시

```bash
# pip 업그레이드
pip install --upgrade pip setuptools wheel

# 캐시 클리어 후 재설치
pip cache purge
pip install -r requirements.txt
```

### 가상환경 활성화 오류 시

```bash
# 가상환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 권한 오류 시

```bash
# 사용자 디렉토리에 설치 (권장)
pip install --user -r requirements.txt

# 또는 sudo 사용 (비권장)
sudo pip install -r requirements.txt
```
