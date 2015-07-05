import jwt

from datetime import datetime
from rest_framework_jwt.settings import api_settings

def jwt_payload_handler(user):
    try:
        username = user.get_username()
    except AttributeError:
        username = user.username

    return {
        'user_id': user.pk,
        'email': user.email,
        'username': username,
        'firstname': user.first_name,
        'lastname': user.last_name,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }

def jwt_response_payload_handler(token, user=None, request=None):
    """
    Returns the response data for both the login and refresh views.
    Override to return a custom response such as including the
    serialized representation of the User.
    """
    return {
        'token': token,
        'exp-time': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }