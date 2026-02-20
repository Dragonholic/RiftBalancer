"""
Player 클래스 모듈
플레이어 정보와 상태를 관리합니다.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta


@dataclass
class RecentMatch:
    """최근 경기 정보를 저장하는 데이터 클래스"""
    win: bool
    kills: int
    deaths: int
    assists: int
    position: str
    game_duration: int  # 초 단위
    champion: Optional[str] = None  # 챔피언 이름
    match_id: Optional[str] = None  # 매치 ID (저장된 매치 추적용)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Player:
    """
    플레이어 정보를 담는 클래스
    
    Attributes:
        name: 플레이어 이름
        riot_id: Riot ID (게임 이름)
        tag_line: 태그 라인
        puuid: 플레이어 고유 ID
        rating: 현재 레이팅 (기본값: 1500, Elo 기반)
        main_position: 주 포지션 (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
        off_positions: 부 포지션 리스트
        recent_matches: 최근 경기 기록
        synergy_data: 다른 플레이어와의 시너지 데이터 {player_name: synergy_score}
    """
    
    name: str
    riot_id: str
    tag_line: str
    puuid: Optional[str] = None
    rating: float = 1500.0  # 기본 Elo 레이팅
    main_position: str = "UNKNOWN"
    off_positions: List[str] = field(default_factory=list)
    fixed_positions: List[str] = field(default_factory=list)  # 고정 포지션 (이 포지션만 가능)
    excluded_positions: List[str] = field(default_factory=list)  # 제외 포지션 (이 포지션은 불가능)
    recent_matches: List[RecentMatch] = field(default_factory=list)
    synergy_data: dict = field(default_factory=dict)
    champion_winrates: Dict[str, Dict[str, float]] = field(default_factory=dict)  # {champion: {wins, total, winrate}}
    team_history: Dict[str, Dict[str, float]] = field(default_factory=dict)  # {player_name: {games_together, wins, winrate}}
    
    def __post_init__(self):
        """초기화 후 검증"""
        valid_positions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY", "UNKNOWN"]
        if self.main_position not in valid_positions:
            self.main_position = "UNKNOWN"
    
    @property
    def form_score(self) -> float:
        """
        최근 폼 점수를 계산합니다 (최근 5경기 기준).
        
        Returns:
            0.0 ~ 1.0 사이의 폼 점수 (승률 기반)
        """
        if not self.recent_matches:
            return 0.5  # 기본값
        
        recent_5 = self.recent_matches[:5]
        wins = sum(1 for match in recent_5 if match.win)
        return wins / len(recent_5)
    
    @property
    def kda_avg(self) -> float:
        """
        최근 경기의 평균 KDA를 계산합니다.
        
        Returns:
            평균 KDA (데스가 0이면 K+A로 계산)
        """
        if not self.recent_matches:
            return 1.0
        
        recent_5 = self.recent_matches[:5]
        total_kills = sum(m.kills for m in recent_5)
        total_deaths = sum(m.deaths for m in recent_5)
        total_assists = sum(m.assists for m in recent_5)
        
        if total_deaths == 0:
            return total_kills + total_assists
        
        return (total_kills + total_assists) / total_deaths

    def _get_recent_streak(self) -> Tuple[int, bool]:
        """
        최근 연승/연패 정보를 계산합니다.

        Returns:
            (streak_len, is_win_streak)
        """
        if not self.recent_matches:
            return 0, True

        first_is_win = self.recent_matches[0].win
        length = 0
        for match in self.recent_matches:
            if match.win == first_is_win:
                length += 1
            else:
                break
        return length, first_is_win

    def _get_form_multiplier(self) -> float:
        """
        근황 폼(연승/연패, 최근 승률)을 반영한 레이팅 보정 계수를 계산합니다.
        
        - **연패**: 다음 판에서 **이기기 쉽도록** 팀을 강하게 만들어주기 위해
          실질 레이팅을 올려서 강한 팀에 배정되기 쉽게 합니다.
        - **연승**: 살짝만 너프해서 한 팀이 계속 이기지 않도록 조정합니다.
        """
        base = 1.0
        
        # 최근 승률 기반 (form_score: 0.0 ~ 1.0, 기본 0.5)
        form = self.form_score
        if form < 0.5:
            # 폼이 나쁘면 보호 버프: 최대 +10% 정도
            # form=0   → +0.10, form=0.25 → +0.05
            base += (0.5 - form) * 0.2
        else:
            # 폼이 좋을수록 살짝만 너프: 최대 -4% 정도
            # form=1 → -0.04
            base -= (form - 0.5) * 0.08
        
        # 연승/연패 스트릭 기반 보정
        streak_len, is_win_streak = self._get_recent_streak()
        if streak_len >= 3:
            if is_win_streak:
                # 연승 스트릭은 약하게 너프 (3연승부터 최대 -4%)
                base -= min(0.04, 0.01 * (streak_len - 2))
            else:
                # 연패 스트릭은 강하게 버프 (3연패부터 최대 +12%)
                base += min(0.12, 0.03 * (streak_len - 2))
        
        # 계수 범위 제한 (연패 보호: 최대 +15%, 연승 너프: 최대 -8%)
        return max(0.92, min(1.15, base))
    
    def can_play_position(self, position: str) -> bool:
        """
        해당 포지션을 플레이할 수 있는지 확인합니다.
        
        Args:
            position: 확인할 포지션
            
        Returns:
            플레이 가능 여부
        """
        # 고정 포지션이 있으면 그 포지션만 가능
        if self.fixed_positions:
            return position in self.fixed_positions
        
        # 제외 포지션이면 불가능
        if position in self.excluded_positions:
            return False
        
        return True
    
    def get_effective_rating(self, position: str) -> float:
        """
        포지션에 따른 유효 레이팅을 계산합니다.
        
        Args:
            position: 플레이할 포지션
            
        Returns:
            포지션 페널티가 적용된 레이팅
        """
        if not self.can_play_position(position):
            return 0.0  # 플레이 불가능한 포지션
        
        # 포지션에 따른 기본 레이팅
        if position == self.main_position:
            base_rating = self.rating  # 주 포지션: 100%
        elif position in self.off_positions:
            base_rating = self.rating * 0.85  # 부 포지션: 85%
        else:
            base_rating = self.rating * 0.70  # 미숙 포지션: 70%

        # 근황 폼(연승/연패, 최근 승률) 보정
        form_multiplier = self._get_form_multiplier()
        return base_rating * form_multiplier
    
    def add_match(self, match: RecentMatch):
        """
        최근 경기를 추가합니다 (최대 10개 유지).
        
        Args:
            match: RecentMatch 객체
        """
        self.recent_matches.insert(0, match)
        if len(self.recent_matches) > 10:
            self.recent_matches = self.recent_matches[:10]
    
    def get_synergy_score(self, other_player_name: str) -> float:
        """
        다른 플레이어와의 시너지 점수를 가져옵니다.
        
        Args:
            other_player_name: 상대 플레이어 이름
            
        Returns:
            시너지 점수 (-1.0 ~ 1.0, 기본값 0.0)
        """
        return self.synergy_data.get(other_player_name, 0.0)
    
    def set_synergy_score(self, other_player_name: str, score: float):
        """
        다른 플레이어와의 시너지 점수를 설정합니다.
        
        Args:
            other_player_name: 상대 플레이어 이름
            score: 시너지 점수 (-1.0 ~ 1.0)
        """
        self.synergy_data[other_player_name] = max(-1.0, min(1.0, score))
    
    def get_team_history(self, other_player_name: str) -> Dict[str, float]:
        """
        다른 플레이어와의 팀 배치 이력을 가져옵니다.
        
        Args:
            other_player_name: 상대 플레이어 이름
            
        Returns:
            {games_together, wins, winrate} 딕셔너리
        """
        return self.team_history.get(other_player_name, {
            'games_together': 0,
            'wins': 0,
            'winrate': 0.5
        })
    
    def update_team_history(self, other_player_name: str, won: bool):
        """
        다른 플레이어와의 팀 배치 이력을 업데이트합니다.
        
        Args:
            other_player_name: 상대 플레이어 이름
            won: 승리 여부
        """
        if other_player_name not in self.team_history:
            self.team_history[other_player_name] = {
                'games_together': 0,
                'wins': 0,
                'winrate': 0.5
            }
        
        history = self.team_history[other_player_name]
        history['games_together'] += 1
        if won:
            history['wins'] += 1
        history['winrate'] = history['wins'] / history['games_together'] if history['games_together'] > 0 else 0.5
    
    def get_position_winrate(self, position: str) -> float:
        """
        특정 포지션의 승률을 계산합니다.
        
        Args:
            position: 포지션
            
        Returns:
            승률 (0.0 ~ 1.0)
        """
        matches = [m for m in self.recent_matches if m.position == position]
        if not matches:
            return 0.5  # 기본값
        
        wins = sum(1 for m in matches if m.win)
        return wins / len(matches)
    
    def get_champion_winrate(self, champion: str) -> float:
        """
        특정 챔피언의 승률을 가져옵니다.
        
        Args:
            champion: 챔피언 이름
            
        Returns:
            승률 (0.0 ~ 1.0)
        """
        if champion not in self.champion_winrates:
            return 0.5  # 기본값
        
        stats = self.champion_winrates[champion]
        return stats.get('winrate', 0.5)
    
    def update_champion_stats(self, champion: str, win: bool):
        """
        챔피언 통계를 업데이트합니다.
        
        Args:
            champion: 챔피언 이름
            win: 승리 여부
        """
        if champion not in self.champion_winrates:
            self.champion_winrates[champion] = {'wins': 0, 'total': 0, 'winrate': 0.5}
        
        stats = self.champion_winrates[champion]
        stats['total'] += 1
        if win:
            stats['wins'] += 1
        stats['winrate'] = stats['wins'] / stats['total']
    
    def to_dict(self) -> dict:
        """플레이어 정보를 딕셔너리로 변환"""
        return {
            "name": self.name,
            "riot_id": self.riot_id,
            "tag_line": self.tag_line,
            "puuid": self.puuid,
            "rating": self.rating,
            "main_position": self.main_position,
            "off_positions": self.off_positions,
            "fixed_positions": self.fixed_positions,
            "excluded_positions": self.excluded_positions,
            "form_score": self.form_score,
            "kda_avg": self.kda_avg,
            "recent_match_count": len(self.recent_matches),
            "champion_count": len(self.champion_winrates)
        }
