import queue
import time
import threading
import signal
import json
import sys
from worker import worker

worker_queue = queue.Queue()
is_app_running = True
worker_queue_lock = threading.Lock()
threads = []
max_threads = 5
# request_locking = threading.Lock()
request_locking = None

def signal_handler(sig, frame):
    global is_app_running
    is_app_running = False

def thread_wait_and_pushback(wait_time, cline):
    global is_app_running, worker_queue, worker_queue_lock
    sleeped_time = 0
    while is_app_running and sleeped_time < wait_time:
        time.sleep(1)
        sleeped_time = sleeped_time + 1
    with worker_queue_lock:
        worker_queue.put(cline)
    return

def schedule_new_iteration(wait_time, cline):
    t = threading.Thread(target=thread_wait_and_pushback, args=(wait_time, cline))
    t.start()

def load_config():
    with open("config.json") as f:
        data = f.read()
        try:
            config = json.loads(data)
            return config
        except Exception as e:
            print("The config.json is wrong")
    return None

def initialized_app():
    global threads, worker_queue, request_locking, max_threads
    config = load_config()
    if config == None:
        print("Exit")
        sys.exit(1)

    for c in config:
        worker_queue.put(c)

    for i in range(0, max_threads):
        t = worker(worker_queue, schedule_new_iteration, request_locking)
        threads.append(t)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    initialized_app()
    for t in threads:
        t.start()
        time.sleep(1)
    while is_app_running:
        time.sleep(1)
    
    for t in threads:
        t.stop()
        # t.join()