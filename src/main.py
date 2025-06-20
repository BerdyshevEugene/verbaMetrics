import asyncio

from fastapi import FastAPI
from rabbitmq.connection import connect_to_rabbitmq
from logger.logger import setup_logger

setup_logger()
app = FastAPI()

rabbitmq_task = None  # глобальная переменная для хранения задачи


@app.on_event("startup")
async def startup_event():
    global rabbitmq_task
    rabbitmq_task = asyncio.create_task(connect_to_rabbitmq())


@app.on_event("shutdown")
async def shutdown_event():
    global rabbitmq_task
    if rabbitmq_task:
        rabbitmq_task.cancel()
        try:
            await rabbitmq_task
        except asyncio.CancelledError:
            pass


# если запускается напрямую
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7999)
