"""复现脚本：好证书必须成功，坏证书必须失败。"""

import os
import ssl

from apiclient import ApiClient
from tls_server import CERT_DIR, TLSServer

CA = os.path.join(CERT_DIR, "ca.pem")

CASES = [
    ("正常证书（自定义 CA）", "server.pem", "server.key", CA, True),
    ("自签证书", "selfsigned.pem", "selfsigned.key", CA, False),
    ("域名不匹配", "wronghost.pem", "wronghost.key", CA, False),
    ("已过期", "expired.pem", "server.key", CA, False),
]


def main():
    problems = []
    for label, cert, key, cafile, should_pass in CASES:
        if not os.path.exists(os.path.join(CERT_DIR, cert)):
            problems.append(f"{label}: 证书文件缺失 {cert}")
            continue
        server = TLSServer(cert, key).start()
        try:
            client = ApiClient(f"https://127.0.0.1:{server.port}", cafile=cafile)
            try:
                client.get("/")
                passed = True
                error = ""
            except ssl.SSLError as exc:
                passed = False
                error = f"SSLError: {exc}"
            except Exception as exc:  # noqa: BLE001
                passed = False
                error = f"{type(exc).__name__}: {exc}"
        finally:
            server.stop()

        if passed != should_pass:
            want = "应当成功" if should_pass else "应当被拒绝"
            problems.append(f"{label}: {want}，实际{'成功' if passed else '被拒绝 ' + error}")

    if problems:
        print(f"FAIL: {len(CASES)} cases, {len(problems)} 处不符合预期")
        for item in problems:
            print("  - " + item)
        raise SystemExit(1)
    print(f"OK: {len(CASES)} cases, good cert accepted, bad certs rejected")


if __name__ == "__main__":
    main()
