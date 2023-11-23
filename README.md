# Message

A general message notification system

## Features

1. websocket/email providers support
2. pure async/await implement with Sanic
3. extensible, only need add providers
4. scalable

## Dependencies

- MongoDB
- RabbitMQ
- Redis

## System Design
![design](docs/design.svg)

1. Server
    recv message, publish message task
2. Planner
    schedule message tasks
3. Executor
    send messages and recv messages

## Development

```shell
docker compose up
```

### Run server/executor/planner in message container
```shell
# start server
make server 
# start executor
make executor
# start planner
make planner
```
