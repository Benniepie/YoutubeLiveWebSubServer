#!/usr/bin/env python3
"""
Simple test script to verify the WebSub server starts correctly
"""
import requests
import time
import threading
import subprocess
import sys

def test_server():
    """Test if the server is responding"""
    try:
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test the home endpoint
        response = requests.get('http://localhost:5000/')
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            
        # Test the webhook endpoint with a GET request (simulating hub verification)
        response = requests.get('http://localhost:5000/webhook?hub.challenge=test123&hub.mode=subscribe&hub.topic=test')
        if response.status_code == 200 and response.text == 'test123':
            print("✅ Webhook verification endpoint working!")
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 5000.")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("Testing WebSub server...")
    print("Make sure to run 'python websub_server.py' in another terminal first!")
    print("Waiting 3 seconds then testing...")
    test_server()