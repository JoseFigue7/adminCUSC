"""
Servicio para manejar pagos con Stripe
"""
import stripe
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Configurar Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY no está configurado. Los pagos con tarjeta no funcionarán.")


class StripePaymentService:
    """Servicio para procesar pagos con Stripe"""
    
    @staticmethod
    def create_payment_intent(amount, currency='mxn', metadata=None):
        """
        Crear un Payment Intent en Stripe
        
        Args:
            amount: Monto en la moneda más pequeña (centavos para MXN)
            currency: Código de moneda (default: 'mxn' para Pesos Mexicanos)
            metadata: Diccionario con información adicional
        
        Returns:
            dict: Payment Intent creado
        """
        try:
            # Convertir monto a centavos (Stripe usa la unidad más pequeña)
            # Para MXN, 1 peso = 100 centavos
            amount_in_cents = int(float(amount) * 100)
            
            intent_data = {
                'amount': amount_in_cents,
                'currency': currency,
                'automatic_payment_methods': {
                    'enabled': True,
                },
            }
            
            if metadata:
                intent_data['metadata'] = metadata
            
            intent = stripe.PaymentIntent.create(**intent_data)
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe al crear Payment Intent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        except Exception as e:
            logger.error(f"Error inesperado al crear Payment Intent: {str(e)}")
            return {
                'success': False,
                'error': 'Error al procesar la solicitud de pago'
            }
    
    @staticmethod
    def confirm_payment(payment_intent_id):
        """
        Confirmar un pago en Stripe
        
        Args:
            payment_intent_id: ID del Payment Intent
        
        Returns:
            dict: Estado del pago
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': intent.status,
                'payment_intent': intent,
                'amount': intent.amount / 100,  # Convertir de centavos a pesos
                'currency': intent.currency,
                'payment_method': intent.payment_method,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe al confirmar pago: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        except Exception as e:
            logger.error(f"Error inesperado al confirmar pago: {str(e)}")
            return {
                'success': False,
                'error': 'Error al confirmar el pago'
            }
    
    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Obtener información de un Payment Intent
        
        Args:
            payment_intent_id: ID del Payment Intent
        
        Returns:
            dict: Información del Payment Intent
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency,
                'payment_method': intent.payment_method,
                'charges': intent.charges.data if intent.charges else [],
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error de Stripe al obtener Payment Intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_card_last_four(payment_intent_id):
        """
        Obtener los últimos 4 dígitos de la tarjeta usada
        
        Args:
            payment_intent_id: ID del Payment Intent
        
        Returns:
            str: Últimos 4 dígitos de la tarjeta
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.payment_method:
                payment_method = stripe.PaymentMethod.retrieve(intent.payment_method)
                if payment_method.card:
                    return payment_method.card.last4
            
            # Intentar obtener de los cargos
            if intent.charges and len(intent.charges.data) > 0:
                charge = intent.charges.data[0]
                if charge.payment_method_details and charge.payment_method_details.card:
                    return charge.payment_method_details.card.last4
            
            return None
        except Exception as e:
            logger.error(f"Error al obtener últimos 4 dígitos: {str(e)}")
            return None



