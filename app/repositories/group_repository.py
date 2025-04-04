from app import db
from app.models.group import Group
from app.models.user import User

class GroupRepository:
    @staticmethod
    def get_by_id(group_id: int) -> Group | None:
        return db.session.get(Group, group_id)

    @staticmethod
    def get_by_moderator_id(moderator_id: int) -> Group | None:
        return Group.query.filter_by(moderator_id=moderator_id).first()

    @staticmethod
    def get_all() -> list[Group]:
        return Group.query.all()

    @staticmethod
    def create(name: str, moderator_id: int) -> Group:
        group = Group(name=name, moderator_id=moderator_id)
        db.session.add(group)
        db.session.commit()
        return group

    @staticmethod
    def get_with_users() -> list[tuple]:
        return db.session.query(Group, User).join(User, Group.moderator_id == User.id).all()