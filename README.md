# Full-Stack-App-Backend
Python Tornado websocket server. It connects to the Bitfinex and GDAX websockets and emits the snapshots/updates to connected clients. There is also a REST endpoint which only serves up the snapshot.

## Instlal required packages
`>pip install -r requirements.txt`

## Run the server!
`>python server.py`

## If using virtualenv for windows
Execute the following commands before pip install

`>virtualenv venv --python=python.exe`

`>.\venv\Scripts\activate.bat`
