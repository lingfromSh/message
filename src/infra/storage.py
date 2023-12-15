# Standard Library
import io
import os
import typing
from asyncio.queues import Queue
from asyncio.queues import QueueEmpty
from collections import OrderedDict

# Third Party Library
import aiofiles

# First Library
from infra.abc import Infrastructure


class StorageFile:
    def __init__(self, name: str, *, storage: "StorageInfrastructure"):
        self._name = name
        self._storage = storage
        self._content: typing.Optional[bytes] = None
        self._wait_to_write = Queue()

    def __str__(self) -> str:
        return self.name

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._storage.get_size(self._name)

    @property
    def path(self):
        return self._storage.get_path(self._name)

    async def delete(self):
        self._wait_to_write = Queue()
        self._content = None
        await self._storage.delete(self._name)

    async def read(self) -> bytes:
        if self._content is None:
            self._content = await self._storage._get(self._name)
        return self._content

    async def write(self, content: typing.Union[str, bytes, io.IOBase]):
        await self._wait_to_write.put(content)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            del self._wait_to_write
            self._wait_to_write = Queue()

        if self._content is None:
            self._content = b""

        for _ in range(self._wait_to_write.qsize()):
            try:
                b = await self._wait_to_write.get()
                if isinstance(b, io.IOBase):
                    self._content += await b.read()
                elif isinstance(b, bytes):
                    self._content += b
            except QueueEmpty:
                break

        if self._content:
            await self._storage._write(self._name, self._content)

        return


class Backend:
    __registries__ = OrderedDict()

    def __init__(self, override: bool = True):
        self.override = override

    def __init_subclass__(cls, mode: typing.AnyStr) -> None:
        assert (
            mode not in Backend.__registries__
        ), f"Backend with mode {mode} already registered"
        Backend.__registries__[mode] = cls

    @classmethod
    def from_mode(cls, mode: typing.AnyStr, **kwargs) -> "Backend":
        assert (
            mode in Backend.__registries__
        ), f"Backend with mode {mode} not registered"
        return Backend.__registries__[mode](**kwargs)

    def get_size(self, name: str) -> int:
        raise NotImplementedError

    def get_path(self, name: str) -> str:
        raise NotImplementedError

    async def get(self, name: str) -> bytes:
        raise NotImplementedError

    async def put(self, name: str, content: bytes) -> bool:
        raise NotImplementedError

    async def delete(self, *names: typing.List[str]) -> bool:
        raise NotImplementedError


class LocalFileSystemBackend(Backend, mode="local"):
    def __init__(self, **kwargs):
        self.root = kwargs.pop("root", os.path.abspath(os.path.dirname(__file__)))
        super().__init__(**kwargs)

    def _path(self, name: str) -> str:
        return os.path.join(self.root, name)

    def get_path(self, name: str) -> str:
        return self._path(name)

    def get_size(self, name: str) -> int:
        return os.path.getsize(self._path(name))

    async def get(self, name: str) -> typing.Optional[bytes]:
        content = None
        async with aiofiles.open(self._path(name), "rb") as fp:
            content = await fp.read()
        return content

    async def put(self, name: str, content: bytes) -> bool:
        if os.path.exists(self._path(name)) and not self.override:
            raise FileExistsError("file already exists, but override is False")

        async with aiofiles.open(self._path(name), "wb+") as f:
            await f.write(content)

        return True

    async def delete(self, *names: typing.List[str]) -> bool:
        for path in map(self._path, names):
            if not os.path.exists(path):
                continue
            if not os.path.isfile(path):
                continue
            os.remove(path)
        return True


class StorageInfrastructure(Infrastructure):
    """
    >>> local_storage = StorageInfrastructure(mode="local")
    >>> async with local_storage.open("test.txt") as fp:
    >>>     await fp.write("Hello, world!")
    >>>     await fp.write("Hello, world!")
    >>>     await fp.write("Hello, world!")
    >>> file = local_storage.get("test.txt")
    >>> await file.read()
    b'Hello, world!Hello, world!Hello, world!'
    >>> await local_storage.delete("test.txt")
    """

    def __init__(self, mode: typing.Literal["local"], options: typing.Dict = None):
        options = {} if options is None else options
        self._backend: Backend = Backend.from_mode(mode, **options)

    def open(self, name: str) -> StorageFile:
        return StorageFile(name, storage=self)

    def get_size(self, name: str) -> int:
        return self._backend.get_size(name)

    def get_path(self, name: str) -> str:
        return self._backend.get_path(name)

    async def _get(self, name: str) -> StorageFile:
        return await self._backend.get(name)

    async def _write(self, name: str, content: bytes):
        await self._backend.put(name, content)

    async def delete(self, *names: typing.List[str]) -> None:
        await self._backend.delete(*names)
