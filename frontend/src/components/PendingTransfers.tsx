import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { paymentsApi, approvePayment, rejectPayment, uploadPaymentReceipt, updatePaymentReference, getPendingPaymentsCount } from '../services/api';
import { FiDollarSign, FiCheck, FiX, FiAlertCircle, FiDownload, FiUpload, FiEdit2, FiSave, FiArrowLeft } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import Pagination from './Pagination';
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
  amount: number | string;
  month_display: string;
  year: number;
  status: string;
  status_display: string;
  payment_date: string;
  transfer_receipt?: string | null;
  payment_reference?: string | null;
  career_name?: string | null;
  career_code?: string | null;
}

const PendingTransfers: React.FC = () => {
  const { success, error, warning } = useToast();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectNotes, setRejectNotes] = useState<string>('');
  const [showRejectModal, setShowRejectModal] = useState<string | null>(null);
  const [uploadingReceipt, setUploadingReceipt] = useState<string | null>(null);
  const receiptFileInputRef = useRef<{ [key: string]: HTMLInputElement | null }>({});
  const [editingReference, setEditingReference] = useState<string | null>(null);
  const [referenceValue, setReferenceValue] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const itemsPerPage = 20;

  const loadPayments = useCallback(async (page: number = 1, search: string = '') => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: itemsPerPage,
      };
      
      if (search && search.trim()) {
        params.search = search.trim();
      }

      const response = await paymentsApi.getPendingTransfers(params);
      const data = response.data;
      
      if (data.results) {
        setPayments(data.results);
        setTotalPages(Math.ceil(data.count / itemsPerPage));
        setTotalItems(data.count);
      } else {
        const paymentsArray = Array.isArray(data) ? data : [];
        setPayments(paymentsArray);
        setTotalPages(1);
        setTotalItems(paymentsArray.length);
      }
    } catch (err: any) {
      console.error('Error loading pending transfers:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error || 
                          'Error al cargar transferencias pendientes';
      error(errorMessage);
      setPayments([]);
      setTotalPages(1);
      setTotalItems(0);
    } finally {
      setLoading(false);
    }
  }, [error]);

  useEffect(() => {
    loadPayments(currentPage, searchQuery);
  }, [currentPage, loadPayments]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadPayments(1, searchQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setCurrentPage(1);
    loadPayments(1, '');
  };

  const handleApprove = async (id: string) => {
    setProcessingId(id);
    try {
      await approvePayment(id);
      // Recargar la lista para reflejar el cambio
      await loadPayments(currentPage, searchQuery);
      success('Transferencia aprobada exitosamente');
      
      // Si la lista queda vacía después de aprobar, volver a la primera página
      if (payments.length === 1 && currentPage > 1) {
        setCurrentPage(1);
        loadPayments(1, searchQuery);
      }
    } catch (err: any) {
      console.error('Error approving payment:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error || 
                          'Error al aprobar la transferencia';
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
      // Recargar la lista para reflejar el cambio
      await loadPayments(currentPage, searchQuery);
      setShowRejectModal(null);
      setRejectNotes('');
      success('Transferencia rechazada exitosamente');
      
      // Si la lista queda vacía después de rechazar, volver a la primera página
      if (payments.length === 1 && currentPage > 1) {
        setCurrentPage(1);
        loadPayments(1, searchQuery);
      }
    } catch (err: any) {
      console.error('Error rejecting payment:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error || 
                          'Error al rechazar la transferencia';
      error(errorMessage);
      // No cerrar el modal si hay error, para que el usuario pueda corregir
    } finally {
      setProcessingId(null);
    }
  };

  const formatAmount = (amount: number | string): string => {
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
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

  const handleDownloadReceipt = (receiptUrl: string) => {
    if (!receiptUrl) return;
    const fullUrl = receiptUrl.startsWith('http') 
      ? receiptUrl 
      : `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/${receiptUrl}`;
    window.open(fullUrl, '_blank');
  };

  const handleReceiptFileChange = async (paymentId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      error('El archivo es demasiado grande. El tamaño máximo es 10MB.');
      return;
    }

    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      error('Tipo de archivo no permitido. Solo se permiten PDF, JPG y PNG.');
      return;
    }

    setUploadingReceipt(paymentId);
    try {
      await uploadPaymentReceipt(paymentId, file);
      await loadPayments(currentPage, searchQuery);
      success('Comprobante subido exitosamente');
    } catch (err: any) {
      console.error('Error uploading receipt:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al subir el comprobante';
      error(errorMessage);
    } finally {
      setUploadingReceipt(null);
      if (receiptFileInputRef.current[paymentId]) {
        receiptFileInputRef.current[paymentId]!.value = '';
      }
    }
  };

  const handleStartEditReference = (payment: Payment) => {
    setEditingReference(payment.id);
    setReferenceValue(payment.payment_reference || '');
  };

  const handleCancelEditReference = () => {
    setEditingReference(null);
    setReferenceValue('');
  };

  const handleSaveReference = async (paymentId: string) => {
    setProcessingId(paymentId);
    try {
      await updatePaymentReference(paymentId, referenceValue);
      await loadPayments(currentPage, searchQuery);
      setEditingReference(null);
      setReferenceValue('');
      success('Referencia actualizada exitosamente');
    } catch (err: any) {
      console.error('Error updating reference:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al actualizar la referencia';
      error(errorMessage);
    } finally {
      setProcessingId(null);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando transferencias pendientes...</p>
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
              <h1>Transferencias Pendientes</h1>
              <p className="header-subtitle">
                {totalItems} transferencia{totalItems !== 1 ? 's' : ''} pendiente{totalItems !== 1 ? 's' : ''} de confirmación
              </p>
            </div>
          </div>
          <div className="header-actions">
            <Link to="/payments" className="btn btn-secondary">
              <FiArrowLeft /> Volver a Pagos
            </Link>
          </div>
        </div>
      </div>

      <div className="filters-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Buscar por nombre, carnet, referencia..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="btn btn-primary">
            Buscar
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="btn btn-secondary"
            >
              Limpiar
            </button>
          )}
        </form>
      </div>

      {payments.length === 0 ? (
        <div className="empty-state">
          <FiAlertCircle className="empty-icon" />
          <h2>No hay transferencias pendientes</h2>
          <p>Todas las transferencias han sido procesadas.</p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Estudiante</th>
                  <th>Carrera</th>
                  <th>Tipo de Pago</th>
                  <th>Monto</th>
                  <th>Referencia</th>
                  <th>Comprobante</th>
                  <th>Fecha</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr key={payment.id}>
                    <td>
                      <div>
                        <strong>{payment.student_name}</strong>
                        <br />
                        <small style={{ color: '#666' }}>Carnet: {payment.student_carnet}</small>
                      </div>
                    </td>
                    <td>
                      {payment.career_name ? (
                        <div>
                          <strong>{payment.career_name}</strong>
                          {payment.career_code && (
                            <>
                              <br />
                              <small style={{ color: '#666' }}>{payment.career_code}</small>
                            </>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: '#999' }}>N/A</span>
                      )}
                    </td>
                    <td>
                      {payment.payment_type_name ? (
                        <div>
                          <strong>{payment.payment_type_name}</strong>
                          {payment.payment_type_code && (
                            <>
                              <br />
                              <small style={{ color: '#666' }}>{payment.payment_type_code}</small>
                            </>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: '#999' }}>N/A</span>
                      )}
                    </td>
                    <td>
                      <strong>{formatAmount(payment.amount)}</strong>
                    </td>
                    <td>
                      {editingReference === payment.id ? (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <input
                            type="text"
                            value={referenceValue}
                            onChange={(e) => setReferenceValue(e.target.value)}
                            className="form-input"
                            style={{ width: '150px' }}
                            autoFocus
                          />
                          <button
                            onClick={() => handleSaveReference(payment.id)}
                            className="btn-icon"
                            disabled={processingId === payment.id}
                            title="Guardar"
                          >
                            <FiSave />
                          </button>
                          <button
                            onClick={handleCancelEditReference}
                            className="btn-icon"
                            title="Cancelar"
                          >
                            <FiX />
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span>{payment.payment_reference || 'Sin referencia'}</span>
                          <button
                            onClick={() => handleStartEditReference(payment)}
                            className="btn-icon"
                            title="Editar referencia"
                          >
                            <FiEdit2 />
                          </button>
                        </div>
                      )}
                    </td>
                    <td>
                      {payment.transfer_receipt ? (
                        <button
                          onClick={() => handleDownloadReceipt(payment.transfer_receipt!)}
                          className="btn-icon"
                          title="Ver comprobante"
                        >
                          <FiDownload />
                        </button>
                      ) : (
                        <div>
                          <input
                            type="file"
                            ref={(el) => {
                              receiptFileInputRef.current[payment.id] = el;
                            }}
                            onChange={(e) => handleReceiptFileChange(payment.id, e)}
                            accept=".pdf,.jpg,.jpeg,.png"
                            style={{ display: 'none' }}
                            id={`receipt-${payment.id}`}
                          />
                          <label
                            htmlFor={`receipt-${payment.id}`}
                            className="btn-icon"
                            title="Subir comprobante"
                            style={{ cursor: 'pointer' }}
                          >
                            {uploadingReceipt === payment.id ? (
                              <div className="spinner-small" />
                            ) : (
                              <FiUpload />
                            )}
                          </label>
                        </div>
                      )}
                    </td>
                    <td>{formatDate(payment.payment_date)}</td>
                    <td>
                      <span className={`status-badge status-${payment.status.toLowerCase()}`}>
                        {payment.status_display}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          onClick={() => handleApprove(payment.id)}
                          className="btn btn-success btn-sm"
                          disabled={processingId === payment.id}
                          title="Aprobar transferencia"
                        >
                          <FiCheck /> Aprobar
                        </button>
                        <button
                          onClick={() => setShowRejectModal(payment.id)}
                          className="btn btn-danger btn-sm"
                          disabled={processingId === payment.id}
                          title="Rechazar transferencia"
                        >
                          <FiX /> Rechazar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          )}
        </>
      )}

      {/* Modal de rechazo */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => setShowRejectModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Rechazar Transferencia</h2>
            <p>Por favor, ingrese el motivo del rechazo:</p>
            <textarea
              value={rejectNotes}
              onChange={(e) => setRejectNotes(e.target.value)}
              placeholder="Motivo del rechazo..."
              rows={4}
              className="form-textarea"
            />
            <div className="modal-actions">
              <button
                onClick={() => handleReject(showRejectModal)}
                className="btn btn-danger"
                disabled={!rejectNotes.trim() || processingId === showRejectModal}
              >
                Rechazar
              </button>
              <button
                onClick={() => {
                  setShowRejectModal(null);
                  setRejectNotes('');
                }}
                className="btn btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PendingTransfers;
