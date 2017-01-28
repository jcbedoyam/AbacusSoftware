import time
import serial

ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)

ser.isOpen()

print "Waiting..."

while 1:
    try:
        out = ser.readline()
        if out != '':
            out = out[:-2]
            print ">> %s"%out
        if out[:3] == 'do:':
            command = out[4:]
            try:
                exec(command)
            except:
                print "Error: %s is not valid"%command
        time.sleep(0.1)
    except KeyboardInterrupt:
        ser.close()
        break
