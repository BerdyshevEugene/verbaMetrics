import asyncio

from fastapi import FastAPI
from rabbitmq.connection import connect_to_rabbitmq
from logger.logger import setup_logger

setup_logger()
app = FastAPI()


@app.on_event('startup')
async def startup_event():
    asyncio.create_task(connect_to_rabbitmq())


@app.on_event('shutdown')
async def shutdown_event():
    pass

# если запускается напрямую
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=7999)
