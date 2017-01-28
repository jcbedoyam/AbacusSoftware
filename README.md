# reimagined-quantum
## Models

[1](http://www.waveshare.com/ft232-usb-uart-board-type-a.htm)

[2](http://www.robotshop.com/en/cytron-usb-uart-converter.html)

## Python
### Serial
[1](http://www.varesano.net/blog/fabio/serial%20rs232%20connections%20python)

[2](https://electrosome.com/uart-raspberry-pi-python/)

[3](https://www.raspberrypi.org/forums/viewtopic.php?f=44&t=41055)

[4](http://stackoverflow.com/questions/676172/full-examples-of-using-pyserial-package)

```
Step 1 - Install Raspbian Jessie onto a SD card and boot the Pi when connected to a network Login via terminal or desktop and shell Configure the system with:

sudo raspi-config

Expand filesystem and enable serial on advanced page, exit and reboot.

Step 2 -this won't necessary if you have jessie new release Update the system with:

sudo apt-get update

sudo apt-get upgrade

Step 3 - Device Tree settings as below:

Add device tree to /boot/config.txt to disable the Raspberry Pi 3 bluetooth.

sudo nano /boot/config.txt

Add at the end of the file

*if you want to change the blutooth to miniuart port(bad)

dtoverlay=pi3-miniuart-bt

*if you want to disable the blutooth(good)

dtoverlay=pi3-disable-bt

Exit the editor saving your changes.

Step 4 - reboot the pi

sudo reboot

step 5 -

a)to disable the Serial Console edit the file using

sudo nano /boot/cmdline.txt

remove the word phase "console=serial0,115200" or "console=ttyAMA0,115200"

Exit and save your changes

b)to Enable the Serial Console edit the file using

sudo nano /boot/cmdline.txt

Change the file to the following:

dwc_otg.lpm_enable=0 console=tty1 console=serial0(or ttyAMA0),115200 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait

Exit and save your changes

Step 6 - reboot the pi

sudo reboot
```

### GUI
### Binaries
MS Visual C++ dll
