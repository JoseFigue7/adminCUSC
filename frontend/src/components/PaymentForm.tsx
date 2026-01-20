import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStudents, createPayment, uploadPaymentReceipt, getPaymentTypes } from '../services/api';
import { FiDollarSign, FiSave, FiX, FiLoader, FiUpload, FiSearch } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './PaymentForm.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
  full_name?: string;
}

interface PaymentType {
  id: string;
  code: string;
  name: string;
  description?: string;
  amount?: number;
  requires_career?: boolean;
  requires_semester?: boolean;
  requires_month?: boolean;
  requires_year?: boolean;
  requires_quantity?: boolean;
}

const PaymentForm: React.FC = () => {
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [payment, setPayment] = useState({
    student: '',
    payment_type: '',
    payment_method: 'TRANSFERENCIA',
    amount: '',
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    receipt_number: '',
    card_last_four: '',
    transaction_id: '',
  });

  const [students, setStudents] = useState<Student[]>([]);
  const [paymentTypes, setPaymentTypes] = useState<PaymentType[]>([]);
  const [studentSearch, setStudentSearch] = useState('');
  const [filteredStudents, setFilteredStudents] = useState<Student[]>([]);
  const [showStudentDropdown, setShowStudentDropdown] = useState(false);
  const [selectedPaymentType, setSelectedPaymentType] = useState<PaymentType | null>(null);
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const studentSearchRef = useRef<HTMLDivElement>(null);

  const months = [
    { value: 1, label: 'Enero' },
    { value: 2, label: 'Febrero' },
    { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Mayo' },
    { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' },
    { value: 11, label: 'Noviembre' },
    { value: 12, label: 'Diciembre' },
  ];

  useEffect(() => {
    loadStudents();
    loadPaymentTypes();
  }, []);

  useEffect(() => {
    // Filtrar estudiantes según búsqueda
    if (studentSearch.trim()) {
      const searchTerm = studentSearch.toLowerCase();
      const filtered = students.filter(student => 
        student.carnet.toLowerCase().includes(searchTerm) ||
        student.first_name.toLowerCase().includes(searchTerm) ||
        student.last_name.toLowerCase().includes(searchTerm) ||
        `${student.carnet} - ${student.first_name} ${student.last_name}`.toLowerCase().includes(searchTerm)
      );
      setFilteredStudents(filtered);
      setShowStudentDropdown(true);
    } else {
      setFilteredStudents([]);
      setShowStudentDropdown(false);
    }
  }, [studentSearch, students]);

  // Sincronizar el campo de búsqueda con el estudiante seleccionado
  useEffect(() => {
    if (payment.student) {
      const student = students.find(s => s.id === payment.student);
      if (student && studentSearch !== `${student.carnet} - ${student.first_name} ${student.last_name}`) {
        setStudentSearch(`${student.carnet} - ${student.first_name} ${student.last_name}`);
      }
    }
  }, [payment.student, students]);

  useEffect(() => {
    // Cerrar dropdown al hacer click fuera
    const handleClickOutside = (event: MouseEvent) => {
      if (studentSearchRef.current && !studentSearchRef.current.contains(event.target as Node)) {
        setShowStudentDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadStudents = async () => {
    setLoadingData(true);
    try {
      const response = await getStudents({ page_size: 1000, is_active: true });
      const data = response.data.results || response.data;
      setStudents(data);
    } catch (err) {
      console.error('Error loading students:', err);
      error('Error al cargar estudiantes');
    } finally {
      setLoadingData(false);
    }
  };

  const loadPaymentTypes = async () => {
    try {
      const response = await getPaymentTypes();
      const data = response.data.results || response.data;
      setPaymentTypes(data);
    } catch (err) {
      console.error('Error loading payment types:', err);
      error('Error al cargar tipos de pago');
    }
  };

  const handleStudentSelect = (student: Student) => {
    setPayment({ ...payment, student: student.id });
    setStudentSearch(`${student.carnet} - ${student.first_name} ${student.last_name}`);
    setShowStudentDropdown(false);
    setErrors({ ...errors, student: '' });
  };

  const handlePaymentTypeChange = (paymentTypeId: string) => {
    const paymentType = paymentTypes.find(pt => pt.id === paymentTypeId);
    setSelectedPaymentType(paymentType || null);
    setPayment({ ...payment, payment_type: paymentTypeId });
    
    // Si el tipo de pago tiene un monto fijo, establecerlo
    if (paymentType && paymentType.amount) {
      setPayment(prev => ({ ...prev, payment_type: paymentTypeId, amount: paymentType.amount!.toString() }));
    }
    
    setErrors({ ...errors, payment_type: '' });
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!payment.student) {
      newErrors.student = 'El estudiante es requerido';
    }
    if (!payment.payment_type) {
      newErrors.payment_type = 'El tipo de pago es requerido';
    }
    if (!payment.amount || parseFloat(payment.amount) <= 0) {
      newErrors.amount = 'El monto debe ser mayor a 0';
    }
    // Validar campos requeridos según el tipo de pago seleccionado
    if (selectedPaymentType) {
      if (selectedPaymentType.requires_month && !payment.month) {
        newErrors.month = 'El mes es requerido para este tipo de pago';
      }
      if (selectedPaymentType.requires_year && !payment.year) {
        newErrors.year = 'El año es requerido para este tipo de pago';
      }
    } else {
      if (!payment.month) {
        newErrors.month = 'El mes es requerido';
      }
      if (!payment.year || payment.year < 2020 || payment.year > 2100) {
        newErrors.year = 'El año debe ser válido';
      }
    }

    // Validaciones específicas por método de pago
    if (payment.payment_method === 'TRANSFERENCIA' && !receiptFile) {
      newErrors.receipt = 'El comprobante de transferencia es requerido';
    }
    if (payment.payment_method === 'EFECTIVO' && !payment.receipt_number.trim()) {
      newErrors.receipt_number = 'El número de recibo es requerido';
    }
    if (payment.payment_method === 'TARJETA') {
      if (!payment.card_last_four.trim()) {
        newErrors.card_last_four = 'Los últimos 4 dígitos de la tarjeta son requeridos';
      } else if (!/^\d{4}$/.test(payment.card_last_four)) {
        newErrors.card_last_four = 'Debe ser exactamente 4 dígitos';
      }
      if (!payment.transaction_id.trim()) {
        newErrors.transaction_id = 'El ID de transacción es requerido';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar tamaño (10MB máximo)
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        error('El archivo es demasiado grande. El tamaño máximo es 10MB.');
        return;
      }

      // Validar tipo de archivo
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
      if (!allowedTypes.includes(file.type)) {
        error('Tipo de archivo no permitido. Solo se permiten PDF, JPG y PNG.');
        return;
      }

      setReceiptFile(file);
      setErrors({ ...errors, receipt: '' });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    // Validar y convertir amount
    const amountValue = parseFloat(payment.amount.toString());
    if (isNaN(amountValue) || amountValue <= 0) {
      error('El monto debe ser un número válido mayor a 0');
      setLoading(false);
      return;
    }

    // Preparar datos del pago
    const paymentData: any = {
      student: payment.student,
      payment_type: payment.payment_type || null,
      payment_method: payment.payment_method,
      amount: amountValue, // Enviar como número (DRF acepta números para DecimalField)
      month: payment.month ? parseInt(payment.month.toString()) : null,
      year: payment.year ? parseInt(payment.year.toString()) : null,
    };

    // Agregar campos específicos según el método (solo si tienen valor)
    if (payment.payment_method === 'EFECTIVO' && payment.receipt_number.trim()) {
      paymentData.receipt_number = payment.receipt_number.trim();
    } else if (payment.payment_method === 'TARJETA') {
      if (payment.card_last_four.trim()) {
        paymentData.card_last_four = payment.card_last_four.trim();
      }
      if (payment.transaction_id.trim()) {
        paymentData.transaction_id = payment.transaction_id.trim();
      }
    }

    console.log('Sending payment data:', paymentData);

    try {
      // Crear el pago
      const response = await createPayment(paymentData);
      const createdPayment = response.data;

      // Si es transferencia y hay archivo, subirlo
      if (payment.payment_method === 'TRANSFERENCIA' && receiptFile) {
        await uploadPaymentReceipt(createdPayment.id, receiptFile);
      }

      success('Pago registrado exitosamente');
      setTimeout(() => navigate('/payments'), 1000);
    } catch (err: any) {
      console.error('Error creating payment:', err);
      console.error('Error response:', err.response?.data);
      console.error('Payment data sent:', paymentData);
      if (err.response?.data) {
        const errorData = err.response.data;
        if (typeof errorData === 'object' && !errorData.detail && !errorData.error) {
          // Si es un objeto con campos de error (serializer errors)
          setErrors(errorData);
          // Mostrar el primer error
          const firstError = Object.values(errorData)[0];
          const errorMessage = Array.isArray(firstError) ? firstError[0] : firstError;
          error(typeof errorMessage === 'string' ? errorMessage : 'Error al registrar el pago');
        } else {
          const errorMessage = errorData.detail || errorData.error || JSON.stringify(errorData);
          error(errorMessage);
        }
      } else {
        error('Error al registrar el pago');
      }
    } finally {
      setLoading(false);
    }
  };

  const selectedStudent = students.find(s => s.id === payment.student);

  if (loadingData) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando datos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-title">
          <FiDollarSign className="header-icon" />
          <div>
            <h1>Registrar Nuevo Pago</h1>
            <p className="header-subtitle">Registra un nuevo pago de estudiante</p>
          </div>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="payment-form">
          <div className="form-section">
            <h3 className="section-title">Información del Pago</h3>
            
            <div className="form-row">
              <div className="form-group student-search-group" ref={studentSearchRef}>
                <label>Estudiante *</label>
                <div className="student-search-container">
                  <FiSearch className="search-icon" />
                  <input
                    type="text"
                    value={studentSearch}
                    onChange={(e) => {
                      setStudentSearch(e.target.value);
                      if (!e.target.value) {
                        setPayment({ ...payment, student: '' });
                      }
                    }}
                    onFocus={() => {
                      if (studentSearch.trim() && filteredStudents.length > 0) {
                        setShowStudentDropdown(true);
                      }
                    }}
                    placeholder="Buscar por carnet, nombre o apellido..."
                    className={errors.student ? 'error' : ''}
                    required
                  />
                  {showStudentDropdown && filteredStudents.length > 0 && (
                    <div className="student-dropdown">
                      {filteredStudents.map((student) => (
                        <div
                          key={student.id}
                          className="student-dropdown-item"
                          onClick={() => handleStudentSelect(student)}
                        >
                          <div className="student-item-carnet">{student.carnet}</div>
                          <div className="student-item-name">
                            {student.first_name} {student.last_name}
                          </div>
                        </div>
                      ))}
                      {filteredStudents.length === 0 && studentSearch.trim() && (
                        <div className="student-dropdown-item no-results">
                          No se encontraron estudiantes
                        </div>
                      )}
                    </div>
                  )}
                </div>
                {errors.student && <span className="error-message">{errors.student}</span>}
                {selectedStudent && (
                  <p className="form-hint">Carnet: {selectedStudent.carnet}</p>
                )}
              </div>

              <div className="form-group">
                <label>Tipo de Pago *</label>
                <select
                  value={payment.payment_type}
                  onChange={(e) => handlePaymentTypeChange(e.target.value)}
                  className={errors.payment_type ? 'error' : ''}
                  required
                >
                  <option value="">Seleccione un tipo de pago</option>
                  {paymentTypes.map((paymentType) => (
                    <option key={paymentType.id} value={paymentType.id}>
                      {paymentType.name} ({paymentType.code})
                    </option>
                  ))}
                </select>
                {errors.payment_type && <span className="error-message">{errors.payment_type}</span>}
                {selectedPaymentType && selectedPaymentType.description && (
                  <p className="form-hint">{selectedPaymentType.description}</p>
                )}
              </div>
            </div>

            <div className="form-row">

              <div className="form-group">
                <label>Método de Pago *</label>
                <select
                  value={payment.payment_method}
                  onChange={(e) => {
                    setPayment({ 
                      ...payment, 
                      payment_method: e.target.value,
                      receipt_number: '',
                      card_last_four: '',
                      transaction_id: '',
                    });
                    setReceiptFile(null);
                    setErrors({});
                  }}
                  required
                >
                  <option value="TRANSFERENCIA">Transferencia</option>
                  <option value="TARJETA">Tarjeta</option>
                  <option value="EFECTIVO">Efectivo</option>
                </select>
              </div>
              <div className="form-group">
                <label>Monto *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={payment.amount}
                  onChange={(e) => setPayment({ ...payment, amount: e.target.value })}
                  className={`${errors.amount ? 'error' : ''} ${selectedPaymentType && selectedPaymentType.amount ? 'readonly-field' : ''}`}
                  placeholder="0.00"
                  readOnly={selectedPaymentType && selectedPaymentType.amount ? true : false}
                  required
                  title={selectedPaymentType && selectedPaymentType.amount ? 'El monto está determinado por el tipo de pago seleccionado' : ''}
                />
                {errors.amount && <span className="error-message">{errors.amount}</span>}
                {selectedPaymentType && selectedPaymentType.amount && (
                  <p className="form-hint">Monto fijo determinado por el tipo de pago</p>
                )}
              </div>

              {(!selectedPaymentType || selectedPaymentType.requires_month || selectedPaymentType.requires_year) && (
                <div className="form-row-inline">
                  {(!selectedPaymentType || selectedPaymentType.requires_month) && (
                    <div className="form-group">
                      <label>Mes {selectedPaymentType?.requires_month ? '*' : ''}</label>
                      <select
                        value={payment.month || ''}
                        onChange={(e) => setPayment({ ...payment, month: e.target.value ? parseInt(e.target.value) : undefined })}
                        className={errors.month ? 'error' : ''}
                        required={selectedPaymentType?.requires_month}
                      >
                        <option value="">Seleccione un mes</option>
                        {months.map((month) => (
                          <option key={month.value} value={month.value}>
                            {month.label}
                          </option>
                        ))}
                      </select>
                      {errors.month && <span className="error-message">{errors.month}</span>}
                    </div>
                  )}

                  {(!selectedPaymentType || selectedPaymentType.requires_year) && (
                    <div className="form-group">
                      <label>Año {selectedPaymentType?.requires_year ? '*' : ''}</label>
                      <input
                        type="number"
                        min="2020"
                        max="2100"
                        value={payment.year || ''}
                        onChange={(e) => setPayment({ ...payment, year: e.target.value ? parseInt(e.target.value) : undefined })}
                        className={errors.year ? 'error' : ''}
                        required={selectedPaymentType?.requires_year}
                      />
                      {errors.year && <span className="error-message">{errors.year}</span>}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Campos específicos según método de pago */}
          {payment.payment_method === 'TRANSFERENCIA' && (
            <div className="form-section">
              <h3 className="section-title">Comprobante de Transferencia</h3>
              <div className="form-group">
                <label>Comprobante de Transferencia *</label>
                <div className="file-upload-area">
                  <input
                    type="file"
                    id="receipt-upload"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    className="file-input"
                  />
                  <label htmlFor="receipt-upload" className="file-upload-label">
                    <FiUpload /> {receiptFile ? receiptFile.name : 'Seleccionar archivo'}
                  </label>
                  {receiptFile && (
                    <button
                      type="button"
                      className="btn-icon-small"
                      onClick={() => setReceiptFile(null)}
                      title="Eliminar archivo"
                    >
                      <FiX />
                    </button>
                  )}
                </div>
                {errors.receipt && <span className="error-message">{errors.receipt}</span>}
                <p className="form-hint">Formatos permitidos: PDF, JPG, PNG (máx. 10MB)</p>
              </div>
            </div>
          )}

          {payment.payment_method === 'EFECTIVO' && (
            <div className="form-section">
              <h3 className="section-title">Información de Recibo</h3>
              <div className="form-group">
                <label>Número de Recibo *</label>
                <input
                  type="text"
                  value={payment.receipt_number}
                  onChange={(e) => setPayment({ ...payment, receipt_number: e.target.value })}
                  className={errors.receipt_number ? 'error' : ''}
                  placeholder="Ej: REC-2024-001"
                  required
                />
                {errors.receipt_number && <span className="error-message">{errors.receipt_number}</span>}
              </div>
            </div>
          )}

          {payment.payment_method === 'TARJETA' && (
            <div className="form-section">
              <h3 className="section-title">Información de Tarjeta</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Últimos 4 dígitos de la tarjeta *</label>
                  <input
                    type="text"
                    maxLength={4}
                    value={payment.card_last_four}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, '');
                      setPayment({ ...payment, card_last_four: value });
                    }}
                    className={errors.card_last_four ? 'error' : ''}
                    placeholder="1234"
                    required
                  />
                  {errors.card_last_four && <span className="error-message">{errors.card_last_four}</span>}
                </div>

                <div className="form-group">
                  <label>ID de Transacción *</label>
                  <input
                    type="text"
                    value={payment.transaction_id}
                    onChange={(e) => setPayment({ ...payment, transaction_id: e.target.value })}
                    className={errors.transaction_id ? 'error' : ''}
                    placeholder="ID de la transacción"
                    required
                  />
                  {errors.transaction_id && <span className="error-message">{errors.transaction_id}</span>}
                </div>
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-large" disabled={loading}>
              {loading ? (
                <>
                  <FiLoader className="spinning" /> Guardando...
                </>
              ) : (
                <>
                  <FiSave /> Registrar Pago
                </>
              )}
            </button>
            <button type="button" className="btn btn-secondary btn-large" onClick={() => navigate('/payments')}>
              <FiX /> Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PaymentForm;


