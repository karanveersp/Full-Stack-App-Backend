from tornado.gen import coroutine
from tornado.websocket import websocket_connect
from models.book_item import Book_Item
from helper_functions import send_update_to_clients

import json


class Bitfinex_Client:
    # static variable to flag receipt of snapshot
    snapshot_received = False

    def __init__(self, session):
        self.session = session

    @coroutine
    def connect_to_websocket(self):
        """
        This async function connects to the Bitfinex websocket and subscribes to their order book \n
        for the BTCUSD pair. It creates a snapshot in database when it is received     \n
        from the websocket. Any updates received thereafter are made on the snapshot in the database
        and emitted to clients connected to this server. \n
        :return: void
        """
        conn = yield websocket_connect("wss://api.bitfinex.com/ws")

        req = {
            "event": "subscribe",
            "channel": "book",
            "pair": "BTCUSD",
            "freq": "F0",
        }
        conn.write_message(json.dumps(req))
        while True:
            msg = yield conn.read_message()
            response = json.loads(msg)
            if response:
                if self.snapshot_received:
                    # Perform update in database
                    # and emit update to client
                    self.perform_update(response)

                if isinstance(response, list) and not self.snapshot_received:  # If true, store snapshot in database

                    for data in response[1]:  # here data is of form [price, count, amount]
                        item_type = "bid" if data[2] > 0 else "ask"  # bid if amt > 0, else ask
                        item = self.add_new_bitfinex_item(item_type, data[0], data[1])
                        self.session.add(item)
                    self.session.commit()
                    print("Bitfinex Snapshot Received")
                    self.snapshot_received = True  # Set flag
            else:
                break

    @staticmethod
    def add_new_bitfinex_item(new_type, new_price, new_count):
        """
        Initializes a new Book_Item object of exchange = "Bitfinex", pairname = "BTCUSD" \n
        :param new_type: "bid" or "ask"
        :param new_price: price of item
        :param new_count: count of item
        :return: Book_Item object
        """
        new_item = Book_Item(exchange="Bitfinex", pairname="BTCUSD", type=new_type, price=new_price, count=new_count)
        return new_item

    def perform_update(self, response):
        """
        Performs update with received websocket response. \n
        If change contains a count = 0, then the object is deleted from the database. \n
        If the object doesn't exist in the database, then it is added to it. \n
        The object in question is then emitted to clients to be processed there similarly. \n
        :param response: JSON parsed data from Bitfinex Websocket
        :return: void
        """
        if len(response) == 4:  # Received data consists of [channelid, price, count, amount]
            # omit channelid from list because we only subscribed to BTCUSD channel
            update_item = response[1:]

            update_type = "bid" if update_item[2] > 0 else "ask"  # set type = "bid" if amount > 0 else "ask"
            row = self.session.query(Book_Item).filter_by(exchange='Bitfinex',
                                                          type=update_type,
                                                          price=update_item[0]).first()

            if row:
                row.count = update_item[1]  # update count
                if row.count == 0:  # if row is updated to count = 0, delete row
                    self.session.delete(row)
                    self.session.commit()
                    # print(row, "Deleted from Bitfinex")
            else:  # if row doesn't exist, add item to db
                new_item = self.add_new_bitfinex_item(update_type, update_item[0], update_item[1])
                self.session.add(new_item)
                self.session.commit()  # commit in order to set the id attribute
                row = self.session.query(Book_Item).filter_by(exchange=new_item.exchange,
                                                              price=new_item.price,
                                                              type=new_item.type,
                                                              count=new_item.count).first()
                # print(row, "Added to Bitfinex")

            send_update_to_clients(row)
