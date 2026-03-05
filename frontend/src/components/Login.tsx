import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiLogIn, FiUser, FiLock, FiLoader } from '../utils/icons';
import { useToastContext } from '../context/ToastContext';
import './shared.css';
import './Login.css';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const { success, error } = useToastContext();
  
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!credentials.username.trim()) {
      setErrors({ username: 'El usuario es requerido' });
      return;
    }
    if (!credentials.password) {
      setErrors({ password: 'La contraseña es requerida' });
      return;
    }

    setLoading(true);
    try {
      await login(credentials.username, credentials.password);
      success('Inicio de sesión exitoso');
      navigate('/');
    } catch (err: any) {
      console.error('Login error:', err);
      // Mostrar mensaje de error específico para credenciales incorrectas
      error('Usuario y/o contraseña incorrecto');
      // Limpiar errores de campos específicos si los hay
      setErrors({});
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <img src="/SC Logo.png" alt="AdminCUSC Logo" className="auth-logo" />
          <h1>Iniciar Sesión</h1>
          <p>Ingresa tus credenciales para acceder al sistema</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>
              <FiUser className="input-icon" />
              Usuario
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
              className={errors.username ? 'error' : ''}
              placeholder="Ingresa tu usuario"
              autoComplete="username"
              required
            />
            {errors.username && <span className="error-message">{errors.username}</span>}
          </div>

          <div className="form-group">
            <label>
              <FiLock className="input-icon" />
              Contraseña
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
              className={errors.password ? 'error' : ''}
              placeholder="Ingresa tu contraseña"
              autoComplete="current-password"
              required
            />
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-large btn-block" disabled={loading}>
            {loading ? (
              <>
                <FiLoader className="spinning" /> Iniciando sesión...
              </>
            ) : (
              <>
                <FiLogIn /> Iniciar Sesión
              </>
            )}
          </button>
          
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
            <a 
              href="/forgot-password" 
              onClick={(e) => {
                e.preventDefault();
                navigate('/forgot-password');
              }}
              style={{ 
                color: 'var(--primary-color)', 
                textDecoration: 'none',
                fontSize: '0.9rem'
              }}
            >
              ¿Olvidaste tu contraseña?
            </a>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;




