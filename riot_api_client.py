"""
Riot API 클라이언트 모듈
라이엇 공식 API와의 통신을 담당합니다.
"""

import requests
import time
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class RateLimiter:
    """API Rate Limit 관리를 위한 클래스"""
    requests_per_second: int = 20
    requests_per_2min: int = 100
    
    def __init__(self):
        self.last_request_time = 0
        self.request_times = []
    
    def wait_if_needed(self):
        """Rate Limit을 고려하여 필요시 대기"""
        current_time = time.time()
        
        # 초당 요청 제한 체크
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        # 2분당 요청 제한 체크
        two_minutes_ago = current_time - 120
        self.request_times = [t for t in self.request_times if t > two_minutes_ago]
        
        if len(self.request_times) >= self.requests_per_2min:
            sleep_time = 120 - (current_time - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(time.time())
        self.last_request_time = time.time()


class RiotAPIClient:
    """
    라이엇 API와 통신하는 클라이언트 클래스
    
    Attributes:
        api_key: 라이엇 API 키
        rate_limiter: Rate Limit 관리 객체
        base_url_account: Account API 기본 URL
        base_url_match: Match API 기본 URL
    """
    
    BASE_URL_ACCOUNT = "https://asia.api.riotgames.com"
    BASE_URL_MATCH = "https://asia.api.riotgames.com"
    
    def __init__(self, api_key: str):
        """
        RiotAPIClient 초기화
        
        Args:
            api_key: 라이엇 API 키
        """
        self.api_key = api_key
        self.rate_limiter = RateLimiter()
        self.session = requests.Session()
        self.session.headers.update({
            "X-Riot-Token": api_key
        })
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        API 요청을 수행하는 내부 메서드
        
        Args:
            url: 요청할 URL
            params: 쿼리 파라미터
            
        Returns:
            API 응답 JSON 또는 None (실패 시)
        """
        self.rate_limiter.wait_if_needed()
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API 요청 실패: {e}")
            return None
    
    def get_puuid_by_riot_id(self, game_name: str, tag_line: str) -> Optional[str]:
        """
        Riot ID로 PUUID를 조회합니다.
        
        Args:
            game_name: 게임 이름 (예: "Hide on bush")
            tag_line: 태그 라인 (예: "KR1")
            
        Returns:
            PUUID 문자열 또는 None
        """
        url = f"{self.BASE_URL_ACCOUNT}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        result = self._make_request(url)
        
        if result:
            return result.get("puuid")
        return None
    
    def get_match_history(self, puuid: str, count: int = 20) -> List[str]:
        """
        플레이어의 최근 매치 ID 목록을 가져옵니다.
        
        Args:
            puuid: 플레이어의 PUUID
            count: 가져올 매치 수 (최대 100)
            
        Returns:
            매치 ID 리스트
        """
        url = f"{self.BASE_URL_MATCH}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"start": 0, "count": min(count, 100)}
        result = self._make_request(url, params)
        
        if result:
            return result
        return []
    
    def get_match_details(self, match_id: str) -> Optional[Dict]:
        """
        매치 상세 정보를 가져옵니다.
        
        Args:
            match_id: 매치 ID
            
        Returns:
            매치 상세 정보 딕셔너리 또는 None
        """
        url = f"{self.BASE_URL_MATCH}/lol/match/v5/matches/{match_id}"
        return self._make_request(url)
    
    def is_custom_game(self, match_data: Dict) -> bool:
        """
        매치가 내전(Custom Game)인지 확인합니다.
        
        Args:
            match_data: 매치 상세 정보
            
        Returns:
            내전 여부
        """
        if not match_data or "info" not in match_data:
            return False
        
        info = match_data["info"]
        game_type = info.get("gameType", "")
        game_mode = info.get("gameMode", "")
        
        # Custom Game 확인
        return game_type == "CUSTOM_GAME" or (game_mode == "CLASSIC" and game_type == "MATCHED_GAME")
    
    def get_custom_game_matches(self, puuid: str, count: int = 100) -> List[str]:
        """
        플레이어의 내전 매치 ID 목록을 가져옵니다.
        
        Args:
            puuid: 플레이어의 PUUID
            count: 가져올 매치 수 (최대 100)
            
        Returns:
            내전 매치 ID 리스트
        """
        all_matches = self.get_match_history(puuid, count)
        custom_matches = []
        
        for match_id in all_matches:
            match_data = self.get_match_details(match_id)
            if match_data and self.is_custom_game(match_data):
                custom_matches.append(match_id)
        
        return custom_matches
    
    def extract_match_stats(self, match_data: Dict, puuid: str) -> Optional[Dict]:
        """
        매치 데이터에서 특정 플레이어의 통계를 추출합니다.
        
        Args:
            match_data: 매치 상세 정보
            puuid: 플레이어의 PUUID
            
        Returns:
            통계 정보 딕셔너리:
            {
                'win': bool,
                'kills': int,
                'deaths': int,
                'assists': int,
                'position': str,
                'champion': str,
                'game_duration': int,
                'gold_earned': int,
                'team_gold_diff': int,
                'team_kill_diff': int
            }
        """
        if not match_data or "info" not in match_data:
            return None
        
        info = match_data["info"]
        participants = info.get("participants", [])
        
        # 해당 PUUID의 플레이어 찾기
        player_data = None
        for participant in participants:
            if participant.get("puuid") == puuid:
                player_data = participant
                break
        
        if not player_data:
            return None
        
        # 팀 정보 추출
        team_id = player_data.get("teamId")
        teams = info.get("teams", [])
        player_team = next((t for t in teams if t["teamId"] == team_id), None)
        enemy_team = next((t for t in teams if t["teamId"] != team_id), None)
        
        # 골드 및 킬 차이 계산
        team_gold_diff = 0
        team_kill_diff = 0
        if player_team and enemy_team:
            team_gold_diff = player_team.get("objectives", {}).get("champion", {}).get("kills", 0) - \
                           enemy_team.get("objectives", {}).get("champion", {}).get("kills", 0)
            team_kill_diff = sum(p.get("kills", 0) for p in participants if p.get("teamId") == team_id) - \
                           sum(p.get("kills", 0) for p in participants if p.get("teamId") != team_id)
        
        return {
            "win": player_data.get("win", False),
            "kills": player_data.get("kills", 0),
            "deaths": player_data.get("deaths", 0),
            "assists": player_data.get("assists", 0),
            "position": player_data.get("teamPosition", "UNKNOWN"),
            "champion": player_data.get("championName", ""),
            "game_duration": info.get("gameDuration", 0),  # 초 단위
            "gold_earned": player_data.get("goldEarned", 0),
            "team_gold_diff": team_gold_diff,
            "team_kill_diff": team_kill_diff
        }
