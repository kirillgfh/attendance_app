from app import db
from app.models.user import User

class UserRepository:
    @staticmethod
    def get_by_id(user_id: int) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_username(username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    @staticmethod
    def create(username: str, password: str, role: str) -> User:
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def delete(user_id: int) -> None:
        user = db.session.get(User, user_id)
        if user:
            db.session.delete(user)
            db.session.commit()

    @staticmethod
    def update_password(user_id: int, new_password: str) -> User | None:
        user = db.session.get(User, user_id)
        if user:
            user.set_password(new_password)
            db.session.commit()
        return user

    @staticmethod
    def get_all_moderators() -> list[User]:
        return User.query.filter_by(role='moderator').all()