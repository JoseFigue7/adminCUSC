import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiUserPlus, FiUser, FiLock, FiMail, FiPhone, FiLoader } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './Login.css';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const { success, error } = useToast();
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
    phone: '',
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validaciones
    const newErrors: Record<string, string> = {};
    
    if (!formData.username.trim()) {
      newErrors.username = 'El usuario es requerido';
    }
    if (!formData.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'El email no es válido';
    }
    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 8) {
      newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
    }
    if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = 'Las contraseñas no coinciden';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      await register(formData);
      success('Registro exitoso. Bienvenido al sistema.');
      navigate('/');
    } catch (err: any) {
      console.error('Register error:', err);
      const errorMessage = err.response?.data?.detail || 
                          err.response?.data?.error || 
                          'Error al registrar. Intenta nuevamente.';
      error(errorMessage);
      if (err.response?.data) {
        setErrors(err.response.data);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <FiUserPlus className="auth-icon" />
          <h1>Registro</h1>
          <p>Crea una cuenta para acceder al sistema</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>
                <FiUser className="input-icon" />
                Nombre
              </label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                placeholder="Nombre"
                autoComplete="given-name"
              />
            </div>

            <div className="form-group">
              <label>
                <FiUser className="input-icon" />
                Apellido
              </label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                placeholder="Apellido"
                autoComplete="family-name"
              />
            </div>
          </div>

          <div className="form-group">
            <label>
              <FiUser className="input-icon" />
              Usuario *
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className={errors.username ? 'error' : ''}
              placeholder="Nombre de usuario"
              autoComplete="username"
              required
            />
            {errors.username && <span className="error-message">{errors.username}</span>}
          </div>

          <div className="form-group">
            <label>
              <FiMail className="input-icon" />
              Email *
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className={errors.email ? 'error' : ''}
              placeholder="correo@ejemplo.com"
              autoComplete="email"
              required
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label>
              <FiPhone className="input-icon" />
              Teléfono
            </label>
            <input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="Teléfono (opcional)"
              autoComplete="tel"
            />
          </div>

          <div className="form-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>
                <FiLock className="input-icon" />
                Contraseña *
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className={errors.password ? 'error' : ''}
                placeholder="Mínimo 8 caracteres"
                autoComplete="new-password"
                required
              />
              {errors.password && <span className="error-message">{errors.password}</span>}
            </div>

            <div className="form-group">
              <label>
                <FiLock className="input-icon" />
                Confirmar Contraseña *
              </label>
              <input
                type="password"
                value={formData.password_confirm}
                onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
                className={errors.password_confirm ? 'error' : ''}
                placeholder="Repite la contraseña"
                autoComplete="new-password"
                required
              />
              {errors.password_confirm && <span className="error-message">{errors.password_confirm}</span>}
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-large btn-block" disabled={loading}>
            {loading ? (
              <>
                <FiLoader className="spinning" /> Registrando...
              </>
            ) : (
              <>
                <FiUserPlus /> Registrarse
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            ¿Ya tienes una cuenta?{' '}
            <Link to="/login" className="auth-link">
              Inicia sesión aquí
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;




