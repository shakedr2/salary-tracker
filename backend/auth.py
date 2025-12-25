# -*- coding: utf-8 -*-
"""
Basic authentication module - JWT-based authentication for multi-user support.

This is a basic implementation for demonstration purposes.
For production, consider using Flask-Login or Flask-JWT-Extended.
"""
import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, current_app

from .observability import get_structured_logger

logger = get_structured_logger("backend.auth")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret-key-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def generate_token(user_id: str, username: str) -> str:
    """
    Generate JWT token for user.
    
    Args:
        user_id: User identifier
        username: Username
    
    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info("Token generated", user_id=user_id, username=username)
    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info("Token verified", user_id=payload.get("user_id"))
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid token", error=str(e))
        return None


def hash_password(password: str) -> str:
    """
    Hash password using SHA-256 (for demo purposes).
    In production, use bcrypt or argon2.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def require_auth(f):
    """
    Decorator to require authentication for endpoints.
    
    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            return jsonify({"message": "Protected"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                logger.warning("Invalid authorization header format")
                return jsonify({
                    "error": "Invalid authorization header format",
                    "timestamp": datetime.utcnow().isoformat()
                }), 401
        
        if not token:
            logger.warning("Missing authentication token", endpoint=request.path)
            return jsonify({
                "error": "Authentication required",
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        payload = verify_token(token)
        if not payload:
            logger.warning("Invalid authentication token", endpoint=request.path)
            return jsonify({
                "error": "Invalid or expired token",
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        # Add user info to request context
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function


# Simple user store (in production, use database)
_users: Dict[str, Dict[str, str]] = {
    "demo": {
        "user_id": "1",
        "username": "demo",
        "password_hash": hash_password("demo123"),  # In production, use secure password
    }
}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user and return user info.
    
    Args:
        username: Username
        password: Plain text password
    
    Returns:
        User dict if authenticated, None otherwise
    """
    if username not in _users:
        logger.warning("Authentication failed - user not found", username=username)
        return None
    
    user = _users[username]
    password_hash = hash_password(password)
    
    if user["password_hash"] != password_hash:
        logger.warning("Authentication failed - invalid password", username=username)
        return None
    
    logger.info("User authenticated", username=username, user_id=user["user_id"])
    return {
        "user_id": user["user_id"],
        "username": user["username"]
    }

