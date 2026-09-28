"""本机 HTTPS 服务端，用指定证书启动。"""

import http.server
import os
import ssl
import threading

CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        return


class TLSServer:
    def __init__(self, cert_name, key_name):
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            os.path.join(CERT_DIR, cert_name), os.path.join(CERT_DIR, key_name)
        )
        self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
