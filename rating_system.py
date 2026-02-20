"""
RatingSystem 클래스 모듈
레이팅 업데이트 로직을 담당합니다.
"""

from typing import List, Dict
from player import Player
from team import Team


class RatingSystem:
    """
    레이팅 업데이트를 관리하는 클래스
    
    야구의 피타고리안 기대승률 개념을 차용하여,
    게임 시간, 골드 차이, 킬 차이를 가중치로 사용합니다.
    """
    
    BASE_K_FACTOR = 32.0  # 기본 K-factor (Elo 시스템)
    MIN_GAME_DURATION = 1200  # 최소 게임 시간 (20분, 초 단위)
    MAX_GAME_DURATION = 2400  # 최대 게임 시간 (40분, 초 단위)
    
    def __init__(self):
        """RatingSystem 초기화"""
        pass
    
    def calculate_match_importance(self, game_duration: int, gold_diff: int, kill_diff: int) -> float:
        """
        매치의 중요도(가중치)를 계산합니다.
        
        압도적인 짧은 게임(20분 이하)은 높은 가중치,
        팽팽한 장기전(40분 이상)은 낮은 가중치를 부여합니다.
        
        Args:
            game_duration: 게임 시간 (초)
            gold_diff: 팀 골드 차이
            kill_diff: 팀 킬 차이
            
        Returns:
            가중치 배수 (0.5 ~ 2.0)
        """
        # 게임 시간 기반 가중치
        if game_duration <= self.MIN_GAME_DURATION:
            time_weight = 2.0  # 압도적인 승리
        elif game_duration >= self.MAX_GAME_DURATION:
            time_weight = 0.5  # 팽팽한 장기전
        else:
            # 선형 보간
            time_weight = 2.0 - (game_duration - self.MIN_GAME_DURATION) / \
                         (self.MAX_GAME_DURATION - self.MIN_GAME_DURATION) * 1.5
        
        # 골드/킬 차이 기반 가중치 (차이가 클수록 높은 가중치)
        score_diff = abs(gold_diff) + abs(kill_diff) * 1000  # 킬당 약 1000골드로 환산
        if score_diff > 10000:
            diff_weight = 1.5
        elif score_diff > 5000:
            diff_weight = 1.2
        else:
            diff_weight = 1.0
        
        # 최종 가중치 (시간과 차이의 평균)
        final_weight = (time_weight + diff_weight) / 2
        
        return max(0.5, min(2.0, final_weight))
    
    def update_ratings(self, team_a: Team, team_b: Team, team_a_won: bool, 
                      game_duration: int, gold_diff: int, kill_diff: int):
        """
        경기 결과를 바탕으로 플레이어들의 레이팅을 업데이트합니다.
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
            team_a_won: 팀 A가 승리했는지 여부
            game_duration: 게임 시간 (초)
            gold_diff: 팀 A의 골드 차이 (양수면 A가 앞섬)
            kill_diff: 팀 A의 킬 차이 (양수면 A가 앞섬)
        """
        # 매치 중요도 계산
        importance = self.calculate_match_importance(game_duration, gold_diff, kill_diff)
        
        # 예상 승률 계산
        expected_win_rate_a = self._calculate_expected_win_rate(team_a, team_b)
        expected_win_rate_b = 1.0 - expected_win_rate_a
        
        # 실제 결과
        actual_score_a = 1.0 if team_a_won else 0.0
        actual_score_b = 1.0 - actual_score_a
        
        # 각 플레이어의 레이팅 업데이트
        k_factor = self.BASE_K_FACTOR * importance
        
        for player in team_a.players:
            position = team_a.positions.get(player.name, player.main_position)
            effective_rating = player.get_effective_rating(position)
            
            # 개인 기여도 보정 (간단한 휴리스틱)
            # 실제로는 KDA, 골드, 데미지 등을 고려해야 함
            contribution_factor = 1.0
            
            # 레이팅 업데이트
            rating_change = k_factor * (actual_score_a - expected_win_rate_a) * contribution_factor
            player.rating += rating_change
        
        for player in team_b.players:
            position = team_b.positions.get(player.name, player.main_position)
            effective_rating = player.get_effective_rating(position)
            
            contribution_factor = 1.0
            
            rating_change = k_factor * (actual_score_b - expected_win_rate_b) * contribution_factor
            player.rating += rating_change
    
    def _calculate_expected_win_rate(self, team_a: Team, team_b: Team) -> float:
        """
        팀 A의 예상 승률을 계산합니다.
        
        Args:
            team_a: 첫 번째 팀
            team_b: 두 번째 팀
            
        Returns:
            팀 A의 예상 승률 (0.0 ~ 1.0)
        """
        mmr_a = team_a.adjusted_mmr
        mmr_b = team_b.adjusted_mmr
        
        # Elo 공식
        expected_score = 1 / (1 + 10 ** ((mmr_b - mmr_a) / 400))
        
        return expected_score
    
    def update_from_match_result(self, players: List[Player], match_result: Dict):
        """
        매치 결과 딕셔너리로부터 레이팅을 업데이트합니다.
        
        Args:
            players: 참가 플레이어 리스트
            match_result: 매치 결과 딕셔너리
                {
                    'team_a': [player_names],
                    'team_b': [player_names],
                    'team_a_won': bool,
                    'game_duration': int,
                    'gold_diff': int,
                    'kill_diff': int
                }
        """
        # 플레이어 이름으로 객체 찾기
        player_dict = {p.name: p for p in players}
        
        team_a_players = [player_dict[name] for name in match_result['team_a']]
        team_b_players = [player_dict[name] for name in match_result['team_b']]
        
        team_a = Team(players=team_a_players)
        team_b = Team(players=team_b_players)
        
        # 포지션 할당 (간단히 주 포지션 사용)
        for player in team_a_players:
            team_a.assign_position(player.name, player.main_position)
        for player in team_b_players:
            team_b.assign_position(player.name, player.main_position)
        
        self.update_ratings(
            team_a=team_a,
            team_b=team_b,
            team_a_won=match_result['team_a_won'],
            game_duration=match_result['game_duration'],
            gold_diff=match_result['gold_diff'],
            kill_diff=match_result['kill_diff']
        )
