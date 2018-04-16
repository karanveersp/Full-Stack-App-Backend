import json
from models.book_item import Book_Item

# Clients list that will hold websocket client instances
Clients = []

def send_update_to_clients(update):
    """
    Sends JSON formatted string to all connected clients \n
    :param update: Book_Item object
    :return: void
    """
    dict_obj = json.loads(str(update))  # create a dict obj from Book_Item's __str__ method (to avoid Escape chars)
    if any(Clients):
        for client in Clients:
            try:
                client.write_message(dict_obj)
            except Exception:
                print("Exception when trying to write to clients!", dict_obj)


def get_snapshot(session, price_greater_than=0, exchange=None):
    """
    Returns JSON formatted order book from database \n
    :param session: Current db session
    :param price_greater_than: OPTIONAL query parameter
    :param exchange: OPTIONAL query parameter
    :return: order_book string
    """
    if exchange:
        rows = session.query(Book_Item).filter(Book_Item.exchange == exchange).filter(Book_Item.price > price_greater_than).all()
    else:
        rows = session.query(Book_Item).filter(Book_Item.price > price_greater_than).all()
    order_book = []
    for row in rows:
        order_book.append(json.loads(str(row)))
    return json.dumps(order_book)
