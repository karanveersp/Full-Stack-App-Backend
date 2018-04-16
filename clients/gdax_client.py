from tornado.gen import coroutine
from tornado.websocket import websocket_connect
from models.book_item import Book_Item
from helper_functions import send_update_to_clients
import json


class GDAX_Client:
    # static variable to flag receipt of snapshot
    snapshot_received = False

    def __init__(self, session):
        self.session = session

    @coroutine
    def connect_to_websocket(self):
        """
        This async function connects to the Gdax websocket and  \n
        subscribes to their order book for the BTCUSD pair.     \n
        It creates a snapshot in database when it is received from the websocket        \n
        and makes updates thereafter, emitting them to clients connected to this server.\n
        :return: void
        """
        # conn = yield websocket_connect("wss://ws-feed-public.sandbox.gdax.com")
        conn = yield websocket_connect("wss://ws-feed.gdax.com")
        req = {
            "type": "subscribe",
            "product_ids": [
                "BTC-USD"
            ],
            "channels": [
                "level2"
            ]
        }
        conn.write_message(json.dumps(req))
        while True:
            msg = yield conn.read_message()
            if msg:
                response = json.loads(msg)
                # print(response['type'])
                if response['type'] == 'l2update':
                    # # Perform update in database
                    # and emit update to client
                    self.perform_update(response)

                elif response['type'] == 'snapshot':
                    # Store snapshot in database
                    for bid_data in response['bids']:
                        # Intialize a new row of data
                        item = self.add_new_gdax_item("bid", bid_data[0], bid_data[1])
                        self.session.add(item)

                    for ask_data in response['asks']:
                        item = self.add_new_gdax_item("ask", ask_data[0], ask_data[1])
                        self.session.add(item)

                    self.session.commit()
                    print("GDAX Snapshot Received")
                    # print(response)
                    self.snapshot_received = True
                elif response['type'] == 'error':
                    print(response)
            else:
                break

    @staticmethod
    def add_new_gdax_item(new_type, new_price, new_count):
        """
        Initializes a new Book_Item object of exchange = "Gdax", pairname = "BTCUSD" \n
        :param new_type: "bid" or "ask"
        :param new_price: price of item
        :param new_count: count of item
        :return: Book_Item object
        """
        new_item = Book_Item(exchange="Gdax",
                             pairname="BTCUSD",
                             type=new_type,
                             price=float(new_price),
                             count=float(new_count))
        return new_item

    def perform_update(self, response):
        update_item = response["changes"][0]  # where response is of form ["changes": []
        # Change 'buy'/'sell' string into 'bid'/'ask'
        if update_item[0] == "sell":
            update_item[0] = "ask"
        else:
            update_item[0] = "bid"
        # Query for row from snapshot to update its count
        row = self.session.query(Book_Item).filter_by(exchange='Gdax', type=update_item[0],
                                                      price=update_item[1]).first()
        if row:
            # print(str(row))
            # print("Updating Gdax Count=", row.count, "with Count=", update_item[2])
            row.count = update_item[2]
            if row.count == 0:
                self.session.delete(row)
                self.session.commit()

        else:
            new_item = self.add_new_gdax_item(update_item[0], update_item[1], update_item[2])
            self.session.add(new_item)
            self.session.commit()
            row = self.session.query(Book_Item).filter_by(exchange=new_item.exchange,
                                                          price=new_item.price,
                                                          type=new_item.type,
                                                          count=new_item.count).first()

        send_update_to_clients(row)
