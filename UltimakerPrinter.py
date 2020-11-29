import requests
from requests.auth import HTTPDigestAuth
import configparser

class Printer:
    def __init__(self, printer_name):
        config = configparser.ConfigParser()
        config.read('ultimaker.ini')

        # printer
        self.printerName = 'ultimaker.' + printer_name
        self.printerIP = config[self.printerName]['printer_ip']
        self.printerURL = 'http://'+ self.printerIP + '/api/v1/'
        # user 
        self.userID = config[self.printerName]['id']
        self.userKey = config[self.printerName]['key']
        
        # HTTP session
        self.session = requests.Session()
        self.session.auth = HTTPDigestAuth(self.userID, self.userKey)

        # check whether printer exists in config file
        if self.printerIP is None:
            print('Error: no such printer')

        # check user is authorized or not
        if not self.authVerify():
            print('Error: user not authorized')

    # Authentication
    def authVerify(self):
        r = self.getRequest('auth/verify')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.json()['message'] == 'ok'

    # Printer
    def getPrinterState(self):
        r = self.getRequest('printer/status')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.json()
    
    def getPrinterLED(self):
        r = self.getRequest('printer/led')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            msg = r.json()
            return [msg['hue'], msg['saturation'], msg['brightness']]
    
    def setPrinterLED(self, HSV):
        payload = {
            "hue": HSV[0],
            "saturation": HSV[1],
            "brightness": HSV[2]
        }
        r = self.putRequest('printer/led', json=payload)
        if r.status_code != 204:
            print(r.text)

    # PrintJob
    def getPrintJob(self):
        r = self.getRequest('print_job')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.json()

    def getPrintJobName(self):
        r = self.getRequest('print_job/name')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.json()

    def getPrintJobProgress(self):
        r = self.getRequest('print_job/progress')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.json()

    def getPrintJobGcode(self):
        r = self.getRequest('print_job/gcode')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.text

    def getPrintJobState(self):
        r = self.getRequest('print_job/state')
        if r.status_code != 200:
            print(r.json())
            return None
        else:
            return r.json()

    # Camera
    def getCameraSnapshot(self, index=0):
        # old fashion: suitable for all printer
        r = self.session.get('http://{}:{}/?action=snapshot'.format(self.printerIP, 8080+index), stream=True)
        # API: not suitable for 3, 3E
        # r = self.getRequest('camera/{}/snapshot'.format(index), stream=True)
        if r.status_code != 200:
            print(r.text)
            return None
        else:
            return r.raw

    def getCameraSnapshotOld(self, index=0):
        r = self.session.get('http://{}:{}/?action=snapshot'.format(self.printerIP, 8080+index), stream=True)
        if r.status_code != 200:
            print(r.text)
            return None
        else:
            return r.raw
        
    # HTTP Requests
    def getRequest(self, method, **kargs):
        r = self.session.get(self.printerURL + method, **kargs)
        return r

    def putRequest(self, method, **kargs):
        r = self.session.put(self.printerURL + method, **kargs)
        return r


if __name__ == '__main__':
    
    import shutil

    printer = Printer('3Ex')

    print(printer.getPrintJobState())

    printer.setPrinterLED([0, 0, 100])
    print(printer.getPrintJobProgress())

    img = printer.getCameraSnapshotOld()
    if img is None:
        print('oh no')
    
    with open('data/image.png', 'wb') as fp:
        shutil.copyfileobj(img, fp)