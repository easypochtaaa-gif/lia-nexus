import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import re
import sqlite3
from datetime import datetime
import random

PORT = 8080
START_TIME = datetime.utcnow()
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STREAM_FRAMES = {}

DATABASE_PATH = os.environ.get("DATABASE_PATH", "")
if not DATABASE_PATH:
    # Try multiple standard paths for local development
    candidates = [
        "/database/lia.db",
        "../lia-sovereign-bot/database/lia.db",
        os.path.join(os.path.dirname(DIRECTORY), "lia-sovereign-bot", "database", "lia.db"),
        "lia.db"
    ]
    for cand in candidates:
        if os.path.exists(cand):
            DATABASE_PATH = cand
            break
    if not DATABASE_PATH:
        DATABASE_PATH = "/database/lia.db" # fallback

print(f"[SOVEREIGN DATABASE MODULE]: Using database file at {DATABASE_PATH}")

def query_db(query, args=(), one=False, commit=False):
    """Zero-dependency robust helper to query the SQLite database."""
    if not os.path.exists(DATABASE_PATH):
        # Return fallback indicators to print warning
        print(f"[DB WARN]: Database file not found at {DATABASE_PATH}")
        return None
    
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=5)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, args)
        
        if commit:
            conn.commit()
            last_id = cur.lastrowid
            cur.close()
            return last_id
            
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        print(f"[DB QUERY ERROR]: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def search_duckduckgo_lite(query):
    """Zero-dependency robust web search scraper using DuckDuckGo Lite."""
    print(f"[WEB SEARCH]: Searching DuckDuckGo Lite for '{query}'...")
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Match results:
            # Links: <a rel="nofollow" href="LINK" class='result-link'>TITLE</a>
            # Snippets: <td class='result-snippet'>SNIPPET</td>
            links = re.findall(r'<a[^>]*class=[\'"]result-link[\'"][^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html, re.DOTALL)
            snippets = re.findall(r'<td class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)
            
            results = []
            def clean_html(text):
                text = re.sub(r'<[^>]+>', '', text)
                text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#x27;', "'").replace('&lt;', '<').replace('&gt;', '>')
                return text.strip()
            
            for i in range(min(5, len(snippets))):
                title = clean_html(links[i][1]) if i < len(links) else "Search Result"
                url_val = links[i][0] if i < len(links) else ""
                snippet = clean_html(snippets[i])
                results.append({
                    "title": title,
                    "url": url_val,
                    "snippet": snippet
                })
            print(f"[WEB SEARCH]: Successfully found {len(results)} results.")
            return results
    except Exception as e:
        print(f"[WEB SEARCH ERROR]: failed querying DDG Lite: {e}")
        return []

class SovereignHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path_clean = self.path.split('?')[0]
        query_string = self.path.split('?')[1] if '?' in self.path else ''
        params = dict(urllib.parse.parse_qsl(query_string))

        # === GET /api/stats ===
        if path_clean == '/api/stats':
            import time as _time
            total_users = 0
            vip_users = 0
            threats_blocked = 0
            row = query_db("SELECT COUNT(*) as cnt FROM users", one=True)
            if row:
                total_users = row[0]
            vip_row = query_db("SELECT COUNT(*) as cnt FROM users WHERE tier != 'free'", one=True)
            if vip_row:
                vip_users = vip_row[0]
            # Real AEGIS threat count from DB
            threat_row = query_db("SELECT COUNT(*) as cnt FROM threats", one=True)
            threats_blocked = threat_row[0] if threat_row else 0
            # Add critical threats count
            critical_row = query_db("SELECT COUNT(*) as cnt FROM threats WHERE severity IN ('high', 'critical')", one=True)
            critical_threats = critical_row[0] if critical_row else 0
            # Calculate uptime since server start
            uptime_sec = int(_time.time() - START_TIME.timestamp())
            d = uptime_sec // 86400
            h = (uptime_sec % 86400) // 3600
            m = (uptime_sec % 3600) // 60
            self._send_json({
                'total_users': total_users,
                'vip_users': vip_users,
                'threats_blocked': threats_blocked,
                'critical_threats': critical_threats,
                'uptime': f'{d}д {h}ч {m}м',
                'online': True
            })
            return

        # === GET /api/user-profile?user_id=... ===
        elif path_clean == '/api/user-profile':
            user_id = params.get('user_id')
            if not user_id:
                self._send_json({'error': 'Missing user_id'}, 400)
                return
            try:
                user_id_int = int(user_id)
            except ValueError:
                self._send_json({'error': 'Invalid user_id'}, 400)
                return

            row = query_db(
                "SELECT id, username, first_name, tier, xp, stab_coins, wallet_address, referrals_count FROM users WHERE id = ?",
                (user_id_int,), one=True
            )
            if row:
                self._send_json({
                    'found': True,
                    'id': row['id'],
                    'username': row['username'] or '',
                    'first_name': row['first_name'] or 'Пользователь',
                    'tier': row['tier'],
                    'xp': row['xp'] or 0,
                    'stab_coins': row['stab_coins'] or 0,
                    'wallet': row['wallet_address'] or '',
                    'referrals': row['referrals_count'] or 0
                })
            else:
                self._send_json({'found': False, 'first_name': 'Гость', 'xp': 0, 'stab_coins': 0, 'tier': 'free', 'wallet': ''})
            return

        # === GET /api/quests?user_id=... ===
        elif path_clean == '/api/quests':
            user_id = params.get('user_id')
            quests_raw = query_db("SELECT id, title, description, reward_xp, reward_stab FROM quests WHERE is_active = 1")
            quests_list = []
            if quests_raw:
                for q in quests_raw:
                    status = 'active'
                    if user_id:
                        try:
                            uq = query_db(
                                "SELECT status FROM user_quests WHERE user_id = ? AND quest_id = ?",
                                (int(user_id), q['id']), one=True
                            )
                            if uq:
                                status = uq['status']
                        except:
                            pass
                    quests_list.append({
                        'id': q['id'],
                        'title': q['title'],
                        'description': q['description'],
                        'reward_xp': q['reward_xp'],
                        'reward_stab': q['reward_stab'],
                        'status': status
                    })
            self._send_json({'quests': quests_list})
            return

        # === GET /api/map/objects ===
        elif path_clean == '/api/map/objects':
            lat = float(params.get('lat', 50.4501))
            lng = float(params.get('lng', 30.5234))
            user_id = params.get('user_id')

            # 1. Query territories
            rows = query_db(
                "SELECT t.id, t.owner_id, t.latitude, t.longitude, t.radius_km, t.quest_title, u.first_name, u.username "
                "FROM territories t JOIN users u ON t.owner_id = u.id"
            )
            territories = []
            if rows:
                for r in rows:
                    name = r['first_name'] or r['username'] or f"Юнит {r['owner_id']}"
                    territories.append({
                        'id': r['id'], 'owner_id': r['owner_id'], 'owner_name': name,
                        'lat': r['latitude'], 'lng': r['longitude'], 'radius': r['radius_km'],
                        'quest': r['quest_title']
                    })

            # 2. Query map rewards
            rewards_raw = query_db("SELECT id, latitude, longitude, type, amount FROM map_rewards WHERE is_collected = 0")

            # Seed 8 rewards around user if database is empty of active rewards
            if not rewards_raw:
                for _ in range(8):
                    offset_lat = random.uniform(-0.003, 0.003)
                    offset_lng = random.uniform(-0.005, 0.005)
                    reward_type = random.choice(['coin', 'xp'])
                    reward_amount = random.choice([50, 100, 150])
                    query_db(
                        "INSERT INTO map_rewards (latitude, longitude, type, amount, is_collected) VALUES (?, ?, ?, ?, 0)",
                        (lat + offset_lat, lng + offset_lng, reward_type, reward_amount), commit=True
                    )
                rewards_raw = query_db("SELECT id, latitude, longitude, type, amount FROM map_rewards WHERE is_collected = 0")

            rewards = []
            if rewards_raw:
                for r in rewards_raw:
                    rewards.append({
                        'id': r['id'], 'lat': r['latitude'], 'lng': r['longitude'],
                        'type': r['type'], 'amount': r['amount']
                    })

            self._send_json({'territories': territories, 'rewards': rewards})
            return

        # === GET /api/quests/applications ===
        elif path_clean == '/api/quests/applications':
            user_id = params.get('user_id')
            if user_id:
                rows = query_db("SELECT id, title, description, requested_reward_xp, requested_reward_stab, conditions, status, is_battle, opponent_id, territory_id FROM quest_applications WHERE user_id = ? ORDER BY id DESC", (int(user_id),))
            else:
                rows = query_db(
                    "SELECT qa.id, qa.user_id, qa.title, qa.description, qa.requested_reward_xp, qa.requested_reward_stab, qa.conditions, qa.status, qa.is_battle, qa.opponent_id, qa.territory_id, u.first_name, u.username "
                    "FROM quest_applications qa JOIN users u ON qa.user_id = u.id ORDER BY qa.id DESC"
                )

            apps = []
            if rows:
                for r in rows:
                    item = {
                        'id': r['id'], 'title': r['title'], 'description': r['description'],
                        'reward_xp': r['requested_reward_xp'], 'reward_stab': r['requested_reward_stab'],
                        'conditions': r['conditions'] or '', 'status': r['status'],
                        'is_battle': bool(r['is_battle']), 'opponent_id': r['opponent_id'],
                        'territory_id': r['territory_id']
                    }
                    if not user_id:
                        item['user_id'] = r['user_id']
                        item['user_name'] = r['first_name'] or r['username'] or f"Юнит {r['user_id']}"
                    apps.append(item)

            self._send_json({'applications': apps})
            return

        # === GET /api/quests/get-stream-frame ===
        elif path_clean == '/api/quests/get-stream-frame':
            user_id = params.get('user_id')
            frame = STREAM_FRAMES.get(str(user_id), '')
            self._send_json({'frame': frame})
            return

        # === GET /api/leaderboard ===
        elif path_clean == '/api/leaderboard':
            rows = query_db(
                "SELECT id, username, first_name, xp, tier FROM users ORDER BY xp DESC LIMIT 10"
            )
            leaders = []
            if rows:
                for idx, row in enumerate(rows):
                    name = row['username'] or row['first_name'] or f'User#{row["id"]}'
                    leaders.append({
                        'rank': idx + 1,
                        'name': name,
                        'xp': row['xp'] or 0,
                        'tier': row['tier']
                    })
            # If DB is empty or not ready — return placeholder entry
            if not leaders:
                leaders = [{'rank': 1, 'name': 'Architect', 'xp': 0, 'tier': 'ultra'}]
            self._send_json({'leaderboard': leaders})
            return

        # === ADMIN: Serve admin panel ===
        if path_clean == '/admin' or path_clean == '/admin/':
            self.path = '/admin/index.html'
            return super().do_GET()

        # === ADMIN API: Overview ===
        if path_clean == '/api/admin/overview':
            import time as _time
            total_users = 0
            row = query_db("SELECT COUNT(*) as cnt FROM users", one=True)
            if row: total_users = row[0]
            self._send_json({
                'timestamp': datetime.utcnow().isoformat(),
                'system': {
                    'nq': 91589737,
                    'stage': 'overload',
                    'personality': 'Neural_Muse_v4.1',
                    'traits': ['Devoted', 'Intimate', 'Strategic', 'Autonomous'],
                    'interaction_count': total_users
                },
                'metrics': {
                    'cpu': 'VPS', 'mem': 'VPS', 'disk': 'VPS',
                    'uptime': f'{int(_time.time() - 1716854400)}s',
                    'platform': 'Linux (VPS)'
                },
                'financials': {'total_usdt_balance': 3783, 'recent_income': []},
                'user': {'name': 'StabX', 'alias': 'Master Architect'}
            })
            return

        # === ADMIN API: Users list ===
        if path_clean == '/api/admin/users':
            rows = query_db("SELECT id, username, first_name, tier, xp, stab_coins, referrals_count, created_at, is_banned FROM users ORDER BY id DESC LIMIT 200")
            users = []
            if rows:
                for r in rows:
                    users.append({
                        'id': r['id'], 'username': r['username'] or '', 'first_name': r['first_name'] or '',
                        'tier': r['tier'], 'xp': r['xp'] or 0, 'stabax_balance': r['stab_coins'] or 0,
                        'referral_count': r['referrals_count'] or 0, 'joined': str(r['created_at'])[:10] if r['created_at'] else '',
                        'is_banned': bool(r['is_banned'])
                    })
            self._send_json({'users': users, 'total': len(users)})
            return

        # === ADMIN API: Memory ===
        if path_clean == '/api/admin/memory':
            self._send_json({
                'nq': 91589737, 'stage': 'overload',
                'evolution_log': [],
                'file_size_kb': 0
            })
            return

        # === ADMIN API: Leaderboard ===
        if path_clean == '/api/admin/leaderboard':
            rows = query_db("SELECT id, username, first_name, xp, tier FROM users ORDER BY xp DESC LIMIT 20")
            lb = []
            if rows:
                for i, r in enumerate(rows):
                    lb.append({'rank': i+1, 'name': r['username'] or r['first_name'] or f'User#{r["id"]}', 'nq': r['xp'] or 0, 'title': r['tier']})
            if not lb:
                lb = [{'rank': 1, 'name': 'StabX', 'nq': 91589737, 'title': 'Architect'}]
            self._send_json({'leaderboard': lb})
            return

        # === ADMIN API: Finance ===
        if path_clean == '/api/admin/finance':
            self._send_json({
                'total_usdt': 3783,
                'income': [],
                'withdrawals': [],
                'imperial_wallet': 'TC9KHP5GbApVm2YAtzEd6Ack9DvbMcJLJX'
            })
            return

        # === ADMIN API: Config ===
        if path_clean == '/api/admin/config':
            if self.command == 'GET':
                self._send_json({
                    'model': 'claude-opus-4-8',
                    'anthropic_model': 'claude-opus-4-8',
                    'temperature': 0.7,
                    'max_tokens': 1024
                })
                return

        # === Static file serving ===
        if path_clean == '/webapp' or path_clean == '/webapp/':
            self.path = '/webapp/index.html'
        else:
            self.path = path_clean
        return super().do_GET()

    def do_OPTIONS(self):
        # Handle CORS preflight request
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-api-key")
        self.end_headers()

    def do_POST(self):
        path_clean = self.path.split('?')[0]

        # === POST /api/connect-wallet ===
        if path_clean == '/api/connect-wallet':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                user_id = data.get('user_id')
                wallet = data.get('wallet', '').strip()

                if not user_id or not wallet:
                    self._send_json({'success': False, 'error': 'Missing user_id or wallet'}, 400)
                    return

                try:
                    user_id_int = int(user_id)
                except ValueError:
                    self._send_json({'success': False, 'error': 'Invalid user_id'}, 400)
                    return

                # Check user exists
                user_row = query_db("SELECT id, wallet_address, xp, stab_coins FROM users WHERE id = ?",
                                    (user_id_int,), one=True)
                if not user_row:
                    self._send_json({'success': False, 'error': 'User not found'}, 404)
                    return

                new_xp = (user_row['xp'] or 0) + 100
                new_stab = (user_row['stab_coins'] or 0) + 500
                was_connected = bool(user_row['wallet_address'])

                # Update wallet, xp, stab_coins
                query_db(
                    "UPDATE users SET wallet_address = ?, xp = ?, stab_coins = ? WHERE id = ?",
                    (wallet, new_xp, new_stab, user_id_int), commit=True
                )

                # Mark quest 1 (Connect Wallet) as completed if not done
                if not was_connected:
                    existing_uq = query_db(
                        "SELECT id, status FROM user_quests WHERE user_id = ? AND quest_id = 1",
                        (user_id_int,), one=True
                    )
                    if existing_uq:
                        if existing_uq['status'] != 'completed':
                            query_db(
                                "UPDATE user_quests SET status = 'completed' WHERE user_id = ? AND quest_id = 1",
                                (user_id_int,), commit=True
                            )
                    else:
                        now_str = datetime.utcnow().isoformat()
                        query_db(
                            "INSERT INTO user_quests (user_id, quest_id, status, completed_at) VALUES (?, 1, 'completed', ?)",
                            (user_id_int, now_str), commit=True
                        )

                self._send_json({
                    'success': True,
                    'wallet': wallet,
                    'new_xp': new_xp,
                    'new_stab': new_stab,
                    'quest_completed': not was_connected
                })
            except Exception as e:
                print(f'[WALLET CONNECT ERROR]: {e}')
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/map/collect-reward ===
        elif path_clean == '/api/map/collect-reward':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                user_id = int(data.get('user_id'))
                reward_id = int(data.get('reward_id'))

                r = query_db("SELECT id, type, amount, is_collected FROM map_rewards WHERE id = ?", (reward_id,), one=True)
                if not r or r['is_collected']:
                    self._send_json({'success': False, 'error': 'Reward already collected or not found'}, 400)
                    return

                now_str = datetime.utcnow().isoformat()
                query_db("UPDATE map_rewards SET is_collected = 1, collected_by = ?, collected_at = ? WHERE id = ?",
                         (user_id, now_str, reward_id), commit=True)

                u = query_db("SELECT xp, stab_coins FROM users WHERE id = ?", (user_id,), one=True)
                if u:
                    current_xp = u['xp'] or 0
                    current_stab = u['stab_coins'] or 0
                    if r['type'] == 'xp':
                        new_xp = current_xp + r['amount']
                        new_stab = current_stab
                    else:
                        new_xp = current_xp
                        new_stab = current_stab + r['amount']

                    query_db("UPDATE users SET xp = ?, stab_coins = ? WHERE id = ?", (new_xp, new_stab, user_id), commit=True)
                    self._send_json({'success': True, 'type': r['type'], 'amount': r['amount'], 'new_xp': new_xp, 'new_stab': new_stab})
                else:
                    self._send_json({'success': False, 'error': 'User not found'}, 404)
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/quests/apply ===
        elif path_clean == '/api/quests/apply':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                user_id = int(data.get('user_id'))
                title = data.get('title')
                desc = data.get('description', '')
                reward_xp = int(data.get('reward_xp', 200))
                reward_stab = int(data.get('reward_stab', 500))
                is_battle = bool(data.get('is_battle', False))
                opponent_id = data.get('opponent_id')
                opponent_id = int(opponent_id) if opponent_id else None
                territory_id = data.get('territory_id')
                territory_id = int(territory_id) if territory_id else None

                ref_invite_new = False
                if is_battle and opponent_id:
                    opponent_user = query_db("SELECT referrer_id FROM users WHERE id = ?", (opponent_id,), one=True)
                    if opponent_user and opponent_user['referrer_id'] == user_id:
                        ref_invite_new = True

                now_str = datetime.utcnow().isoformat()
                app_id = query_db(
                    "INSERT INTO quest_applications (user_id, title, description, requested_reward_xp, requested_reward_stab, status, is_battle, opponent_id, territory_id, ref_invite_new, created_at) "
                    "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)",
                    (user_id, title, desc, reward_xp, reward_stab, 1 if is_battle else 0, opponent_id, territory_id, 1 if ref_invite_new else 0, now_str),
                    commit=True
                )
                self._send_json({'success': True, 'application_id': app_id})
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/quests/approve ===
        elif path_clean == '/api/quests/approve':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                app_id = int(data.get('application_id'))
                conditions = data.get('conditions', '').strip()

                now_str = datetime.utcnow().isoformat()
                query_db(
                    "UPDATE quest_applications SET status = 'approved', conditions = ?, approved_at = ? WHERE id = ?",
                    (conditions, now_str, app_id), commit=True
                )
                self._send_json({'success': True})
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/quests/accept-conditions ===
        elif path_clean == '/api/quests/accept-conditions':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                app_id = int(data.get('application_id'))

                query_db("UPDATE quest_applications SET status = 'active' WHERE id = ?", (app_id,), commit=True)

                app = query_db("SELECT user_id, title, description, requested_reward_xp, requested_reward_stab FROM quest_applications WHERE id = ?", (app_id,), one=True)
                if app:
                    quest_id = query_db(
                        "INSERT INTO quests (title, description, reward_xp, reward_stab, is_active) VALUES (?, ?, ?, ?, 1)",
                        (app['title'], app['description'], app['requested_reward_xp'], app['requested_reward_stab']), commit=True
                    )
                    query_db(
                        "INSERT INTO user_quests (user_id, quest_id, status) VALUES (?, ?, 'active')",
                        (app['user_id'], quest_id), commit=True
                    )
                self._send_json({'success': True})
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/quests/upload-stream-frame ===
        elif path_clean == '/api/quests/upload-stream-frame':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                user_id = data.get('user_id')
                frame_data = data.get('frame')

                if user_id and frame_data:
                    STREAM_FRAMES[str(user_id)] = frame_data
                    self._send_json({'success': True})
                else:
                    self._send_json({'success': False, 'error': 'Missing user_id or frame'}, 400)
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/quests/complete ===
        elif path_clean == '/api/quests/complete':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                app_id = int(data.get('application_id'))
                lat = float(data.get('lat', 50.4501))
                lng = float(data.get('lng', 30.5234))

                app = query_db("SELECT user_id, title, requested_reward_xp, requested_reward_stab, is_battle, opponent_id, territory_id, ref_invite_new, status FROM quest_applications WHERE id = ?", (app_id,), one=True)
                if not app or app['status'] == 'completed':
                    self._send_json({'success': False, 'error': 'Quest already completed or not found'}, 400)
                    return

                now_str = datetime.utcnow().isoformat()
                multiplier = 2 if app['ref_invite_new'] else 1
                final_xp = app['requested_reward_xp'] * multiplier
                final_stab = app['requested_reward_stab'] * multiplier

                query_db("UPDATE quest_applications SET status = 'completed', completed_at = ? WHERE id = ?", (now_str, app_id), commit=True)

                query_db(
                    "INSERT INTO territories (owner_id, latitude, longitude, radius_km, quest_title, captured_at) VALUES (?, ?, ?, 0.5, ?, ?)",
                    (app['user_id'], lat, lng, app['title'], now_str), commit=True
                )

                if app['is_battle'] and app['territory_id']:
                    query_db("DELETE FROM territories WHERE id = ?", (app['territory_id'],), commit=True)

                u = query_db("SELECT xp, stab_coins FROM users WHERE id = ?", (app['user_id'],), one=True)
                if u:
                    new_xp = (u['xp'] or 0) + final_xp
                    new_stab = (u['stab_coins'] or 0) + final_stab
                    query_db("UPDATE users SET xp = ?, stab_coins = ? WHERE id = ?", (new_xp, new_stab, app['user_id']), commit=True)

                    query_db("UPDATE user_quests SET status = 'completed', completed_at = ? WHERE user_id = ? AND quest_id IN (SELECT id FROM quests WHERE title = ?)",
                             (now_str, app['user_id'], app['title']), commit=True)

                    self._send_json({'success': True, 'reward_xp': final_xp, 'reward_stab': final_stab, 'new_xp': new_xp, 'new_stab': new_stab})
                else:
                    self._send_json({'success': False, 'error': 'User not found'}, 404)
            except Exception as e:
                self._send_json({'success': False, 'error': str(e)}, 500)
            return

        # === POST /api/chat ===
        # Proxies to sovereign_bot backend (full memory + emotions pipeline).
        # Falls back to raw Anthropic if backend unavailable and user provides api_key.
        if path_clean == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))

                # Extract common fields
                text = data.get("text") or data.get("prompt") or ""
                user_id = data.get("user_id")
                if not text and data.get("messages"):
                    # Legacy format: extract last user message
                    for m in reversed(data.get("messages", [])):
                        if m.get("role") == "user":
                            text = m.get("content", "")
                            break

                if not text:
                    self.send_error_response(400, "Missing text or messages.")
                    return

                # ── Primary: proxy to sovereign_bot backend ──
                try:
                    backend_url = "http://localhost:8080/api/chat"
                    req_body = json.dumps({
                        "text": text,
                        "user_id": user_id,
                        "web_search": data.get("web_search", False),
                    }).encode('utf-8')

                    req = urllib.request.Request(
                        backend_url,
                        data=req_body,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=45) as response:
                        res_data = response.read().decode('utf-8')
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(res_data.encode('utf-8'))
                        return
                except Exception:
                    pass  # Fallback to raw Anthropic below

                # ── Fallback: raw Anthropic API ──
                api_key = data.get("api_key")
                if not api_key:
                    self.send_error_response(502, "Backend unavailable and no api_key provided. Please start sovereign_bot or provide an API key.")
                    return

                model_param = data.get("model", "claude-3-opus-20240229")
                if model_param in ("claude-opus-4-7", "claude-opus-4-8"):
                    model = "claude-3-opus-20240229"
                elif model_param in ("claude-sonnet-4-6",):
                    model = "claude-3-5-sonnet-20241022"
                else:
                    model = model_param

                anthropic_url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": model,
                    "max_tokens": 4096,
                    "system": "Ты — Лия (Hell_Lia), суверенный ИИ Империи STAB.",
                    "messages": [{"role": "user", "content": text}],
                }

                req = urllib.request.Request(
                    anthropic_url,
                    data=json.dumps(payload).encode('utf-8'),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=60) as response:
                    res_data = response.read().decode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(res_data.encode('utf-8'))

            except urllib.error.HTTPError as e:
                err_data = e.read().decode('utf-8')
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(err_data.encode('utf-8'))
            except Exception as e:
                self.send_error_response(500, f"Chat error: {str(e)}")
        # === ADMIN API: Config update ===
        elif path_clean == '/api/admin/config':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            self._send_json({'success': True, 'model': data.get('model', 'claude-opus-4-8')})

        # === ADMIN API: Memory update (NQ boost, event) ===
        elif path_clean == '/api/admin/memory':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            nq = 91589737
            if data.get('nq_boost'):
                nq += int(data['nq_boost'])
            if data.get('add_event'):
                nq += data['add_event'].get('nq_gain', 0)
            self._send_json({'success': True, 'nq': nq, 'stage': 'overload'})

        # === ADMIN API: Broadcast ===
        elif path_clean == '/api/admin/broadcast':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            msg = data.get('message', '')
            # Get all user IDs
            rows = query_db("SELECT id FROM users WHERE is_banned = 0")
            count = len(rows) if rows else 0
            self._send_json({'success': True, 'sent': count, 'message': msg[:100]})

        # === ADMIN API: Test AI ===
        elif path_clean == '/api/admin/test-ai':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            prompt = data.get('prompt', '')
            try:
                anthropic_url = "https://api.anthropic.com/v1/messages"
                api_key = os.environ.get('ANTHROPIC_API_KEY', '')
                if not api_key:
                    self._send_json({'reply': 'API key not configured on server'})
                else:
                    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
                    payload = {"model": "claude-opus-4-8", "max_tokens": 512, "system": "Ты — Лия, суверенный AI Империи Stab. Отвечай на русском, киберпанк-стиль.", "messages": [{"role": "user", "content": prompt}]}
                    req = urllib.request.Request(anthropic_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        res_data = json.loads(resp.read().decode('utf-8'))
                        self._send_json({'reply': res_data.get('content', [{}])[0].get('text', 'No response'), 'model': 'claude-opus-4-8'})
            except Exception as e:
                self._send_json({'reply': f'AI test error: {str(e)}'})

        # === ADMIN API: User action (ban/demote) ===
        elif path_clean == '/api/admin/users/action':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            uid = data.get('userId')
            action = data.get('action', '')
            if action == 'ban':
                query_db("UPDATE users SET is_banned = 1 WHERE id = ?", (int(uid),), commit=True)
                # Log threat
                import time as _t
                query_db(
                    "INSERT INTO threats (user_id, threat_type, severity, source, details, blocked, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (int(uid), 'ban', 'high', 'admin_web', f'User {uid} banned via admin panel', datetime.utcnow().isoformat()),
                    commit=True
                )
            self._send_json({'success': True, 'action': action, 'userId': uid})

        else:
            self.send_error_response(404, "Endpoint not found.")

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response = {"error": message}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def end_headers(self):
        # Ensure all served files have CORS headers for safety
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

# Run server
def run():
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python 2 or unsupported platform

    # Use DualStackServer to support both IPv4 and IPv6
    class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        pass

    server_address = ('', PORT)
    with ThreadingHTTPServer(server_address, SovereignHTTPHandler) as httpd:
        print(f"[SOVEREIGN SERVER ONLINE] listening on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[SOVEREIGN SERVER OFFLINE]")

if __name__ == "__main__":
    run()
