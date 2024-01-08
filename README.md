# Message

> I want to provider a general message notification system, which can be used in any project.

A general message notification system

## Features

1. pure async/await implement with FastAPI
2. extensible, only need add providers
3. scalable

## Dependencies

- PostgresQL
- RabbitMQ
- Redis

## Framework

- fastapi
- tortoise-orm
- pydantic
- taskiq
- apprise (support tons of notification services) amazing lib

## Development

```shell
make dev
```
