import threading
import subprocess
import multiprocessing
import matplotlib.pyplot as plt
import random
import time
import os

N_ACCOUNTS = 120
INIT_BALANCE = 100
def init():
    global accounts, locks
    accounts = {i: INIT_BALANCE for i in range(N_ACCOUNTS)}
    locks = {i: threading.Lock() for i in range(N_ACCOUNTS)}

def total():
    return sum(accounts.values())

#SEQUENTIAL
def transfer_seq(a, b, amount):
    if accounts[a] >= amount:
        accounts[a] -= amount
        accounts[b] += amount

def run_sequential():
    init()
    start = time.perf_counter()

    for _ in range(5000):
        a, b = random.sample(range(N_ACCOUNTS), 2)
        transfer_seq(a, b, 5)

    t = time.perf_counter() - start

    print("\nSEQUENTIAL")
    print("Time:", round(t, 4))
    print("Total:", total())

    return t  

#RACE CONDITION (BROKEN)
def transfer_race(a, b, amount):
    tmp = accounts[a]
    time.sleep(0.000001)
    accounts[a] = tmp - amount
    accounts[b] += amount

def worker_race():
    for _ in range(2000):
        a, b = random.sample(range(N_ACCOUNTS), 2)
        transfer_race(a, b, random.randint(1, 10))

def run_race():
    init()
    start = time.perf_counter()

    threads = []
    for _ in range(500):
        t = threading.Thread(target=worker_race)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    t = time.perf_counter() - start
    print("\nRACE CONDITION (BROKEN)")
    print("Time:", round(t, 4))
    print("Total:", total())
    return t

def transfer_safe(a, b, amount):
    x, y = sorted([a, b])
    with locks[x]:
        with locks[y]:
            if accounts[a] >= amount:
                accounts[a] -= amount
                accounts[b] += amount

def worker_safe():
    for _ in range(2000):
        a, b = random.sample(range(N_ACCOUNTS), 2)
        transfer_safe(a, b, random.randint(1, 10))

def run_safe():
    init()
    start = time.perf_counter()

    threads = []
    for _ in range(500):
        t = threading.Thread(target=worker_safe)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    t = time.perf_counter() - start
    print("\nSAFE VERSION")
    print("Time:", round(t, 4))
    print("Total:", total())
    return t

#DEADLOCK SIMULATION
log = []

def transfer_deadlock_sim(a, b):
    if not locks[a].acquire(timeout=0.01):
        log.append("fail A")
        return

    time.sleep(0.001)

    if not locks[b].acquire(timeout=0.01):
        locks[a].release()
        log.append(f"deadlock avoided {a}-{b}")
        return

    log.append(f"ok {a}->{b}")
    locks[b].release()
    locks[a].release()

def worker_deadlock():
    for _ in range(1000):
        a, b = random.sample(range(N_ACCOUNTS), 2)
        transfer_deadlock_sim(a, b)

def run_deadlock():
    init()
    start = time.perf_counter()

    threads = []
    for _ in range(300):
        t = threading.Thread(target=worker_deadlock)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    t = time.perf_counter() - start
    print("\nDEADLOCK SIMULATION")
    print("Time:", round(t, 4))
    print("Total:", total())
    return t

#MESSAGE PASSING
def worker_queue(q):
    while True:
        x = q.get()
        if x is None:
            break
        q.put(x * 2)

def run_queue():
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=worker_queue, args=(q,))
    p.start()

    start = time.perf_counter()

    for i in range(10):
        q.put(i + 1)

    time.sleep(1)
    q.put(None)
    p.join()

    t = time.perf_counter() - start
    print("\nQUEUE:", round(t, 4))
    return t

def worker_pipe(conn):
    while True:
        x = conn.recv()
        if x == -1:
            break
        conn.send(x * 3)

def run_pipe():
    parent, child = multiprocessing.Pipe()
    p = multiprocessing.Process(target=worker_pipe, args=(child,))
    p.start()

    start = time.perf_counter()

    for i in range(10):
        parent.send(i + 1)
        parent.recv()

    parent.send(-1)
    p.join()

    t = time.perf_counter() - start
    print("\nPIPE:", round(t, 4))
    return t

def worker_shared(val, lock):
    for _ in range(5):
        with lock:
            val.value *= 2
        time.sleep(0.01)

def run_shared():
    val = multiprocessing.Value('i', 1)
    lock = multiprocessing.Lock()

    p = multiprocessing.Process(target=worker_shared, args=(val, lock))
    p.start()

    start = time.perf_counter()

    for _ in range(5):
        with lock:
            val.value += 1

    p.join()

    t = time.perf_counter() - start
    print("\nSHARED:", round(t, 4))
    print("Value:", val.value)
    return t, val.value

#с++
def run_cpp_process():
    print("\nC++ PROCESS (Cross-language IPC)")

    proc = subprocess.Popen(
        ["./worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    start = time.perf_counter()

    for _ in range(10):
        num = random.randint(1, 100)

        proc.stdin.write(f"{num}\n")
        proc.stdin.flush()

        result = proc.stdout.readline().strip()

        if not result:
            continue

        print(f"Sent: {num}, Received: {result}")

        time.sleep(0.01)

    proc.stdin.write("exit\n")
    proc.stdin.flush()

    proc.wait()

    t = time.perf_counter() - start
    print("C++ Time:", round(t, 4))
    return t

#BENCHMARK THREAD SCALING
def benchmark_threads():
    labels = []
    times = []

    for n in [100, 300, 500]:
        init()
        start = time.perf_counter()

        threads = []
        for _ in range(n):
            t = threading.Thread(target=worker_safe)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        labels.append(n)
        times.append(time.perf_counter() - start)

    return labels, times

#main 
if __name__ == "__main__":
    os.makedirs("plots", exist_ok=True)
    print("INITIAL:", N_ACCOUNTS * INIT_BALANCE)

    seq = run_sequential()
    race = run_race() 
    safe = run_safe()
    dead = run_deadlock()

    q = run_queue()
    p = run_pipe()
    sh, val = run_shared()
    cpp_time = run_cpp_process()

    labels, thread_times = benchmark_threads()
    
    print("DEBUG VALUES:")
    print("seq =", seq)
    print("race =", race)
    print("safe =", safe)
    print("dead =", dead)
    
    #1`
    plt.figure()
    plt.bar(["Seq", "Race", "Safe", "Deadlock"], [seq, race, safe, dead])
    plt.yscale("log")
    plt.title("Execution Comparison")
    plt.savefig("plots/01_execution.png")
    plt.show()

    #2
    plt.figure()
    plt.bar(["Race", "Safe"], [race, safe])
    plt.title("Race vs Safe")
    plt.savefig("plots/02_race_safe.png")
    plt.show()

    #3
    plt.figure()
    plt.bar(["Queue", "Pipe", "Shared", "C++ IPC"], [q, p, sh, cpp_time])
    plt.title("Message Passing")
    plt.savefig("plots/03_messaging.png")
    plt.show()

    #4
    plt.plot(labels, thread_times, marker='o')
    plt.title("Thread Scaling")
    plt.xlabel("Threads")
    plt.ylabel("Time")
    plt.savefig("plots/04_scaling.png")
    plt.show()

    #5
    plt.figure()
    plt.bar(["Seq", "Parallel Safe"], [seq, safe])
    plt.yscale("log")
    plt.title("Overhead Comparison")
    plt.savefig("plots/05_overhead.png")
    plt.show()