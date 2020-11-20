import asyncio
from threading import Timer


async def main():
    print('main')

if __name__ == "__main__":
    loop = asyncio.new_event_loop()    
    asyncio.set_event_loop(loop)
    try:        
        loop.create_task(main())
        loop.run_forever()        
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
