from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(app):
    from crypto.tasks import check_blockchain_deposits
    print("Lifespan startup")
    # Запускаем задачу в фоне
    task = asyncio.create_task(check_blockchain_deposits())
    yield
    #Действия при завершении работы
    print("Lifespan shutdown")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Task cancelled successfully")
