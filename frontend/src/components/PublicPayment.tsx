import React, { useState, useEffect } from 'react';
import { getStudentByCarnet, getPaymentTypes, processPublicPayment } from '../services/api';
import './PublicPayment.css';

interface Student {
  id: string;
  carnet: string;
  full_name: string;
  career: {
    id: string;
    name: string;
    code: string;
  };
  has_scholarship: boolean;
  scholarship_type: string;
}

interface PaymentType {
  id: string;
  code: string;
  name: string;
  description: string;
  amount: string | null;
  requires_career: boolean;
  requires_semester: boolean;
  requires_month: boolean;
  requires_year: boolean;
  requires_quantity: boolean;
}

const PublicPayment: React.FC = () => {
  const [step, setStep] = useState<'carnet' | 'payment' | 'success'>('carnet');
  const [carnet, setCarnet] = useState('');
  const [student, setStudent] = useState<Student | null>(null);
  const [paymentTypes, setPaymentTypes] = useState<PaymentType[]>([]);
  const [selectedPaymentType, setSelectedPaymentType] = useState<PaymentType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Form fields
  const [amount, setAmount] = useState('');
  const [month, setMonth] = useState('');
  const [year, setYear] = useState('');
  const [semester, setSemester] = useState('');
  const [quantity, setQuantity] = useState('');
  
  // Card fields
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvv, setCardCvv] = useState('');

  useEffect(() => {
    loadPaymentTypes();
  }, []);

  const loadPaymentTypes = async () => {
    try {
      const response = await getPaymentTypes();
      setPaymentTypes(response.data.results || response.data);
    } catch (err: any) {
      console.error('Error loading payment types:', err);
    }
  };

  const handleCarnetSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await getStudentByCarnet(carnet);
      setStudent(response.data);
      setStep('payment');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al buscar el estudiante. Verifique el número de carné.');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentTypeChange = (paymentTypeId: string) => {
    const paymentType = paymentTypes.find(pt => pt.id === paymentTypeId);
    setSelectedPaymentType(paymentType || null);
    
    // Reset form fields
    setAmount('');
    setMonth('');
    setYear('');
    setSemester('');
    setQuantity('');
    
    // Set default amount if payment type has fixed amount
    if (paymentType?.amount) {
      setAmount(paymentType.amount);
    }
    
    // Set current year if required
    if (paymentType?.requires_year) {
      setYear(new Date().getFullYear().toString());
    }
  };

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(' ');
    } else {
      return v;
    }
  };

  const formatExpiry = (value: string) => {
    const v = value.replace(/\D/g, '');
    if (v.length >= 2) {
      return v.substring(0, 2) + '/' + v.substring(2, 4);
    }
    return v;
  };

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCardNumber(formatCardNumber(e.target.value));
  };

  const handleCardExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCardExpiry(formatExpiry(e.target.value));
  };

  const handleCardCvvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value.replace(/\D/g, '').substring(0, 3);
    setCardCvv(v);
  };

  const validateForm = (): boolean => {
    if (!selectedPaymentType) {
      setError('Por favor seleccione un tipo de pago');
      return false;
    }

    if (!amount || parseFloat(amount) <= 0) {
      setError('Por favor ingrese un monto válido');
      return false;
    }

    if (selectedPaymentType.requires_month && !month) {
      setError('Por favor seleccione el mes');
      return false;
    }

    if (selectedPaymentType.requires_year && !year) {
      setError('Por favor ingrese el año');
      return false;
    }

    if (selectedPaymentType.requires_semester && !semester) {
      setError('Por favor seleccione el semestre/trimestre');
      return false;
    }

    if (selectedPaymentType.requires_quantity && !quantity) {
      setError('Por favor ingrese la cantidad');
      return false;
    }

    // Validate card
    const cardNumberClean = cardNumber.replace(/\s/g, '');
    if (cardNumberClean.length < 13 || cardNumberClean.length > 19) {
      setError('Por favor ingrese un número de tarjeta válido');
      return false;
    }

    if (!cardName.trim()) {
      setError('Por favor ingrese el nombre del titular de la tarjeta');
      return false;
    }

    if (!cardExpiry || cardExpiry.length !== 5) {
      setError('Por favor ingrese una fecha de expiración válida (MM/AA)');
      return false;
    }

    if (!cardCvv || cardCvv.length !== 3) {
      setError('Por favor ingrese un CVV válido');
      return false;
    }

    return true;
  };

  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // En producción, aquí se generaría un token seguro de la tarjeta usando una pasarela de pago
      // Por ahora, simulamos el token (en producción usar Stripe, PayPal, etc.)
      const cardToken = `tok_${cardNumber.replace(/\s/g, '').slice(-4)}_${Date.now()}`;

      const paymentData: any = {
        carnet: carnet,
        payment_type: selectedPaymentType!.id,
        amount: parseFloat(amount),
        card_token: cardToken,
      };

      if (selectedPaymentType!.requires_month && month) {
        paymentData.month = parseInt(month);
      }

      if (selectedPaymentType!.requires_year && year) {
        paymentData.year = parseInt(year);
      }

      if (selectedPaymentType!.requires_semester && semester) {
        paymentData.semester = parseInt(semester);
      }

      if (selectedPaymentType!.requires_quantity && quantity) {
        paymentData.quantity = parseInt(quantity);
      }

      const response = await processPublicPayment(paymentData);
      
      setSuccess(true);
      setStep('success');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al procesar el pago. Por favor intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  const months = [
    { value: '1', label: 'Enero' },
    { value: '2', label: 'Febrero' },
    { value: '3', label: 'Marzo' },
    { value: '4', label: 'Abril' },
    { value: '5', label: 'Mayo' },
    { value: '6', label: 'Junio' },
    { value: '7', label: 'Julio' },
    { value: '8', label: 'Agosto' },
    { value: '9', label: 'Septiembre' },
    { value: '10', label: 'Octubre' },
    { value: '11', label: 'Noviembre' },
    { value: '12', label: 'Diciembre' },
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 10 }, (_, i) => currentYear - i);

  return (
    <div className="public-payment-container">
      <div className="public-payment-card">
        <h1>Pagos con Tarjeta de Crédito y Débito</h1>

        {step === 'carnet' && (
          <form onSubmit={handleCarnetSearch} className="payment-form">
            <div className="form-group">
              <label htmlFor="carnet">No. de Carné</label>
              <input
                type="text"
                id="carnet"
                value={carnet}
                onChange={(e) => setCarnet(e.target.value)}
                placeholder="Ingrese su número de carné"
                required
                maxLength={9}
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Buscando...' : 'Continuar'}
            </button>
          </form>
        )}

        {step === 'payment' && student && (
          <div>
            <div className="student-info">
              <h3>Información del Estudiante</h3>
              <p><strong>Nombre:</strong> {student.full_name}</p>
              <p><strong>Carné:</strong> {student.carnet}</p>
              <p><strong>Carrera:</strong> {student.career.name}</p>
            </div>

            <form onSubmit={handlePaymentSubmit} className="payment-form">
              <div className="form-group">
                <label htmlFor="payment_type">Tipo de Pago</label>
                <select
                  id="payment_type"
                  value={selectedPaymentType?.id || ''}
                  onChange={(e) => handlePaymentTypeChange(e.target.value)}
                  required
                >
                  <option value="">Seleccione...</option>
                  {paymentTypes.map((pt) => (
                    <option key={pt.id} value={pt.id}>
                      {pt.code} - {pt.name}
                    </option>
                  ))}
                </select>
                {selectedPaymentType?.description && (
                  <small className="form-help">{selectedPaymentType.description}</small>
                )}
              </div>

              {selectedPaymentType && (
                <>
                  <div className="form-group">
                    <label htmlFor="amount">
                      Monto {selectedPaymentType.amount && `(Fijo: MX$${parseFloat(selectedPaymentType.amount).toFixed(2)})`}
                    </label>
                    <input
                      type="number"
                      id="amount"
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      placeholder="0.00"
                      step="0.01"
                      min="0.01"
                      required
                      disabled={!!selectedPaymentType.amount}
                    />
                  </div>

                  {selectedPaymentType.requires_month && (
                    <div className="form-group">
                      <label htmlFor="month">Mes</label>
                      <select
                        id="month"
                        value={month}
                        onChange={(e) => setMonth(e.target.value)}
                        required
                      >
                        <option value="">Seleccione...</option>
                        {months.map((m) => (
                          <option key={m.value} value={m.value}>
                            {m.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {selectedPaymentType.requires_year && (
                    <div className="form-group">
                      <label htmlFor="year">Año del Ciclo Académico</label>
                      <select
                        id="year"
                        value={year}
                        onChange={(e) => setYear(e.target.value)}
                        required
                      >
                        <option value="">Seleccione...</option>
                        {years.map((y) => (
                          <option key={y} value={y}>
                            {y}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {selectedPaymentType.requires_semester && (
                    <div className="form-group">
                      <label htmlFor="semester">Semestre/Trimestre</label>
                      <select
                        id="semester"
                        value={semester}
                        onChange={(e) => setSemester(e.target.value)}
                        required
                      >
                        <option value="">Seleccione...</option>
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                          <option key={s} value={s}>
                            {s === 1 ? 'Primero' : s === 2 ? 'Segundo' : s === 3 ? 'Tercero' : s === 4 ? 'Cuarto' : s === 5 ? 'Quinto' : s === 6 ? 'Sexto' : s === 7 ? 'Séptimo' : 'Octavo'}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {selectedPaymentType.requires_quantity && (
                    <div className="form-group">
                      <label htmlFor="quantity">Cantidad</label>
                      <input
                        type="number"
                        id="quantity"
                        value={quantity}
                        onChange={(e) => setQuantity(e.target.value)}
                        placeholder="1"
                        min="1"
                        required
                      />
                    </div>
                  )}

                  <div className="card-section">
                    <h3>Información de la Tarjeta</h3>
                    
                    <div className="form-group">
                      <label htmlFor="card_number">Número de Tarjeta</label>
                      <input
                        type="text"
                        id="card_number"
                        value={cardNumber}
                        onChange={handleCardNumberChange}
                        placeholder="1234 5678 9012 3456"
                        maxLength={19}
                        required
                      />
                    </div>

                    <div className="form-group">
                      <label htmlFor="card_name">Nombre del Titular</label>
                      <input
                        type="text"
                        id="card_name"
                        value={cardName}
                        onChange={(e) => setCardName(e.target.value)}
                        placeholder="Como aparece en la tarjeta"
                        required
                      />
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="card_expiry">Fecha de Expiración</label>
                        <input
                          type="text"
                          id="card_expiry"
                          value={cardExpiry}
                          onChange={handleCardExpiryChange}
                          placeholder="MM/AA"
                          maxLength={5}
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="card_cvv">CVV</label>
                        <input
                          type="text"
                          id="card_cvv"
                          value={cardCvv}
                          onChange={handleCardCvvChange}
                          placeholder="123"
                          maxLength={3}
                          required
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}

              {error && <div className="error-message">{error}</div>}

              <div className="form-actions">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setStep('carnet');
                    setError('');
                    setStudent(null);
                  }}
                >
                  Volver
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading || !selectedPaymentType}>
                  {loading ? 'Procesando...' : 'Generar Boleta'}
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 'success' && (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h2>¡Pago Procesado Exitosamente!</h2>
            <p>Su pago ha sido procesado correctamente. Recibirá un comprobante por correo electrónico.</p>
            <button
              className="btn btn-primary"
              onClick={() => {
                setStep('carnet');
                setCarnet('');
                setStudent(null);
                setSelectedPaymentType(null);
                setError('');
                setSuccess(false);
                setAmount('');
                setMonth('');
                setYear('');
                setSemester('');
                setQuantity('');
                setCardNumber('');
                setCardName('');
                setCardExpiry('');
                setCardCvv('');
              }}
            >
              Realizar Otro Pago
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PublicPayment;

