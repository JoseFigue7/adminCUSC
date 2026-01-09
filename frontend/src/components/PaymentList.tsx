import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { getPayments, approvePayment, rejectPayment, uploadPaymentReceipt, getPaymentTypes } from '../services/api';
import { FiDollarSign, FiCheck, FiX, FiAlertCircle, FiPlus, FiDownload, FiUpload, FiArrowUp, FiArrowDown } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import Pagination from './Pagination';
import AdvancedSearch, { FilterParams } from './AdvancedSearch';
import './shared.css';
import './PaymentList.css';

interface Payment {
  id: string;
  student_name: string;
  student_carnet: string;
  payment_method: string;
  payment_method_display: string;
  payment_type_name?: string | null;
  payment_type_code?: string | null;
  amount: number | string; // Puede venir como string desde la API
  month_display: string;
  year: number;
  status: string;
  status_display: string;
  payment_date: string;
  transfer_receipt?: string | null;
}

interface PaymentType {
  id: string;
  code: string;
  name: string;
}

const PaymentList: React.FC = () => {
  const { success, error, warning } = useToast();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterParams>({});
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectNotes, setRejectNotes] = useState<string>('');
  const [showRejectModal, setShowRejectModal] = useState<string | null>(null);
  const [uploadingReceipt, setUploadingReceipt] = useState<string | null>(null);
  const receiptFileInputRef = useRef<{ [key: string]: HTMLInputElement | null }>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;
  const [paymentTypes, setPaymentTypes] = useState<PaymentType[]>([]);
  const [ordering, setOrdering] = useState<string>('-payment_date');

  const loadPaymentTypes = useCallback(async () => {
    try {
      const response = await getPaymentTypes();
      const data = response.data.results || response.data;
      setPaymentTypes(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading payment types:', error);
    }
  }, []);

  const loadPayments = useCallback(async (page: number = 1, filterParams: FilterParams = {}, orderBy: string = '-payment_date') => {
    setLoading(true);
    try {
      const paramsWithOrdering = { ...filterParams, ordering: orderBy };
      const response = await getPayments(page, itemsPerPage, paramsWithOrdering);
      const data = response.data;
      
      // Manejar respuesta paginada o no paginada
      if (data.results) {
        setPayments(data.results);
        setTotalPages(Math.ceil(data.count / itemsPerPage));
        setTotalItems(data.count);
      } else {
        // Si no hay paginación, tratar como array
        const paymentsArray = Array.isArray(data) ? data : [];
        setPayments(paymentsArray);
        setTotalPages(1);
        setTotalItems(paymentsArray.length);
      }
    } catch (error) {
      console.error('Error loading payments:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPaymentTypes();
  }, [loadPaymentTypes]);

  useEffect(() => {
    loadPayments(currentPage, filters, ordering);
  }, [currentPage, filters, ordering, loadPayments]);

  const handleFilterChange = (newFilters: FilterParams) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleResetFilters = () => {
    setFilters({});
    setCurrentPage(1);
  };

  const loadPendingStudents = () => {
    // Aplicar filtro de estado pendiente
    setFilters({ status: 'PENDIENTE' });
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleOrderingChange = (newOrdering: string) => {
    setOrdering(newOrdering);
    setCurrentPage(1); // Reset to first page when ordering changes
  };

  const getSortIcon = (field: string) => {
    if (ordering === field) {
      return <FiArrowDown style={{ marginLeft: '4px', display: 'inline-block' }} />;
    } else if (ordering === `-${field}`) {
      return <FiArrowUp style={{ marginLeft: '4px', display: 'inline-block' }} />;
    }
    return null;
  };

  const handleSort = (field: string) => {
    const newOrdering = ordering === field ? `-${field}` : field;
    handleOrderingChange(newOrdering);
  };

  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'APROBADO':
        return 'status-approved';
      case 'RECHAZADO':
        return 'status-rejected';
      default:
        return 'status-pending';
    }
  };

  const handleApprove = async (id: string) => {
    setProcessingId(id);
    try {
      await approvePayment(id);
      await loadPayments(currentPage, filters, ordering);
      success('Pago aprobado exitosamente');
    } catch (err: any) {
      console.error('Error approving payment:', err);
      const errorMessage = err.response?.data?.detail || 'Error al aprobar el pago';
      error(errorMessage);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: string) => {
    if (!rejectNotes.trim()) {
      warning('Por favor ingrese un motivo para el rechazo');
      return;
    }
    
    setProcessingId(id);
    try {
      await rejectPayment(id, rejectNotes);
      await loadPayments(currentPage, filters, ordering);
      setShowRejectModal(null);
      setRejectNotes('');
      success('Pago rechazado exitosamente');
    } catch (err: any) {
      console.error('Error rejecting payment:', err);
      const errorMessage = err.response?.data?.detail || 'Error al rechazar el pago';
      error(errorMessage);
    } finally {
      setProcessingId(null);
    }
  };

  const formatAmount = (amount: number | string): string => {
    // Convertir a número si viene como string
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    
    // Verificar que sea un número válido
    if (isNaN(numAmount) || numAmount === null || numAmount === undefined) {
      return 'MX$0.00';
    }
    
    return `MX$${numAmount.toFixed(2)}`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const handleDownloadReceipt = (receiptUrl: string, paymentId: string) => {
    if (!receiptUrl) return;
    
    // Construir la URL completa
    const fullUrl = receiptUrl.startsWith('http') 
      ? receiptUrl 
      : `http://localhost:8000/${receiptUrl}`;
    
    window.open(fullUrl, '_blank');
  };

  const handleReceiptFileChange = async (paymentId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

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

    setUploadingReceipt(paymentId);
    try {
      await uploadPaymentReceipt(paymentId, file);
      await loadPayments(currentPage, filters, ordering);
      success('Comprobante subido exitosamente');
    } catch (err: any) {
      console.error('Error uploading receipt:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al subir el comprobante';
      error(errorMessage);
    } finally {
      setUploadingReceipt(null);
      // Limpiar el input
      if (receiptFileInputRef.current[paymentId]) {
        receiptFileInputRef.current[paymentId]!.value = '';
      }
    }
  };

  const pendingCount = payments.filter(p => p.status === 'PENDIENTE' || p.status === 'EN_REVISION').length;

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando pagos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <FiDollarSign className="header-icon" />
            <div>
              <h1>Gestión de Pagos</h1>
              <p className="header-subtitle">Administra y aprueba los pagos de estudiantes</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <Link to="/payments/new" className="btn btn-primary btn-large">
              <FiPlus /> Nuevo Pago
            </Link>
            {pendingCount > 0 && (
              <button className="btn btn-warning btn-large" onClick={loadPendingStudents}>
                <FiAlertCircle /> {pendingCount} Pendientes
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <AdvancedSearch
          type="payments"
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
          paymentTypes={paymentTypes}
        />
        
        <div className="card-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div className="stats-badge">
            {totalItems} pago{totalItems !== 1 ? 's' : ''}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <label style={{ fontSize: '0.9rem', fontWeight: 500 }}>Ordenar por:</label>
            <select
              value={ordering}
              onChange={(e) => handleOrderingChange(e.target.value)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-color)',
                color: 'var(--text-color)',
                fontSize: '0.9rem',
                cursor: 'pointer'
              }}
            >
              <option value="-payment_date">Fecha (Más reciente primero)</option>
              <option value="payment_date">Fecha (Más antiguo primero)</option>
              <option value="-amount">Monto (Mayor a menor)</option>
              <option value="amount">Monto (Menor a mayor)</option>
              <option value="student_name">Nombre (A-Z)</option>
              <option value="-student_name">Nombre (Z-A)</option>
              <option value="-year">Año (Mayor a menor)</option>
              <option value="year">Año (Menor a mayor)</option>
            </select>
          </div>
        </div>

        {payments.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th 
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    onClick={() => handleSort('student_name')}
                  >
                    Estudiante {getSortIcon('student_name')}
                  </th>
                  <th>Carnet</th>
                  <th>Tipo de Pago</th>
                  <th>Método</th>
                  <th 
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    onClick={() => handleSort('amount')}
                  >
                    Monto {getSortIcon('amount')}
                  </th>
                  <th>Mes/Año</th>
                  <th 
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    onClick={() => handleSort('payment_date')}
                  >
                    Fecha {getSortIcon('payment_date')}
                  </th>
                  <th>Comprobante</th>
                  <th>Estado</th>
                  <th className="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id} className="table-row">
                    <td className="student-cell">
                      <strong>{payment.student_name}</strong>
                    </td>
                    <td>
                      <span className="carnet-badge">{payment.student_carnet}</span>
                    </td>
                    <td>
                      {payment.payment_type_name ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                            {payment.payment_type_name}
                          </span>
                          {payment.payment_type_code && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', opacity: 0.8 }}>
                              {payment.payment_type_code}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>N/A</span>
                      )}
                    </td>
                    <td>
                      <span className="method-badge">{payment.payment_method_display}</span>
                    </td>
                    <td className="amount-cell">
                      <strong>{formatAmount(payment.amount)}</strong>
                    </td>
                    <td>
                      {payment.month_display} {payment.year}
                    </td>
                    <td className="date-cell">
                      {formatDate(payment.payment_date)}
                    </td>
                    <td className="receipt-cell">
                      {payment.payment_method === 'TRANSFERENCIA' ? (
                        payment.transfer_receipt ? (
                          <button
                            className="btn-icon-small btn-icon-info"
                            onClick={() => handleDownloadReceipt(payment.transfer_receipt!, payment.id)}
                            title="Ver comprobante"
                          >
                            <FiDownload />
                          </button>
                        ) : (
                          <div className="receipt-upload-container">
                            <input
                              type="file"
                              id={`receipt-${payment.id}`}
                              accept=".pdf,.jpg,.jpeg,.png"
                              onChange={(e) => handleReceiptFileChange(payment.id, e)}
                              style={{ display: 'none' }}
                              ref={(el) => {
                                if (el) {
                                  receiptFileInputRef.current[payment.id] = el;
                                }
                              }}
                            />
                            <button
                              className="btn-icon-small btn-icon-warning"
                              onClick={() => document.getElementById(`receipt-${payment.id}`)?.click()}
                              disabled={uploadingReceipt === payment.id}
                              title="Subir comprobante"
                            >
                              {uploadingReceipt === payment.id ? (
                                <div className="mini-spinner"></div>
                              ) : (
                                <FiUpload />
                              )}
                            </button>
                          </div>
                        )
                      ) : (
                        <span className="no-receipt">-</span>
                      )}
                    </td>
                    <td>
                      <span className={`status-badge ${getStatusClass(payment.status)}`}>
                        {payment.status_display}
                      </span>
                    </td>
                    <td className="actions-cell">
                      {(payment.status === 'PENDIENTE' || payment.status === 'EN_REVISION') && (
                        <div className="action-buttons">
                          <button
                            className="btn-icon btn-icon-success"
                            onClick={() => handleApprove(payment.id)}
                            disabled={processingId === payment.id}
                            title="Aprobar"
                          >
                            {processingId === payment.id ? (
                              <div className="mini-spinner"></div>
                            ) : (
                              <FiCheck />
                            )}
                          </button>
                          <button
                            className="btn-icon btn-icon-danger"
                            onClick={() => setShowRejectModal(payment.id)}
                            disabled={processingId === payment.id}
                            title="Rechazar"
                          >
                            <FiX />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {totalPages > 1 && (
          <div style={{ marginTop: '2rem' }}>
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
              totalItems={totalItems}
              itemsPerPage={itemsPerPage}
            />
          </div>
        )}

        {payments.length === 0 && !loading ? (
          <div className="empty-state">
            <FiDollarSign className="empty-icon" />
            <h3>No se encontraron pagos</h3>
            <p>
              {Object.keys(filters).length > 0
                ? 'No hay pagos que coincidan con los filtros aplicados'
                : 'No hay pagos registrados en el sistema'}
            </p>
          </div>
        ) : null}
      </div>

      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Rechazar Pago</h3>
              <button className="modal-close" onClick={() => setShowRejectModal(null)}>×</button>
            </div>
            <div className="modal-body">
              <label>Motivo del rechazo *</label>
              <textarea
                value={rejectNotes}
                onChange={(e) => setRejectNotes(e.target.value)}
                placeholder="Ingrese el motivo por el cual se rechaza este pago..."
                autoFocus
              />
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setShowRejectModal(null);
                  setRejectNotes('');
                }}
              >
                Cancelar
              </button>
              <button
                className="btn btn-danger"
                onClick={() => handleReject(showRejectModal)}
                disabled={processingId === showRejectModal || !rejectNotes.trim()}
              >
                {processingId === showRejectModal ? 'Rechazando...' : 'Rechazar Pago'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentList;
