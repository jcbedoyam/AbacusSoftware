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
                ser.write("Done\r\n")
                exec(command)
            except Exception as e:
                out = e
                print "Error: %s is not valid"%command
                ser.write("Error: %s\r\n"%out)
        else:
            ser.write("Ok\r\n")
        time.sleep(0.01)
    except KeyboardInterrupt:
        ser.close()
        break
