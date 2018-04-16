from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler

from clients.bitfinex_client import Bitfinex_Client
from clients.gdax_client import GDAX_Client
from helper_functions import get_snapshot, Clients

from base import engine, Session, Base

Base.metadata.drop_all(engine)    # Drop table if exists
Base.metadata.create_all(engine)  # Create table
session = Session()               # Create session


class Web_Socket_Handler(WebSocketHandler):

    def data_received(self, chunk):
        pass

    def check_origin(self, origin):
        return True

    @coroutine
    def open(self):
        Clients.append(self)
        snapshot = get_snapshot(session)
        try:
            self.write_message(snapshot)
        except Exception:
            print("Exception when trying to send snapshot!")
        print("Websocket opened, Snapshot sent!")

    def on_message(self, message):
        print("Message from client:", message)

    def on_close(self):
        print("Websocket closed")
        Clients.remove(self)


class Snapshot_Poll(RequestHandler):

    def data_received(self, chunk):
        pass

    def set_default_headers(self):
        print("Headers set")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET')

    def get(self):
        exchange_specified = self.get_argument('exchange', None, True)
        price_specified = self.get_argument('price_greater_than', 0, True)

        snapshot = get_snapshot(session, price_specified, exchange_specified)
        self.write(snapshot)
        print("Snapshot poll sent!")


def make_app():
    return Application([
        (r"/snapshot", Snapshot_Poll),
        (r"/websocket", Web_Socket_Handler),
    ], debug=True, autoreload=False)


if __name__ == "__main__":
    app = make_app()
    app.listen(5000)

    bitfinex_client = Bitfinex_Client(session)
    gdax_client = GDAX_Client(session)

    ioloop = IOLoop.current()
    try:
        ioloop.add_callback(bitfinex_client.connect_to_websocket)
        ioloop.add_callback(gdax_client.connect_to_websocket)
        ioloop.start()
    except KeyboardInterrupt:
        ioloop.stop()
        session.close()

'''
    Standard HTTP
        RequestHandler.write() automatically encodes dicts to JSON.
        
        To get/post form and access request body - 
        
        class MyFormHandler(tornado.web.RequestHandler):
            def get(self):
                self.write('<html><body><form action="/myform" method="POST">'
                           '<input type="text" name="message">'
                           '<input type="submit" value="Submit">'
                           '</form></body></html>')

            def post(self):
                self.set_header("Content-Type", "text/plain")
                self.write("You wrote " + self.get_body_argument("message"))
        
        To parse a request into JSON -
        define this
        def prepare(self):
            if self.request.headers.get("Content-Type", "").startswith("application/json"):
                self.json_args = json.loads(self.request.body)
            else:
                self.json_args = None
'''
