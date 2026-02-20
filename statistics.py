"""
통계 계산 모듈
포지션별 및 챔피언별 승률 통계를 계산합니다.
"""

from typing import Dict, List
from player import Player
from collections import defaultdict


class StatisticsCalculator:
    """통계 계산 클래스"""
    
    def __init__(self, players: List[Player]):
        """
        StatisticsCalculator 초기화
        
        Args:
            players: 플레이어 리스트
        """
        self.players = players
    
    def calculate_position_statistics(self) -> Dict[str, Dict]:
        """
        포지션별 통계를 계산합니다.
        
        Returns:
            {
                'TOP': {'total_games': int, 'wins': int, 'losses': int, 'winrate': float, 'avg_kda': float},
                ...
            }
        """
        position_stats = defaultdict(lambda: {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'total_kills': 0,
            'total_deaths': 0,
            'total_assists': 0,
            'players': set()
        })
        
        for player in self.players:
            for match in player.recent_matches:
                position = match.position
                if position == 'UNKNOWN':
                    continue
                
                stats = position_stats[position]
                stats['total_games'] += 1
                stats['players'].add(player.name)
                
                if match.win:
                    stats['wins'] += 1
                else:
                    stats['losses'] += 1
                
                stats['total_kills'] += match.kills
                stats['total_deaths'] += match.deaths
                stats['total_assists'] += match.assists
        
        # 결과 포맷팅
        result = {}
        for position, stats in position_stats.items():
            total = stats['total_games']
            if total == 0:
                continue
            
            wins = stats['wins']
            losses = stats['losses']
            
            # KDA 계산
            total_deaths = stats['total_deaths']
            if total_deaths == 0:
                avg_kda = (stats['total_kills'] + stats['total_assists']) / total
            else:
                avg_kda = (stats['total_kills'] + stats['total_assists']) / total_deaths
            
            result[position] = {
                'total_games': total,
                'wins': wins,
                'losses': losses,
                'winrate': wins / total if total > 0 else 0.0,
                'avg_kda': round(avg_kda, 2),
                'unique_players': len(stats['players'])
            }
        
        return result
    
    def calculate_champion_statistics(self) -> Dict[str, Dict]:
        """
        챔피언별 통계를 계산합니다.
        
        Returns:
            {
                'ChampionName': {'total_games': int, 'wins': int, 'losses': int, 'winrate': float, 'players': List[str]},
                ...
            }
        """
        champion_stats = defaultdict(lambda: {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'players': set()
        })
        
        for player in self.players:
            # 챔피언 승률 데이터에서 통계 수집
            for champion, stats in player.champion_winrates.items():
                champ_stats = champion_stats[champion]
                champ_stats['total_games'] += stats.get('total', 0)
                champ_stats['wins'] += stats.get('wins', 0)
                champ_stats['losses'] += champ_stats['total_games'] - champ_stats['wins']
                champ_stats['players'].add(player.name)
            
            # 최근 경기에서 챔피언 정보 수집
            for match in player.recent_matches:
                if match.champion:
                    champ_stats = champion_stats[match.champion]
                    champ_stats['total_games'] += 1
                    champ_stats['players'].add(player.name)
                    if match.win:
                        champ_stats['wins'] += 1
                    else:
                        champ_stats['losses'] += 1
        
        # 결과 포맷팅
        result = {}
        for champion, stats in champion_stats.items():
            total = stats['total_games']
            if total == 0:
                continue
            
            wins = stats['wins']
            losses = stats['losses']
            
            result[champion] = {
                'total_games': total,
                'wins': wins,
                'losses': losses,
                'winrate': wins / total if total > 0 else 0.0,
                'unique_players': len(stats['players']),
                'players': list(stats['players'])
            }
        
        # 승률 기준으로 정렬
        result = dict(sorted(result.items(), key=lambda x: x[1]['winrate'], reverse=True))
        
        return result
    
    def calculate_player_statistics(self) -> Dict[str, Dict]:
        """
        플레이어별 통계를 계산합니다.
        
        Returns:
            {
                'PlayerName': {
                    'total_games': int,
                    'wins': int,
                    'losses': int,
                    'winrate': float,
                    'avg_kda': float,
                    'position_stats': Dict,
                    'champion_stats': Dict
                },
                ...
            }
        """
        result = {}
        
        for player in self.players:
            matches = player.recent_matches
            total = len(matches)
            
            if total == 0:
                continue
            
            wins = sum(1 for m in matches if m.win)
            losses = total - wins
            
            # KDA 계산
            total_kills = sum(m.kills for m in matches)
            total_deaths = sum(m.deaths for m in matches)
            total_assists = sum(m.assists for m in matches)
            
            if total_deaths == 0:
                avg_kda = total_kills + total_assists
            else:
                avg_kda = (total_kills + total_assists) / total_deaths
            
            # 포지션별 통계
            position_stats = {}
            for position in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']:
                pos_matches = [m for m in matches if m.position == position]
                if pos_matches:
                    pos_wins = sum(1 for m in pos_matches if m.win)
                    position_stats[position] = {
                        'games': len(pos_matches),
                        'wins': pos_wins,
                        'winrate': pos_wins / len(pos_matches)
                    }
            
            # 챔피언별 통계 (상위 5개)
            champion_stats = {}
            sorted_champions = sorted(
                player.champion_winrates.items(),
                key=lambda x: x[1].get('total', 0),
                reverse=True
            )[:5]
            
            for champion, stats in sorted_champions:
                champion_stats[champion] = {
                    'games': stats.get('total', 0),
                    'wins': stats.get('wins', 0),
                    'winrate': stats.get('winrate', 0.0)
                }
            
            result[player.name] = {
                'total_games': total,
                'wins': wins,
                'losses': losses,
                'winrate': wins / total if total > 0 else 0.0,
                'avg_kda': round(avg_kda, 2),
                'rating': player.rating,
                'form_score': player.form_score,
                'position_stats': position_stats,
                'champion_stats': champion_stats
            }
        
        return result
    
    def get_overall_statistics(self) -> Dict:
        """
        전체 통계를 계산합니다.
        
        Returns:
            전체 통계 딕셔너리
        """
        position_stats = self.calculate_position_statistics()
        champion_stats = self.calculate_champion_statistics()
        player_stats = self.calculate_player_statistics()
        
        # 전체 게임 수
        total_games = sum(len(p.recent_matches) for p in self.players)
        
        return {
            'total_players': len(self.players),
            'total_games': total_games,
            'position_statistics': position_stats,
            'champion_statistics': champion_stats,
            'player_statistics': player_stats
        }
