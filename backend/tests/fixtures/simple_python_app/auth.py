class AuthService:
    """Handles authentication logic."""
    def __init__(self):
        pass

    def login(self, username, password):
        """Validates credentials."""
        token = hash_password(password)
        return token

def hash_password(raw):
    return "hashed_" + raw
