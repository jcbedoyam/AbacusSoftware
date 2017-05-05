import numpy as np
import serial
from time import sleep

class serialPort():
    BAUDRATE = 115200
    TIMEOUT = 0.02
    BOUNCE_TIMEOUT = 20
    def __init__(self, port, parent=None):
        self.parent = parent
        self.port = port
        self.serial = None
        if self.port != '':
            self.serial = serial.Serial(port=port, baudrate=self.BAUDRATE, parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS, timeout=self.TIMEOUT)

    def close(self):
        self.serial.close()

    def message(self, info, read = False, receive = False):
        def sender():
            if type(info) is list:
                if not read:
                    value = "%04X"%info[2]
                    msb = int(value[:2], 16)
                    lsb = int(value[2:], 16)
                    encoded = [0x02, info[0], info[1], msb, lsb, 0x04]
                else:
                    value = "%04X"%sum(info[1:])
                    check = value[-2:]
                    check = 0xff - int(check, 16)
                    encoded = [0x7E] + info + [check]

                encoded = serial.to_bytes(encoded)
            else:
                encoded = info.encode()
            self.serial.write(encoded)
        def receiver():
            hexa = [codecs.encode(self.serial.read(1), "hex_codec").decode()]
            ints = []
            if hexa[0] == '':
                raise Exception('Timeout: device does not answer.')
            if hexa[0] == '7e':
                while True:
                    byte = codecs.encode(self.serial.read(1), "hex_codec").decode()
                    if byte == '':
                        break
                    hexa.append(byte)
                    ints.append(int(byte, 16))
                check = int(("%02X"%sum(ints[1:-1]))[-2:], 16) + ints[-1]
                if check == 0xff:
                    hexa = hexa[2:-1]
                    ans = []
                    for i in range(int(len(hexa)/3)):
                        channel = int(hexa[3*i], 16)
                        print(channel)
                        value = hexa[3*i+1] + hexa[3*i+2]
                        ans.append([channel, value])
                    return ans
        sender()
        if receive:
            n = 0
            while n < self.BOUNCE_TIMEOUT:
                try:
                    return receiver()
                except Exception as e:
                    n += 1
                    sender()
                    if n < self.BOUNCE_TIMEOUT:
                        continue
                    raise Exception(e)
        else:
            return None

ser = serialPort('/dev/ttyAMA0')
INFORMATION = np.zeros(30, dtype=object)
for i in range(30):
    INFORMATION[i] = "%04X"%0

print("Waiting...")

while 1:
    try:
        out = ser.serial.read(6).encode('hex')
        output = ' '.join(map(lambda x:x.encode('hex'), out))
        if out != '':
            for i in range(3):
                value = "%08X"%np.random.randint(100)
                INFORMATION[24+2*i] = value[4:]
                INFORMATION[25+2*i] = value[:4]
            out = map(''.join, zip(*[iter(out)]*2))
            print(">>> %s"%out)
            if len(out) >= 6:
                address = int(out[2], 16)
                if int(out[1], 16) == 0x0E:
                    additional_channels = int("%s%s"%(out[3], out[4]), 16)
                    number_of_channels = additional_channels
                    if additional_channels == 0:
                        number_of_channels = 1
                    
                    n_bytes = 3*number_of_channels
                    send = [n_bytes]

                    for i in range(number_of_channels):
                        value = INFORMATION[i + address]
                        send += [i + address] + [int(value[2*j:2*j+2], 16) for j in range(2)]
                    ser.message(send, read=True)
                elif int(out[1], 16) == 0x0f:
                    INFORMATION[address] = out[3] + out[4]
                    #pass
        sleep(0.00001)
    except KeyboardInterrupt:
        ser.close()
        break
