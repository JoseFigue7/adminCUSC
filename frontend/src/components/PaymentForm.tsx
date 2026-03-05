import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStudents, createPayment, updatePayment, uploadPaymentReceipt, getPaymentTypes, findOldestUnpaidPayment, paymentsApi } from '../services/api';
import { FiDollarSign, FiSave, FiX, FiLoader, FiUpload, FiSearch, FiAlertCircle } from '../utils/icons';
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
  const [foundPayment, setFoundPayment] = useState<any>(null);
  const [searchingPayment, setSearchingPayment] = useState(false);
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

  const loadStudents = useCallback(async () => {
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
  }, [error]);

  const loadPaymentTypes = useCallback(async () => {
    try {
      const response = await getPaymentTypes();
      const data = response.data.results || response.data;
      setPaymentTypes(data);
    } catch (err) {
      console.error('Error loading payment types:', err);
      error('Error al cargar tipos de pago');
    }
  }, [error]);

  useEffect(() => {
    loadStudents();
    loadPaymentTypes();
  }, [loadStudents, loadPaymentTypes]);

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
  }, [payment.student, students, studentSearch]);

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
  }, [studentSearch]);

  const handleStudentSelect = async (student: Student) => {
    setPayment({ ...payment, student: student.id });
    setStudentSearch(`${student.carnet} - ${student.first_name} ${student.last_name}`);
    setShowStudentDropdown(false);
    setErrors({ ...errors, student: '' });
    setFoundPayment(null);
    
    // Si ya hay un tipo de pago seleccionado
    if (payment.payment_type) {
      const paymentType = paymentTypes.find(pt => pt.id === payment.payment_type);
      
      // Si es el pago 101, obtener el monto del backend
      if (paymentType && paymentType.code === '101') {
        try {
          const response = await paymentsApi.getPaymentAmount(student.id, payment.payment_type);
          const amountData = response.data;
          setPayment(prev => ({
            ...prev,
            student: student.id,
            amount: amountData.amount ? amountData.amount.toString() : prev.amount,
          }));
        } catch (err: any) {
          console.error('Error obteniendo monto del pago:', err);
          // Si hay error, continuar sin establecer el monto
        }
      }
      
      // Solo buscar pagos pendientes para colegiaturas mensuales (102, 103, 105)
      // Estos son los únicos tipos de pago que pueden tener pagos pendientes preexistentes
      if (paymentType && ['102', '103', '105'].includes(paymentType.code)) {
        await searchOldestUnpaidPayment(student.id, payment.payment_type);
      }
    }
  };

  const handlePaymentTypeChange = async (paymentTypeId: string) => {
    const paymentType = paymentTypes.find(pt => pt.id === paymentTypeId);
    setSelectedPaymentType(paymentType || null);
    
    // Si es el pago 100 (gratis), establecer monto en 0, método efectivo y limpiar foundPayment
    if (paymentType && paymentType.code === '100') {
      setPayment(prev => ({ 
        ...prev, 
        payment_type: paymentTypeId,
        amount: '0.00',
        payment_method: 'EFECTIVO',
        receipt_number: '',
        card_last_four: '',
        transaction_id: ''
      }));
      setFoundPayment(null); // No mostrar pago encontrado para pago gratis
      setReceiptFile(null); // Limpiar archivo de recibo
    } else {
      setPayment({ ...payment, payment_type: paymentTypeId });
      setFoundPayment(null);
      
      // Si es el pago 101 y hay estudiante seleccionado, obtener el monto del backend
      if (paymentType && paymentType.code === '101' && payment.student) {
        try {
          const response = await paymentsApi.getPaymentAmount(payment.student, paymentTypeId);
          const amountData = response.data;
          setPayment(prev => ({
            ...prev,
            amount: amountData.amount ? amountData.amount.toString() : prev.amount,
          }));
        } catch (err: any) {
          console.error('Error obteniendo monto del pago:', err);
          // Si hay error, no establecer el monto, el usuario lo puede ingresar manualmente
        }
      }
      
      // Solo buscar pagos pendientes para colegiaturas mensuales (102, 103, 105)
      // Estos son los únicos tipos de pago que pueden tener pagos pendientes preexistentes
      if (payment.student && paymentTypeId && paymentType && ['102', '103', '105'].includes(paymentType.code)) {
        await searchOldestUnpaidPayment(payment.student, paymentTypeId);
      }
    }
    setErrors({ ...errors, payment_type: '' });
  };

  const searchOldestUnpaidPayment = async (studentId: string, paymentTypeId: string) => {
    setSearchingPayment(true);
    setErrors({ ...errors, payment_type: '' });
    try {
      const response = await findOldestUnpaidPayment(studentId, paymentTypeId);
      const found = response.data;
      setFoundPayment(found);
      
      // Actualizar el estado del pago con la información encontrada
      setPayment(prev => ({
        ...prev,
        month: found.month || undefined,
        year: found.year || undefined,
        amount: found.final_amount ? found.final_amount.toString() : (found.amount ? found.amount.toString() : prev.amount),
      }));
    } catch (err: any) {
      if (err.response?.status === 404) {
        const debugInfo = err.response?.data?.debug_info;
        let errorMsg = 'No se encontró ningún pago pendiente para este estudiante y tipo de pago';
        
        if (debugInfo) {
          console.log('Debug info:', debugInfo);
          if (debugInfo.total_payments === 0) {
            errorMsg = 'No se han generado pagos para este estudiante. Primero debe confirmar la asignación de cursos.';
          } else if (debugInfo.approved_payments === debugInfo.total_payments) {
            errorMsg = 'Todos los pagos de este tipo ya están aprobados.';
          } else {
            errorMsg = `No hay pagos pendientes. Total: ${debugInfo.total_payments}, Aprobados: ${debugInfo.approved_payments}, Pendientes: ${debugInfo.pending_payments}`;
          }
        }
        
        setErrors({ ...errors, payment_type: errorMsg });
        setFoundPayment(null);
        // No mostrar toast de error aquí, solo establecer el error en el campo
      } else {
        console.error('Error searching payment:', err);
        const errorMsg = err.response?.data?.error || 'Error al buscar el pago pendiente';
        setErrors({ ...errors, payment_type: errorMsg });
        setFoundPayment(null);
      }
    } finally {
      setSearchingPayment(false);
    }
  };


  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    // Verificar si es pago 100 (gratis) - declarar una sola vez
    const isFreePayment = selectedPaymentType?.code === '100';
    // Verificar si es un tipo de pago que puede crear nuevos pagos sin foundPayment
    const canCreateNewPayment = isFreePayment || selectedPaymentType?.code === '101' || !['102', '103', '105'].includes(selectedPaymentType?.code || '');

    if (!payment.student) {
      newErrors.student = 'El estudiante es requerido';
    }
    if (!payment.payment_type) {
      newErrors.payment_type = 'El tipo de pago es requerido';
    }
    // Para pagos 100, 101 y otros que no sean colegiaturas mensuales, no se requiere foundPayment
    // Solo las colegiaturas mensuales (102, 103, 105) requieren foundPayment
    if (!foundPayment && !canCreateNewPayment) {
      newErrors.payment_type = 'No se encontró un pago pendiente para procesar';
    }
    // Para pago 100 (gratis), permitir monto 0
    if (!payment.amount || (parseFloat(payment.amount) < 0 || (!isFreePayment && parseFloat(payment.amount) <= 0))) {
      newErrors.amount = isFreePayment ? 'El monto debe ser 0 para pago gratis' : 'El monto debe ser mayor a 0';
    }

    // Validaciones específicas por método de pago (no aplican para pago 100 gratis)
    if (!isFreePayment) {
      // El comprobante de transferencia ya no es requerido, funciona igual que el efectivo
      // El número de recibo se genera automáticamente para efectivo, no es requerido
      // if (payment.payment_method === 'EFECTIVO' && !payment.receipt_number.trim()) {
      //   newErrors.receipt_number = 'El número de recibo es requerido';
      // }
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

    // Verificar si es pago 100 (gratis)
    const isFreePayment = selectedPaymentType?.code === '100';

    // Validar y convertir amount (permitir 0 para pago gratis)
    const amountValue = parseFloat(payment.amount.toString());
    if (isNaN(amountValue) || amountValue < 0 || (!isFreePayment && amountValue <= 0)) {
      error(isFreePayment ? 'El monto debe ser 0 para pago gratis' : 'El monto debe ser un número válido mayor a 0');
      setLoading(false);
      return;
    }

    // Si hay foundPayment, actualizar el pago existente
    if (foundPayment) {
      // Preparar datos para actualizar el pago encontrado
      const paymentData: any = {
        payment_method: payment.payment_method,
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

      console.log('Updating payment data:', paymentData);

      try {
        // Actualizar el pago encontrado (el backend manejará la aprobación automática según el método)
        const response = await updatePayment(foundPayment.id, paymentData);
        const updatedPayment = response.data;

        // Si es transferencia y hay archivo, subirlo
        if (payment.payment_method === 'TRANSFERENCIA' && receiptFile) {
          await uploadPaymentReceipt(updatedPayment.id, receiptFile);
        }

        success('Pago registrado exitosamente. El recibo se ha enviado por correo electrónico.');
        
        // Descargar el recibo automáticamente
        try {
          const receiptResponse = await paymentsApi.downloadReceipt(updatedPayment.id);
          const blob = new Blob([receiptResponse.data], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `recibo_${updatedPayment.receipt_number || updatedPayment.id}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        } catch (err) {
          console.error('Error al descargar recibo:', err);
          // No mostrar error al usuario, solo log
        }
        
        // Limpiar el estado antes de navegar
        setFoundPayment(null);
        setPayment({
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
        setTimeout(() => navigate('/payments'), 2000);
      } catch (err: any) {
        console.error('Error updating payment:', err);
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
    } else if (isFreePayment) {
      // Crear nuevo pago para pago 100 (gratis)
      const paymentData: any = {
        student: payment.student,
        payment_type: payment.payment_type,
        payment_method: payment.payment_method,
        original_amount: amountValue,
        amount: amountValue,  // También enviar amount para compatibilidad
        final_amount: amountValue,  // También enviar final_amount
        year: payment.year,
      };

      // Agregar campos opcionales si existen
      if (payment.month) {
        paymentData.month = payment.month;
      }

      console.log('Creating free payment (100):', paymentData);

      try {
        // Crear el pago nuevo (el backend lo aprobará automáticamente si es pago 100)
        const response = await createPayment(paymentData);
        const createdPayment = response.data;

        success('Pago gratuito registrado exitosamente. El recibo se ha enviado por correo electrónico.');
        
        // Descargar el recibo automáticamente
        try {
          const receiptResponse = await paymentsApi.downloadReceipt(createdPayment.id);
          const blob = new Blob([receiptResponse.data], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `recibo_${createdPayment.receipt_number || createdPayment.id}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        } catch (err) {
          console.error('Error al descargar recibo:', err);
          // No mostrar error al usuario, solo log
        }
        
        // Limpiar el estado antes de navegar
        setPayment({
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
        setTimeout(() => navigate('/payments'), 2000);
      } catch (err: any) {
        console.error('Error creating free payment:', err);
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
    } else {
      // Verificar si es pago 100 o 101 para usar el endpoint específico
      const isEnrollmentPayment = selectedPaymentType?.code === '100' || selectedPaymentType?.code === '101';
      
      if (isEnrollmentPayment) {
        // Usar endpoint específico para pagos de inscripción (más simple y directo)
        const paymentData: any = {
          student: payment.student,
          payment_type: payment.payment_type,
          payment_method: payment.payment_method,
          original_amount: amountValue,
          year: payment.year,
        };

        // Agregar campos opcionales si existen
        if (payment.month) {
          paymentData.month = payment.month;
        }

        // Agregar campos específicos según el método de pago
        if (payment.payment_method === 'EFECTIVO' && payment.receipt_number.trim()) {
          paymentData.receipt_number = payment.receipt_number.trim();
        }

        console.log('Creating enrollment payment (100/101):', paymentData);

        try {
          // Usar el endpoint específico para pagos de inscripción
          const response = await paymentsApi.createEnrollmentPayment(paymentData);
          const createdPayment = response.data;
          
          success('Pago de inscripción registrado exitosamente. El recibo se ha enviado por correo electrónico.');
          
          // Descargar el recibo automáticamente
          try {
            const receiptResponse = await paymentsApi.downloadReceipt(createdPayment.id);
            const blob = new Blob([receiptResponse.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `recibo_${createdPayment.receipt_number || createdPayment.id}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
          } catch (err) {
            console.error('Error al descargar recibo:', err);
            // No mostrar error al usuario, solo log
          }
          
          // Limpiar el estado antes de navegar
          setPayment({
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
          setFoundPayment(null);
          setReceiptFile(null);
          setTimeout(() => navigate('/payments'), 2000);
          return;
        } catch (err: any) {
          console.error('Error creating enrollment payment:', err);
          console.error('Error response:', err.response?.data);
          if (err.response?.data) {
            const errorData = err.response.data;
            const errorMessage = errorData.error || errorData.detail || JSON.stringify(errorData);
            error(errorMessage);
          } else {
            error('Error al registrar el pago de inscripción');
          }
          setLoading(false);
          return;
        }
      }
      
      // Para otros tipos de pago, usar el endpoint normal
      const paymentData: any = {
        student: payment.student,
        payment_type: payment.payment_type,
        payment_method: payment.payment_method,
        original_amount: amountValue,
        amount: amountValue,  // También enviar amount para compatibilidad
        final_amount: amountValue,  // También enviar final_amount
        year: payment.year,
      };

      // Agregar campos opcionales si existen
      if (payment.month) {
        paymentData.month = payment.month;
      }

      // Agregar campos específicos según el método de pago
      if (payment.payment_method === 'EFECTIVO' && payment.receipt_number.trim()) {
        paymentData.receipt_number = payment.receipt_number.trim();
      } else if (payment.payment_method === 'TARJETA') {
        if (payment.card_last_four.trim()) {
          paymentData.card_last_four = payment.card_last_four.trim();
        }
        if (payment.transaction_id.trim()) {
          paymentData.transaction_id = payment.transaction_id.trim();
        }
      } else if (payment.payment_method === 'TRANSFERENCIA' && payment.receipt_number.trim()) {
        paymentData.payment_reference = payment.receipt_number.trim();
      }

      console.log('Creating new payment:', paymentData);

      try {
        // Crear el pago nuevo
        const response = await createPayment(paymentData);
        const createdPayment = response.data;

        // Si es transferencia y hay archivo, subirlo
        if (payment.payment_method === 'TRANSFERENCIA' && receiptFile) {
          await uploadPaymentReceipt(createdPayment.id, receiptFile);
        }

        success('Pago registrado exitosamente. El recibo se ha enviado por correo electrónico.');
        
        // Descargar el recibo automáticamente
        try {
          const receiptResponse = await paymentsApi.downloadReceipt(createdPayment.id);
          const blob = new Blob([receiptResponse.data], { type: 'application/pdf' });
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `recibo_${createdPayment.receipt_number || createdPayment.id}.pdf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
        } catch (err) {
          console.error('Error al descargar recibo:', err);
          // No mostrar error al usuario, solo log
        }
        
        // Limpiar el estado antes de navegar
        setPayment({
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
        setFoundPayment(null);
        setReceiptFile(null);
        setTimeout(() => navigate('/payments'), 2000);
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
                  disabled={selectedPaymentType?.code === '100'}
                  required
                >
                  <option value="TRANSFERENCIA">Transferencia</option>
                  <option value="TARJETA">Tarjeta</option>
                  <option value="EFECTIVO">Efectivo</option>
                </select>
                {selectedPaymentType?.code === '100' && (
                  <p className="form-hint" style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Para pagos gratuitos solo se permite efectivo
                  </p>
                )}
              </div>
              <div className="form-group">
                <label>Monto *</label>
                <input
                  type="number"
                  step="0.01"
                  min={selectedPaymentType?.code === '100' ? '0' : '0.01'}
                  value={payment.amount}
                  onChange={(e) => setPayment({ ...payment, amount: e.target.value })}
                  className={`${errors.amount ? 'error' : ''} ${selectedPaymentType?.code === '100' ? '' : 'readonly-field'}`}
                  placeholder="0.00"
                  readOnly={selectedPaymentType?.code !== '100'}
                  required
                  title={selectedPaymentType?.code === '100' ? 'Pago gratis - monto fijo en 0' : 'El monto se calcula automáticamente según el pago encontrado (incluye mora si aplica)'}
                />
                {errors.amount && <span className="error-message">{errors.amount}</span>}
                {selectedPaymentType?.code === '100' && (
                  <p className="form-hint" style={{ color: 'var(--success-color)' }}>
                    Este es un pago gratuito (0 MXN)
                  </p>
                )}
                {foundPayment && foundPayment.penalty_amount > 0 && selectedPaymentType?.code !== '100' && (
                  <p className="form-hint" style={{ color: 'var(--warning-color)' }}>
                    <FiAlertCircle /> Incluye mora de ${foundPayment.penalty_amount}
                  </p>
                )}
              </div>

              {/* Mostrar información del pago encontrado (solo si NO es pago 100) */}
              {foundPayment && selectedPaymentType?.code !== '100' && (
                <div className="form-section" style={{ 
                  background: 'var(--bg-secondary)', 
                  padding: '1rem', 
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  marginTop: '1rem'
                }}>
                  <h4 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)' }}>Pago Encontrado:</h4>
                  <div className="form-row" style={{ gap: '1rem' }}>
                    <div>
                      <strong>Mes:</strong> {foundPayment.month_display || months.find(m => m.value === foundPayment.month)?.label || 'N/A'}
                    </div>
                    <div>
                      <strong>Año:</strong> {foundPayment.year || 'N/A'}
                    </div>
                    <div>
                      <strong>Fecha límite:</strong> {foundPayment.due_date ? new Date(foundPayment.due_date).toLocaleDateString('es-ES') : 'N/A'}
                    </div>
                  </div>
                  {foundPayment.penalty_amount > 0 && (
                    <div style={{ marginTop: '0.5rem', color: 'var(--warning-color)', fontWeight: 600 }}>
                      ⚠️ Este pago tiene mora aplicada por pasar la fecha límite
                    </div>
                  )}
                </div>
              )}

              {searchingPayment && selectedPaymentType?.code !== '100' && (
                <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <FiLoader className="spinning" /> Buscando pago pendiente...
                </div>
              )}
            </div>
          </div>

          {/* Campos específicos según método de pago */}
          {payment.payment_method === 'TRANSFERENCIA' && (
            <div className="form-section">
              <h3 className="section-title">Comprobante de Transferencia</h3>
              <div className="form-group">
                <label>Comprobante de Transferencia (Opcional)</label>
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

          {/* El número de recibo se genera automáticamente para efectivo, no se muestra el campo */}
          {/* {payment.payment_method === 'EFECTIVO' && selectedPaymentType?.code !== '100' && (
            <div className="form-section">
              <h3 className="section-title">Información de Recibo</h3>
              <div className="form-group">
                <label>Número de Recibo</label>
                <input
                  type="text"
                  value={payment.receipt_number}
                  onChange={(e) => setPayment({ ...payment, receipt_number: e.target.value })}
                  className={errors.receipt_number ? 'error' : ''}
                  placeholder="Se generará automáticamente"
                  disabled
                />
                <p className="form-hint" style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  El número de recibo se generará automáticamente al registrar el pago
                </p>
              </div>
            </div>
          )} */}

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


