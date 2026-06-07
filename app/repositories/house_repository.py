from ..models import House


class HouseRepository:
    def list_ordered(self):
        return House.query.order_by(House.house_number).all()

    def list_all(self):
        return House.query.all()

    def count(self):
        return House.query.count()

    def first(self):
        return House.query.first()

