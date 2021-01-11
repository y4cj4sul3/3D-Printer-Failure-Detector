import socket

import requests
from urllib3.exceptions import ReadTimeoutError


class DetectorVisualizerClient:

    def __init__(self, printer_name, ip='localhost', port=8000):

        self.url = 'http://{}:{}/'.format(ip, port)

        self.session = requests.Session()

        self.printer_name = printer_name

        self.printer_info = {
            'printer_name': self.printer_name,
            'printjob_name': None,
            'printer_state': None,
            'printjob_state': None,
            'input_img_path': None,
            'sim_img_path': None,
            'predict_img_path': None,
            'iou_img_path': None,
            'blend_img_path': None,
            'result': None
        }

    def sendPrinterInfo(self, printer_name=None, printer_state=None, printjob_name=None, printjob_state=None, input_img_path=None, sim_img_path=None, predict_img_path=None, iou_img_path=None, blend_img_path=None, result=None):
        self.updatePrinterInfo(printer_name=printer_name, printer_state=printer_state, printjob_name=printjob_name, printjob_state=printjob_state,
                               input_img_path=input_img_path, sim_img_path=sim_img_path, predict_img_path=predict_img_path, iou_img_path=iou_img_path, blend_img_path=blend_img_path, result=result)

        return self.postRequest(self.url + 'printer_info', json=self.printer_info)

    def updatePrinterInfo(self, **kargs):
        for key in self.printer_info:
            if kargs[key] is not None:
                self.printer_info[key] = kargs[key]

    def getPrinterInfo(self):
        return self.getRequest(self.url + 'get_printer_info')

    def getRequest(self, url, timeout=10, **kargs):

        try:
            r = self.session.get(url, timeout=timeout, **kargs)

        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            # handle timeout
            print('Request Timeout: ' + url)
            r = requests.models.Response()
            r.status_code = 408
            r._content = b'{"message": "request timeout"}'

        except (socket.timeout, ReadTimeoutError):
            # handle timeout
            print('Request Timeout (urllib): ' + url)
            r = requests.models.Response()
            r.status_code = 408
            r._content = b'{"message": "request timeout"}'

        return r

    def postRequest(self, url, **kargs):
        r = self.session.post(url, **kargs)
        return r

    def putRequest(self, url, **kargs):
        r = self.session.put(url, **kargs)
        return r


if __name__ == "__main__":
    client = DetectorVisualizerClient('S5')
    r = client.sendPrinterInfo(printer_state='idle')
    r = client.sendPrinterInfo(result="0.1256,0.6371", printjob_name='test')
    r = client.sendPrinterInfo(input_img_path='test.png', sim_img_path='test.png', predict_img_path='test.png', iou_img_path='test.png', blend_img_path='test.png')
    print(r.text)
    r = client.getPrinterInfo()
    print(r.json())
