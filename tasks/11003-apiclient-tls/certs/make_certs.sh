#!/usr/bin/env bash
# 生成测试用的证书（一次性运行，产物已提交到仓库）。
set -e
cd "$(dirname "$0")"

openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout ca.key -out ca.pem -subj "/CN=GSB Test CA" >/dev/null 2>&1

# 正常服务端证书：SAN 指向 127.0.0.1，由 CA 签发
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr \
  -subj "/CN=127.0.0.1" >/dev/null 2>&1
printf 'subjectAltName=IP:127.0.0.1\nbasicConstraints=CA:FALSE\n' > san.cnf
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out server.pem -days 3650 -extfile san.cnf >/dev/null 2>&1

# 自签证书：不在信任链里
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -keyout selfsigned.key \
  -out selfsigned.pem -subj "/CN=127.0.0.1" \
  -addext "subjectAltName=IP:127.0.0.1" >/dev/null 2>&1

# 域名不匹配：由 CA 签发，但 SAN 是 example.com
openssl req -newkey rsa:2048 -nodes -keyout wronghost.key -out wronghost.csr \
  -subj "/CN=example.com" >/dev/null 2>&1
printf 'subjectAltName=DNS:example.com\nbasicConstraints=CA:FALSE\n' > san2.cnf
openssl x509 -req -in wronghost.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
  -out wronghost.pem -days 3650 -extfile san2.cnf >/dev/null 2>&1

# 已过期：用 openssl ca 指定过去的时间窗
cat > ca.cnf <<'EOF'
[ca]
default_ca = CA_default
[CA_default]
dir = .
database = index.txt
serial = serial.txt
new_certs_dir = newcerts
certificate = ca.pem
private_key = ca.key
default_md = sha256
policy = policy_any
email_in_dn = no
rand_serial = no
unique_subject = no
[policy_any]
commonName = supplied
EOF
: > index.txt
mkdir -p newcerts
echo 1000 > serial.txt
openssl ca -batch -config ca.cnf -in server.csr -out expired.pem \
  -startdate 20200101000000Z -enddate 20200102000000Z \
  -extfile san.cnf >/dev/null 2>&1

rm -f server.csr wronghost.csr san.cnf san2.cnf ca.srl index.txt* serial.txt* \
      ca.cnf newcerts/* 2>/dev/null || true
rmdir newcerts 2>/dev/null || true
ls -1 *.pem *.key
