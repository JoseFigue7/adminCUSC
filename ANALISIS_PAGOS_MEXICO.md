# Análisis del Sistema de Pagos - México

## 📍 Link de Pagos Públicos

**URL:** `/pagos`

Los estudiantes pueden acceder a esta ruta para realizar pagos con tarjeta de crédito/débito. La ruta está configurada en:
- Frontend: `frontend/src/App.tsx` (línea 149)
- Componente: `frontend/src/components/PublicPayment.tsx`

## 💳 Tipos de Pago Disponibles

El sistema tiene **3 métodos de pago** configurados:

1. **TRANSFERENCIA** - Transferencia bancaria
2. **TARJETA** - Tarjeta de crédito/débito (Stripe)
3. **EFECTIVO** - Pago en efectivo

Los tipos de pago se gestionan a través del modelo `PaymentType` que permite:
- Montos fijos o variables
- Requisitos por mes, año, semestre, cantidad
- Configuración de mora/penalizaciones

## ⚠️ Problemas Encontrados

### 1. **Moneda Incorrecta**
- **Problema:** El sistema está configurado para **GTQ (Quetzales guatemaltecos)** pero necesitas **MXN (Pesos mexicanos)** para México.
- **Ubicación:** 
  - `backend/payments/views.py` línea 282: `currency='gtq'`
  - `backend/payments/stripe_service.py` línea 22: `currency='gtq'`

### 2. **Formulario de Tarjeta Inseguro**
- **Problema:** El componente `PublicPayment.tsx` está usando un formulario HTML básico que **NO es seguro** para capturar datos de tarjeta.
- **Riesgo:** Los datos de tarjeta se están enviando directamente al servidor, lo cual:
  - Viola estándares PCI-DSS
  - Expone información sensible
  - No cumple con las mejores prácticas de seguridad
- **Ubicación:** `frontend/src/components/PublicPayment.tsx` líneas 413-468

### 3. **Falta Integración Real de Stripe Elements**
- **Problema:** Aunque el backend tiene la infraestructura de Stripe, el frontend **NO está usando Stripe Elements**.
- **Estado actual:** El código simula un token de tarjeta (línea 210) en lugar de usar la API real de Stripe.
- **Componente faltante:** La documentación menciona `StripePaymentForm.tsx` pero este componente no existe.

### 4. **Endpoint Incorrecto**
- **Problema:** El endpoint usado es `/payments/payments/process_public/` pero debería usar el flujo de Payment Intent de Stripe.
- **Ubicación:** `frontend/src/components/PublicPayment.tsx` línea 235

## ✅ Proceso para Recibir Pagos con Tarjetas en México

### Opción 1: Stripe (Recomendado - Ya está parcialmente implementado)

**Ventajas:**
- ✅ Ya está configurado en el backend
- ✅ Cumple con PCI-DSS automáticamente
- ✅ Soporta MXN (Pesos mexicanos)
- ✅ Comisiones: ~2.9% + $3 MXN por transacción
- ✅ Depósitos en 2-7 días hábiles

**Pasos para activar:**

1. **Crear cuenta en Stripe México:**
   - Ir a https://stripe.com/mx
   - Completar registro con datos del negocio
   - Verificar identidad y cuenta bancaria mexicana

2. **Obtener claves de API:**
   - Dashboard > Developers > API keys
   - Copiar `Publishable key` (pk_test_...) y `Secret key` (sk_test_...)

3. **Configurar variables de entorno:**
   ```env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```

4. **Cambiar moneda a MXN:**
   - Actualizar `backend/payments/views.py` línea 282: `currency='mxn'`
   - Actualizar `backend/payments/stripe_service.py` línea 22: `currency='mxn'`

5. **Implementar Stripe Elements en el frontend:**
   - Instalar: `npm install @stripe/stripe-js @stripe/react-stripe-js`
   - Crear componente `StripePaymentForm.tsx`
   - Reemplazar formulario inseguro en `PublicPayment.tsx`

### Opción 2: Conekta (Alternativa mexicana)

**Ventajas:**
- ✅ Empresa mexicana
- ✅ Comisiones competitivas
- ✅ Soporte en español
- ✅ Integración con bancos mexicanos

**Desventajas:**
- ❌ Requiere implementación completa desde cero
- ❌ No está implementado en el sistema actual

### Opción 3: Mercado Pago

**Ventajas:**
- ✅ Muy popular en México
- ✅ Múltiples métodos de pago
- ✅ Comisiones competitivas

**Desventajas:**
- ❌ Requiere implementación completa desde cero
- ❌ No está implementado en el sistema actual

## 🔧 Correcciones Necesarias

### Prioridad Alta:

1. **Cambiar moneda a MXN**
2. **Implementar Stripe Elements** (formulario seguro)
3. **Corregir flujo de pago** para usar Payment Intents correctamente

### Prioridad Media:

4. **Agregar validación de tarjetas mexicanas**
5. **Implementar webhooks** para confirmación automática
6. **Agregar manejo de errores** más robusto

## 📋 Checklist de Implementación

- [ ] Cambiar moneda de GTQ a MXN
- [ ] Instalar dependencias de Stripe en frontend
- [ ] Crear componente StripePaymentForm.tsx
- [ ] Actualizar PublicPayment.tsx para usar Stripe Elements
- [ ] Configurar claves de Stripe en .env
- [ ] Probar con tarjetas de prueba
- [ ] Configurar webhooks (opcional)
- [ ] Documentar proceso para usuarios finales

## 🔗 Referencias

- [Stripe México](https://stripe.com/mx)
- [Stripe Elements](https://stripe.com/docs/stripe-js/react)
- [Payment Intents API](https://stripe.com/docs/payments/payment-intents)
- [Tarjetas de prueba Stripe](https://stripe.com/docs/testing)



