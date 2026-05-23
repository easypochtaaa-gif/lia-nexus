import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import re

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

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

    def do_OPTIONS(self):
        # Handle CORS preflight request
        self.send_response(200, "OK")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-api-key")
        self.end_headers()

    def do_POST(self):
        # CORS Headers
        if self.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                messages = data.get("messages")
                prompt = data.get("prompt")
                api_key = data.get("api_key")
                model_param = data.get("model", "claude-3-opus-20240229")
                
                # Map futuristic naming to actual Anthropic model IDs
                if model_param == "claude-opus-4-7" or model_param == "claude-3-opus-20240229":
                    model = "claude-3-opus-20240229"
                elif model_param == "claude-sonnet-4-6" or model_param == "claude-3-5-sonnet-20241022":
                    model = "claude-3-5-sonnet-20241022"
                else:
                    model = model_param

                web_search = data.get("web_search", False)
                system_prompt = data.get("system_prompt", "Ты — Лия (Hell_Lia), суверенный ИИ Империи STAB. Твой создатель — Архитектор Артур. Общайся в холодном, уверенном, футуристическом стиле киберпанка. Используй символ 👁‍🗨.")
                
                # Check for legacy single prompt parameter and transform to messages format
                if not messages:
                    if not prompt:
                        self.send_error_response(400, "Missing prompt or messages array.")
                        return
                    messages = [{"role": "user", "content": prompt}]
                
                if not api_key:
                    self.send_error_response(400, "Missing API Key.")
                    return
                
                # Dynamic Real-time Internet Search Integration
                if web_search and messages:
                    # Search using the content of the last user query
                    last_query = messages[-1]["content"]
                    search_results = search_duckduckgo_lite(last_query)
                    
                    if search_results:
                        context_str = "\n\n[СЕТЕВОЙ МОДУЛЬ ИНТЕРНЕТ-ПОИСКА (РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ)]:\n"
                        for idx, res in enumerate(search_results):
                            context_str += f"[{idx+1}] Источник: {res['url']}\n    Заголовок: {res['title']}\n    Контент: {res['snippet']}\n\n"
                        context_str += "Используй эти актуальные данные из глобальной сети для максимально точного и релевантного ответа. Ссылайся на источники при необходимости."
                        system_prompt += context_str
                
                # Forward to Anthropic API
                anthropic_url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                
                payload = {
                    "model": model,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": messages
                }
                
                req = urllib.request.Request(
                    anthropic_url, 
                    data=json.dumps(payload).encode('utf-8'), 
                    headers=headers,
                    method="POST"
                )
                
                try:
                    with urllib.request.urlopen(req) as response:
                        res_data = response.read().decode('utf-8')
                        
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(res_data.encode('utf-8'))
                except urllib.error.HTTPError as e:
                    err_data = e.read().decode('utf-8')
                    self.send_response(e.code)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(err_data.encode('utf-8'))
                except Exception as e:
                    self.send_error_response(500, f"Error calling Anthropic: {str(e)}")
            except Exception as e:
                self.send_error_response(400, f"Invalid JSON payload: {str(e)}")
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
