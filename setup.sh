#!/bin/bash
# 라즈베리파이 초기 설정 스크립트

set -e

echo "=========================================="
echo "LoL Custom Matchmaker 설치 스크립트"
echo "=========================================="

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 시스템 업데이트
echo -e "${YELLOW}[1/7] 시스템 업데이트 중...${NC}"
sudo apt update
sudo apt upgrade -y

# 2. 필수 패키지 설치
echo -e "${YELLOW}[2/7] 필수 패키지 설치 중...${NC}"
sudo apt install python3 python3-pip python3-venv git ufw -y

# 3. 가상환경 생성
echo -e "${YELLOW}[3/7] 가상환경 생성 중...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 4. 의존성 설치
echo -e "${YELLOW}[4/7] Python 패키지 설치 중...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 5. 디렉토리 권한 설정
echo -e "${YELLOW}[5/7] 디렉토리 권한 설정 중...${NC}"
chmod +x app.py
mkdir -p static/css static/js templates

# 6. 방화벽 설정
echo -e "${YELLOW}[6/7] 방화벽 설정 중...${NC}"
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 5000/tcp
echo -e "${GREEN}포트 5000이 열렸습니다.${NC}"

# 7. Systemd 서비스 설정
echo -e "${YELLOW}[7/7] Systemd 서비스 설정 중...${NC}"
CURRENT_DIR=$(pwd)
USER_NAME=$(whoami)

# 서비스 파일 경로 수정
sed "s|/home/pi/RiftBalancer|$CURRENT_DIR|g" riftbalancer.service | \
sed "s|User=pi|User=$USER_NAME|g" > /tmp/riftbalancer.service

sudo cp /tmp/riftbalancer.service /etc/systemd/system/riftbalancer.service
sudo systemctl daemon-reload

echo ""
echo -e "${GREEN}=========================================="
echo "설치 완료!"
echo "==========================================${NC}"
echo ""
echo "다음 명령어로 서비스를 시작할 수 있습니다:"
echo "  sudo systemctl start riftbalancer.service"
echo ""
echo "자동 시작을 활성화하려면:"
echo "  sudo systemctl enable riftbalancer.service"
echo ""
echo "서비스 상태 확인:"
echo "  sudo systemctl status riftbalancer.service"
echo ""
echo "라즈베리파이 IP 주소:"
hostname -I | awk '{print $1}'
echo ""
echo "외부 접속을 위해 라우터에서 포트 포워딩을 설정하세요."
echo "자세한 내용은 DEPLOYMENT.md를 참고하세요."
