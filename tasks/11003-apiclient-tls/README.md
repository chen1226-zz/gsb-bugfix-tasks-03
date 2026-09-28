# 11003 · HTTPS 客户端证书校验（apiclient）

接口：`make_context(cafile)` / `ApiClient(base_url, cafile, timeout).get(path)`。

| 文件 | 说明 |
| --- | --- |
| `apiclient.py` | 待修复的模块 |
| `tls_server.py` | 本机 HTTPS 服务端（可指定任意证书） |
| `certs/` | 预先用 openssl 生成好的测试证书（含 CA、正常、自签、域名不匹配、已过期） |
| `certs/make_certs.sh` | 证书生成脚本（一次性，产物已提交） |
| `repro_tls.py` | 复现脚本：好证书必须成功，坏证书必须失败 |
| `tests/test_apiclient.py` | unittest 用例 |

## 已知现象

安全扫描报告：客户端不校验证书（代码里把 ssl 上下文设成不校验，且自定义校验回调
恒通过），中间人可解密并篡改流量。

## 运行

```
python3 repro_tls.py
python3 -m unittest tests/test_apiclient.py -v
```
