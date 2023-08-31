from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class CarInfo:
    trim: str
    new_price: int
    old_price: int
    features: str
    timestamp: datetime
    area: str
    link: str
    data_id: str

    @property
    def discount(self):
        return self.old_price - self.new_price

    @property
    def feature_str(self):
        return self.features.replace("\n", " | ")

    @property
    def datetime_str(self):
        pdt_timezone = timezone(timedelta(hours=-7))
        pdt_time = self.timestamp.astimezone(pdt_timezone)
        return pdt_time.strftime("%m/%d/%Y, %H:%M:%S") + " PDT"

    def __str__(self):
        return f"{self.trim}, {self.new_price}, {self.old_price}, {self.discount}, {self.feature_str}, {self.datetime_str}, {self.area}, {self.link}, {self.data_id}"

    def to_gs_row(self):
        return [
            self.trim,
            self.new_price,
            self.old_price,
            self.discount,
            self.feature_str,
            self.datetime_str,
            self.area,
            self.link,
            self.data_id,
        ]
