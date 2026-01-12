import React, { useState, useEffect } from 'react';
import { getStudentByCarnet, getPaymentTypes } from '../services/api';
import StripePaymentForm from './StripePaymentForm';
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

    return true;
  };

  const handlePaymentSuccess = (data: any) => {
    setSuccess(true);
    setStep('success');
    setError('');
  };

  const handlePaymentError = (errorMessage: string) => {
    setError(errorMessage);
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

            <div className="payment-form-container">
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

                  {validateForm() && (
                    <div className="stripe-payment-wrapper">
                      <StripePaymentForm
                        carnet={carnet}
                        paymentTypeId={selectedPaymentType.id}
                        amount={parseFloat(amount)}
                        month={month ? parseInt(month) : undefined}
                        year={year ? parseInt(year) : undefined}
                        semester={semester ? parseInt(semester) : undefined}
                        quantity={quantity ? parseInt(quantity) : undefined}
                        onSuccess={handlePaymentSuccess}
                        onError={handlePaymentError}
                      />
                    </div>
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
                        setSelectedPaymentType(null);
                        setAmount('');
                        setMonth('');
                        setYear('');
                        setSemester('');
                        setQuantity('');
                      }}
                    >
                      Volver
                    </button>
                  </div>
                </>
              )}
            </div>
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

