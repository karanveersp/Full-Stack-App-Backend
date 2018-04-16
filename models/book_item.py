from sqlalchemy import Column, Integer, Enum, DECIMAL
import json

from base import Base


class Book_Item(Base):
    __tablename__ = 'order_book'

    id = Column(Integer, primary_key=True)
    exchange = Column(Enum('Bitfinex', 'Gdax'), nullable=False)
    pairname = Column(Enum('BTCUSD'), nullable=False)
    type = Column(Enum('bid', 'ask'), nullable=False)
    price = Column(DECIMAL(12, 2), nullable=False)
    count = Column(DECIMAL(16, 10), nullable=False)

    def __init__(self, exchange, pairname, type, price, count):
        self.exchange = exchange
        self.pairname = pairname
        self.type = type
        self.price = price
        self.count = count

    def __str__(self):
        dict_obj = {"id": str(self.id), "exchange": self.exchange, "pairname": self.pairname, "type": self.type,
                    "price": str(self.price), "count": str(self.count)}
        return json.dumps(dict_obj)

    def __repr__(self):
        return "<%s %s %s %s %s>" % (self.exchange, self.pairname, self.type, self.price, self.count)

