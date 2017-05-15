import psutil
from time import time, strftime, localtime, sleep

file_name = 'ram.dat'
init_time = time()
MB = 1024**2
while True:
    try:
        time_ = time() - init_time
        current_time = strftime("%H:%M:%S", localtime())
        memory = psutil.virtual_memory().used/MB
        data = "%.3f %s %d\n"%(time_, current_time, memory)
        with open(file_name, 'a') as file:
            file.write(data)
        sleep(1)
    except KeyboardInterrupt:
        break
