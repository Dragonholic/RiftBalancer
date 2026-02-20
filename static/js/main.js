// 플레이어 목록 로드
async function loadPlayers() {
    try {
        const response = await fetch('/api/players');
        const data = await response.json();
        displayPlayers(data.players);
        updatePlayerCheckboxes(data.players);
        updateTeamSelection(data.players);
        updateStatisticsPlayerFilter(data.players);
        updateSyncPlayerSelect(data.players);
    } catch (error) {
        console.error('플레이어 로드 실패:', error);
    }
}

// 플레이어 목록 표시
function displayPlayers(players) {
    const container = document.getElementById('players-container');
    if (players.length === 0) {
        container.innerHTML = '<p>등록된 플레이어가 없습니다.</p>';
        return;
    }

    container.innerHTML = players.map(player => {
        const constraints = [];
        if (player.fixed_positions && player.fixed_positions.length > 0) {
            constraints.push(`고정: ${player.fixed_positions.map(p => getPositionName(p)).join(', ')}`);
        }
        if (player.excluded_positions && player.excluded_positions.length > 0) {
            constraints.push(`제외: ${player.excluded_positions.map(p => getPositionName(p)).join(', ')}`);
        }
        const constraintText = constraints.length > 0 ? `<div class="constraints">${constraints.join(' | ')}</div>` : '';
        
        return `
        <div class="player-card">
            <div class="player-info">
                <strong>${player.name}</strong>
                <div class="player-stats">
                    <span>레이팅: ${player.rating.toFixed(0)}</span>
                    <span>포지션: ${getPositionName(player.main_position)}</span>
                    <span>폼: ${(player.form_score * 100).toFixed(0)}%</span>
                </div>
                ${constraintText}
            </div>
            <div>
                <button class="edit-btn" onclick="editPlayerConstraints('${player.name}')">제약조건 수정</button>
                <button class="delete-btn" onclick="deletePlayer('${player.name}')">삭제</button>
            </div>
        </div>
    `;
    }).join('');
}

// 포지션 이름 변환
function getPositionName(position) {
    const names = {
        'TOP': '탑',
        'JUNGLE': '정글',
        'MIDDLE': '미드',
        'BOTTOM': '원딜',
        'UTILITY': '서포터',
        'UNKNOWN': '미정'
    };
    return names[position] || position;
}

// 플레이어 추가
document.getElementById('add-player-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('player-name').value;
    const riotId = document.getElementById('riot-id').value;
    const tagLine = document.getElementById('tag-line').value;
    const mainPosition = document.getElementById('main-position').value;
    const offPositions = Array.from(document.querySelectorAll('#players-tab input[type="checkbox"]:not([name]):checked'))
        .map(cb => cb.value);
    const fixedPositions = Array.from(document.querySelectorAll('#players-tab input[name="fixed"]:checked'))
        .map(cb => cb.value);
    const excludedPositions = Array.from(document.querySelectorAll('#players-tab input[name="excluded"]:checked'))
        .map(cb => cb.value);

    try {
        const response = await fetch('/api/players', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                riot_id: riotId,
                tag_line: tagLine,
                main_position: mainPosition,
                off_positions: offPositions,
                fixed_positions: fixedPositions,
                excluded_positions: excludedPositions
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('플레이어가 추가되었습니다.');
            document.getElementById('add-player-form').reset();
            loadPlayers();
        } else {
            alert('오류: ' + data.error);
        }
    } catch (error) {
        console.error('플레이어 추가 실패:', error);
        alert('플레이어 추가 중 오류가 발생했습니다.');
    }
});

// 플레이어 삭제
async function deletePlayer(name) {
    if (!confirm(`정말로 "${name}" 플레이어를 삭제하시겠습니까?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/players/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('플레이어가 삭제되었습니다.');
            loadPlayers();
        } else {
            const data = await response.json();
            alert('오류: ' + data.error);
        }
    } catch (error) {
        console.error('플레이어 삭제 실패:', error);
        alert('플레이어 삭제 중 오류가 발생했습니다.');
    }
}

// 매치메이킹용 선택된 플레이어 리스트
let selectedPlayersForMatchmaking = [];

// 플레이어 드롭다운 업데이트
function updatePlayerDropdown(players) {
    const dropdown = document.getElementById('player-select-dropdown');
    dropdown.innerHTML = '<option value="">플레이어 선택...</option>' + 
        players.filter(p => !selectedPlayersForMatchmaking.includes(p.name))
            .map(p => `<option value="${p.name}">${p.name} (${p.rating.toFixed(0)})</option>`)
            .join('');
}

// 매치메이킹에 플레이어 추가
function addPlayerToMatchmaking() {
    const dropdown = document.getElementById('player-select-dropdown');
    const playerName = dropdown.value;
    
    if (!playerName) {
        alert('플레이어를 선택해주세요.');
        return;
    }
    
    if (selectedPlayersForMatchmaking.length >= 10) {
        alert('최대 10명까지만 선택할 수 있습니다.');
        return;
    }
    
    if (selectedPlayersForMatchmaking.includes(playerName)) {
        alert('이미 선택된 플레이어입니다.');
        return;
    }
    
    selectedPlayersForMatchmaking.push(playerName);
    updateSelectedPlayersList();
    updateMatchmakingButton();
}

// 선택된 플레이어 리스트 업데이트
function updateSelectedPlayersList() {
    const container = document.getElementById('selected-players-list');
    const countDisplay = document.getElementById('player-count-display');
    
    countDisplay.innerHTML = `선택된 플레이어: <strong>${selectedPlayersForMatchmaking.length}</strong>/10`;
    
    if (selectedPlayersForMatchmaking.length === 0) {
        container.innerHTML = '<p>선택된 플레이어가 없습니다.</p>';
        return;
    }
    
    container.innerHTML = selectedPlayersForMatchmaking.map(name => `
        <div class="selected-player-item">
            <span>${name}</span>
            <button onclick="removePlayerFromMatchmaking('${name}')" class="remove-btn">제거</button>
        </div>
    `).join('');
    
    // 드롭다운 업데이트
    loadPlayers();
}

// 매치메이킹에서 플레이어 제거
function removePlayerFromMatchmaking(playerName) {
    selectedPlayersForMatchmaking = selectedPlayersForMatchmaking.filter(n => n !== playerName);
    updateSelectedPlayersList();
    updateMatchmakingButton();
}

// 매치메이킹 버튼 상태 업데이트
function updateMatchmakingButton() {
    const btn = document.getElementById('matchmaking-btn');
    btn.disabled = selectedPlayersForMatchmaking.length !== 10;
}

// 플레이어 체크박스 업데이트 (레거시, 사용 안 함)
function updatePlayerCheckboxes(players) {
    updatePlayerDropdown(players);
}

// 플레이어 제약 조건 수정
async function editPlayerConstraints(playerName) {
    const players = await fetch('/api/players').then(r => r.json()).then(d => d.players);
    const player = players.find(p => p.name === playerName);
    
    if (!player) return;
    
    const fixedPositions = prompt(`고정 포지션 (쉼표로 구분):\n예: JUNGLE 또는 TOP,JUNGLE\n현재: ${player.fixed_positions.join(',') || '없음'}`, player.fixed_positions.join(','));
    if (fixedPositions === null) return;
    
    const excludedPositions = prompt(`제외 포지션 (쉼표로 구분):\n예: BOTTOM 또는 TOP,BOTTOM\n현재: ${player.excluded_positions.join(',') || '없음'}`, player.excluded_positions.join(','));
    if (excludedPositions === null) return;
    
    const fixed = fixedPositions.trim() ? fixedPositions.split(',').map(p => p.trim().toUpperCase()) : [];
    const excluded = excludedPositions.trim() ? excludedPositions.split(',').map(p => p.trim().toUpperCase()) : [];
    
    try {
        const response = await fetch(`/api/players/${encodeURIComponent(playerName)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fixed_positions: fixed,
                excluded_positions: excluded
            })
        });
        
        if (response.ok) {
            alert('제약 조건이 업데이트되었습니다.');
            loadPlayers();
        } else {
            const data = await response.json();
            alert('오류: ' + data.error);
        }
    } catch (error) {
        console.error('제약 조건 업데이트 실패:', error);
        alert('제약 조건 업데이트 중 오류가 발생했습니다.');
    }
}

// 매치메이킹 실행
async function runMatchmaking() {
    if (selectedPlayersForMatchmaking.length !== 10) {
        alert('정확히 10명의 플레이어를 선택해주세요.');
        return;
    }

    try {
        const response = await fetch('/api/matchmaking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_names: selectedPlayersForMatchmaking
            })
        });

        const data = await response.json();
        if (response.ok) {
            displayMatchmakingResults(data.matches);
        } else {
            alert('오류: ' + data.error);
        }
    } catch (error) {
        console.error('매치메이킹 실패:', error);
        alert('매치메이킹 중 오류가 발생했습니다.');
    }
}

// 매치메이킹 결과 표시
function displayMatchmakingResults(matches) {
    const container = document.getElementById('matchmaking-results');
    
    container.innerHTML = matches.map((match, index) => `
        <div class="match-result">
            <div class="match-header">
                <h3>조합 ${index + 1}</h3>
                <div class="match-cost">Cost: ${match.cost}</div>
            </div>
            <p style="text-align: center; font-size: 1.2em; margin-bottom: 15px;">
                예상 승률: 팀 A ${match.expected_win_rate}% vs 팀 B ${(100 - match.expected_win_rate).toFixed(2)}%
            </p>
            <div class="team-display">
                <div class="team-box team-a">
                    <h4>팀 A (MMR: ${match.team_a.mmr})</h4>
                    ${match.team_a.players.map((name, idx) => `
                        <div class="team-player">
                            <span>${name}</span>
                            <span style="color: #666; font-size: 0.9em;">
                                ${getPositionName(match.team_a.positions[name] || 'UNKNOWN')}
                            </span>
                        </div>
                    `).join('')}
                </div>
                <div class="team-box team-b">
                    <h4>팀 B (MMR: ${match.team_b.mmr})</h4>
                    ${match.team_b.players.map((name, idx) => `
                        <div class="team-player">
                            <span>${name}</span>
                            <span style="color: #666; font-size: 0.9em;">
                                ${getPositionName(match.team_b.positions[name] || 'UNKNOWN')}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

// 팀 선택 업데이트
function updateTeamSelection(players) {
    const teamAContainer = document.getElementById('team-a-selection');
    const teamBContainer = document.getElementById('team-b-selection');
    
    const checkboxHtml = players.map(player => `
        <label>
            <input type="checkbox" name="team-a" value="${player.name}" 
                   onchange="updateTeamSelection()">
            ${player.name}
        </label>
    `).join('');
    
    teamAContainer.innerHTML = checkboxHtml;
    teamBContainer.innerHTML = checkboxHtml.replace(/name="team-a"/g, 'name="team-b"');
}

// 경기 결과 제출
document.getElementById('match-result-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const teamA = Array.from(document.querySelectorAll('input[name="team-a"]:checked'))
        .map(cb => cb.value);
    const teamB = Array.from(document.querySelectorAll('input[name="team-b"]:checked'))
        .map(cb => cb.value);
    const winner = document.getElementById('winner-team').value;
    const gameDuration = parseInt(document.getElementById('game-duration').value);
    const goldDiff = parseInt(document.getElementById('gold-diff').value);
    const killDiff = parseInt(document.getElementById('kill-diff').value);

    if (teamA.length !== 5 || teamB.length !== 5) {
        alert('각 팀은 정확히 5명이어야 합니다.');
        return;
    }

    try {
        const response = await fetch('/api/match-result', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                team_a: teamA,
                team_b: teamB,
                team_a_won: winner === 'team_a',
                game_duration: gameDuration,
                gold_diff: goldDiff,
                kill_diff: killDiff
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('경기 결과가 반영되었습니다.');
            document.getElementById('match-result-form').reset();
            loadPlayers();
        } else {
            alert('오류: ' + data.error);
        }
    } catch (error) {
        console.error('경기 결과 제출 실패:', error);
        alert('경기 결과 제출 중 오류가 발생했습니다.');
    }
});

// 설정 저장
document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const apiKey = document.getElementById('api-key').value;

    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: apiKey
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('설정이 저장되었습니다.');
            document.getElementById('api-key').value = '';
        } else {
            alert('오류: ' + data.error);
        }
    } catch (error) {
        console.error('설정 저장 실패:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    }
});

// 탭 전환
function showTab(tabName) {
    // 모든 탭 숨기기
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 모든 탭 버튼 비활성화
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 선택한 탭 표시
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    // 플레이어 목록 새로고침
    if (tabName === 'players' || tabName === 'matchmaking' || tabName === 'results') {
        loadPlayers();
    }
    
    // 통계 탭일 경우 통계 로드
    if (tabName === 'statistics') {
        loadStatistics();
    }
}

// 통계 로드
async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        displayStatistics(data);
    } catch (error) {
        console.error('통계 로드 실패:', error);
        alert('통계 로드 중 오류가 발생했습니다.');
    }
}

// 필터링된 통계 로드
async function loadFilteredStatistics() {
    const selected = Array.from(document.querySelectorAll('#statistics-player-filter option:checked'))
        .map(opt => opt.value)
        .filter(v => v);
    
    const url = selected.length > 0 
        ? `/api/statistics?players=${selected.map(encodeURIComponent).join('&players=')}`
        : '/api/statistics';
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        displayStatistics(data);
    } catch (error) {
        console.error('통계 로드 실패:', error);
        alert('통계 로드 중 오류가 발생했습니다.');
    }
}

// 통계 표시
function displayStatistics(data) {
    // 포지션별 통계
    const posContainer = document.getElementById('position-statistics');
    if (data.position_statistics && Object.keys(data.position_statistics).length > 0) {
        posContainer.innerHTML = `
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>포지션</th>
                        <th>총 게임</th>
                        <th>승</th>
                        <th>패</th>
                        <th>승률</th>
                        <th>평균 KDA</th>
                        <th>플레이어 수</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(data.position_statistics).map(([pos, stats]) => `
                        <tr>
                            <td><strong>${getPositionName(pos)}</strong></td>
                            <td>${stats.total_games}</td>
                            <td>${stats.wins}</td>
                            <td>${stats.losses}</td>
                            <td>${(stats.winrate * 100).toFixed(1)}%</td>
                            <td>${stats.avg_kda}</td>
                            <td>${stats.unique_players}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else {
        posContainer.innerHTML = '<p>포지션별 통계 데이터가 없습니다.</p>';
    }
    
    // 챔피언별 통계
    const champContainer = document.getElementById('champion-statistics');
    if (data.champion_statistics && Object.keys(data.champion_statistics).length > 0) {
        const topChampions = Object.entries(data.champion_statistics).slice(0, 20);
        champContainer.innerHTML = `
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>챔피언</th>
                        <th>총 게임</th>
                        <th>승</th>
                        <th>패</th>
                        <th>승률</th>
                        <th>플레이어 수</th>
                    </tr>
                </thead>
                <tbody>
                    ${topChampions.map(([champ, stats]) => `
                        <tr>
                            <td><strong>${champ}</strong></td>
                            <td>${stats.total_games}</td>
                            <td>${stats.wins}</td>
                            <td>${stats.losses}</td>
                            <td>${(stats.winrate * 100).toFixed(1)}%</td>
                            <td>${stats.unique_players}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } else {
        champContainer.innerHTML = '<p>챔피언별 통계 데이터가 없습니다.</p>';
    }
    
    // 플레이어별 통계
    const playerContainer = document.getElementById('player-statistics');
    if (data.player_statistics && Object.keys(data.player_statistics).length > 0) {
        playerContainer.innerHTML = Object.entries(data.player_statistics).map(([name, stats]) => `
            <div class="player-stat-card">
                <h4>${name}</h4>
                <div class="stat-grid">
                    <div><strong>총 게임:</strong> ${stats.total_games}</div>
                    <div><strong>승률:</strong> ${(stats.winrate * 100).toFixed(1)}%</div>
                    <div><strong>평균 KDA:</strong> ${stats.avg_kda}</div>
                    <div><strong>레이팅:</strong> ${stats.rating.toFixed(0)}</div>
                </div>
                ${Object.keys(stats.position_stats).length > 0 ? `
                    <div class="position-stats">
                        <strong>포지션별 승률:</strong>
                        ${Object.entries(stats.position_stats).map(([pos, posStats]) => 
                            `${getPositionName(pos)}: ${(posStats.winrate * 100).toFixed(1)}% (${posStats.games}게임)`
                        ).join(', ')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    } else {
        playerContainer.innerHTML = '<p>플레이어별 통계 데이터가 없습니다.</p>';
    }
}

// 통계 플레이어 필터 업데이트
function updateStatisticsPlayerFilter(players) {
    const filter = document.getElementById('statistics-player-filter');
    filter.innerHTML = '<option value="">모든 플레이어</option>' +
        players.map(p => `<option value="${p.name}">${p.name}</option>`).join('');
}

// 매치 동기화
async function syncMatches() {
    const selectedPlayers = Array.from(document.querySelectorAll('#sync-player-select option:checked'))
        .map(opt => opt.value)
        .filter(v => v);
    const matchCount = parseInt(document.getElementById('sync-match-count').value) || 20;
    
    const syncBtn = document.getElementById('sync-btn');
    const syncStatus = document.getElementById('sync-status');
    
    syncBtn.disabled = true;
    syncBtn.textContent = '동기화 중...';
    syncStatus.innerHTML = '<div class="alert">동기화를 시작합니다. 시간이 걸릴 수 있습니다...</div>';
    
    try {
        const response = await fetch('/api/sync-matches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_names: selectedPlayers,
                match_count: matchCount
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            syncStatus.innerHTML = `
                <div class="alert alert-success">
                    <strong>동기화 완료!</strong><br>
                    ${data.synced_matches}개의 매치가 동기화되었습니다.<br>
                    업데이트된 플레이어: ${data.updated_players.join(', ') || '없음'}<br>
                    ${data.errors.length > 0 ? '오류: ' + data.errors.join('<br>') : ''}
                </div>
            `;
            
            // 플레이어 목록 및 통계 새로고침
            loadPlayers();
            loadMatchCount();
            if (document.getElementById('statistics-tab').classList.contains('active')) {
                loadStatistics();
            }
        } else {
            syncStatus.innerHTML = `
                <div class="alert alert-error">
                    오류: ${data.error}
                </div>
            `;
        }
    } catch (error) {
        console.error('매치 동기화 실패:', error);
        syncStatus.innerHTML = `
            <div class="alert alert-error">
                동기화 중 오류가 발생했습니다: ${error.message}
            </div>
        `;
    } finally {
        syncBtn.disabled = false;
        syncBtn.textContent = '매치 동기화 시작';
    }
}

// 저장된 매치 수 로드
async function loadMatchCount() {
    try {
        const response = await fetch('/api/matches');
        const data = await response.json();
        document.getElementById('stored-match-count').textContent = data.total_matches;
    } catch (error) {
        console.error('매치 수 로드 실패:', error);
    }
}

// 동기화 플레이어 선택 업데이트
function updateSyncPlayerSelect(players) {
    const select = document.getElementById('sync-player-select');
    select.innerHTML = players.map(p => 
        `<option value="${p.name}">${p.name} (${p.riot_id}#${p.tag_line})</option>`
    ).join('');
}

// 페이지 로드 시 플레이어 목록 로드
window.addEventListener('DOMContentLoaded', () => {
    loadPlayers();
    loadStatistics();
    loadMatchCount();
});
