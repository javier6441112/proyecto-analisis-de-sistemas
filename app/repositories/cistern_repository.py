from ..models import Cistern


class CisternRepository:
    def latest(self):
        return Cistern.query.order_by(Cistern.id.desc()).first()

    def first(self):
        return Cistern.query.first()

    def count(self):
        return Cistern.query.count()

