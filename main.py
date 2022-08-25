from aiogram.utils import executor
    
import asyncio
    
from holders import *
    
from handlers.admin import *
from handlers.user import *
from handlers.seller import *

loop = asyncio.get_event_loop()
loop.create_task(coro=check_holds())

if __name__ == '__main__':
    executor.start_polling(dp, loop=loop)
