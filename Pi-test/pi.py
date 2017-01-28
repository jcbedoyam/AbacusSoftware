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

while 1:
    try:
        out = ''
        while ser.inWaiting() > 0:
            out += ser.read(1)
        if out != '':
            out = out[:-2]
            print ">> %s"%out
        if out[:3] == 'do:':
            command = out[4:]
            try:
                eval(command)
            except:
                print "Error: %s is not valid"%command
        time.sleep(0.1)
    except KeyboardInterrupt:
        ser.close()
        break
