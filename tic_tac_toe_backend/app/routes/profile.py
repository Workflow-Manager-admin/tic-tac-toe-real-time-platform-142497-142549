from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from app.models import User
import jwt
import os

blp = Blueprint("Profile", "profile", url_prefix="/profile", description="User profile endpoints")
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')

def decode_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded['sub']
    except Exception:
        return None

def require_auth():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, message="Missing Bearer token.")
    token = auth_header[7:]
    user_id = decode_jwt(token)
    if not user_id:
        abort(401, message="Invalid or expired token.")
    return user_id

# PUBLIC_INTERFACE
@blp.route("/")
class UserProfileView(MethodView):
    """Get or update the profile of the authenticated user."""
    def get(self):
        user_id = require_auth()
        user = User.get_by_id(user_id)
        if not user:
            abort(404, message="User not found.")
        return {"id": user['id'], "username": user['username'], "email": user['email'], "profile_data": user['profile_data']}

    def put(self):
        user_id = require_auth()
        data = request.get_json()
        profile_data = data.get("profile_data", {})
        user = User.update_profile(user_id, profile_data)
        return {"id": user['id'], "username": user['username'], "email": user['email'], "profile_data": user['profile_data']}
