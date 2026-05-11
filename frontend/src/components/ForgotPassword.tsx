import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestPasswordReset } from '../services/authApi';
import { FiMail, FiLoader, FiArrowLeft } from '../utils/icons';
import { useToastContext } from '../context/ToastContext';
import './shared.css';
import './Login.css';

const ForgotPassword: React.FC = () => {
  const navigate = useNavigate();
  const { success, error } = useToastContext();
  
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    if (!email.trim()) {
      setErrors({ email: 'El correo electrónico es requerido' });
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrors({ email: 'Por favor ingresa un correo electrónico válido' });
      return;
    }

    setLoading(true);
    try {
      await requestPasswordReset(email);
      setSubmitted(true);
      success('Si el correo existe, recibirás un enlace para recuperar tu contraseña');
    } catch (err: any) {
      console.error('Password reset request error:', err);
      const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Error al solicitar recuperación de contraseña';
      error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <img src="/SC Logo.png" alt="AdminCUSC Logo" className="auth-logo" />
            <h1>Correo Enviado</h1>
            <p>Revisa tu bandeja de entrada</p>
          </div>
          
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Si el correo electrónico existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña.
            </p>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              El enlace expirará en 24 horas.
            </p>
          </div>

          <button 
            onClick={() => navigate('/login')} 
            className="btn btn-primary btn-large btn-block"
          >
            <FiArrowLeft /> Volver al inicio de sesión
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <img src="/SC Logo.png" alt="AdminCUSC Logo" className="auth-logo" />
          <h1>Recuperar Contraseña</h1>
          <p>Ingresa tu correo electrónico para recibir un enlace de recuperación</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>
              <FiMail className="input-icon" />
              Correo Electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={errors.email ? 'error' : ''}
              placeholder="Ingresa tu correo electrónico"
              autoComplete="email"
              required
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-large btn-block" disabled={loading}>
            {loading ? (
              <>
                <FiLoader className="spinning" /> Enviando...
              </>
            ) : (
              <>
                Enviar enlace de recuperación
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

export default ForgotPassword;
