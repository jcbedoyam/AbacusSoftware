import serial

ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
)

ser.isOpen()

print('Enter your commands below.\r\nInsert "exit" to leave the application.')

while 1 :
    text = input(">> ")
    if text == 'exit':
        ser.close()
        exit()
    else:
        text = text.encode()
        ser.write(text + b'\r\n')
