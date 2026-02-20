"""
LoL Custom Matchmaker 테스트 코드
더미 데이터를 사용한 간단한 테스트 실행
"""

from player import Player, RecentMatch
from team import Team
from match_manager import MatchManager
from rating_system import RatingSystem
from datetime import datetime, timedelta


def create_dummy_players():
    """더미 플레이어 데이터 생성"""
    players = []
    
    # 플레이어 데이터 (이름, Riot ID, Tag, 레이팅, 주 포지션, 부 포지션)
    player_data = [
        ("Hide on bush", "Hide on bush", "KR1", 1800, "MIDDLE", ["TOP", "JUNGLE"]),
        ("Faker", "Faker", "KR1", 1750, "MIDDLE", ["TOP"]),
        ("TheShy", "TheShy", "KR1", 1700, "TOP", ["MIDDLE"]),
        ("Uzi", "Uzi", "CN1", 1680, "BOTTOM", ["MIDDLE"]),
        ("Mata", "Mata", "KR1", 1650, "UTILITY", ["JUNGLE"]),
        ("Bengi", "Bengi", "KR1", 1620, "JUNGLE", ["TOP"]),
        ("Rookie", "Rookie", "CN1", 1600, "MIDDLE", ["TOP", "BOTTOM"]),
        ("Deft", "Deft", "KR1", 1580, "BOTTOM", ["MIDDLE"]),
        ("Keria", "Keria", "KR1", 1550, "UTILITY", ["MIDDLE"]),
        ("Canyon", "Canyon", "KR1", 1520, "JUNGLE", ["TOP", "MIDDLE"])
    ]
    
    for name, riot_id, tag, rating, main_pos, off_pos in player_data:
        player = Player(
            name=name,
            riot_id=riot_id,
            tag_line=tag,
            rating=rating,
            main_position=main_pos,
            off_positions=off_pos
        )
        
        # 더미 최근 경기 추가
        for i in range(5):
            match = RecentMatch(
                win=i % 2 == 0,  # 번갈아가며 승패
                kills=5 + i,
                deaths=3 - (i % 2),
                assists=8 + i,
                position=main_pos,
                game_duration=1800 + i * 300,  # 30분 ~ 45분
                timestamp=datetime.now() - timedelta(days=i)
            )
            player.add_match(match)
        
        players.append(player)
    
    return players


def test_matchmaking():
    """매치메이킹 테스트"""
    print("=" * 60)
    print("LoL Custom Matchmaker 테스트")
    print("=" * 60)
    
    # 더미 플레이어 생성
    players = create_dummy_players()
    print(f"\n총 {len(players)}명의 플레이어가 등록되었습니다.")
    
    # 플레이어 정보 출력
    print("\n[플레이어 정보]")
    for player in players:
        print(f"  {player.name:15s} | 레이팅: {player.rating:6.0f} | "
              f"포지션: {player.main_position:8s} | 폼: {player.form_score:.2f}")
    
    # 매치메이킹 실행
    print("\n" + "=" * 60)
    print("매치메이킹 실행 중...")
    print("=" * 60)
    
    match_manager = MatchManager(players)
    best_matches = match_manager.find_best_matches(top_n=3)
    
    # 결과 출력
    for idx, (team_a, team_b, cost) in enumerate(best_matches, 1):
        win_rate_a = match_manager.get_expected_win_rate(team_a, team_b)
        
        print(f"\n[조합 {idx}] Cost: {cost:.2f}")
        print(f"예상 승률: 팀 A {win_rate_a*100:.2f}% vs 팀 B {(1-win_rate_a)*100:.2f}%")
        print(f"\n팀 A (MMR: {team_a.adjusted_mmr:.2f}, 시너지: {team_a.synergy_bonus:.2f}):")
        for player in team_a.players:
            position = team_a.positions.get(player.name, player.main_position)
            print(f"  - {player.name:15s} ({position})")
        
        print(f"\n팀 B (MMR: {team_b.adjusted_mmr:.2f}, 시너지: {team_b.synergy_bonus:.2f}):")
        for player in team_b.players:
            position = team_b.positions.get(player.name, player.main_position)
            print(f"  - {player.name:15s} ({position})")
        print("-" * 60)
    
    # 레이팅 업데이트 테스트
    print("\n" + "=" * 60)
    print("경기 결과 반영 테스트")
    print("=" * 60)
    
    if best_matches:
        team_a, team_b, _ = best_matches[0]
        rating_system = RatingSystem()
        
        print("\n경기 전 레이팅:")
        all_players = team_a.players + team_b.players
        for player in all_players:
            print(f"  {player.name:15s}: {player.rating:.2f}")
        
        # 경기 결과 시뮬레이션 (팀 A 승리, 25분 게임, 큰 점수 차이)
        rating_system.update_ratings(
            team_a=team_a,
            team_b=team_b,
            team_a_won=True,
            game_duration=1500,  # 25분
            gold_diff=8000,  # 큰 골드 차이
            kill_diff=12  # 큰 킬 차이
        )
        
        print("\n경기 후 레이팅 (팀 A 승리, 압도적 승리):")
        for player in all_players:
            print(f"  {player.name:15s}: {player.rating:.2f} ({player.rating - create_dummy_players()[all_players.index(player)].rating:+.2f})")
        
        # 다시 더미 데이터로 리셋하고 장기전 테스트
        players = create_dummy_players()
        match_manager = MatchManager(players)
        best_matches = match_manager.find_best_matches(top_n=1)
        team_a, team_b, _ = best_matches[0]
        
        # 장기전, 팽팽한 경기
        rating_system.update_ratings(
            team_a=team_a,
            team_b=team_b,
            team_a_won=True,
            game_duration=2400,  # 40분 장기전
            gold_diff=2000,  # 작은 골드 차이
            kill_diff=3  # 작은 킬 차이
        )
        
        print("\n경기 후 레이팅 (팀 A 승리, 팽팽한 장기전):")
        all_players = team_a.players + team_b.players
        for player in all_players:
            original_rating = create_dummy_players()[all_players.index(player)].rating
            print(f"  {player.name:15s}: {player.rating:.2f} ({player.rating - original_rating:+.2f})")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    test_matchmaking()
