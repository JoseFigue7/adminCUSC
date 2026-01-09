import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { changePassword } from '../services/authApi';
import { FiUser, FiLock, FiSave, FiLoader } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './UserProfile.css';

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




