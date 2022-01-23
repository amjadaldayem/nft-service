class User:
    def __init__(self, user_id, preferred_username, email, phone=''):
        self.user_id = user_id
        self.preferred_username = preferred_username
        self.email = email
        self.phone = phone

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id
