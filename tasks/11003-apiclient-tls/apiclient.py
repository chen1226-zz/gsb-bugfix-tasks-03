"""调用外部 HTTPS 服务的客户端。

对外接口（不得更改签名）：
    make_context(cafile=None) -> ssl.SSLContext
    ApiClient(base_url, cafile=None, timeout=5.0)
        .get(path) -> bytes
"""

import ssl
import urllib.request


def make_context(cafile=None):
    context = ssl.create_default_context(cafile=cafile)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


class ApiClient:
    def __init__(self, base_url, cafile=None, timeout=5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.context = make_context(cafile)

    def get(self, path):
        url = f"{self.base_url}{path}"
        with urllib.request.urlopen(url, context=self.context, timeout=self.timeout) as resp:
            return resp.read()
