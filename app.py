"""
Flask 웹 애플리케이션
라즈베리파이에서 실행되는 웹 서버
"""

from flask import Flask, render_template, request, jsonify, session
import json
import os
from typing import List, Dict, Optional
from player import Player, RecentMatch
from team import Team
from match_manager import MatchManager
from rating_system import RatingSystem
from riot_api_client import RiotAPIClient
from statistics import StatisticsCalculator
from match_storage import MatchStorage
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# 전역 상태 관리
players_db: Dict[str, Player] = {}
riot_client: Optional[RiotAPIClient] = None
rating_system = RatingSystem()
match_storage = MatchStorage()


def init_riot_client(api_key: str):
    """Riot API 클라이언트 초기화"""
    global riot_client
    riot_client = RiotAPIClient(api_key)


def load_players_from_file():
    """파일에서 플레이어 데이터 로드"""
    global players_db
    if os.path.exists('players.json'):
        try:
            with open('players.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, player_data in data.items():
                    player = Player(
                        name=player_data['name'],
                        riot_id=player_data['riot_id'],
                        tag_line=player_data['tag_line'],
                        puuid=player_data.get('puuid'),
                        rating=player_data.get('rating', 1500.0),
                        main_position=player_data.get('main_position', 'UNKNOWN'),
                        off_positions=player_data.get('off_positions', []),
                        fixed_positions=player_data.get('fixed_positions', []),
                        excluded_positions=player_data.get('excluded_positions', [])
                    )
                    # 챔피언 승률 데이터 로드
                    if 'champion_winrates' in player_data:
                        player.champion_winrates = player_data['champion_winrates']
                    # 최근 경기 로드
                    for match_data in player_data.get('recent_matches', []):
                        match = RecentMatch(
                            win=match_data['win'],
                            kills=match_data['kills'],
                            deaths=match_data['deaths'],
                            assists=match_data['assists'],
                            position=match_data['position'],
                            game_duration=match_data['game_duration'],
                            champion=match_data.get('champion'),
                            timestamp=datetime.fromisoformat(match_data['timestamp'])
                        )
                        player.add_match(match)
                    players_db[name] = player
        except Exception as e:
            print(f"플레이어 데이터 로드 실패: {e}")


def save_players_to_file():
    """플레이어 데이터를 파일에 저장"""
    data = {}
    for name, player in players_db.items():
        data[name] = {
            'name': player.name,
            'riot_id': player.riot_id,
            'tag_line': player.tag_line,
            'puuid': player.puuid,
            'rating': player.rating,
            'main_position': player.main_position,
            'off_positions': player.off_positions,
            'fixed_positions': player.fixed_positions,
            'excluded_positions': player.excluded_positions,
            'champion_winrates': player.champion_winrates,
            'recent_matches': [
                {
                    'win': m.win,
                    'kills': m.kills,
                    'deaths': m.deaths,
                    'assists': m.assists,
                    'position': m.position,
                    'game_duration': m.game_duration,
                    'champion': m.champion,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in player.recent_matches
            ],
            'synergy_data': player.synergy_data
        }
    
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/players', methods=['GET'])
def get_players():
    """모든 플레이어 목록 조회"""
    return jsonify({
        'players': [p.to_dict() for p in players_db.values()]
    })


@app.route('/api/players', methods=['POST'])
def add_player():
    """새 플레이어 추가"""
    data = request.json
    
    name = data.get('name')
    riot_id = data.get('riot_id')
    tag_line = data.get('tag_line')
    main_position = data.get('main_position', 'UNKNOWN')
    off_positions = data.get('off_positions', [])
    fixed_positions = data.get('fixed_positions', [])
    excluded_positions = data.get('excluded_positions', [])
    
    if not name or not riot_id or not tag_line:
        return jsonify({'error': '필수 필드가 누락되었습니다.'}), 400
    
    # PUUID 조회 (Riot API 클라이언트가 있는 경우)
    puuid = None
    if riot_client:
        puuid = riot_client.get_puuid_by_riot_id(riot_id, tag_line)
    
    player = Player(
        name=name,
        riot_id=riot_id,
        tag_line=tag_line,
        puuid=puuid,
        main_position=main_position,
        off_positions=off_positions,
        fixed_positions=fixed_positions,
        excluded_positions=excluded_positions
    )
    
    players_db[name] = player
    save_players_to_file()
    
    return jsonify({'message': '플레이어가 추가되었습니다.', 'player': player.to_dict()})


@app.route('/api/players/<player_name>', methods=['DELETE'])
def delete_player(player_name):
    """플레이어 삭제"""
    if player_name in players_db:
        del players_db[player_name]
        save_players_to_file()
        return jsonify({'message': '플레이어가 삭제되었습니다.'})
    return jsonify({'error': '플레이어를 찾을 수 없습니다.'}), 404


@app.route('/api/players/<player_name>', methods=['PUT'])
def update_player(player_name):
    """플레이어 정보 업데이트"""
    if player_name not in players_db:
        return jsonify({'error': '플레이어를 찾을 수 없습니다.'}), 404
    
    data = request.json
    player = players_db[player_name]
    
    # 업데이트 가능한 필드들
    if 'main_position' in data:
        player.main_position = data['main_position']
    if 'off_positions' in data:
        player.off_positions = data['off_positions']
    if 'fixed_positions' in data:
        player.fixed_positions = data['fixed_positions']
    if 'excluded_positions' in data:
        player.excluded_positions = data['excluded_positions']
    
    save_players_to_file()
    return jsonify({'message': '플레이어 정보가 업데이트되었습니다.', 'player': player.to_dict()})


@app.route('/api/matchmaking', methods=['POST'])
def matchmaking():
    """매치메이킹 실행"""
    data = request.json
    player_names = data.get('player_names', [])
    
    if len(player_names) < 10:
        return jsonify({'error': '최소 10명의 플레이어가 필요합니다.'}), 400
    
    if len(player_names) > 10:
        return jsonify({'error': '최대 10명의 플레이어만 선택할 수 있습니다.'}), 400
    
    # 플레이어 객체 가져오기
    selected_players = []
    for name in player_names:
        if name not in players_db:
            return jsonify({'error': f'플레이어 "{name}"를 찾을 수 없습니다.'}), 404
        selected_players.append(players_db[name])
    
    # 매치메이킹 실행
    match_manager = MatchManager(selected_players)
    best_matches = match_manager.find_best_matches(top_n=3)
    
    # 결과 포맷팅
    results = []
    for team_a, team_b, cost in best_matches:
        win_rate_a = match_manager.get_expected_win_rate(team_a, team_b)
        results.append({
            'team_a': {
                'players': [p.name for p in team_a.players],
                'positions': team_a.positions,
                'mmr': round(team_a.adjusted_mmr, 2),
                'synergy_bonus': round(team_a.synergy_bonus, 2)
            },
            'team_b': {
                'players': [p.name for p in team_b.players],
                'positions': team_b.positions,
                'mmr': round(team_b.adjusted_mmr, 2),
                'synergy_bonus': round(team_b.synergy_bonus, 2)
            },
            'cost': round(cost, 2),
            'expected_win_rate': round(win_rate_a * 100, 2)
        })
    
    return jsonify({'matches': results})


@app.route('/api/match-result', methods=['POST'])
def submit_match_result():
    """경기 결과 제출 및 레이팅 업데이트"""
    data = request.json
    
    team_a_names = data.get('team_a', [])
    team_b_names = data.get('team_b', [])
    team_a_won = data.get('team_a_won', False)
    game_duration = data.get('game_duration', 1800)  # 기본 30분
    gold_diff = data.get('gold_diff', 0)
    kill_diff = data.get('kill_diff', 0)
    
    # 플레이어 객체 가져오기
    team_a_players = [players_db[name] for name in team_a_names if name in players_db]
    team_b_players = [players_db[name] for name in team_b_names if name in players_db]
    
    if len(team_a_players) != 5 or len(team_b_players) != 5:
        return jsonify({'error': '각 팀은 정확히 5명이어야 합니다.'}), 400
    
    team_a = Team(players=team_a_players)
    team_b = Team(players=team_b_players)
    
    # 포지션 할당
    for player in team_a_players:
        team_a.assign_position(player.name, player.main_position)
    for player in team_b_players:
        team_b.assign_position(player.name, player.main_position)
    
    # 레이팅 업데이트
    rating_system.update_ratings(
        team_a=team_a,
        team_b=team_b,
        team_a_won=team_a_won,
        game_duration=game_duration,
        gold_diff=gold_diff,
        kill_diff=kill_diff
    )
    
    # 챔피언 정보 가져오기 (요청에 포함된 경우)
    champion_data = data.get('champions', {})  # {player_name: champion_name}
    
    # 최근 경기 기록 추가
    for player in team_a_players:
        champion = champion_data.get(player.name)
        match = RecentMatch(
            win=team_a_won,
            kills=0,  # 실제 데이터는 API에서 가져와야 함
            deaths=0,
            assists=0,
            position=team_a.positions.get(player.name, player.main_position),
            game_duration=game_duration,
            champion=champion
        )
        player.add_match(match)
        
        # 챔피언 승률 업데이트
        if champion:
            player.update_champion_stats(champion, team_a_won)
    
    for player in team_b_players:
        champion = champion_data.get(player.name)
        match = RecentMatch(
            win=not team_a_won,
            kills=0,
            deaths=0,
            assists=0,
            position=team_b.positions.get(player.name, player.main_position),
            game_duration=game_duration,
            champion=champion
        )
        player.add_match(match)
        
        # 챔피언 승률 업데이트
        if champion:
            player.update_champion_stats(champion, not team_a_won)
    
    save_players_to_file()
    
    return jsonify({
        'message': '경기 결과가 반영되었습니다.',
        'updated_ratings': {p.name: round(p.rating, 2) for p in team_a_players + team_b_players}
    })


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """통계 조회"""
    player_names = request.args.getlist('players')
    use_stored_matches = request.args.get('use_stored_matches', 'false').lower() == 'true'
    
    if player_names:
        selected_players = [players_db[name] for name in player_names if name in players_db]
    else:
        selected_players = list(players_db.values())
    
    if not selected_players:
        return jsonify({'error': '플레이어가 없습니다.'}), 400
    
    # 저장된 매치 데이터를 플레이어 통계에 반영
    if use_stored_matches:
        for player in selected_players:
            if player.puuid:
                stored_matches = match_storage.get_player_matches(player.puuid)
                for stored_match in stored_matches:
                    stats = match_storage.extract_player_stats_from_match(stored_match, player.puuid)
                    if stats:
                        # 이미 추가된 매치인지 확인 (match_id로)
                        existing_match_ids = [m.match_id for m in player.recent_matches if hasattr(m, 'match_id')]
                        if stored_match.match_id not in existing_match_ids:
                            match = RecentMatch(
                                win=stats['win'],
                                kills=stats['kills'],
                                deaths=stats['deaths'],
                                assists=stats['assists'],
                                position=stats['position'],
                                game_duration=stats['game_duration'],
                                champion=stats.get('champion'),
                                timestamp=datetime.fromtimestamp(stats['game_creation'] / 1000)
                            )
                            player.add_match(match)
                            
                            # 챔피언 승률 업데이트
                            if stats.get('champion'):
                                player.update_champion_stats(stats['champion'], stats['win'])
    
    calculator = StatisticsCalculator(selected_players)
    stats = calculator.get_overall_statistics()
    
    return jsonify(stats)


@app.route('/api/sync-matches', methods=['POST'])
def sync_matches():
    """Riot API에서 내전 기록을 동기화합니다."""
    if not riot_client:
        return jsonify({'error': 'Riot API 클라이언트가 초기화되지 않았습니다. 설정에서 API 키를 입력해주세요.'}), 400
    
    data = request.json
    player_names = data.get('player_names', [])
    match_count = data.get('match_count', 20)  # 기본 20개
    
    if not player_names:
        # 모든 플레이어 동기화
        player_names = list(players_db.keys())
    
    synced_matches = []
    updated_players = []
    errors = []
    
    for player_name in player_names:
        if player_name not in players_db:
            errors.append(f'플레이어 "{player_name}"를 찾을 수 없습니다.')
            continue
        
        player = players_db[player_name]
        
        # PUUID가 없으면 조회
        if not player.puuid:
            puuid = riot_client.get_puuid_by_riot_id(player.riot_id, player.tag_line)
            if puuid:
                player.puuid = puuid
            else:
                errors.append(f'플레이어 "{player_name}"의 PUUID를 조회할 수 없습니다.')
                continue
        
        # 내전 매치 ID 가져오기
        try:
            custom_match_ids = riot_client.get_custom_game_matches(player.puuid, match_count)
            
            # 각 매치 상세 정보 가져오기 및 저장
            for match_id in custom_match_ids:
                match_data = riot_client.get_match_details(match_id)
                if match_data:
                    # 매치 저장
                    if match_storage.store_match(match_id, match_data):
                        synced_matches.append(match_id)
                        
                        # 플레이어 통계 추출 및 업데이트
                        stats = riot_client.extract_match_stats(match_data, player.puuid)
                        if stats:
                            match = RecentMatch(
                                win=stats['win'],
                                kills=stats['kills'],
                                deaths=stats['deaths'],
                                assists=stats['assists'],
                                position=stats['position'],
                                game_duration=stats['game_duration'],
                                champion=stats.get('champion'),
                                timestamp=datetime.fromtimestamp(match_data['info']['gameCreation'] / 1000)
                            )
                            player.add_match(match)
                            
                            # 챔피언 승률 업데이트
                            if stats.get('champion'):
                                player.update_champion_stats(stats['champion'], stats['win'])
            
            updated_players.append(player_name)
            
        except Exception as e:
            errors.append(f'플레이어 "{player_name}" 동기화 실패: {str(e)}')
    
    # 변경사항 저장
    save_players_to_file()
    
    return jsonify({
        'message': f'{len(synced_matches)}개의 매치가 동기화되었습니다.',
        'synced_matches': len(synced_matches),
        'updated_players': updated_players,
        'errors': errors
    })


@app.route('/api/matches', methods=['GET'])
def get_matches():
    """저장된 매치 목록 조회"""
    player_name = request.args.get('player')
    days = int(request.args.get('days', 30))
    
    if player_name and player_name in players_db:
        player = players_db[player_name]
        if player.puuid:
            matches = match_storage.get_player_matches(player.puuid)
        else:
            matches = []
    else:
        matches = match_storage.get_recent_matches(days)
    
    # 매치 정보 포맷팅
    match_list = []
    for match in matches:
        match_list.append({
            'match_id': match.match_id,
            'game_creation': match.game_creation,
            'game_duration': match.game_duration,
            'game_mode': match.game_mode,
            'game_type': match.game_type,
            'participant_count': len(match.participants),
            'saved_at': match.saved_at
        })
    
    return jsonify({
        'total_matches': match_storage.get_match_count(),
        'matches': match_list[:100]  # 최대 100개만 반환
    })


@app.route('/api/config', methods=['POST'])
def set_config():
    """설정 저장 (Riot API 키 등)"""
    data = request.json
    api_key = data.get('api_key')
    
    if api_key:
        init_riot_client(api_key)
        return jsonify({'message': 'API 키가 설정되었습니다.'})
    
    return jsonify({'error': 'API 키가 제공되지 않았습니다.'}), 400


if __name__ == '__main__':
    # 플레이어 데이터 로드
    load_players_from_file()
    
    # Flask 앱 실행
    # 라즈베리파이에서 모든 네트워크 인터페이스에서 접근 가능하도록 설정
    app.run(host='0.0.0.0', port=5000, debug=True)
