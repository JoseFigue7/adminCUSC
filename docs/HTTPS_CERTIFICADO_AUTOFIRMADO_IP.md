# HTTPS con certificado autofirmado (solo IP 137.184.188.234)

El navegador mostrará "No seguro" / "Certificado no válido". Debes aceptar la excepción para continuar. Stripe y otras APIs pueden no aceptar este certificado.

---

## Paso 1: Generar el certificado en el servidor

Conéctate por SSH o consola al servidor y ejecuta:

```bash
# Crear directorio para la clave privada (si no existe)
sudo mkdir -p /etc/ssl/private

# Generar certificado autofirmado válido 1 año, con la IP en el certificado (SAN)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/admincusc-selfsigned.key \
  -out /etc/ssl/certs/admincusc-selfsigned.crt \
  -subj "/CN=137.184.188.234" \
  -addext "subjectAltName=IP:137.184.188.234"
```

Si tu OpenSSL no soporta `-addext` (versión antigua), usa:

```bash
# Alternativa sin SAN (algunos navegadores pueden seguir quejándose)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/admincusc-selfsigned.key \
  -out /etc/ssl/certs/admincusc-selfsigned.crt \
  -subj "/CN=137.184.188.234"
```

---

## Paso 2: Permisos de la clave privada

```bash
sudo chmod 600 /etc/ssl/private/admincusc-selfsigned.key
```

---

## Paso 3: Configurar Nginx para HTTPS

Tienes dos opciones.

### Opción A: Usar el archivo de ejemplo del repo

En el servidor, si ya tienes el repo actualizado:

```bash
# Copiar la config que incluye HTTPS (desde el repo)
sudo cp /var/www/admincusc/nginx.conf /etc/nginx/sites-available/admincusc
```

### Opción B: Añadir el bloque HTTPS a mano

Edita la config de Nginx:

```bash
sudo nano /etc/nginx/sites-available/admincusc
```

Añade **después** del primer `server { ... }` (el que escucha en el puerto 80) este segundo bloque:

```nginx
# HTTPS con certificado autofirmado (IP 137.184.188.234)
server {
    listen 443 ssl http2;
    server_name 137.184.188.234;

    ssl_certificate     /etc/ssl/certs/admincusc-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/admincusc-selfsigned.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 10M;

    location ~* ^/(\.env|\.env\.|\.git|config\.json|config\.js|credentials\.json|keyfile\.json|service-account\.json|appsettings\.json|application\.yml|\.npmrc|\.pgpass|wp-config\.php|configuration\.php|settings\.php|docker-compose\.|\.svn/|actuator/|debug/|phpinfo\.php) {
        return 404;
        access_log off;
    }

    location /static/ {
        alias /var/www/admincusc/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/admincusc/backend/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Guarda (Ctrl+O, Enter, Ctrl+X).

---

## Paso 4: Probar y recargar Nginx

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Si `nginx -t` muestra "syntax is ok", el reload está bien.

---

## Paso 5: Abrir el puerto 443 (firewall)

Si usas UFW:

```bash
sudo ufw allow 443/tcp
sudo ufw status
sudo ufw reload
```

En Digital Ocean, en el panel del Droplet → Networking → Firewall, asegúrate de que el puerto 443 esté permitido.

---

## Paso 6: Usar la app por HTTPS

1. Abre **https://137.184.188.234** (con `https://`).
2. El navegador mostrará "Tu conexión no es privada" o "Certificado no válido".
3. Avanzar: en Chrome "Avanzado" → "Acceder a 137.184.188.234 (sitio no seguro)". En Firefox "Aceptar el riesgo y continuar".
4. La app cargará por HTTPS.

---

## (Opcional) Redirigir HTTP → HTTPS

Si quieres que al entrar por `http://137.184.188.234` se redirija a `https://`:

Dentro del bloque `server { listen 80; ... }` añade al inicio (después de `server_name`):

```nginx
return 301 https://$host$request_uri;
```

y comenta o elimina el resto de ese bloque (locations, etc.), o deja solo ese `return` y el cierre `}`. Luego:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Renovar el certificado (cada año)

El certificado dura 365 días. Para renovar:

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/admincusc-selfsigned.key \
  -out /etc/ssl/certs/admincusc-selfsigned.crt \
  -subj "/CN=137.184.188.234" \
  -addext "subjectAltName=IP:137.184.188.234"
sudo systemctl reload nginx
```

Puedes crear un cron o un recordatorio para ejecutarlo cada año.
