from ..models import Resident


class ResidentRepository:
    def count(self):
        return Resident.query.count()

    def list(self, house_id=None):
        query = Resident.query
        if house_id:
            query = query.filter_by(house_id=house_id)
        return query.order_by(Resident.last_name).all()

