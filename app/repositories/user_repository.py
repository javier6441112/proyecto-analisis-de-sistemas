from ..models import User


class UserRepository:
    def list_recent(self):
        return User.query.order_by(User.created_at.desc()).all()

    def find_by_dpi(self, dpi):
        return User.query.filter_by(dpi=dpi).first()

