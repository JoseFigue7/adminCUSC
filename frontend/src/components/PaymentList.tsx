import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { getPayments, approvePayment, rejectPayment, uploadPaymentReceipt, updatePaymentReference, getPaymentTypes, getPendingPaymentsCount, paymentsApi } from '../services/api';
import { FiDollarSign, FiCheck, FiX, FiAlertCircle, FiPlus, FiDownload, FiUpload, FiArrowUp, FiArrowDown, FiEdit2, FiSave, FiCreditCard } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import Pagination from './Pagination';
import AdvancedSearch, { FilterParams } from './AdvancedSearch';
import PaymentDashboard from './PaymentDashboard';
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
  payment_reference?: string | null;
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
  const [editingReference, setEditingReference] = useState<string | null>(null);
  const [referenceValue, setReferenceValue] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;
  const [paymentTypes, setPaymentTypes] = useState<PaymentType[]>([]);
  const [ordering, setOrdering] = useState<string>('-payment_date');
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [exporting, setExporting] = useState<boolean>(false);
  const [showExportModal, setShowExportModal] = useState<boolean>(false);
  const [exportDateFrom, setExportDateFrom] = useState<string>('');
  const [exportDateTo, setExportDateTo] = useState<string>('');

  const loadPaymentTypes = useCallback(async () => {
    try {
      const response = await getPaymentTypes();
      const data = response.data.results || response.data;
      setPaymentTypes(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error loading payment types:', error);
    }
  }, []);

  const loadPendingCount = useCallback(async () => {
    try {
      const response = await getPendingPaymentsCount();
      setPendingCount(response.data.pending_count || 0);
    } catch (error) {
      console.error('Error loading pending count:', error);
      setPendingCount(0);
    }
  }, []);

  const loadPayments = useCallback(async (page: number = 1, filterParams: FilterParams = {}, orderBy: string = '-payment_date') => {
    setLoading(true);
    try {
      // Limpiar filtros vacíos o undefined antes de enviar
      const cleanFilters: FilterParams = {};
      Object.keys(filterParams).forEach(key => {
        const value = filterParams[key];
        if (value !== undefined && value !== null && value !== '') {
          cleanFilters[key] = value;
        }
      });
      
      const paramsWithOrdering = { ...cleanFilters, ordering: orderBy };
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
    } catch (error: any) {
      console.error('Error loading payments:', error);
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPaymentTypes();
    loadPendingCount();
  }, [loadPaymentTypes, loadPendingCount]); // Solo ejecutar una vez al montar

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

  const isPendingFilterActive = filters.pending === true || filters.pending === 'true';
  
  const loadPendingStudents = () => {
    // Aplicar filtro de estado pendiente (PENDIENTE y EN_REVISION)
    // Si ya está filtrado por pendientes, resetear filtros; si no, aplicar filtro
    if (isPendingFilterActive) {
      // Si ya está activo, resetear
      const newFilters = { ...filters };
      delete newFilters.pending;
      delete newFilters.status;
      setFilters(newFilters);
    } else {
      // Aplicar filtro de pendientes, limpiando otros filtros de estado
      const newFilters = { ...filters };
      delete newFilters.status; // Eliminar filtro de estado único si existe
      delete newFilters.status__in; // Limpiar el antiguo filtro si existe
      newFilters.pending = true;
      setFilters(newFilters);
    }
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
      // Actualizar conteo solo si estamos viendo pagos pendientes o no hay filtro de estado
      if (!filters.status || filters.pending) {
        await loadPendingCount();
      }
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
      // Actualizar conteo solo si estamos viendo pagos pendientes o no hay filtro de estado
      if (!filters.status || filters.pending) {
        await loadPendingCount();
      }
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
      await loadPayments(currentPage, filters, ordering);
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

  const handleOpenExportModal = () => {
    // Inicializar con las fechas de los filtros actuales si existen
    setExportDateFrom(filters.payment_date_from || '');
    setExportDateTo(filters.payment_date_to || '');
    setShowExportModal(true);
  };

  const handleCloseExportModal = () => {
    setShowExportModal(false);
    setExportDateFrom('');
    setExportDateTo('');
  };

  const handleExportCsv = async (useDateRange: boolean = false) => {
    setExporting(true);
    try {
      // Limpiar filtros vacíos antes de exportar
      const cleanFilters: FilterParams = {};
      Object.keys(filters).forEach(key => {
        const value = filters[key];
        if (value !== undefined && value !== null && value !== '') {
          cleanFilters[key] = value;
        }
      });
      
      // Si se especifica un rango de fechas para exportación, usarlo en lugar de los filtros
      if (useDateRange) {
        if (exportDateFrom) {
          cleanFilters.payment_date_from = exportDateFrom;
        } else {
          delete cleanFilters.payment_date_from;
        }
        if (exportDateTo) {
          cleanFilters.payment_date_to = exportDateTo;
        } else {
          delete cleanFilters.payment_date_to;
        }
      }
      
      // Agregar ordenamiento
      const params = { ...cleanFilters, ordering };
      
      const response = await paymentsApi.exportCsv(params);
      
      // Crear blob y descargar
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      // Generar nombre de archivo con rango de fechas si está disponible
      let filename = `pagos_${new Date().toISOString().split('T')[0]}.csv`;
      if (useDateRange && exportDateFrom && exportDateTo) {
        const fromDate = exportDateFrom.replace(/-/g, '');
        const toDate = exportDateTo.replace(/-/g, '');
        filename = `pagos_${fromDate}_${toDate}.csv`;
      } else if (useDateRange && exportDateFrom) {
        const fromDate = exportDateFrom.replace(/-/g, '');
        filename = `pagos_desde_${fromDate}.csv`;
      } else if (useDateRange && exportDateTo) {
        const toDate = exportDateTo.replace(/-/g, '');
        filename = `pagos_hasta_${toDate}.csv`;
      }
      
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      const dateRangeText = useDateRange && (exportDateFrom || exportDateTo) 
        ? ` (${exportDateFrom || 'inicio'} - ${exportDateTo || 'fin'})`
        : '';
      success(`Exportación exitosa${dateRangeText}`);
      
      // Cerrar el modal después de exportar
      if (useDateRange) {
        handleCloseExportModal();
      }
    } catch (err: any) {
      console.error('Error exporting payments:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al exportar pagos';
      error(errorMessage);
    } finally {
      setExporting(false);
    }
  };

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
            <button
              className="btn btn-secondary btn-large"
              onClick={handleOpenExportModal}
              disabled={exporting}
              title="Exportar pagos a CSV con rango de fechas"
            >
              <FiDownload /> {exporting ? 'Exportando...' : 'Exportar CSV'}
            </button>
            <Link to="/payments/new" className="btn btn-primary btn-large">
              <FiPlus /> Nuevo Pago
            </Link>
            {pendingCount > 0 && (
              <>
                <Link 
                  to="/payments/pending-transfers"
                  className="btn btn-warning btn-large"
                  title="Ver transferencias pendientes de confirmación"
                >
                  <FiCreditCard /> {pendingCount} Transferencias Pendientes
                </Link>
                <button 
                  className={`btn btn-large ${isPendingFilterActive ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={loadPendingStudents}
                  title={isPendingFilterActive ? "Quitar filtro de pendientes" : "Ver todos los pagos pendientes"}
                >
                  <FiAlertCircle /> Todos los Pendientes
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Dashboard de Estadísticas */}
      <PaymentDashboard />

      <div className="card" style={{ marginTop: '2rem' }}>
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
                  <th>Referencia</th>
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
                    <td className="reference-cell">
                      {editingReference === payment.id ? (
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                          <input
                            type="text"
                            value={referenceValue}
                            onChange={(e) => setReferenceValue(e.target.value)}
                            placeholder="Referencia..."
                            style={{
                              padding: '4px 8px',
                              borderRadius: '4px',
                              border: '1px solid var(--border-color)',
                              fontSize: '0.85rem',
                              width: '150px'
                            }}
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleSaveReference(payment.id);
                              } else if (e.key === 'Escape') {
                                handleCancelEditReference();
                              }
                            }}
                          />
                          <button
                            className="btn-icon-small btn-icon-success"
                            onClick={() => handleSaveReference(payment.id)}
                            disabled={processingId === payment.id}
                            title="Guardar"
                          >
                            {processingId === payment.id ? (
                              <div className="mini-spinner"></div>
                            ) : (
                              <FiSave />
                            )}
                          </button>
                          <button
                            className="btn-icon-small btn-icon-danger"
                            onClick={handleCancelEditReference}
                            disabled={processingId === payment.id}
                            title="Cancelar"
                          >
                            <FiX />
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.85rem', color: payment.payment_reference ? 'var(--text-color)' : 'var(--text-secondary)' }}>
                            {payment.payment_reference || '-'}
                          </span>
                          {(payment.status === 'PENDIENTE' || payment.status === 'EN_REVISION') && (
                            <button
                              className="btn-icon-small btn-icon-info"
                              onClick={() => handleStartEditReference(payment)}
                              title="Editar referencia"
                            >
                              <FiEdit2 />
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="receipt-cell">
                      {payment.transfer_receipt ? (
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
