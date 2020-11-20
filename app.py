import asyncio
from timer import RepeatedTimer

def sensor_callback():
    pass

sensor_timer = RepeatedTimer(1,sensor_callback)

async def main():
    print('main')
    sensor_timer.start()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()    
    asyncio.set_event_loop(loop)
    try:        
        loop.create_task(main())
        loop.run_forever()        
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
