import socket
import threading
import pickle

HEADER = 64
PORT = 5051
SERVER = socket.gethostbyname(socket.gethostname())
FORMAT = 'utf-8'
DELIM = "::"

DISCONNECT_MESSAGE = "!DISCONNECT"
CONTINUE_MESSAGE = "!CONTINUE"
HANDSHAKE_MESSAGE = "!HANDSHAKE"
MESSAGE_MESSAGE = "!MESSAGE"

ADDR = (SERVER, PORT)

_PLAYERS = {}
_DATA = {
    "spaceships": {
        "yellow": {
            "x": 100,
            "y": 100,
            'bullets': []
        },
        "red": {
            "y": 100,
            'x': 700,
            'bullets': []
        }
    }
}
IDS = {
    1: 'yellow',
    2: 'red'
}
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_handshake(addr, name):
    if len(_PLAYERS) < 2:
        id_key = len(_PLAYERS) + 1
        id = IDS[id_key]
        _PLAYERS[addr] = {
            "name": name,
            "id": id,
            "addr": addr
        }
    else:
        _PLAYERS[addr] = {
            "name": name,
            "id": 0
        }

def handle_game_message(addr, data):
    id = _PLAYERS[addr]['id']
    _DATA['spaceships'][id] = data.copy()
    # print(_DATA)

def handle_client_disconnect(addr):
    _PLAYERS.pop(addr)

def handle_client_message(addr, message_obj):
    if message_obj['type'] == HANDSHAKE_MESSAGE:
        handle_handshake(addr, message_obj['name'])
    elif message_obj['type'] == MESSAGE_MESSAGE:
        handle_game_message(addr, message_obj['data'])
    else:
        pass
        # print(message_obj)


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = pickle.loads(conn.recv(msg_length))
            if msg['type'] == DISCONNECT_MESSAGE:
                connected = False
                handle_client_disconnect(addr)
                data_string = pickle.dumps("Disconnected")
            else:
                if(msg['type'] != CONTINUE_MESSAGE):
                    handle_client_message(addr, msg)
            # print(f"[{addr}] {msg}")
                Response = {
                    "id": _PLAYERS[addr]['id'],
                    "data": _DATA,
                    "players": _PLAYERS
                }
                data_string = pickle.dumps(Response)
            conn.send(data_string)
        # print(_DATA)
    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}:{PORT}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
    

if __name__ == '__main__':
    print("[STARTING] server is starting...")
    start()
