import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getStudent, paymentsApi } from '../services/api';
import { FiDollarSign, FiEye, FiCalendar, FiCreditCard, FiArrowLeft } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';

interface Payment {
  id: string;
  payment_date: string | null;
  payment_method: string;
  payment_method_display: string;
  status: string;
  status_display: string;
  amount: number;
  original_amount: number;
  scholarship_discount: number;
  penalty_amount: number;
  month: number | null;
  month_display: string | null;
  year: number | null;
  payment_type: {
    id: string;
    code: string;
    name: string;
  } | null;
  payment_reference: string;
  receipt_number: string;
  transfer_receipt: string | null;
  transaction_id: string;
  card_last_four: string;
  /** Si el API serializa payment_type como PK, vienen estos campos */
  payment_type_name?: string;
  payment_type_code?: string;
}

interface PendingDebt {
  month: number;
  month_display: string;
  year: number;
  amount: number;
  base_amount: number;
  penalty_amount: number;
  payment_type: {
    id: string;
    code: string;
    name: string;
  };
}

interface AccountingData {
  student: {
    id: string;
    carnet: string;
    full_name: string;
    email: string;
  };
  summary: {
    total_paid: number;
    total_debt: number;
    balance: number;
    total_payments: number;
    approved_payments: number;
    pending_payments: number;
  };
  pending_debts: PendingDebt[];
  payments: Payment[];
}

const EMPTY_SUMMARY: AccountingData['summary'] = {
  total_paid: 0,
  total_debt: 0,
  balance: 0,
  total_payments: 0,
  approved_payments: 0,
  pending_payments: 0,
};

/** Asegura la forma esperada si el API devolvió datos incompletos o otra ruta respondió 200. */
function normalizeAccountingPayload(raw: unknown): AccountingData {
  const r = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  const s = r.summary && typeof r.summary === 'object' ? (r.summary as Record<string, unknown>) : {};
  const st = r.student && typeof r.student === 'object' ? (r.student as Record<string, unknown>) : {};
  return {
    student: {
      id: String(st.id ?? ''),
      carnet: String(st.carnet ?? ''),
      full_name: String(st.full_name ?? ''),
      email: String(st.email ?? ''),
    },
    summary: {
      total_paid: Number(s.total_paid ?? 0),
      total_debt: Number(s.total_debt ?? 0),
      balance: Number(s.balance ?? 0),
      total_payments: Number(s.total_payments ?? 0),
      approved_payments: Number(s.approved_payments ?? 0),
      pending_payments: Number(s.pending_payments ?? 0),
    },
    pending_debts: Array.isArray(r.pending_debts) ? (r.pending_debts as PendingDebt[]) : [],
    payments: Array.isArray(r.payments) ? (r.payments as Payment[]) : [],
  };
}

function summaryForDisplay(data: AccountingData): AccountingData['summary'] {
  const s = data.summary;
  if (!s || typeof s !== 'object') {
    return { ...EMPTY_SUMMARY };
  }
  return {
    total_paid: Number(s.total_paid ?? 0),
    total_debt: Number(s.total_debt ?? 0),
    balance: Number(s.balance ?? 0),
    total_payments: Number(s.total_payments ?? 0),
    approved_payments: Number(s.approved_payments ?? 0),
    pending_payments: Number(s.pending_payments ?? 0),
  };
}

const StudentAccounting: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { error } = useToast();
  
  const [student, setStudent] = useState<any>(null);
  const [accountingData, setAccountingData] = useState<AccountingData | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (id) {
      loadData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- cargar al cambiar id
  }, [id]);

  const loadData = async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const [studentRes, accountingRes] = await Promise.all([
        getStudent(id),
        paymentsApi.getStudentAccounting(id)
      ]);
      
      setStudent(studentRes.data);
      setAccountingData(normalizeAccountingPayload(accountingRes.data));
    } catch (err: any) {
      console.error('Error loading data:', err);
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.detail || 
                          'Error al cargar los datos';
      error(errorMessage);
      
      if (err.response?.status === 404) {
        navigate('/students');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const handleDownloadReceipt = (payment: Payment) => {
    if (payment.transfer_receipt) {
      window.open(payment.transfer_receipt, '_blank');
    } else {
      error('No hay comprobante disponible para este pago');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!student || !accountingData) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiDollarSign className="empty-icon" />
          <h3>No se encontró información</h3>
          <p>No se pudo cargar la información del estudiante o su estado de cuenta.</p>
          <button onClick={() => navigate('/students')} className="btn btn-primary">
            <FiArrowLeft /> Volver a Estudiantes
          </button>
        </div>
      </div>
    );
  }

  const summary = summaryForDisplay(accountingData);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <FiDollarSign className="header-icon" />
            <div>
              <h1>Estado de Cuenta</h1>
              <p className="header-subtitle">
                {student.full_name || `${student.first_name} ${student.first_last_name || student.last_name || ''} ${student.second_last_name || ''}`.trim()} - {student.carnet} | {student.career_name}
              </p>
            </div>
          </div>
          <div className="header-actions">
            <button 
              onClick={() => navigate(`/students/${id}`)} 
              className="btn btn-secondary btn-large"
            >
              <FiArrowLeft /> Volver
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="profile-section">
          <h3 className="section-title">Estado de Cuenta</h3>
          
          {/* Resumen */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '1rem',
            marginBottom: '2rem',
            padding: '1rem',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)'
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Total Pagado
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#10b981' }}>
                {formatCurrency(summary.total_paid)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Deudas Pendientes
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#ef4444' }}>
                {formatCurrency(summary.total_debt)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Balance
              </div>
              <div style={{ 
                fontSize: '1.5rem', 
                fontWeight: '600', 
                color: summary.balance >= 0 ? '#10b981' : '#ef4444'
              }}>
                {formatCurrency(summary.balance)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Pagos Totales
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                {summary.total_payments}
              </div>
            </div>
          </div>

          {/* Deudas Pendientes */}
          {accountingData.pending_debts && accountingData.pending_debts.length > 0 && (
            <div style={{ marginBottom: '2rem' }}>
              <h4 style={{ marginBottom: '1rem', fontSize: '1.1rem', fontWeight: '600' }}>
                Deudas Pendientes
              </h4>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Mes/Año</th>
                      <th>Tipo de Pago</th>
                      <th>Monto Base</th>
                      <th>Mora</th>
                      <th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accountingData.pending_debts.map((debt, index) => (
                      <tr key={index}>
                        <td>{debt.month_display} {debt.year}</td>
                        <td>{debt.payment_type?.name || 'N/A'}</td>
                        <td>{formatCurrency(debt.base_amount)}</td>
                        <td>{formatCurrency(debt.penalty_amount)}</td>
                        <td style={{ fontWeight: '600', color: '#ef4444' }}>
                          {formatCurrency(debt.amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Historial de Pagos */}
          <div>
            <h4 style={{ marginBottom: '1rem', fontSize: '1.1rem', fontWeight: '600' }}>
              Historial de Pagos
            </h4>
            {accountingData.payments && accountingData.payments.length > 0 ? (
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Método</th>
                      <th>Tipo</th>
                      <th>Mes/Año</th>
                      <th>Monto</th>
                      <th>Estado</th>
                      <th>Comprobante</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accountingData.payments.map((payment) => (
                      <tr key={payment.id}>
                        <td>
                          {payment.payment_date ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <FiCalendar style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }} />
                              {new Date(payment.payment_date).toLocaleDateString('es-MX')}
                            </div>
                          ) : (
                            'N/A'
                          )}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <FiCreditCard style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }} />
                            {payment.payment_method_display}
                          </div>
                        </td>
                        <td>
                          {payment.payment_type &&
                          typeof payment.payment_type === 'object' &&
                          payment.payment_type !== null ? (
                            <div>
                              <div style={{ fontWeight: '500' }}>{payment.payment_type.name}</div>
                              {payment.payment_type.code && (
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                  {payment.payment_type.code}
                                </div>
                              )}
                            </div>
                          ) : (
                            <div>
                              <div style={{ fontWeight: '500' }}>
                                {payment.payment_type_name ?? 'N/A'}
                              </div>
                              {payment.payment_type_code ? (
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                  {payment.payment_type_code}
                                </div>
                              ) : null}
                            </div>
                          )}
                        </td>
                        <td>
                          {payment.month_display && payment.year ? (
                            `${payment.month_display} ${payment.year}`
                          ) : (
                            'N/A'
                          )}
                        </td>
                        <td style={{ fontWeight: '600' }}>
                          {formatCurrency(payment.amount)}
                        </td>
                        <td>
                          <span className={`status-badge status-${payment.status.toLowerCase().replace('_', '-')}`}>
                            {payment.status_display}
                          </span>
                        </td>
                        <td>
                          {payment.transfer_receipt ? (
                            <button
                              onClick={() => handleDownloadReceipt(payment)}
                              className="btn-icon btn-icon-primary"
                              title="Ver Comprobante"
                            >
                              <FiEye />
                            </button>
                          ) : (
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                              No disponible
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ 
                padding: '2rem', 
                textAlign: 'center', 
                color: 'var(--text-secondary)',
                background: 'var(--bg-secondary)',
                borderRadius: 'var(--radius-md)'
              }}>
                No hay pagos registrados
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentAccounting;
