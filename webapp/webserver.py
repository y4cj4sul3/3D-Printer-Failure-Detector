'''
Improper Temperary Local Web Server for Visualization
'''

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json

printer_info = {}


class Handler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # routing
        if self.path.startswith('/get_printer_info'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(printer_info).encode('utf-8'))

        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(open('index.html', 'rb').read())

        elif self.path.endswith(('.html', '.js')):
            self.send_response(200)
            self.send_header('Content-type', 'text/' + self.path.split('.')[-1])
            self.end_headers()
            self.wfile.write(open(self.path[1:], 'rb').read())

        elif self.path.endswith('.png'):
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            print(self.path)
            self.wfile.write(open('..' + self.path, 'rb').read())

        else:
            self.pageNotFound()

    def do_POST(self):
        if self.path == '/printer_info':
            data = self.rfile.read(int(self.headers['Content-Length']))
            data_json = json.loads(data.decode('utf-8'))
            print(data_json)
            # store data
            printer_info[data_json['printer_name']] = data_json

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        else:
            self.pageNotFound()

    def pageNotFound(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


def run(server_class=HTTPServer, handler_class=Handler, addr='localhost', port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print('Serving on {}:{}'.format(addr, port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=8000)
    args = parser.parse_args()

    run(port=args.port)
