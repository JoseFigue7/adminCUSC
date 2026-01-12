# Crear Tipos de Pago

## Problema

Si no aparecen tipos de pago en el selector, es porque no se han creado en la base de datos.

## Solución

Ejecuta el comando de Django para crear los tipos de pago iniciales:

### Opción 1: Desde la terminal (Recomendado)

```bash
cd backend
# Activa tu entorno virtual si lo tienes
source venv/bin/activate  # o el nombre de tu entorno virtual

# Ejecuta el comando seed
python manage.py seed_payment_types
```

### Opción 2: Desde el Admin de Django

1. Ve a: `http://localhost:8000/admin`
2. Inicia sesión con tu usuario administrador
3. Ve a **Payments > Tipos de Pago**
4. Click en **"Agregar Tipo de Pago"**
5. Completa los campos:
   - **Código:** (ej: `010`)
   - **Nombre:** (ej: `Inscripción ordinaria`)
   - **Descripción:** (opcional)
   - **Monto fijo:** (opcional, déjalo vacío si es variable)
   - **Activo:** ✓ (marcado)
   - **Requiere mes/año/semestre:** según corresponda

### Opción 3: Desde la consola de Python

```bash
cd backend
python manage.py shell
```

Luego en la consola:

```python
from payments.models import PaymentType
from decimal import Decimal

# Crear un tipo de pago de ejemplo
PaymentType.objects.create(
    code='010',
    name='Inscripción ordinaria',
    description='Inscripción ordinaria para el ciclo académico',
    amount=None,  # Monto variable
    requires_semester=True,
    requires_year=True,
    is_active=True
)

# Verificar que se creó
print(f"Tipos de pago activos: {PaymentType.objects.filter(is_active=True).count()}")
```

## Tipos de Pago Predefinidos

El comando `seed_payment_types` crea los siguientes tipos:

1. **010** - Inscripción ordinaria
2. **011** - Inscripción extraordinaria
3. **111** - Pronto Pago
4. **201** - Colegiatura cursos
5. **202** - Cursos libres idiomas intensivos
6. **300** - Evaluación Primer Parcial Extraordinario
7. **302** - Examen de Recuperación
8. **305** - Evaluación Segundo Parcial Extraordinario
9. **308** - Evaluación especial
10. **309** - Evaluación por suficiencia
11. **410** - Reposición carné
12. **411** - Certificación de cursos
13. **412** - Cierre de Pensum
14. **418** - Certificación de Matrícula
15. **453** - Parqueo
16. **476** - Abono multa

## Verificar que Funciona

Después de ejecutar el comando:

1. Recarga la página de pagos: `http://localhost:3000/pagos`
2. Busca un estudiante por carné
3. Deberías ver los tipos de pago en el selector

## Si Aún No Aparecen

1. **Verifica que el backend esté corriendo:**
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **Verifica la consola del navegador:**
   - Abre las herramientas de desarrollador (F12)
   - Ve a la pestaña "Console"
   - Busca errores relacionados con la carga de tipos de pago

3. **Verifica la respuesta de la API:**
   - En las herramientas de desarrollador, ve a "Network"
   - Busca la petición a `/api/payments/payment-types/`
   - Verifica que devuelva datos

4. **Verifica que los tipos estén activos:**
   ```bash
   python manage.py shell
   ```
   ```python
   from payments.models import PaymentType
   PaymentType.objects.filter(is_active=True).count()
   ```



