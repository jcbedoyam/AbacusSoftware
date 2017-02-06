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
                    n_bytes = 3*(stop-address)
                    send = [n_bytes]
                    
                    items = int((stop-address)/2)
                    for i in range(items):
                        value = 6*np.random.random()
                        value = int(10**value)
                        
                        value = "%08X"%value
                        send += [2*i + address] + [int(value[2*j:2*j+2], 16) for j in range(2)]
                        send += [2*i+1 + address] + [int(value[2*j:2*j+2], 16) for j in range(2, 4)]
                    print(send)
                    ser.message(send, read=True)
        sleep(0.00001)
    except KeyboardInterrupt:
        ser.close()
        break
