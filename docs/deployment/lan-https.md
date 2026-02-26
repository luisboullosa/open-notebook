# LAN HTTPS Deployment (Orange Pi/Home Lab)

This guide configures Open Notebook for secure HTTPS access on a local network without exposing ports to the public internet.

Use this when:

- You access Open Notebook from other devices on the same LAN
- You want browser lock/security indicators on local IP access
- You do not want public DNS + Let's Encrypt complexity

## Overview

The LAN HTTPS setup in this repository uses:

- [docker-compose.orangepi.dev.yml](../../docker-compose.orangepi.dev.yml)
- [Caddyfile.lan](../../Caddyfile.lan)
- A local CA and server certificate in `letsencrypt/lan/`

### Exposed endpoints

- `https://<server-ip>` → Open Notebook UI (and `/api`)
- `https://<server-ip>:4444` → Music Partner UI
- `http://<server-ip>:8088/lan-ca.crt` → LAN CA certificate download
- `http://<server-ip>:8088/lan-ca.crl` → CA revocation list (CRL)

## 1) Start services

```bash
docker compose -f docker-compose.orangepi.dev.yml up -d
```

## 2) Generate LAN CA + server certificate (with CRL support)

Run on the Orange Pi inside the repository root:

```bash
mkdir -p letsencrypt/lan
cd letsencrypt/lan

# Create CA
openssl genrsa -out lan-ca.key 4096
openssl req -x509 -new -key lan-ca.key -sha256 -days 3650 \
  -subj '/CN=OpenNotebook LAN Root CA' \
  -addext 'basicConstraints=critical,CA:TRUE,pathlen:1' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign' \
  -addext 'subjectKeyIdentifier=hash' \
  -out lan-ca.crt

# OpenSSL CA config (includes CRL Distribution Point)
cat > openssl-lan.cnf << 'EOF'
[ ca ]
default_ca = CA_default

[ CA_default ]
certificate       = /root/open-notebook/letsencrypt/lan/lan-ca.crt
private_key       = /root/open-notebook/letsencrypt/lan/lan-ca.key
database          = /root/open-notebook/letsencrypt/lan/index.txt
new_certs_dir     = /root/open-notebook/letsencrypt/lan
serial            = /root/open-notebook/letsencrypt/lan/serial
crlnumber         = /root/open-notebook/letsencrypt/lan/crlnumber
default_md        = sha256
policy            = policy_any
x509_extensions   = server_cert
copy_extensions   = copy
default_days      = 825
default_crl_days  = 30

[ policy_any ]
commonName = supplied

[ server_cert ]
basicConstraints=CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
authorityKeyIdentifier=keyid,issuer
subjectKeyIdentifier=hash
crlDistributionPoints=URI:http://192.168.2.129:8088/lan-ca.crl
EOF

[ -f index.txt ] || touch index.txt
[ -f serial ] || echo 1000 > serial
[ -f crlnumber ] || echo 1000 > crlnumber

# Create server cert for LAN IP (update IP if needed)
openssl genrsa -out lan-server.key 2048
openssl req -new -key lan-server.key \
  -subj '/CN=192.168.2.129' \
  -addext 'subjectAltName=IP:192.168.2.129' \
  -out lan-server.csr

openssl ca -batch -config openssl-lan.cnf \
  -in lan-server.csr -out lan-server.crt -notext

# Generate CRL for revocation checking
openssl ca -gencrl -config openssl-lan.cnf -out lan-ca.crl

chmod 600 lan-ca.key lan-server.key
chmod 644 lan-ca.crt lan-server.crt lan-ca.crl
```

Restart Caddy:

```bash
cd /root/open-notebook
docker compose -f docker-compose.orangepi.dev.yml restart caddy
```

## 3) Install LAN CA on client devices

Download CA cert:

`http://<server-ip>:8088/lan-ca.crt`

### Windows

Admin shell:

```powershell
certutil -addstore -f Root .\lan-ca.crt
```

Non-admin fallback (current user store):

```powershell
certutil -user -addstore -f Root .\lan-ca.crt
```

### Android

1. Open `http://<server-ip>:8088/lan-ca.crt`
2. Install as CA certificate in system security settings
3. Ensure lock screen is configured (required by Android)

## 4) Verify fingerprint

On Orange Pi:

```bash
openssl x509 -in letsencrypt/lan/lan-ca.crt -noout -fingerprint -sha256
```

On Windows file:

```powershell
certutil -dump .\lan-ca.crt | findstr /I "Cert Hash(sha256)"
```

Values must match exactly.

## Troubleshooting

### Windows shows `CRYPT_E_NO_REVOCATION_CHECK`

- Ensure `http://<server-ip>:8088/lan-ca.crl` is reachable from the client
- Ensure server cert includes CRL Distribution Point
- Restart browser after importing new CA

### Browser still shows insecure after cert import

- Remove old CA entries (for previous test certs)
- Reimport current `lan-ca.crt`
- Reopen browser or reboot device

### Caddy starts but HTTPS fails

Validate config and cert file mounts:

```bash
docker compose -f docker-compose.orangepi.dev.yml logs caddy --tail=100
ls -l letsencrypt/lan/
```
