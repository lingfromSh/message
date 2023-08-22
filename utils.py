import asyncio
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from sanic import Sanic


def get_app():
    return Sanic.get_app()


class CallResult:
    result = None
    exception = None


def async_to_sync(co_func):
    def wrapper():
        return asyncio.run(co_func())

    def do():
        executor = ThreadPoolExecutor()
        fut = executor.submit(wrapper)

        ret = []
        for f in as_completed(fut):
            ret.append(f.result())
        executor.shutdown()
        return ret[0]

    return do
