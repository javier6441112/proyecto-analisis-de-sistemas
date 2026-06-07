from ..models import WaterReading


class WaterReadingRepository:
    def list_recent(self, limit):
        return WaterReading.query.order_by(WaterReading.created_at.desc()).limit(limit).all()

