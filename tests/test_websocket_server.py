# Third Party Library
import websockets
from websockets.sync.server import serve


def handler(websocket):
    for message in websocket:
        print(message)


def main():
    with serve(handler, "0.0.0.0", 8000, max_size=128 * 20) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
