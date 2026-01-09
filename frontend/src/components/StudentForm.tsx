import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getStudent, createStudent, updateStudent, getCareers } from '../services/api';
import { FiUser, FiSave, FiX, FiLoader } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './StudentForm.css';

interface Career {
  id: string;
  name: string;
}

const StudentForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { success, error } = useToast();
  const isEdit = !!id;

  const [student, setStudent] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    gender: 'M',
    curp: '',
    address: '',
    career: '',
    scholarship_type: 'NINGUNA',
  });

  const [careers, setCareers] = useState<Career[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadCareers();
    if (isEdit && id) {
      loadStudent(id);
    }
  }, [id, isEdit]);

  const loadCareers = async () => {
    try {
      const response = await getCareers();
      const data = response.data.results || response.data;
      setCareers(data);
    } catch (error) {
      console.error('Error loading careers:', error);
    }
  };

  const loadStudent = async (studentId: string) => {
    setLoadingData(true);
    try {
      const response = await getStudent(studentId);
      const data = response.data;
      setStudent({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        email: data.email || '',
        phone: data.phone || '',
        date_of_birth: data.date_of_birth || '',
        gender: data.gender || 'M',
        curp: data.curp || '',
        address: data.address || '',
        career: data.career || '',
        scholarship_type: data.scholarship_type || 'NINGUNA',
      });
    } catch (err: any) {
      console.error('Error loading student:', err);
      error('Error al cargar estudiante');
    } finally {
      setLoadingData(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!student.first_name.trim()) {
      newErrors.first_name = 'El nombre es requerido';
    }
    if (!student.last_name.trim()) {
      newErrors.last_name = 'El apellido es requerido';
    }
    if (!student.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(student.email)) {
      newErrors.email = 'El email no es válido';
    }
    if (!student.phone.trim()) {
      newErrors.phone = 'El teléfono es requerido';
    }
    if (!student.date_of_birth) {
      newErrors.date_of_birth = 'La fecha de nacimiento es requerida';
    }
    if (!student.curp.trim()) {
      newErrors.curp = 'El CURP es requerido';
    } else if (student.curp.length !== 18) {
      newErrors.curp = 'El CURP debe tener 18 caracteres';
    }
    if (!student.address.trim()) {
      newErrors.address = 'La dirección es requerida';
    }
    if (!student.career) {
      newErrors.career = 'La carrera es requerida';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      if (isEdit && id) {
        await updateStudent(id, student);
        success('Estudiante actualizado exitosamente');
      } else {
        await createStudent(student);
        success('Estudiante creado exitosamente');
      }
      setTimeout(() => navigate('/students'), 1000);
    } catch (err: any) {
      console.error('Error saving student:', err);
      if (err.response?.data) {
        setErrors(err.response.data);
        const errorMessage = err.response.data.detail || 'Error al guardar estudiante';
        error(errorMessage);
      } else {
        error('Error al guardar estudiante');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando datos del estudiante...</p>
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
            <h1>{isEdit ? 'Editar Estudiante' : 'Nuevo Estudiante'}</h1>
            <p className="header-subtitle">
              {isEdit ? 'Modifica la información del estudiante' : 'Registra un nuevo estudiante en el sistema'}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="student-form">
          <div className="form-section">
            <h3 className="section-title">Información Personal</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Nombres *</label>
                <input
                  type="text"
                  value={student.first_name}
                  onChange={(e) => setStudent({ ...student, first_name: e.target.value })}
                  className={errors.first_name ? 'error' : ''}
                  required
                />
                {errors.first_name && <span className="error-message">{errors.first_name}</span>}
              </div>
              
              <div className="form-group">
                <label>Apellidos *</label>
                <input
                  type="text"
                  value={student.last_name}
                  onChange={(e) => setStudent({ ...student, last_name: e.target.value })}
                  className={errors.last_name ? 'error' : ''}
                  required
                />
                {errors.last_name && <span className="error-message">{errors.last_name}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={student.email}
                  onChange={(e) => setStudent({ ...student, email: e.target.value })}
                  className={errors.email ? 'error' : ''}
                  required
                />
                {errors.email && <span className="error-message">{errors.email}</span>}
              </div>
              
              <div className="form-group">
                <label>Teléfono *</label>
                <input
                  type="tel"
                  value={student.phone}
                  onChange={(e) => setStudent({ ...student, phone: e.target.value })}
                  className={errors.phone ? 'error' : ''}
                  required
                />
                {errors.phone && <span className="error-message">{errors.phone}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Fecha de Nacimiento *</label>
                <input
                  type="date"
                  value={student.date_of_birth}
                  onChange={(e) => setStudent({ ...student, date_of_birth: e.target.value })}
                  className={errors.date_of_birth ? 'error' : ''}
                  required
                />
                {errors.date_of_birth && <span className="error-message">{errors.date_of_birth}</span>}
              </div>
              
              <div className="form-group">
                <label>Género *</label>
                <select
                  value={student.gender}
                  onChange={(e) => setStudent({ ...student, gender: e.target.value })}
                  required
                >
                  <option value="M">Masculino</option>
                  <option value="F">Femenino</option>
                  <option value="O">Otro</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3 className="section-title">Información de Identificación</h3>
            <div className="form-group">
              <label>CURP *</label>
              <input
                type="text"
                value={student.curp}
                onChange={(e) => setStudent({ ...student, curp: e.target.value.toUpperCase() })}
                maxLength={18}
                className={errors.curp ? 'error' : ''}
                required
                placeholder="ABCD123456HIJKLM01"
              />
              {errors.curp && <span className="error-message">{errors.curp}</span>}
            </div>
            
            <div className="form-group">
              <label>Dirección *</label>
              <textarea
                value={student.address}
                onChange={(e) => setStudent({ ...student, address: e.target.value })}
                className={errors.address ? 'error' : ''}
                required
                rows={3}
                placeholder="Calle, número, colonia, ciudad, estado"
              />
              {errors.address && <span className="error-message">{errors.address}</span>}
            </div>
          </div>

          <div className="form-section">
            <h3 className="section-title">Información Académica</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Carrera *</label>
                <select
                  value={student.career}
                  onChange={(e) => setStudent({ ...student, career: e.target.value })}
                  className={errors.career ? 'error' : ''}
                  required
                >
                  <option value="">Seleccione una carrera</option>
                  {careers.map((career) => (
                    <option key={career.id} value={career.id}>
                      {career.name}
                    </option>
                  ))}
                </select>
                {errors.career && <span className="error-message">{errors.career}</span>}
              </div>
              
              <div className="form-group">
                <label>Tipo de Beca</label>
                <select
                  value={student.scholarship_type}
                  onChange={(e) => setStudent({ ...student, scholarship_type: e.target.value })}
                >
                  <option value="NINGUNA">Sin Beca</option>
                  <option value="COMPLETA">Beca Completa</option>
                  <option value="MEDIA">Media Beca</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-large" disabled={loading}>
              {loading ? (
                <>
                  <FiLoader className="spinning" /> Guardando...
                </>
              ) : (
                <>
                  <FiSave /> {isEdit ? 'Actualizar' : 'Crear'} Estudiante
                </>
              )}
            </button>
            <button type="button" className="btn btn-secondary btn-large" onClick={() => navigate('/students')}>
              <FiX /> Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StudentForm;
