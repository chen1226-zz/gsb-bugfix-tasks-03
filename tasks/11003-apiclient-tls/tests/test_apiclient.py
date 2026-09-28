import os
import ssl
import unittest

from apiclient import ApiClient, make_context
from tls_server import CERT_DIR, TLSServer

CA = os.path.join(CERT_DIR, "ca.pem")


class TestApiClient(unittest.TestCase):
    def test_client_builds_tls_context(self):
        """既有断言：客户端持有一个可用的 SSLContext。"""
        client = ApiClient("https://127.0.0.1:1", cafile=CA)
        self.assertIsInstance(client.context, ssl.SSLContext)
        self.assertIsInstance(make_context(CA), ssl.SSLContext)

    def test_good_cert_request_succeeds(self):
        """既有断言：受信任的证书可以请求成功。"""
        server = TLSServer("server.pem", "server.key").start()
        try:
            client = ApiClient(f"https://127.0.0.1:{server.port}", cafile=CA)
            self.assertEqual(client.get("/"), b"ok")
        finally:
            server.stop()

    def test_reads_body_over_tls(self):
        """既有断言：返回体通过 TLS 正常读取。"""
        server = TLSServer("server.pem", "server.key").start()
        try:
            client = ApiClient(f"https://127.0.0.1:{server.port}", cafile=CA)
            self.assertEqual(len(client.get("/")), 2)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
