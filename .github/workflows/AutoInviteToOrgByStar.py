#!/usr/bin/env python3
"""
Auto-invite GitHub user to organization team when they star the repo.
Hardened for production CI environments.
"""

import os
import sys
import json
import requests

def load_event_data():
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path or not os.path.isfile(event_path):
        raise FileNotFoundError("GITHUB_EVENT_PATH is missing or invalid.")
    
    with open(event_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def send_github_invite(username, team_id, token):
    # Use the more modern /orgs/{org}/teams/{team_slug} if ID is problematic,
    # but the provided ID-based URL works fine for legacy compatibility.
    url = f'https://api.github.com/teams/{team_id}/memberships/{username}'
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'Bearer {token}' # 'Bearer' is the preferred modern standard over 'token'
    }

    try:
        print(f"📨 Processing invite for @{username}...")
        response = requests.put(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ User is already a member or invitation is active.")
        elif response.status_code == 201:
            print("🎉 Invite sent successfully.")
        elif response.status_code == 404:
            print("⚠️ Team ID or User not found. Check your COMMUNITY_TEAM_ID.")
        elif response.status_code == 403:
            print("❌ Permission denied. Your MY_GITHUB_KEY may lack 'admin:org' scope.")
        else:
            # We avoid printing response.text to prevent secret leakage in logs
            print(f"⚠️ API returned status: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")

def main():
    # Only log essential info to keep the log "clean"
    if not os.getenv('GITHUB_ACTIONS'):
        print("⚠️ Running outside of GitHub Actions.")

    # Validate inputs immediately
    github_token = os.getenv('MY_GITHUB_KEY')
    team_id = os.getenv('COMMUNITY_TEAM_ID')

    if not github_token or not team_id:
        print("❌ Error: MY_GITHUB_KEY and COMMUNITY_TEAM_ID must be set.")
        sys.exit(1)

    try:
        event_data = load_event_data()
        
        # Verify this is actually a 'started' (star) action
        action = event_data.get('action')
        if action != 'started':
            print(f"ℹ️ Ignoring action type: {action}")
            return

        username = event_data['sender']['login']
        send_github_invite(username, team_id, github_token)
        
    except Exception as e:
        print(f"❌ Script failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
