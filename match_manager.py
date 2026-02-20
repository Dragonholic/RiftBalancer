"""
MatchManager 클래스 모듈
매치메이킹 알고리즘을 담당합니다.
"""

from typing import List, Tuple, Dict
from itertools import combinations
from team import Team
from player import Player


class MatchManager:
    """
    매치메이킹을 관리하는 클래스
    
    Attributes:
        players: 매치에 참가할 플레이어 리스트 (10명)
        position_requirements: 필요한 포지션 리스트
    """
    
    POSITIONS = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    
    def __init__(self, players: List[Player]):
        """
        MatchManager 초기화
        
        Args:
            players: 참가 플레이어 리스트 (정확히 10명이어야 함)
        """
        if len(players) != 10:
            raise ValueError("매치메이킹을 위해서는 정확히 10명의 플레이어가 필요합니다.")
        self.players = players
    
    def generate_all_combinations(self) -> List[Tuple[Team, Team]]:
        """
        가능한 모든 5:5 팀 조합을 생성합니다 (브루트 포스).
        
        Returns:
            (Team A, Team B) 튜플의 리스트
        """
        combinations_list = []
        
        # 10명 중 5명을 선택하는 모든 조합
        for team_a_indices in combinations(range(10), 5):
            team_a_players = [self.players[i] for i in team_a_indices]
            team_b_players = [self.players[i] for i in range(10) if i not in team_a_indices]
            
            # 포지션 할당
            team_a = Team(players=team_a_players)
            team_b = Team(players=team_b_players)
            
            # 최적 포지션 할당 시도
            self._assign_positions(team_a, team_b)
            
            combinations_list.append((team_a, team_b))
        
        return combinations_list
    
    def _assign_positions(self, team_a: Team, team_b: Team):
        """
        두 팀에 포지션을 할당합니다 (포지션 제약 조건 고려).
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
        """
        # 각 팀에 대해 포지션 할당
        for team in [team_a, team_b]:
            available_positions = self.POSITIONS.copy()
            players_to_assign = team.players.copy()
            
            # 1단계: 고정 포지션이 있는 플레이어 먼저 할당
            for player in players_to_assign[:]:
                if player.fixed_positions:
                    for fixed_pos in player.fixed_positions:
                        if fixed_pos in available_positions:
                            team.assign_position(player.name, fixed_pos)
                            available_positions.remove(fixed_pos)
                            players_to_assign.remove(player)
                            break
            
            # 2단계: 주 포지션이 있는 플레이어 할당
            for player in players_to_assign[:]:
                if player.main_position in available_positions and player.can_play_position(player.main_position):
                    team.assign_position(player.name, player.main_position)
                    available_positions.remove(player.main_position)
                    players_to_assign.remove(player)
            
            # 3단계: 부 포지션 중 사용 가능한 것 할당
            for player in players_to_assign[:]:
                if not available_positions:
                    break
                assigned = False
                for off_pos in player.off_positions:
                    if off_pos in available_positions and player.can_play_position(off_pos):
                        team.assign_position(player.name, off_pos)
                        available_positions.remove(off_pos)
                        players_to_assign.remove(player)
                        assigned = True
                        break
            
            # 4단계: 남은 플레이어는 가능한 포지션에 할당
            for player in players_to_assign[:]:
                if not available_positions:
                    break
                for pos in available_positions[:]:
                    if player.can_play_position(pos):
                        team.assign_position(player.name, pos)
                        available_positions.remove(pos)
                        players_to_assign.remove(player)
                        break
            
            # 5단계: 아직 할당되지 않은 플레이어는 강제 할당 (제약 조건 위반)
            for player in players_to_assign:
                if available_positions:
                    team.assign_position(player.name, available_positions[0])
                    available_positions.pop(0)
    
    def calculate_cost(self, team_a: Team, team_b: Team) -> float:
        """
        두 팀 조합의 Cost를 계산합니다.
        Cost가 낮을수록 더 균형잡힌 매치입니다.
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
            
        Returns:
            Cost 값 (낮을수록 좋음)
        """
        # MMR 차이
        mmr_diff = abs(team_a.adjusted_mmr - team_b.adjusted_mmr)
        
        # 포지션 페널티 계산
        position_penalty = 0.0
        for team in [team_a, team_b]:
            for player in team.players:
                position = team.positions.get(player.name, player.main_position)
                if position != player.main_position:
                    if position in player.off_positions:
                        position_penalty += 10.0  # 부 포지션 페널티
                    else:
                        position_penalty += 30.0  # 미숙 포지션 페널티
        
        # 밸런스 페널티 계산 (같은 팀에 자주 배치되고 승률이 높은 조합에 페널티)
        balance_penalty = self._calculate_balance_penalty(team_a, team_b)
        
        # Cost = MMR 차이 + 포지션 페널티 + 밸런스 페널티
        # 시너지는 이미 adjusted_mmr에 반영되지만, 밸런스를 위해 분리 페널티 추가
        cost = mmr_diff + position_penalty + balance_penalty
        
        return cost
    
    def _calculate_balance_penalty(self, team_a: Team, team_b: Team) -> float:
        """
        밸런스 페널티를 계산합니다.
        같은 팀에 자주 배치되고 승률이 높은 조합에 페널티를 부여하여 분리합니다.
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
            
        Returns:
            밸런스 페널티 값
        """
        penalty = 0.0
        
        # 각 팀에 대해 분석
        for team in [team_a, team_b]:
            team_penalty = 0.0
            
            # 팀 내 모든 플레이어 쌍에 대해 분석
            for i, player1 in enumerate(team.players):
                for player2 in team.players[i+1:]:
                    # 팀 배치 이력 가져오기
                    history = player1.get_team_history(player2.name)
                    games_together = history.get('games_together', 0)
                    winrate = history.get('winrate', 0.5)
                    
                    # 같은 팀에 3회 이상 배치되고 승률이 70% 이상이면 페널티
                    if games_together >= 3 and winrate >= 0.7:
                        # 게임 횟수와 승률에 비례하여 페널티 증가
                        frequency_factor = min(1.0, games_together / 5)  # 5회 이상이면 최대
                        winrate_factor = (winrate - 0.7) / 0.3  # 0.7~1.0을 0~1로 정규화
                        
                        # 페널티 계산 (최대 100점)
                        pair_penalty = (frequency_factor * winrate_factor) * 100
                        team_penalty += pair_penalty
                    
                    # 같은 팀에 5회 이상 배치되면 추가 페널티 (승률 무관)
                    elif games_together >= 5:
                        frequency_penalty = (games_together - 4) * 20  # 5회부터 회당 20점
                        team_penalty += frequency_penalty
            
            penalty += team_penalty
        
        return penalty
    
    def find_best_matches(self, top_n: int = 3) -> List[Tuple[Team, Team, float]]:
        """
        최적의 팀 조합을 찾습니다.
        
        Args:
            top_n: 반환할 상위 조합 수
            
        Returns:
            (Team A, Team B, Cost) 튜플의 리스트 (Cost 오름차순)
        """
        all_combinations = self.generate_all_combinations()
        
        # 각 조합의 Cost 계산
        scored_matches = []
        for team_a, team_b in all_combinations:
            cost = self.calculate_cost(team_a, team_b)
            scored_matches.append((team_a, team_b, cost))
        
        # Cost 기준으로 정렬
        scored_matches.sort(key=lambda x: x[2])
        
        return scored_matches[:top_n]
    
    def get_expected_win_rate(self, team_a: Team, team_b: Team) -> float:
        """
        팀 A의 예상 승률을 계산합니다 (Elo 공식 기반).
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
            
        Returns:
            팀 A의 예상 승률 (0.0 ~ 1.0)
        """
        mmr_a = team_a.adjusted_mmr
        mmr_b = team_b.adjusted_mmr
        
        # Elo 공식: E_A = 1 / (1 + 10^((R_B - R_A) / 400))
        expected_score = 1 / (1 + 10 ** ((mmr_b - mmr_a) / 400))
        
        return expected_score
