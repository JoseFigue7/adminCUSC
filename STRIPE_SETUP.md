# Configuración de Pagos con Stripe

Este documento explica cómo configurar Stripe para procesar pagos reales con tarjeta.

## 1. Crear cuenta en Stripe

1. Ve a [https://stripe.com](https://stripe.com)
2. Crea una cuenta (es gratuita)
3. Completa la información de tu negocio
4. Verifica tu cuenta

## 2. Obtener las claves de API

### Modo de Prueba (Testing)

1. En el Dashboard de Stripe, ve a **Developers** > **API keys**
2. Encuentra la sección **Test mode**
3. Copia:
   - **Publishable key** (clave pública, empieza con `pk_test_`)
   - **Secret key** (clave secreta, empieza con `sk_test_`)

### Modo de Producción

1. Cambia el toggle a **Live mode** en el Dashboard
2. Copia las claves de producción:
   - **Publishable key** (empieza con `pk_live_`)
   - **Secret key** (empieza con `sk_live_`)

## 3. Configurar variables de entorno

Crea o actualiza el archivo `.env` en la carpeta `backend/`:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_tu_clave_secreta_aqui
STRIPE_PUBLISHABLE_KEY=pk_test_tu_clave_publica_aqui
STRIPE_WEBHOOK_SECRET=whsec_tu_webhook_secret_aqui  # Opcional, para webhooks
```

## 4. Instalar dependencias

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## 5. Configurar Stripe en el Frontend

El frontend necesita la clave pública de Stripe. Actualiza el componente `PublicPayment.tsx` para incluir:

```typescript
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe('pk_test_tu_clave_publica_aqui');
```

**Nota:** En producción, deberías obtener esta clave desde una variable de entorno o desde el backend.

## 6. Tarjetas de prueba

Stripe proporciona tarjetas de prueba para el modo de testing:

### Tarjetas que funcionan:
- **Visa:** `4242 4242 4242 4242`
- **Mastercard:** `5555 5555 5555 4444`
- **American Express:** `3782 822463 10005`

### Cualquier:
- **CVV:** `123` (o cualquier 3 dígitos)
- **Fecha de expiración:** Cualquier fecha futura (ej: `12/34`)
- **Código postal:** Cualquier código postal válido

### Tarjetas que fallan:
- **Tarjeta rechazada:** `4000 0000 0000 0002`
- **Tarjeta insuficiente:** `4000 0000 0000 9995`

## 7. Moneda

El sistema está configurado para usar **GTQ (Quetzales guatemaltecos)**. Si necesitas cambiar la moneda, actualiza:

- `backend/payments/views.py`: Cambia `currency='gtq'` en `create_payment_intent`
- `backend/payments/stripe_service.py`: Ajusta la conversión de centavos según la moneda

## 8. Webhooks (Opcional)

Para recibir notificaciones de Stripe sobre pagos:

1. En el Dashboard de Stripe, ve a **Developers** > **Webhooks**
2. Click en **Add endpoint**
3. URL: `https://tu-dominio.com/api/payments/webhook/`
4. Selecciona eventos:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copia el **Signing secret** y agrégalo a `.env` como `STRIPE_WEBHOOK_SECRET`

## 9. Verificar que funciona

1. Inicia el servidor backend:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. Inicia el frontend:
   ```bash
   cd frontend
   npm start
   ```

3. Ve a `http://localhost:3000/pagos`
4. Ingresa un carné válido
5. Selecciona un tipo de pago
6. Usa una tarjeta de prueba de Stripe
7. Completa el pago

## 10. Ver pagos en Stripe

1. Ve al Dashboard de Stripe
2. Click en **Payments**
3. Verás todos los pagos procesados (tanto exitosos como fallidos)

## Solución de problemas

### Error: "No such payment_intent"
- Verifica que estés usando el `payment_intent_id` correcto
- Asegúrate de que el Payment Intent se creó antes de intentar confirmarlo

### Error: "Invalid API Key"
- Verifica que las claves en `.env` sean correctas
- Asegúrate de usar claves de prueba en desarrollo y claves de producción en producción

### Error: "Currency not supported"
- Stripe puede no soportar GTQ en todas las regiones
- Considera usar USD si GTQ no está disponible en tu región
- Verifica en [Stripe Docs](https://stripe.com/docs/currencies) qué monedas están disponibles

### El pago se procesa pero no se guarda en la BD
- Verifica los logs del backend
- Asegúrate de que la migración de la base de datos esté aplicada
- Verifica que el modelo `Payment` tenga todos los campos necesarios

## Recursos adicionales

- [Documentación de Stripe](https://stripe.com/docs)
- [Stripe Elements](https://stripe.com/docs/stripe-js/react)
- [Payment Intents API](https://stripe.com/docs/payments/payment-intents)
- [Testing](https://stripe.com/docs/testing)


