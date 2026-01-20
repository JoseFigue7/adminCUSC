import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { changePassword } from '../services/authApi';
import { paymentsApi } from '../services/api';
import { FiUser, FiLock, FiSave, FiLoader, FiDollarSign, FiDownload, FiEye, FiCalendar, FiCreditCard } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './UserProfile.css';

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

const UserProfile: React.FC = () => {
  const { user } = useAuth();
  const { success, error } = useToast();
  
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [accountingData, setAccountingData] = useState<AccountingData | null>(null);
  const [loadingAccounting, setLoadingAccounting] = useState(false);
  const [showAccounting, setShowAccounting] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validaciones
    const newErrors: Record<string, string> = {};
    
    if (!passwordData.old_password) {
      newErrors.old_password = 'La contraseña actual es requerida';
    }
    if (!passwordData.new_password) {
      newErrors.new_password = 'La nueva contraseña es requerida';
    } else if (passwordData.new_password.length < 8) {
      newErrors.new_password = 'La contraseña debe tener al menos 8 caracteres';
    }
    if (passwordData.new_password !== passwordData.new_password_confirm) {
      newErrors.new_password_confirm = 'Las contraseñas no coinciden';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      await changePassword(passwordData.old_password, passwordData.new_password);
      success('Contraseña actualizada exitosamente');
      setPasswordData({
        old_password: '',
        new_password: '',
        new_password_confirm: '',
      });
    } catch (err: any) {
      console.error('Password change error:', err);
      const errorMessage = err.response?.data?.error || 
                          err.response?.data?.detail || 
                          'Error al cambiar la contraseña';
      error(errorMessage);
      if (err.response?.data) {
        setErrors(err.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadAccounting = async () => {
    if (accountingData) {
      setShowAccounting(!showAccounting);
      return;
    }

    setLoadingAccounting(true);
    try {
      const response = await paymentsApi.getMyAccounting();
      setAccountingData(response.data);
      setShowAccounting(true);
    } catch (err: any) {
      console.error('Error loading accounting:', err);
      if (err.response?.status === 404) {
        // No se encontró estudiante asociado, no mostrar error
        setAccountingData(null);
        setShowAccounting(false);
      } else {
        const errorMessage = err.response?.data?.error || 
                            err.response?.data?.detail || 
                            'Error al cargar la contabilidad';
        error(errorMessage);
      }
    } finally {
      setLoadingAccounting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(amount);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (!user) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando perfil...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-title">
          <FiUser className="header-icon" />
          <div>
            <h1>Mi Perfil</h1>
            <p className="header-subtitle">Gestiona tu información personal y contraseña</p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="profile-section">
          <h3 className="section-title">Información Personal</h3>
          <div className="profile-info">
            <div className="info-row">
              <span className="info-label">Usuario:</span>
              <span className="info-value">{user.username}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Email:</span>
              <span className="info-value">{user.email}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Nombre:</span>
              <span className="info-value">
                {user.first_name && user.last_name
                  ? `${user.first_name} ${user.last_name}`
                  : 'No especificado'}
              </span>
            </div>
            {user.role && (
              <div className="info-row">
                <span className="info-label">Rol:</span>
                <span className="info-value">
                  <span className="role-badge">{user.role.description || user.role.name}</span>
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {accountingData && showAccounting && (
        <div className="card">
          <div className="profile-section">
            <h3 className="section-title">Mi Contabilidad</h3>
            
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
                  {formatCurrency(accountingData.summary.total_paid)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  Deudas Pendientes
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#ef4444' }}>
                  {formatCurrency(accountingData.summary.total_debt)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  Balance
                </div>
                <div style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: '600', 
                  color: accountingData.summary.balance >= 0 ? '#10b981' : '#ef4444'
                }}>
                  {formatCurrency(accountingData.summary.balance)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  Pagos Totales
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                  {accountingData.summary.total_payments}
                </div>
              </div>
            </div>

            {/* Deudas Pendientes */}
            {accountingData.pending_debts.length > 0 && (
              <div style={{ marginBottom: '2rem' }}>
                <h4 style={{ 
                  fontSize: '1.1rem', 
                  fontWeight: '600', 
                  marginBottom: '1rem',
                  color: '#ef4444'
                }}>
                  Deudas Pendientes
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {accountingData.pending_debts.map((debt, index) => (
                    <div 
                      key={index}
                      style={{
                        padding: '1rem',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: 'var(--radius-md)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: '600', color: '#991b1b' }}>
                          {debt.month_display} {debt.year} - {debt.payment_type.name}
                        </div>
                        {debt.penalty_amount > 0 && (
                          <div style={{ fontSize: '0.85rem', color: '#dc2626', marginTop: '0.25rem' }}>
                            Mora: {formatCurrency(debt.penalty_amount)}
                          </div>
                        )}
                      </div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '600', color: '#ef4444' }}>
                        -{formatCurrency(debt.amount)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Historial de Pagos */}
            <div>
              <h4 style={{ 
                fontSize: '1.1rem', 
                fontWeight: '600', 
                marginBottom: '1rem',
                color: 'var(--text-primary)'
              }}>
                Historial de Pagos
              </h4>
              {accountingData.payments.length === 0 ? (
                <div style={{ 
                  padding: '2rem', 
                  textAlign: 'center', 
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-secondary)',
                  borderRadius: 'var(--radius-md)'
                }}>
                  No hay pagos registrados
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {accountingData.payments.map((payment) => (
                    <div 
                      key={payment.id}
                      style={{
                        padding: '1rem',
                        background: payment.status === 'APROBADO' ? '#f0fdf4' : 
                                   payment.status === 'PENDIENTE' || payment.status === 'EN_REVISION' ? '#fffbeb' :
                                   '#fef2f2',
                        border: `1px solid ${
                          payment.status === 'APROBADO' ? '#86efac' : 
                          payment.status === 'PENDIENTE' || payment.status === 'EN_REVISION' ? '#fde68a' :
                          '#fecaca'
                        }`,
                        borderRadius: 'var(--radius-md)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: '600', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                            {payment.payment_type?.name || 'Pago sin tipo'}
                            {payment.month_display && payment.year && (
                              <span style={{ marginLeft: '0.5rem', color: 'var(--text-secondary)', fontWeight: '400' }}>
                                - {payment.month_display} {payment.year}
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                            <FiCalendar style={{ display: 'inline', marginRight: '0.25rem' }} />
                            {formatDate(payment.payment_date)}
                          </div>
                          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                            <FiCreditCard style={{ display: 'inline', marginRight: '0.25rem' }} />
                            {payment.payment_method_display}
                            {payment.card_last_four && ` •••• ${payment.card_last_four}`}
                            {payment.payment_reference && ` • Ref: ${payment.payment_reference}`}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ 
                            fontSize: '1.25rem', 
                            fontWeight: '600', 
                            color: payment.status === 'APROBADO' ? '#10b981' : 'var(--text-primary)'
                          }}>
                            {payment.status === 'APROBADO' ? '+' : ''}{formatCurrency(payment.amount)}
                          </div>
                          <div style={{ 
                            fontSize: '0.75rem', 
                            padding: '0.25rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                            display: 'inline-block',
                            marginTop: '0.5rem',
                            background: payment.status === 'APROBADO' ? '#d1fae5' :
                                       payment.status === 'PENDIENTE' || payment.status === 'EN_REVISION' ? '#fef3c7' :
                                       '#fee2e2',
                            color: payment.status === 'APROBADO' ? '#065f46' :
                                   payment.status === 'PENDIENTE' || payment.status === 'EN_REVISION' ? '#92400e' :
                                   '#991b1b'
                          }}>
                            {payment.status_display}
                          </div>
                        </div>
                      </div>
                      {payment.transfer_receipt && (
                        <div style={{ marginTop: '0.5rem' }}>
                          <a 
                            href={payment.transfer_receipt} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem',
                              fontSize: '0.85rem',
                              color: 'var(--primary-color)',
                              textDecoration: 'none'
                            }}
                          >
                            <FiEye /> Ver comprobante
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="profile-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 className="section-title" style={{ marginBottom: 0 }}>Mi Contabilidad</h3>
            <button
              onClick={loadAccounting}
              disabled={loadingAccounting}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                background: 'var(--primary-color)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: loadingAccounting ? 'not-allowed' : 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500',
                opacity: loadingAccounting ? 0.6 : 1
              }}
            >
              {loadingAccounting ? (
                <>
                  <FiLoader className="spinning" /> Cargando...
                </>
              ) : (
                <>
                  <FiDollarSign /> {showAccounting ? 'Ocultar' : 'Ver'} Contabilidad
                </>
              )}
            </button>
          </div>
          {!showAccounting && !accountingData && (
            <div style={{ 
              padding: '2rem', 
              textAlign: 'center', 
              color: 'var(--text-secondary)',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-md)'
            }}>
              Haz clic en "Ver Contabilidad" para ver tu historial de pagos y deudas
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="profile-section">
          <h3 className="section-title">Cambiar Contraseña</h3>
          <form onSubmit={handlePasswordChange} className="password-form">
            <div className="form-group">
              <label>
                <FiLock className="input-icon" />
                Contraseña Actual
              </label>
              <input
                type="password"
                value={passwordData.old_password}
                onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                className={errors.old_password ? 'error' : ''}
                placeholder="Ingresa tu contraseña actual"
                required
              />
              {errors.old_password && <span className="error-message">{errors.old_password}</span>}
            </div>

            <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label>
                  <FiLock className="input-icon" />
                  Nueva Contraseña
                </label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  className={errors.new_password ? 'error' : ''}
                  placeholder="Mínimo 8 caracteres"
                  required
                />
                {errors.new_password && <span className="error-message">{errors.new_password}</span>}
              </div>

              <div className="form-group">
                <label>
                  <FiLock className="input-icon" />
                  Confirmar Nueva Contraseña
                </label>
                <input
                  type="password"
                  value={passwordData.new_password_confirm}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password_confirm: e.target.value })}
                  className={errors.new_password_confirm ? 'error' : ''}
                  placeholder="Repite la nueva contraseña"
                  required
                />
                {errors.new_password_confirm && <span className="error-message">{errors.new_password_confirm}</span>}
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-large" disabled={loading}>
                {loading ? (
                  <>
                    <FiLoader className="spinning" /> Actualizando...
                  </>
                ) : (
                  <>
                    <FiSave /> Actualizar Contraseña
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;




