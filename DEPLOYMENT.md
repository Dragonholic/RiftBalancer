# 라즈베리파이 배포 가이드

라즈베리파이에 LoL Custom Matchmaker를 배포하고 외부에서 접근할 수 있도록 설정하는 방법입니다.

## 1. 라즈베리파이 기본 설정

### 1.1 시스템 업데이트

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2 Python 및 필수 패키지 설치

```bash
sudo apt install python3 python3-pip python3-venv git -y
```

### 1.3 프로젝트 클론 및 설정

```bash
# 홈 디렉토리로 이동
cd ~

# 프로젝트 클론 (또는 직접 업로드)
git clone <repository-url> RiftBalancer
cd RiftBalancer

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

## 2. 애플리케이션 설정

### 2.1 환경 변수 설정 (선택사항)

```bash
# .env 파일 생성
nano .env
```

다음 내용 추가:
```
SECRET_KEY=your-secret-key-here-change-this
FLASK_ENV=production
```

### 2.2 app.py 수정 (포트 및 호스트 설정)

`app.py` 파일의 마지막 부분을 확인하고 필요시 수정:

```python
if __name__ == '__main__':
    load_players_from_file()
    app.run(host='0.0.0.0', port=5000, debug=False)  # debug=False로 변경
```

## 3. 방화벽 설정

### 3.1 UFW 방화벽 설치 및 설정

```bash
# UFW 설치 (이미 설치되어 있을 수 있음)
sudo apt install ufw -y

# 기본 정책 설정
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH 포트 허용 (중요: 먼저 해야 함!)
sudo ufw allow 22/tcp

# Flask 애플리케이션 포트 허용
sudo ufw allow 5000/tcp

# 또는 특정 IP만 허용하려면:
# sudo ufw allow from <your-ip> to any port 5000

# 방화벽 활성화
sudo ufw enable

# 상태 확인
sudo ufw status
```

### 3.2 iptables 사용 시 (UFW 대신)

```bash
# 포트 5000 허용
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# 설정 저장 (iptables-persistent 설치 필요)
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

## 4. 라우터 포트 포워딩 설정

외부에서 접근하려면 라우터에서 포트 포워딩을 설정해야 합니다.

### 4.1 라우터 설정 방법

1. **라우터 관리 페이지 접속**
   - 일반적으로 `192.168.0.1` 또는 `192.168.1.1`
   - 브라우저에서 접속

2. **포트 포워딩 메뉴 찾기**
   - "포트 포워딩", "Virtual Server", "NAT", "고급 설정" 등
   - 제조사마다 다름

3. **포트 포워딩 규칙 추가**
   - **외부 포트**: 원하는 포트 (예: 8080, 9000 등)
   - **내부 IP**: 라즈베리파이의 IP 주소 (예: 192.168.1.100)
   - **내부 포트**: 5000
   - **프로토콜**: TCP

4. **라즈베리파이 IP 확인**
   ```bash
   hostname -I
   ```

### 4.2 공인 IP 확인

```bash
curl ifconfig.me
```

또는 브라우저에서 `https://whatismyipaddress.com` 접속

## 5. Systemd 서비스 설정 (자동 시작)

### 5.1 서비스 파일 생성

```bash
sudo nano /etc/systemd/system/riftbalancer.service
```

다음 내용 추가 (경로는 실제 경로에 맞게 수정):

```ini
[Unit]
Description=LoL Custom Matchmaker Web Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RiftBalancer
Environment="PATH=/home/pi/RiftBalancer/venv/bin"
ExecStart=/home/pi/RiftBalancer/venv/bin/python3 /home/pi/RiftBalancer/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5.2 서비스 활성화 및 시작

```bash
# 서비스 파일 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable riftbalancer.service

# 서비스 시작
sudo systemctl start riftbalancer.service

# 상태 확인
sudo systemctl status riftbalancer.service

# 로그 확인
sudo journalctl -u riftbalancer.service -f
```

## 6. Nginx 리버스 프록시 설정 (권장)

Nginx를 사용하면 더 안전하고 효율적으로 서비스를 제공할 수 있습니다.

### 6.1 Nginx 설치

```bash
sudo apt install nginx -y
```

### 6.2 Nginx 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/riftbalancer
```

다음 내용 추가:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 도메인이 있으면 입력, 없으면 IP 주소

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6.3 Nginx 설정 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/riftbalancer /etc/nginx/sites-enabled/

# 기본 설정 비활성화 (선택사항)
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx

# Nginx 자동 시작 설정
sudo systemctl enable nginx
```

### 6.4 방화벽 설정 업데이트

Nginx를 사용하면 포트 80(HTTP) 또는 443(HTTPS)만 열면 됩니다:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Flask 포트는 외부에 노출할 필요 없음
```

## 7. HTTPS 설정 (Let's Encrypt, 선택사항)

### 7.1 Certbot 설치

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 7.2 SSL 인증서 발급

```bash
sudo certbot --nginx -d your-domain.com
```

도메인이 없으면 이 단계는 건너뛰세요.

## 8. 보안 고려사항

### 8.1 기본 보안 설정

1. **강력한 비밀번호 사용**
   ```bash
   passwd
   ```

2. **SSH 키 인증 사용 (권장)**
   ```bash
   # 로컬에서 SSH 키 생성
   ssh-keygen -t rsa -b 4096
   
   # 라즈베리파이에 키 복사
   ssh-copy-id pi@raspberry-pi-ip
   ```

3. **SSH 비밀번호 로그인 비활성화** (키 인증 설정 후)
   ```bash
   sudo nano /etc/ssh/sshd_config
   # PasswordAuthentication no 로 변경
   sudo systemctl restart ssh
   ```

4. **Flask Secret Key 변경**
   - `app.py`에서 `SECRET_KEY`를 강력한 랜덤 문자열로 변경
   - 또는 환경 변수로 설정

### 8.2 방화벽 추가 보안

```bash
# 특정 IP만 허용하려면
sudo ufw allow from <your-home-ip> to any port 22
sudo ufw allow from <your-home-ip> to any port 5000

# 또는 fail2ban 설치 (무차별 대입 공격 방지)
sudo apt install fail2ban -y
```

## 9. 접속 확인

### 9.1 로컬에서 확인

```bash
# 라즈베리파이에서
curl http://localhost:5000

# 또는 브라우저에서
http://localhost:5000
```

### 9.2 외부에서 확인

1. **같은 네트워크에서**
   ```
   http://<라즈베리파이-내부-IP>:5000
   ```

2. **외부 네트워크에서**
   ```
   http://<공인-IP>:<외부-포트>
   ```

## 10. 문제 해결

### 10.1 서비스가 시작되지 않을 때

```bash
# 로그 확인
sudo journalctl -u riftbalancer.service -n 50

# 수동 실행으로 오류 확인
cd /home/pi/RiftBalancer
source venv/bin/activate
python3 app.py
```

### 10.2 포트가 열리지 않을 때

```bash
# 포트 사용 확인
sudo netstat -tlnp | grep 5000

# 방화벽 상태 확인
sudo ufw status verbose

# 방화벽 로그 확인
sudo tail -f /var/log/ufw.log
```

### 10.3 외부 접속이 안 될 때

1. 라우터 포트 포워딩 확인
2. 공인 IP 확인 (동적 IP일 수 있음)
3. 방화벽 설정 확인
4. ISP가 포트 차단하는지 확인

## 11. 유용한 명령어

```bash
# 서비스 재시작
sudo systemctl restart riftbalancer.service

# 서비스 중지
sudo systemctl stop riftbalancer.service

# 서비스 시작
sudo systemctl start riftbalancer.service

# 서비스 상태 확인
sudo systemctl status riftbalancer.service

# 실시간 로그 확인
sudo journalctl -u riftbalancer.service -f

# 디스크 사용량 확인
df -h

# 메모리 사용량 확인
free -h

# 네트워크 연결 확인
netstat -tuln
```

## 12. 동적 IP 대응 (선택사항)

공인 IP가 자주 바뀌는 경우, DDNS(Dynamic DNS) 서비스를 사용할 수 있습니다.

- No-IP: https://www.noip.com/
- Duck DNS: https://www.duckdns.org/

## 참고사항

- 라즈베리파이의 IP 주소가 변경될 수 있으므로, 라우터에서 고정 IP를 할당하는 것을 권장합니다.
- 보안을 위해 가능하면 VPN을 통해 접속하거나, 최소한 IP 화이트리스트를 사용하세요.
- 프로덕션 환경에서는 반드시 HTTPS를 사용하세요.
