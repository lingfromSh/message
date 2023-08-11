import orjson
from sanic.log import logger

from apps.endpoint.models import Endpoint


async def register_websocket_endpoint(connection_id, data):
    try:
        data = orjson.loads(data)
    except orjson.JSONDecodeError:
        return

    if not isinstance(data, dict):
        return

    if "user_id" not in data:
        return

    external_id = data["user_id"]

    try:
        endpoint = await Endpoint.find_one({"external_id": external_id})
        endpoint.websockets.append(connection_id)
    except Exception:
        endpoint = Endpoint(external_id=external_id, websockets=[connection_id])

    await endpoint.commit()

    logger.info(f"register websocket connection: {connection_id} -> {external_id}")
