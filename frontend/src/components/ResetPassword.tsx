import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { confirmPasswordReset } from '../services/authApi';
import { useAuth } from '../context/AuthContext';
import { FiLock, FiLoader, FiCheck, FiArrowLeft } from '../utils/icons';
import { useToastContext } from '../context/ToastContext';
import './shared.css';
import './Login.css';

const ResetPassword: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { success, error } = useToastContext();
  const { isAuthenticated } = useAuth();
  
  const [passwordData, setPasswordData] = useState({
    new_password: '',
    new_password_confirm: '',
  });
  const [loading, setLoading] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const token = searchParams.get('token');
  const uid = searchParams.get('uid');

  useEffect(() => {
    if (!token || !uid) {
      error('Enlace inválido. Por favor solicita un nuevo enlace de recuperación.');
      navigate('/forgot-password');
    }
  }, [token, uid, navigate, error]);

  // Redirigir automáticamente después de éxito
  useEffect(() => {
    if (resetSuccess) {
      console.log('resetSuccess es true, iniciando timer de redirección...');
      console.log('isAuthenticated:', isAuthenticated);
      
      const timer = setTimeout(() => {
        console.log('Ejecutando redirección...');
        try {
          if (isAuthenticated) {
            console.log('Redirigiendo a /');
            navigate('/', { replace: true });
          } else {
            console.log('Redirigiendo a /login');
            navigate('/login', { replace: true });
          }
        } catch (navError) {
          console.error('Error al navegar:', navError);
          // Intentar redirección con window.location como fallback
          if (isAuthenticated) {
            window.location.href = '/';
          } else {
            window.location.href = '/login';
          }
        }
      }, 2000);
      
      return () => {
        console.log('Limpiando timer de redirección');
        clearTimeout(timer);
      };
    }
  }, [resetSuccess, isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!passwordData.new_password) {
      setErrors({ new_password: 'La nueva contraseña es requerida' });
      return;
    }

    if (passwordData.new_password.length < 8) {
      setErrors({ new_password: 'La contraseña debe tener al menos 8 caracteres' });
      return;
    }

    if (passwordData.new_password !== passwordData.new_password_confirm) {
      setErrors({ new_password_confirm: 'Las contraseñas no coinciden' });
      return;
    }

    if (!token || !uid) {
      error('Token o UID faltante');
      return;
    }

    setLoading(true);
    try {
      console.log('=== INICIANDO RESET DE CONTRASEÑA ===');
      console.log('Token:', token);
      console.log('UID:', uid);
      console.log('Nueva contraseña length:', passwordData.new_password.length);
      
      success('Procesando solicitud de restablecimiento...');
      
      const response = await confirmPasswordReset(token, uid, passwordData.new_password, passwordData.new_password_confirm);
      console.log('✅ Respuesta del servidor recibida:', response);
      console.log('Response status:', response.status);
      console.log('Response data:', response.data);
      
      // Mostrar mensaje de éxito
      success('¡Contraseña restablecida exitosamente! Redirigiendo en 2 segundos...');
      
      // Establecer estado de éxito
      console.log('Estableciendo resetSuccess a true...');
      setResetSuccess(true);
      console.log('resetSuccess establecido, el componente debería re-renderizar');
      
    } catch (err: any) {
      console.error('❌ ERROR en reset de contraseña:', err);
      console.error('Error completo:', JSON.stringify(err, null, 2));
      console.error('Error response:', err.response);
      console.error('Error status:', err.response?.status);
      console.error('Error data:', err.response?.data);
      
      let errorMessage = 'Error al restablecer la contraseña';
      
      if (err.response?.data) {
        if (err.response.data.error) {
          errorMessage = err.response.data.error;
        } else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else if (err.response.data.non_field_errors) {
          errorMessage = Array.isArray(err.response.data.non_field_errors) 
            ? err.response.data.non_field_errors[0] 
            : err.response.data.non_field_errors;
        } else {
          // Intentar obtener el primer error del objeto
          const firstKey = Object.keys(err.response.data)[0];
          const firstError = err.response.data[firstKey];
          if (Array.isArray(firstError)) {
            errorMessage = firstError[0];
          } else if (typeof firstError === 'string') {
            errorMessage = firstError;
          } else {
            errorMessage = JSON.stringify(err.response.data);
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      console.error('Mensaje de error final que se mostrará:', errorMessage);
      error(`Error: ${errorMessage}`);
      
      // Si el token es inválido, redirigir a forgot-password
      if (err.response?.status === 400 && (errorMessage.includes('inválido') || errorMessage.includes('expirado') || errorMessage.includes('Token'))) {
        error('Token inválido o expirado. Redirigiendo...');
        setTimeout(() => {
          navigate('/forgot-password');
        }, 3000);
      }
    } finally {
      setLoading(false);
    }
  };

  if (resetSuccess) {
    console.log('Renderizando pantalla de éxito - resetSuccess es true');
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <img src="/SC Logo.png" alt="AdminCUSC Logo" className="auth-logo" />
            <h1>¡Contraseña Restablecida!</h1>
            <p style={{ color: 'var(--success-color)', fontWeight: 600, fontSize: '1.1rem' }}>
              ✅ Tu contraseña ha sido cambiada exitosamente
            </p>
          </div>
          
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{ 
              fontSize: '4rem', 
              color: 'var(--success-color)', 
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              <FiCheck style={{ 
                background: 'var(--success-color-alpha, rgba(34, 197, 94, 0.1))',
                borderRadius: '50%',
                padding: '1rem',
                width: '80px',
                height: '80px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }} />
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', marginBottom: '0.5rem' }}>
              {isAuthenticated 
                ? 'Serás redirigido al panel principal en unos momentos...'
                : 'Ya puedes iniciar sesión con tu nueva contraseña. Serás redirigido al inicio de sesión...'}
            </p>
            <div style={{ 
              marginTop: '1rem',
              display: 'flex',
              justifyContent: 'center',
              gap: '0.5rem'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--primary-color)',
                animation: 'pulse 1.5s ease-in-out infinite'
              }}></div>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--primary-color)',
                animation: 'pulse 1.5s ease-in-out infinite 0.3s'
              }}></div>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--primary-color)',
                animation: 'pulse 1.5s ease-in-out infinite 0.6s'
              }}></div>
            </div>
          </div>

          <button 
            onClick={() => {
              if (isAuthenticated) {
                navigate('/', { replace: true });
              } else {
                navigate('/login', { replace: true });
              }
            }} 
            className="btn btn-primary btn-large btn-block"
          >
            {isAuthenticated ? 'Ir al panel principal' : 'Ir al inicio de sesión'}
          </button>
        </div>
      </div>
    );
  }

  if (!token || !uid) {
    return null;
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <img src="/SC Logo.png" alt="AdminCUSC Logo" className="auth-logo" />
          <h1>Restablecer Contraseña</h1>
          <p>Ingresa tu nueva contraseña</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
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
              placeholder="Ingresa tu nueva contraseña"
              autoComplete="new-password"
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
              placeholder="Confirma tu nueva contraseña"
              autoComplete="new-password"
              required
            />
            {errors.new_password_confirm && <span className="error-message">{errors.new_password_confirm}</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-large btn-block" disabled={loading}>
            {loading ? (
              <>
                <FiLoader className="spinning" /> Restableciendo...
              </>
            ) : (
              <>
                Restablecer Contraseña
              </>
            )}
          </button>
          
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <a 
              href="/login" 
              onClick={(e) => {
                e.preventDefault();
                navigate('/login');
              }}
              style={{ 
                color: 'var(--primary-color)', 
                textDecoration: 'none',
                fontSize: '0.9rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <FiArrowLeft /> Volver al inicio de sesión
            </a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;
