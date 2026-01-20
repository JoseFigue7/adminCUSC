# Checklist de Despliegue en Digital Ocean

## Información Necesaria del Droplet

- [ ] **IP Pública del Droplet:** `_______________`
- [ ] **Dominio (opcional):** `_______________`
- [ ] **Sistema Operativo:** Ubuntu 22.04 LTS (recomendado)
- [ ] **Tamaño del Droplet:** Mínimo 2GB RAM

## Configuración de Base de Datos

- [ ] ¿Usarás MySQL o SQLite?
  - [ ] MySQL (recomendado para producción)
  - [ ] SQLite (solo para pruebas)

Si usas MySQL:
- [ ] Usuario de MySQL: `_______________`
- [ ] Contraseña de MySQL: `_______________`
- [ ] Nombre de la base de datos: `admincusc_db`

## Configuración de Stripe (Opcional)

- [ ] ¿Usarás pagos con tarjeta?
  - [ ] Sí (necesitaré las claves de Stripe)
  - [ ] No

Si usas Stripe:
- [ ] STRIPE_SECRET_KEY: `sk_live_...` o `sk_test_...`
- [ ] STRIPE_PUBLISHABLE_KEY: `pk_live_...` o `pk_test_...`
- [ ] STRIPE_WEBHOOK_SECRET: `whsec_...`

## Pasos de Despliegue

1. [ ] Clonar repositorio en el servidor
2. [ ] Configurar variables de entorno (.env)
3. [ ] Instalar dependencias del sistema
4. [ ] Configurar base de datos
5. [ ] Configurar Gunicorn
6. [ ] Configurar Nginx
7. [ ] Configurar SSL con Let's Encrypt (si tienes dominio)
8. [ ] Configurar firewall
9. [ ] Probar acceso al sitio

## Notas

- Guarda esta información de forma segura
- No compartas credenciales en texto plano en chats públicos
- Las credenciales se configurarán en el archivo `.env` del servidor (no se sube al repositorio)
