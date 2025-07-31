from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.models import User
import os
import jwt
from datetime import datetime, timedelta

blp = Blueprint("Authentication", "auth", url_prefix="/auth", description="Authentication endpoints")

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')

def generate_jwt(user_id):
    expire = datetime.utcnow() + timedelta(hours=24)
    token = jwt.encode({'sub': user_id, 'exp': expire}, SECRET_KEY, algorithm="HS256")
    return token

def decode_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded['sub']
    except Exception:
        return None

# PUBLIC_INTERFACE
@blp.route("/signup")
class SignUpView(MethodView):
    """User signup endpoint."""
    def post(self):
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")

        if not username or not email or not password:
            abort(400, message="Username, email, and password are required.")
        # Check for existing user/email
        if User.get_by_email(email):
            abort(409, message="Email is already registered")
        if User.get_by_username(username):
            abort(409, message="Username is already taken")

        user = User.create_user(username, email, password)
        token = generate_jwt(user['id'])

        return {"user": {"id": user['id'], "username": user['username'], "email": user['email']}, "token": token}

# PUBLIC_INTERFACE
@blp.route("/login")
class LoginView(MethodView):
    """User login endpoint."""
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            abort(400, message="Email and password are required.")

        user = User.get_by_email(email)
        if not user or not User.verify_password(user, password):
            abort(401, message="Invalid credentials")
        token = generate_jwt(user['id'])
        return {"user": {"id": user['id'], "username": user['username'], "email": user['email']}, "token": token}

# PUBLIC_INTERFACE
@blp.route("/me")
class MeView(MethodView):
    """Get current session user's info via token."""
    def get(self):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            abort(401, message="Missing Bearer token.")
        token = auth_header[7:]
        user_id = decode_jwt(token)
        if not user_id:
            abort(401, message="Invalid or expired token.")
        user = User.get_by_id(user_id)
        return {"user": {"id": user['id'], "username": user['username'], "email": user['email'], "profile_data": user["profile_data"]}}
