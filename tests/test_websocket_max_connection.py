# Standard Library
import asyncio
import functools
import itertools
import os
import time
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed

# Third Party Library
import websockets


async def connect(ws_url: str, close_flag: asyncio.Event):
    try:
        async with websockets.connect(ws_url) as websocket:
            while not close_flag.is_set():
                await websocket.ping()
                await asyncio.sleep(1)
    except websockets.ConnectionClosed as err:
        print(err, "Connection Closed")
        return False
    except KeyboardInterrupt:
        return True
    except asyncio.TimeoutError as err:
        print(err, "Connection Timeout")
        return False
    except BaseException as err:
        print(err)
        return False
    return True


async def max_acceptable_connections(ws_url: str):
    over = asyncio.Event()
    tasks = []
    while not over.is_set():
        print("Connecting... {}".format(len(tasks)))
        task = asyncio.create_task(connect(ws_url, over))
        task.add_done_callback(lambda f: not f.result() and over.set())
        tasks.append(task)
        await asyncio.sleep(0.001)
    await asyncio.wait(tasks)
    print(len(list(filter(lambda t: t.result() is True, tasks))))


async def make_connection(ws_url: str, throughput: int = 100):
    print("当前进程:{} 开始尝试连接".format(os.getpid()))
    summary = "当前进程: {}, 连接数: {}/{}"
    tasks = [asyncio.create_task(connect(ws_url)) for i in range(throughput)]
    await asyncio.wait(tasks)
    connected = list(filter(lambda t: t.result() is True, tasks))
    print(summary.format(os.getpid(), len(connected), throughput))
    return True


def process_compatible_make_connection(ws_url: str, throughput: int = 100):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_connection(ws_url, throughput))
    return True


def main():
    ws_url = "wss://127.0.0.1:8000/websocket/"
    asyncio.run(max_acceptable_connections(ws_url))


if __name__ == "__main__":
    main()
