from UltimakerPrinter import Printer
import time

printer = Printer('3Ex')

HSV = [0, 100, 100]
while True:
    # set LED 
    printer.setPrinterLED(HSV)
    # get LED 
    print(printer.getPrinterLED())

    # change color
    HSV[0] = (HSV[0] + 10) % 360

    time.sleep(0.001)