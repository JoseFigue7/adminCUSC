import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getGraduationMethod, updateGraduationMethodStatus, createGraduationMethod, getStudent } from '../services/api';
import { 
  FiBook, FiArrowLeft, FiCheckCircle, FiXCircle, FiEdit2, 
  FiSave, FiLoader, FiTrendingUp, FiPlus
} from '../utils/icons';
import './shared.css';
import './ThesisManagement.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
  career_name: string;
  pensum_closed: boolean;
}

interface GraduationMethod {
  id: string;
  student: string;
  student_name: string;
  method_type: string;
  method_type_display: string;
  title: string;
  advisor: string;
  status: string;
  status_display: string;
  start_date: string;
  defense_date: string | null;
  notes: string;
}

const METHOD_TYPES = [
  { value: 'EXAMEN_PROFESIONAL', label: 'Examen Profesional' },
  { value: 'TESINA', label: 'Tesina' },
  { value: 'TESIS', label: 'Tesis' },
  { value: 'DIPLOMADO', label: 'Diplomado' },
];

const GRADUATION_STATUSES = [
  { value: 'NO_INICIADA', label: 'No Iniciada' },
  { value: 'SOLICITUD_ASESOR', label: 'Solicitud de Asesor' },
  { value: 'REVISION_TEMA', label: 'Revisión de Tema' },
  { value: 'APROBACION_TEMA', label: 'Aprobación de Tema' },
  { value: 'PRIMERA_REVISION', label: 'Primera Revisión' },
  { value: 'SEGUNDA_REVISION', label: 'Segunda Revisión' },
  { value: 'TERCERA_REVISION', label: 'Tercera Revisión' },
  { value: 'APROBADA', label: 'Aprobada' },
  { value: 'RECHAZADA', label: 'Rechazada' },
];

const GraduationMethodManagement: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const studentId = searchParams.get('studentId');

  const [student, setStudent] = useState<Student | null>(null);
  const [graduationMethod, setGraduationMethod] = useState<GraduationMethod | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    method_type: '',
    status: '',
    notes: '',
    title: '',
    advisor: '',
  });

  useEffect(() => {
    if (studentId) {
      loadData();
    }
  }, [studentId]);

  const loadData = async () => {
    if (!studentId) return;
    setLoading(true);
    try {
      const [studentRes, graduationMethodRes] = await Promise.all([
        getStudent(studentId),
        getGraduationMethod(studentId).catch(() => ({ data: null }))
      ]);

      setStudent(studentRes.data);
      if (graduationMethodRes.data && graduationMethodRes.data.id) {
        setGraduationMethod(graduationMethodRes.data);
        setFormData({
          method_type: graduationMethodRes.data.method_type,
          status: graduationMethodRes.data.status,
          notes: graduationMethodRes.data.notes || '',
          title: graduationMethodRes.data.title || '',
          advisor: graduationMethodRes.data.advisor || '',
        });
      } else {
        setGraduationMethod(null);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!graduationMethod || !formData.status) return;
    
    setSaving(true);
    try {
      await updateGraduationMethodStatus(graduationMethod.id, formData.status);
      await loadData();
      setEditing(false);
      alert('Estado del método de graduación actualizado exitosamente');
    } catch (error: any) {
      console.error('Error updating graduation method:', error);
      alert(error.response?.data?.error || 'Error al actualizar el estado del método de graduación');
    } finally {
      setSaving(false);
    }
  };

  const handleCreate = async () => {
    if (!studentId || !formData.method_type) {
      alert('Por favor seleccione un método de graduación');
      return;
    }

    if (!student?.pensum_closed) {
      alert('El estudiante debe haber completado todos los cursos del pensum para iniciar un método de graduación.');
      return;
    }

    setSaving(true);
    try {
      await createGraduationMethod({
        student: studentId,
        method_type: formData.method_type,
        title: formData.title,
        advisor: formData.advisor,
        status: 'NO_INICIADA',
        notes: formData.notes,
      });
      await loadData();
      setCreating(false);
      setFormData({
        method_type: '',
        status: '',
        notes: '',
        title: '',
        advisor: '',
      });
      alert('Método de graduación creado exitosamente');
    } catch (error: any) {
      console.error('Error creating graduation method:', error);
      alert(error.response?.data?.error || error.response?.data?.student?.[0] || 'Error al crear el método de graduación');
    } finally {
      setSaving(false);
    }
  };

  const getStatusClass = (status: string): string => {
    const statusMap: Record<string, string> = {
      'NO_INICIADA': 'status-pending',
      'SOLICITUD_ASESOR': 'status-pending',
      'REVISION_TEMA': 'status-review',
      'APROBACION_TEMA': 'status-approved',
      'PRIMERA_REVISION': 'status-review',
      'SEGUNDA_REVISION': 'status-review',
      'TERCERA_REVISION': 'status-review',
      'APROBADA': 'status-approved',
      'RECHAZADA': 'status-pending',
    };
    return statusMap[status] || 'status-pending';
  };

  const getStatusProgress = (status: string): number => {
    const index = GRADUATION_STATUSES.findIndex(s => s.value === status);
    return index >= 0 ? ((index + 1) / GRADUATION_STATUSES.length) * 100 : 0;
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando información del método de graduación...</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiBook className="empty-icon" />
          <h3>No se especificó un estudiante</h3>
          <button onClick={() => navigate('/students')} className="btn btn-primary">
            <FiArrowLeft /> Volver a estudiantes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <FiBook className="header-icon" />
            <div>
              <h1>Método de Graduación</h1>
              <p className="header-subtitle">
                {student.first_name} {student.last_name} - {student.carnet} | {student.career_name}
              </p>
            </div>
          </div>
          <button onClick={() => navigate(`/students/${studentId}`)} className="btn btn-secondary btn-large">
            <FiArrowLeft /> Volver
          </button>
        </div>
      </div>

      {graduationMethod ? (
        <>
          <div className="card">
            <div className="thesis-header">
              <div>
                <h2 className="thesis-title">{graduationMethod.title || 'Sin título'}</h2>
                <p style={{ marginTop: '8px', color: '#666', fontSize: '14px' }}>
                  <strong>Tipo:</strong> {graduationMethod.method_type_display}
                </p>
              </div>
              {!editing && (
                <button 
                  className="btn btn-primary"
                  onClick={() => setEditing(true)}
                >
                  <FiEdit2 /> Editar Estado
                </button>
              )}
            </div>

            <div className="thesis-info-grid">
              <div className="info-item">
                <label>Asesor</label>
                <p>{graduationMethod.advisor || 'No asignado'}</p>
              </div>
              <div className="info-item">
                <label>Fecha de Inicio</label>
                <p>{graduationMethod.start_date ? new Date(graduationMethod.start_date).toLocaleDateString('es-ES') : 'No especificada'}</p>
              </div>
              {graduationMethod.defense_date && (
                <div className="info-item">
                  <label>Fecha de Defensa/Examen</label>
                  <p>{new Date(graduationMethod.defense_date).toLocaleDateString('es-ES')}</p>
                </div>
              )}
            </div>

            <div className="progress-section">
              <div className="progress-header">
                <h3>Progreso del Método de Graduación</h3>
                <span className={`status-badge ${getStatusClass(graduationMethod.status)}`}>
                  {graduationMethod.status_display}
                </span>
              </div>
              <div className="progress-bar-container">
                <div 
                  className="progress-bar"
                  style={{ width: `${getStatusProgress(graduationMethod.status)}%` }}
                >
                  {Math.round(getStatusProgress(graduationMethod.status))}%
                </div>
              </div>
            </div>

            <div className="status-timeline">
              {GRADUATION_STATUSES.map((status, index) => {
                const isCompleted = GRADUATION_STATUSES.findIndex(s => s.value === graduationMethod.status) >= index;
                const isCurrent = status.value === graduationMethod.status;
                
                return (
                  <div 
                    key={status.value} 
                    className={`timeline-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}
                  >
                    <div className="timeline-marker">
                      {isCompleted ? <FiCheckCircle /> : <div className="marker-dot" />}
                    </div>
                    <div className="timeline-content">
                      <h4>{status.label}</h4>
                      {isCurrent && <span className="current-badge">Estado Actual</span>}
                    </div>
                  </div>
                );
              })}
            </div>

            {editing && (
              <div className="edit-section">
                <h3>Actualizar Estado</h3>
                <div className="form-group">
                  <label>Nuevo Estado</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="form-input"
                  >
                    {GRADUATION_STATUSES.map(status => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Notas</label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="form-input"
                    rows={4}
                    placeholder="Agregar notas sobre el estado del método de graduación..."
                  />
                </div>
                <div className="form-actions">
                  <button 
                    className="btn btn-primary btn-large"
                    onClick={handleSave}
                    disabled={saving}
                  >
                    {saving ? (
                      <>
                        <FiLoader className="spinning" /> Guardando...
                      </>
                    ) : (
                      <>
                        <FiSave /> Guardar Cambios
                      </>
                    )}
                  </button>
                  <button 
                    className="btn btn-secondary btn-large"
                    onClick={() => {
                      setEditing(false);
                      setFormData({
                        method_type: graduationMethod.method_type,
                        status: graduationMethod.status,
                        notes: graduationMethod.notes || '',
                        title: graduationMethod.title || '',
                        advisor: graduationMethod.advisor || '',
                      });
                    }}
                  >
                    <FiXCircle /> Cancelar
                  </button>
                </div>
              </div>
            )}

            {graduationMethod.notes && (
              <div className="notes-section">
                <h3>Notas</h3>
                <p>{graduationMethod.notes}</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="card">
          <div className="empty-state">
            <FiBook className="empty-icon" />
            <h3>No hay método de graduación registrado</h3>
            <p>Este estudiante aún no ha iniciado su proceso de graduación.</p>
            {!student.pensum_closed ? (
              <p className="info-text" style={{ color: '#dc3545', fontWeight: 'bold' }}>
                El estudiante debe haber completado todos los cursos del pensum para iniciar un método de graduación.
              </p>
            ) : (
              <>
                <p className="info-text">
                  Para iniciar un método de graduación, el estudiante debe haber cerrado su pensum.
                </p>
                {!creating ? (
                  <button 
                    className="btn btn-primary btn-large"
                    onClick={() => setCreating(true)}
                    style={{ marginTop: '20px' }}
                  >
                    <FiPlus /> Crear Método de Graduación
                  </button>
                ) : (
                  <div className="edit-section" style={{ marginTop: '20px', textAlign: 'left' }}>
                    <h3>Crear Método de Graduación</h3>
                    <div className="form-group">
                      <label>Método de Graduación *</label>
                      <select
                        value={formData.method_type}
                        onChange={(e) => setFormData({ ...formData, method_type: e.target.value })}
                        className="form-input"
                        required
                      >
                        <option value="">Seleccione un método</option>
                        {METHOD_TYPES.map(method => (
                          <option key={method.value} value={method.value}>
                            {method.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Título</label>
                      <input
                        type="text"
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        className="form-input"
                        placeholder="Título del trabajo (opcional)"
                      />
                    </div>
                    <div className="form-group">
                      <label>Asesor</label>
                      <input
                        type="text"
                        value={formData.advisor}
                        onChange={(e) => setFormData({ ...formData, advisor: e.target.value })}
                        className="form-input"
                        placeholder="Nombre del asesor (opcional)"
                      />
                    </div>
                    <div className="form-group">
                      <label>Notas</label>
                      <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        className="form-input"
                        rows={4}
                        placeholder="Notas adicionales (opcional)"
                      />
                    </div>
                    <div className="form-actions">
                      <button 
                        className="btn btn-primary btn-large"
                        onClick={handleCreate}
                        disabled={saving || !formData.method_type}
                      >
                        {saving ? (
                          <>
                            <FiLoader className="spinning" /> Creando...
                          </>
                        ) : (
                          <>
                            <FiSave /> Crear Método de Graduación
                          </>
                        )}
                      </button>
                      <button 
                        className="btn btn-secondary btn-large"
                        onClick={() => {
                          setCreating(false);
                          setFormData({
                            method_type: '',
                            status: '',
                            notes: '',
                            title: '',
                            advisor: '',
                          });
                        }}
                      >
                        <FiXCircle /> Cancelar
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GraduationMethodManagement;
