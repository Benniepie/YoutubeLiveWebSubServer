"""
Security middleware for WebSub server
Validates requests are from legitimate Google PubSubHubbub servers
"""
import ipaddress
from functools import wraps
from flask import request, abort
import socket

# Google's IP ranges for PubSubHubbub
# These are the known IP ranges for pubsubhubbub.appspot.com
GOOGLE_IP_RANGES = [
    '66.249.80.0/20',      # Google crawlers
    '64.233.160.0/19',     # Google services
    '66.102.0.0/20',       # Google services
    '72.14.192.0/18',      # Google services
    '209.85.128.0/17',     # Google services
    '216.239.32.0/19',     # Google services
    '74.125.0.0/16',       # Google services
    '64.18.0.0/20',        # Google services
    '207.126.144.0/20',    # Google services
    '173.194.0.0/16',      # Google services
    '192.178.11.0/24',     # Google services
    '192.178.15.0/24',     # Google services
]

def is_google_ip(ip_address: str) -> bool:
    """
    Check if an IP address belongs to Google's known ranges
    
    Args:
        ip_address: IP address to check
    
    Returns:
        True if IP is in Google's ranges, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_address)
        
        for ip_range in GOOGLE_IP_RANGES:
            if ip in ipaddress.ip_network(ip_range):
                return True
        
        return False
    except ValueError:
        return False

def verify_google_request():
    """
    Verify that the request is coming from Google's PubSubHubbub servers
    
    Checks:
    1. IP address is in Google's known ranges
    2. User-Agent contains expected patterns
    3. Request has valid signature (already checked in main handler)
    """
    # Get client IP (handle proxies)
    if request.headers.get('X-Forwarded-For'):
        # If behind a proxy, get the original client IP
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        client_ip = request.remote_addr
    
    # Check IP address
    if not is_google_ip(client_ip):
        print(f"⚠️  Rejected request from non-Google IP: {client_ip}")
        return False
    
    # Check User-Agent (optional additional check)
    user_agent = request.headers.get('User-Agent', '')
    expected_patterns = ['FeedFetcher-Google', 'Google', 'AppEngine']
    
    if not any(pattern in user_agent for pattern in expected_patterns):
        print(f"⚠️  Suspicious User-Agent from {client_ip}: {user_agent}")
        # Don't reject based on User-Agent alone, just log it
    
    return True

def require_google_ip(f):
    """
    Decorator to require requests to come from Google IP ranges
    Use this on webhook endpoints
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verify_google_request():
            abort(403, description="Access denied: Invalid source")
        return f(*args, **kwargs)
    return decorated_function

def get_rate_limit_key():
    """Get a key for rate limiting based on IP"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

# Simple in-memory rate limiting (for production, use Redis)
from collections import defaultdict
from datetime import datetime, timedelta

rate_limit_store = defaultdict(list)

def rate_limit(max_requests=100, window_seconds=60):
    """
    Simple rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed in the time window
        window_seconds: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = get_rate_limit_key()
            now = datetime.utcnow()
            
            # Clean old entries
            rate_limit_store[key] = [
                timestamp for timestamp in rate_limit_store[key]
                if now - timestamp < timedelta(seconds=window_seconds)
            ]
            
            # Check rate limit
            if len(rate_limit_store[key]) >= max_requests:
                print(f"⚠️  Rate limit exceeded for {key}")
                abort(429, description="Rate limit exceeded")
            
            # Add current request
            rate_limit_store[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
