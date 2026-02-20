"""
매치 데이터 저장 및 관리 모듈
Riot API에서 가져온 내전 기록을 로컬에 저장합니다.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class StoredMatch:
    """저장된 매치 정보"""
    match_id: str
    game_creation: int  # 게임 생성 시간 (타임스탬프)
    game_duration: int  # 게임 시간 (초)
    game_mode: str
    game_type: str
    participants: List[Dict]  # 참가자 정보 리스트
    teams: List[Dict]  # 팀 정보 리스트
    saved_at: str  # 저장 시간


class MatchStorage:
    """매치 데이터 저장 관리 클래스"""
    
    MATCHES_FILE = "matches.json"
    
    def __init__(self):
        """MatchStorage 초기화"""
        self.matches: Dict[str, StoredMatch] = {}
        self.load_matches()
    
    def load_matches(self):
        """저장된 매치 데이터 로드"""
        if os.path.exists(self.MATCHES_FILE):
            try:
                with open(self.MATCHES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for match_id, match_data in data.items():
                        self.matches[match_id] = StoredMatch(**match_data)
            except Exception as e:
                print(f"매치 데이터 로드 실패: {e}")
                self.matches = {}
    
    def save_matches(self):
        """매치 데이터를 파일에 저장"""
        data = {}
        for match_id, match in self.matches.items():
            data[match_id] = asdict(match)
        
        with open(self.MATCHES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def is_custom_game(self, match_data: Dict) -> bool:
        """
        매치가 내전(Custom Game)인지 확인합니다.
        
        Args:
            match_data: Riot API에서 가져온 매치 데이터
            
        Returns:
            내전 여부
        """
        if not match_data or "info" not in match_data:
            return False
        
        info = match_data["info"]
        game_type = info.get("gameType", "")
        game_mode = info.get("gameMode", "")
        
        # Custom Game 확인
        return game_type == "CUSTOM_GAME" or game_mode == "CLASSIC"
    
    def store_match(self, match_id: str, match_data: Dict) -> bool:
        """
        매치 데이터를 저장합니다.
        
        Args:
            match_id: 매치 ID
            match_data: Riot API에서 가져온 매치 데이터
            
        Returns:
            저장 성공 여부
        """
        if not self.is_custom_game(match_data):
            return False  # 내전이 아니면 저장하지 않음
        
        if match_id in self.matches:
            return False  # 이미 저장된 매치
        
        try:
            info = match_data["info"]
            stored_match = StoredMatch(
                match_id=match_id,
                game_creation=info.get("gameCreation", 0),
                game_duration=info.get("gameDuration", 0),
                game_mode=info.get("gameMode", ""),
                game_type=info.get("gameType", ""),
                participants=info.get("participants", []),
                teams=info.get("teams", []),
                saved_at=datetime.now().isoformat()
            )
            
            self.matches[match_id] = stored_match
            self.save_matches()
            return True
        except Exception as e:
            print(f"매치 저장 실패: {e}")
            return False
    
    def get_match(self, match_id: str) -> Optional[StoredMatch]:
        """
        저장된 매치를 가져옵니다.
        
        Args:
            match_id: 매치 ID
            
        Returns:
            StoredMatch 객체 또는 None
        """
        return self.matches.get(match_id)
    
    def get_all_matches(self) -> List[StoredMatch]:
        """
        모든 저장된 매치를 가져옵니다.
        
        Returns:
            StoredMatch 리스트
        """
        return list(self.matches.values())
    
    def get_player_matches(self, puuid: str) -> List[StoredMatch]:
        """
        특정 플레이어가 참가한 매치를 가져옵니다.
        
        Args:
            puuid: 플레이어의 PUUID
            
        Returns:
            해당 플레이어가 참가한 매치 리스트
        """
        player_matches = []
        for match in self.matches.values():
            for participant in match.participants:
                if participant.get("puuid") == puuid:
                    player_matches.append(match)
                    break
        return player_matches
    
    def get_recent_matches(self, days: int = 30) -> List[StoredMatch]:
        """
        최근 N일간의 매치를 가져옵니다.
        
        Args:
            days: 일수
            
        Returns:
            최근 매치 리스트
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_matches = []
        
        for match in self.matches.values():
            # game_creation은 밀리초 단위이므로 1000으로 나눔
            if match.game_creation / 1000 > cutoff_time:
                recent_matches.append(match)
        
        # 시간순 정렬 (최신순)
        recent_matches.sort(key=lambda m: m.game_creation, reverse=True)
        return recent_matches
    
    def get_match_count(self) -> int:
        """저장된 매치 수를 반환합니다."""
        return len(self.matches)
    
    def extract_player_stats_from_match(self, match: StoredMatch, puuid: str) -> Optional[Dict]:
        """
        저장된 매치에서 플레이어 통계를 추출합니다.
        
        Args:
            match: StoredMatch 객체
            puuid: 플레이어의 PUUID
            
        Returns:
            플레이어 통계 딕셔너리 또는 None
        """
        for participant in match.participants:
            if participant.get("puuid") == puuid:
                # 팀 정보 찾기
                team_id = participant.get("teamId")
                teams = match.teams
                player_team = next((t for t in teams if t.get("teamId") == team_id), None)
                enemy_team = next((t for t in teams if t.get("teamId") != team_id), None)
                
                # 골드 및 킬 차이 계산
                team_gold_diff = 0
                team_kill_diff = 0
                if player_team and enemy_team:
                    team_gold_diff = player_team.get("objectives", {}).get("champion", {}).get("kills", 0) - \
                                   enemy_team.get("objectives", {}).get("champion", {}).get("kills", 0)
                    team_kill_diff = sum(p.get("kills", 0) for p in match.participants if p.get("teamId") == team_id) - \
                                   sum(p.get("kills", 0) for p in match.participants if p.get("teamId") != team_id)
                
                return {
                    "win": participant.get("win", False),
                    "kills": participant.get("kills", 0),
                    "deaths": participant.get("deaths", 0),
                    "assists": participant.get("assists", 0),
                    "position": participant.get("teamPosition", "UNKNOWN"),
                    "champion": participant.get("championName", ""),
                    "game_duration": match.game_duration,
                    "gold_earned": participant.get("goldEarned", 0),
                    "team_gold_diff": team_gold_diff,
                    "team_kill_diff": team_kill_diff,
                    "match_id": match.match_id,
                    "game_creation": match.game_creation
                }
        
        return None
