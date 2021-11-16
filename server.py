import time
import os.path
import asyncio
import logging
import argparse
from collections import deque

import websockets
from ansi2html import Ansi2HTMLConverter

NUM_LINES = 10
HEARTBEAT_INTERVAL = 15

conv = Ansi2HTMLConverter(inline=True)

async def view_log(websocket, path):
    try:
        file_path='log.log'
        tail=True

        i=0
        with open(file_path) as f:
            content = ''.join(deque(f, NUM_LINES))
            content = conv.convert(content, full=False)
            await websocket.send(content)

            if tail:
                last_heartbeat = time.time()
                while True:
                    content = f.read()
                    if content:
                        i+=1
                        content = conv.convert(content, full=False)
                        await websocket.send(content)
                    else:
                        await asyncio.sleep(1)

                    # heartbeat
                    #print(last_heartbeat)
                    if time.time() - last_heartbeat > HEARTBEAT_INTERVAL:
                        try:
                            await websocket.send('ping')
                            pong = await asyncio.wait_for(websocket.recv(), 5)
                            if pong != 'pong':
                                raise Exception()
                        except Exception:
                            raise Exception('Ping error')
                        else:
                            last_heartbeat = time.time()

            else:
                await websocket.close()

    except ValueError as e:
        try:
            await websocket.send(e)
            await websocket.close()
        except Exception:
            pass

        log_close(websocket, path, e)

    except Exception as e:
        log_close(websocket, path, e)

    else:
        log_close(websocket, path)


def log_close(websocket, path, exception=None):
    message = 'Closed, remote={}, path={}'.format(websocket.remote_address, path)
    if exception is not None:
        message += ', exception={}'.format(exception)
    logging.info(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()

    start_server = websockets.serve(view_log, args.host, args.port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
