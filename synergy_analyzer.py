"""
시너지 분석 모듈
경기 결과를 분석하여 플레이어 간 시너지 데이터를 업데이트합니다.
"""

from typing import List, Dict
from player import Player
from team import Team


class SynergyAnalyzer:
    """시너지 분석 및 업데이트 클래스"""
    
    # 시너지 업데이트 가중치
    WIN_SYNERGY_BONUS = 0.05  # 승리 시 시너지 증가량
    LOSS_SYNERGY_PENALTY = -0.03  # 패배 시 시너지 감소량
    DOMINANT_WIN_BONUS = 0.08  # 압도적 승리 시 추가 보너스
    CLOSE_LOSS_PENALTY = -0.01  # 아쉬운 패배 시 감소량 (적음)
    
    def __init__(self):
        """SynergyAnalyzer 초기화"""
        pass
    
    def analyze_match_result(self, team_a: Team, team_b: Team, team_a_won: bool,
                            game_duration: int, gold_diff: int, kill_diff: int,
                            team_a_stats: Dict[str, Dict] = None,
                            team_b_stats: Dict[str, Dict] = None):
        """
        경기 결과를 분석하여 플레이어 간 시너지 및 팀 배치 이력을 업데이트합니다.
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
            team_a_won: 팀 A 승리 여부
            game_duration: 게임 시간 (초)
            gold_diff: 팀 A의 골드 차이
            kill_diff: 팀 A의 킬 차이
            team_a_stats: 팀 A 플레이어별 통계 {player_name: {kills, deaths, assists, ...}}
            team_b_stats: 팀 B 플레이어별 통계
        """
        # 압도적 승리/패배 판단
        is_dominant = abs(gold_diff) > 10000 or abs(kill_diff) > 15
        is_close_game = game_duration > 2400 and abs(gold_diff) < 5000  # 40분 이상, 작은 차이
        
        # 승리 팀의 시너지 업데이트
        if team_a_won:
            self._update_team_synergy(
                team_a.players,
                is_win=True,
                is_dominant=is_dominant,
                is_close=False,
                game_duration=game_duration,
                stats=team_a_stats
            )
            self._update_team_history(team_a.players, won=True)
            
            self._update_team_synergy(
                team_b.players,
                is_win=False,
                is_dominant=False,
                is_close=is_close_game,
                game_duration=game_duration,
                stats=team_b_stats
            )
            self._update_team_history(team_b.players, won=False)
        else:
            self._update_team_synergy(
                team_b.players,
                is_win=True,
                is_dominant=is_dominant,
                is_close=False,
                game_duration=game_duration,
                stats=team_b_stats
            )
            self._update_team_history(team_b.players, won=True)
            
            self._update_team_synergy(
                team_a.players,
                is_win=False,
                is_dominant=False,
                is_close=is_close_game,
                game_duration=game_duration,
                stats=team_a_stats
            )
            self._update_team_history(team_a.players, won=False)
        
        # 상대 팀과의 상성 업데이트 (선택적)
        # 같은 팀에 자주 배치되지 않도록
        self._update_cross_team_synergy(team_a.players, team_b.players, team_a_won)
    
    def _update_team_synergy(self, players: List[Player], is_win: bool, is_dominant: bool,
                             is_close: bool, game_duration: int, stats: Dict[str, Dict] = None):
        """
        팀 내 플레이어 간 시너지를 업데이트합니다.
        
        Args:
            players: 팀 플레이어 리스트
            is_win: 승리 여부
            is_dominant: 압도적 승리/패배 여부
            is_close: 아쉬운 경기 여부
            game_duration: 게임 시간
            stats: 플레이어별 통계
        """
        base_change = self.WIN_SYNERGY_BONUS if is_win else self.LOSS_SYNERGY_PENALTY
        
        # 압도적 승리/패배 보정
        if is_win and is_dominant:
            base_change += self.DOMINANT_WIN_BONUS
        elif not is_win and is_close:
            base_change += self.CLOSE_LOSS_PENALTY
        
        # 게임 시간 보정 (장기전일수록 시너지 영향 큼)
        time_factor = min(1.5, game_duration / 1800)  # 30분 기준
        base_change *= time_factor
        
        # 팀 내 모든 플레이어 쌍에 대해 시너지 업데이트
        for i, player1 in enumerate(players):
            for player2 in players[i+1:]:
                # 현재 시너지 점수 가져오기
                current_synergy_1to2 = player1.get_synergy_score(player2.name)
                current_synergy_2to1 = player2.get_synergy_score(player1.name)
                
                # 새로운 시너지 계산 (가중 평균)
                # 최근 경기일수록 더 큰 영향
                learning_rate = 0.3  # 학습률
                new_synergy_1to2 = current_synergy_1to2 + (base_change - current_synergy_1to2) * learning_rate
                new_synergy_2to1 = current_synergy_2to1 + (base_change - current_synergy_2to1) * learning_rate
                
                # 개인 기여도 보정 (KDA 기반)
                if stats:
                    player1_contribution = self._calculate_contribution(stats.get(player1.name, {}))
                    player2_contribution = self._calculate_contribution(stats.get(player2.name, {}))
                    
                    # 기여도가 높은 플레이어 쌍일수록 시너지 변화가 큼
                    avg_contribution = (player1_contribution + player2_contribution) / 2
                    contribution_factor = 0.7 + (avg_contribution * 0.6)  # 0.7 ~ 1.3
                    
                    new_synergy_1to2 *= contribution_factor
                    new_synergy_2to1 *= contribution_factor
                
                # 시너지 업데이트
                player1.set_synergy_score(player2.name, new_synergy_1to2)
                player2.set_synergy_score(player1.name, new_synergy_2to1)
    
    def _update_cross_team_synergy(self, team_a_players: List[Player], team_b_players: List[Player],
                                   team_a_won: bool):
        """
        상대 팀 플레이어 간 상성을 업데이트합니다.
        (같은 팀에 배치되지 않도록 약간의 페널티)
        
        Args:
            team_a_players: 팀 A 플레이어
            team_b_players: 팀 B 플레이어
            team_a_won: 팀 A 승리 여부
        """
        # 상대 팀과의 시너지는 약간 감소 (다양한 조합 유도)
        cross_penalty = -0.01
        
        for player_a in team_a_players:
            for player_b in team_b_players:
                current_a_to_b = player_a.get_synergy_score(player_b.name)
                current_b_to_a = player_b.get_synergy_score(player_a.name)
                
                # 약간 감소 (너무 많이 감소하지 않도록)
                new_a_to_b = max(-0.5, current_a_to_b + cross_penalty)
                new_b_to_a = max(-0.5, current_b_to_a + cross_penalty)
                
                player_a.set_synergy_score(player_b.name, new_a_to_b)
                player_b.set_synergy_score(player_a.name, new_b_to_a)
    
    def _update_team_history(self, players: List[Player], won: bool):
        """
        팀 내 플레이어 간 팀 배치 이력을 업데이트합니다.
        
        Args:
            players: 팀 플레이어 리스트
            won: 승리 여부
        """
        # 팀 내 모든 플레이어 쌍에 대해 이력 업데이트
        for i, player1 in enumerate(players):
            for player2 in players[i+1:]:
                player1.update_team_history(player2.name, won)
                player2.update_team_history(player1.name, won)
    
    def _calculate_contribution(self, stats: Dict) -> float:
        """
        플레이어의 기여도를 계산합니다 (KDA 기반).
        
        Args:
            stats: 플레이어 통계 {kills, deaths, assists, ...}
            
        Returns:
            기여도 점수 (0.0 ~ 1.0)
        """
        if not stats:
            return 0.5  # 기본값
        
        kills = stats.get('kills', 0)
        deaths = stats.get('deaths', 1)  # 0으로 나누기 방지
        assists = stats.get('assists', 0)
        
        # KDA 계산
        kda = (kills + assists) / max(deaths, 1)
        
        # KDA를 0.0 ~ 1.0 범위로 정규화 (예: KDA 0.5 = 0.3, KDA 3.0 = 1.0)
        normalized = min(1.0, max(0.0, (kda - 0.5) / 2.5))
        
        return normalized
