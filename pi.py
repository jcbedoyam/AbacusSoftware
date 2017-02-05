from core import *
import numpy as np

ser = serialPort('/dev/ttyAMA0')

print("Waiting...")

while 1:
    try:
        out = ser.serial.read(6).encode('hex')
#        output = ' '.join(map(lambda x:x.encode('hex'), out))
        if out != '':
            out = map(''.join, zip(*[iter(out)]*2))
            print(">>> %s"%out)
            if int(out[1], 16) == 0x0E:
                address = int(out[2], 16)
                msb = int(out[3], 16)
                lsb = int(out[4], 16)
                if  msb + lsb == 0:
                    stop = max(ADDRESS.values())
                    n_bytes = 5*(stop-address)
                    send = [n_bytes]
                    for i in range(address, stop+1):
                        value = np.random.randint(200e6)
                        print("%d %d"%(i, value))
                        value = "%08X"%value
                        send += [i] + [int(value[2*j:2*j+2], 16) for j in range(4)]
                    ser.message(send, read=True)
        time.sleep(0.01)
    except KeyboardInterrupt:
        ser.close()
        break
