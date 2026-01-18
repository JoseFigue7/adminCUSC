import React, { useState, useEffect } from 'react';
import { loadStripe, Stripe, StripeElementsOptions } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import { createPaymentIntent, processPublicPayment } from '../services/api';
import './StripePaymentForm.css';

// Cargar Stripe con la clave pública
// En producción, esto debería venir de una variable de entorno
const stripePromise = loadStripe(
  process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || 'pk_test_placeholder'
);

interface StripePaymentFormProps {
  carnet: string;
  paymentTypeId: string;
  amount: number;
  month?: number;
  year?: number;
  semester?: number;
  quantity?: number;
  onSuccess: (data: any) => void;
  onError: (error: string) => void;
}

interface PaymentFormInnerProps {
  carnet: string;
  paymentTypeId: string;
  amount: number;
  month?: number;
  year?: number;
  semester?: number;
  quantity?: number;
  onSuccess: (data: any) => void;
  onError: (error: string) => void;
}

const PaymentFormInner: React.FC<PaymentFormInnerProps> = ({
  carnet,
  paymentTypeId,
  amount,
  month,
  year,
  semester,
  quantity,
  onSuccess,
  onError,
}) => {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null);
  const [error, setError] = useState<string>('');

  // Crear Payment Intent cuando el componente se monta
  useEffect(() => {
    const createIntent = async () => {
      try {
        setLoading(true);
        setError('');
        
        const response = await createPaymentIntent({
          carnet,
          payment_type: paymentTypeId,
          amount: amount,
        });

        setClientSecret(response.data.client_secret);
        setPaymentIntentId(response.data.payment_intent_id);
      } catch (err: any) {
        const errorMessage = err.response?.data?.error || 'Error al inicializar el pago';
        setError(errorMessage);
        onError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    createIntent();
  }, [carnet, paymentTypeId, amount]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements || !clientSecret || !paymentIntentId) {
      setError('Stripe no está inicializado. Por favor recarga la página.');
      return;
    }

    setLoading(true);
    setError('');

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setError('No se encontró el elemento de tarjeta');
      setLoading(false);
      return;
    }

    try {
      // PRIMERO: Crear el registro de pago en la BD con estado PENDIENTE
      // El webhook será el que lo apruebe cuando el pago sea exitoso
      const paymentData: any = {
        carnet: carnet,
        payment_type: paymentTypeId,
        amount: amount,
        payment_intent_id: paymentIntentId,
      };

      if (month) paymentData.month = month;
      if (year) paymentData.year = year;
      if (semester) paymentData.semester = semester;
      if (quantity) paymentData.quantity = quantity;

      let paymentRecord;
      try {
        const response = await processPublicPayment(paymentData);
        paymentRecord = response.data;
      } catch (backendError: any) {
        const errorMessage = backendError.response?.data?.error || 'Error al registrar el pago';
        setError(errorMessage);
        onError(errorMessage);
        setLoading(false);
        return;
      }

      // SEGUNDO: Confirmar el pago con Stripe (solo confirmar, NO aprobar en BD)
      // El webhook payment_intent.succeeded será la única fuente de verdad
      const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(
        clientSecret,
        {
          payment_method: {
            card: cardElement,
          },
        }
      );

      if (stripeError) {
        setError(stripeError.message || 'Error al procesar el pago');
        onError(stripeError.message || 'Error al procesar el pago');
        setLoading(false);
        return;
      }

      if (paymentIntent?.status === 'succeeded') {
        // El pago fue confirmado en Stripe
        // El webhook se encargará de aprobarlo en la BD automáticamente
        // Solo mostramos éxito al usuario
        onSuccess({
          ...paymentRecord,
          message: 'Pago confirmado. El pago será procesado automáticamente.',
        });
      } else {
        setError(`El pago no fue exitoso. Estado: ${paymentIntent?.status}`);
        onError(`El pago no fue exitoso. Estado: ${paymentIntent?.status}`);
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Error inesperado al procesar el pago';
      setError(errorMessage);
      onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
      },
      invalid: {
        color: '#9e2146',
      },
    },
  };

  return (
    <form onSubmit={handleSubmit} className="stripe-payment-form">
      <div className="form-group">
        <label htmlFor="card-element">Información de la Tarjeta</label>
        <div className="card-element-container">
          <CardElement
            id="card-element"
            options={cardElementOptions}
          />
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!stripe || !elements || loading || !clientSecret}
        >
          {loading ? 'Procesando...' : `Pagar MX$${amount.toFixed(2)}`}
        </button>
      </div>

      {loading && !clientSecret && (
        <div className="loading-message">
          Inicializando pago seguro...
        </div>
      )}
    </form>
  );
};

const StripePaymentForm: React.FC<StripePaymentFormProps> = (props) => {
  // Las opciones de Elements se configuran dinámicamente cuando tenemos el client_secret
  // Por ahora usamos opciones básicas
  const options: StripeElementsOptions = {
    appearance: {
      theme: 'stripe',
    },
  };

  return (
    <Elements stripe={stripePromise} options={options}>
      <PaymentFormInner {...props} />
    </Elements>
  );
};

export default StripePaymentForm;

