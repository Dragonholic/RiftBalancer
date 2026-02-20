"""
Team 클래스 모듈
팀 구성과 MMR 계산을 담당합니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from player import Player


@dataclass
class Team:
    """
    팀을 구성하는 클래스
    
    Attributes:
        players: 팀에 속한 플레이어 리스트 (5명)
        positions: 각 플레이어가 맡은 포지션 매핑 {player_name: position}
    """
    
    players: List[Player] = field(default_factory=list)
    positions: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """초기화 후 검증"""
        if len(self.players) > 5:
            raise ValueError("팀은 최대 5명까지 가능합니다.")
    
    @property
    def total_mmr(self) -> float:
        """
        팀의 총 MMR을 계산합니다 (포지션 페널티 적용).
        
        Returns:
            팀의 총 MMR
        """
        total = 0.0
        for player in self.players:
            position = self.positions.get(player.name, player.main_position)
            total += player.get_effective_rating(position)
        return total
    
    @property
    def synergy_bonus(self) -> float:
        """
        팀 내 플레이어 간 시너지 보너스를 계산합니다.
        
        Returns:
            시너지 보너스 점수 (양수일수록 좋음)
        """
        if len(self.players) < 2:
            return 0.0
        
        total_synergy = 0.0
        pair_count = 0
        
        for i, player1 in enumerate(self.players):
            for player2 in self.players[i+1:]:
                synergy = player1.get_synergy_score(player2.name)
                total_synergy += synergy
                pair_count += 1
        
        # 평균 시너지를 레이팅 단위로 변환 (시너지 1.0 = 레이팅 50점 보너스)
        if pair_count > 0:
            avg_synergy = total_synergy / pair_count
            return avg_synergy * 50.0
        
        return 0.0
    
    @property
    def adjusted_mmr(self) -> float:
        """
        시너지 보너스가 적용된 조정된 MMR을 계산합니다.
        
        Returns:
            조정된 총 MMR
        """
        return self.total_mmr + self.synergy_bonus
    
    def assign_position(self, player_name: str, position: str):
        """
        플레이어에게 포지션을 할당합니다.
        
        Args:
            player_name: 플레이어 이름
            position: 할당할 포지션
        """
        self.positions[player_name] = position
    
    def get_player_by_name(self, name: str) -> Player:
        """
        이름으로 플레이어를 찾습니다.
        
        Args:
            name: 플레이어 이름
            
        Returns:
            Player 객체 또는 None
        """
        for player in self.players:
            if player.name == name:
                return player
        raise ValueError(f"플레이어 '{name}'를 찾을 수 없습니다.")
    
    def to_dict(self) -> dict:
        """팀 정보를 딕셔너리로 변환"""
        return {
            "players": [p.to_dict() for p in self.players],
            "positions": self.positions,
            "total_mmr": self.total_mmr,
            "synergy_bonus": self.synergy_bonus,
            "adjusted_mmr": self.adjusted_mmr
        }
