#!/usr/bin/env python3
"""
Upstox OAuth Token Generator
Handles the OAuth 2.0 flow to get access token with proper scopes
"""

import requests
import webbrowser
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
import sys

# Your API credentials
API_KEY = "0cf66f06-dd8e-495e-aec0-49b7b31e4e22"
API_SECRET = "mannlavip1"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "full_access"  # Upstox uses 'full_access' for all permissions

AUTH_CODE = None
AUTH_ERROR = None
SERVER_RUNNING = True


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Upstox"""
    
    def do_GET(self):
        global AUTH_CODE, AUTH_ERROR
        
        # Parse the callback URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Extract authorization code or error
        if 'code' in query_params:
            AUTH_CODE = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = """
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: green;">Authorization Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
            <p>Your access token is being generated...</p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        else:
            AUTH_ERROR = query_params.get('error', ['Unknown error'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = f"""
            <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: red;">Authorization Failed!</h1>
            <p>Error: {AUTH_ERROR}</p>
            <p>Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_callback_server():
    """Start local HTTP server to receive OAuth callback"""
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server


def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    
    url = "https://api.upstox.com/v2/login/authorization/token"
    
    payload = {
        "code": code,
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print("\n[*] Exchanging authorization code for access token...")
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            print("[+] Successfully obtained access token!")
            print(f"\nAccess Token:\n{access_token}\n")
            return access_token
        else:
            print(f"[-] Error: {response.status_code}")
            print(f"[-] Response: {response.text}")
            return None
    except Exception as e:
        print(f"[-] Exception: {str(e)}")
        return None


def main():
    global AUTH_CODE, AUTH_ERROR
    
    print("=" * 80)
    print("Upstox OAuth Token Generator")
    print("=" * 80)
    
    # Step 1: Start local callback server
    print("\n[*] Starting local HTTP server on http://localhost:8080...")
    server = start_callback_server()
    time.sleep(1)
    print("[+] Server ready!")
    
    # Step 2: Build authorization URL
    auth_url = f"https://upstox.com/login?client_id={API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}"
    
    print("\n[*] Opening Upstox login page in your browser...")
    print(f"[*] Authorization URL: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("\n[*] Waiting for authorization callback...")
    print("[*] Please complete the login and consent flow in your browser.")
    
    # Step 3: Wait for callback (max 2 minutes)
    timeout = 120
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if AUTH_CODE:
            print(f"\n[+] Authorization code received: {AUTH_CODE[:20]}...")
            break
        if AUTH_ERROR:
            print(f"\n[-] Authorization error: {AUTH_ERROR}")
            server.shutdown()
            return None
        time.sleep(1)
    else:
        print("\n[-] Timeout waiting for authorization callback")
        server.shutdown()
        return None
    
    # Step 4: Exchange code for token
    server.shutdown()
    token = exchange_code_for_token(AUTH_CODE)
    
    if token:
        # Step 5: Update config
        print("\n[*] Updating config.py with new token...")
        try:
            with open('config.py', 'r') as f:
                config = f.read()
            
            # Find and replace the ACCESS_TOKEN line
            old_token_line = None
            for line in config.split('\n'):
                if line.startswith('ACCESS_TOKEN = '):
                    old_token_line = line
                    break
            
            if old_token_line:
                new_token_line = f'ACCESS_TOKEN = "{token}"'
                config = config.replace(old_token_line, new_token_line)
                
                with open('config.py', 'w') as f:
                    f.write(config)
                
                print("[+] config.py updated successfully!")
                print("\n[+] You can now run the trading bot:")
                print("    python trading_bot.py")
            else:
                print("[-] Could not find ACCESS_TOKEN in config.py")
                print(f"\n[!] Please manually update config.py with this token:\n{token}")
        except Exception as e:
            print(f"[-] Error updating config.py: {str(e)}")
            print(f"\n[!] Please manually update config.py with this token:\n{token}")
    else:
        print("[-] Failed to obtain access token")
        return None


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[-] Interrupted by user")
        sys.exit(1)
