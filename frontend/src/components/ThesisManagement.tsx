import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getThesis, updateThesisStatus, getStudent } from '../services/api';
import { 
  FiBook, FiArrowLeft, FiCheckCircle, FiXCircle, FiEdit2, 
  FiSave, FiLoader, FiTrendingUp 
} from '../utils/icons';
import './shared.css';
import './ThesisManagement.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
  career_name: string;
}

interface Thesis {
  id: string;
  student: string;
  student_name: string;
  title: string;
  advisor_name: string;
  status: string;
  status_display: string;
  start_date: string;
  defense_date: string | null;
  notes: string;
}

const THESIS_STATUSES = [
  { value: 'SOLICITUD_ASESOR', label: 'Solicitud de Asesor' },
  { value: 'REVISION_TEMA', label: 'Revisión de Tema' },
  { value: 'APROBACION_TEMA', label: 'Aprobación de Tema' },
  { value: 'PRIMERA_REVISION', label: 'Primera Revisión' },
  { value: 'SEGUNDA_REVISION', label: 'Segunda Revisión' },
  { value: 'TERCERA_REVISION', label: 'Tercera Revisión' },
  { value: 'APROBACION_FINAL', label: 'Aprobación Final' },
  { value: 'DEFENSA_PROGRAMADA', label: 'Defensa Programada' },
  { value: 'COMPLETADA', label: 'Completada' },
];

const ThesisManagement: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const studentId = searchParams.get('studentId');

  const [student, setStudent] = useState<Student | null>(null);
  const [thesis, setThesis] = useState<Thesis | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    status: '',
    notes: '',
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
      const [studentRes, thesisRes] = await Promise.all([
        getStudent(studentId),
        getThesis(studentId)
      ]);

      setStudent(studentRes.data);
      const theses = thesisRes.data.results || (thesisRes.data.id ? [thesisRes.data] : []);
      if (theses.length > 0) {
        setThesis(theses[0]);
        setFormData({
          status: theses[0].status,
          notes: theses[0].notes || '',
        });
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!thesis || !formData.status) return;
    
    setSaving(true);
    try {
      await updateThesisStatus(thesis.id, formData.status);
      if (formData.notes !== thesis.notes) {
        // Si hay cambios en las notas, actualizar también
        // Nota: Esto requeriría un endpoint adicional para actualizar notas
      }
      await loadData();
      setEditing(false);
      alert('Estado de tesis actualizado exitosamente');
    } catch (error) {
      console.error('Error updating thesis:', error);
      alert('Error al actualizar el estado de la tesis');
    } finally {
      setSaving(false);
    }
  };

  const getStatusClass = (status: string): string => {
    const statusMap: Record<string, string> = {
      'SOLICITUD_ASESOR': 'status-pending',
      'REVISION_TEMA': 'status-review',
      'APROBACION_TEMA': 'status-approved',
      'PRIMERA_REVISION': 'status-review',
      'SEGUNDA_REVISION': 'status-review',
      'TERCERA_REVISION': 'status-review',
      'APROBACION_FINAL': 'status-approved',
      'DEFENSA_PROGRAMADA': 'status-scheduled',
      'COMPLETADA': 'status-completed',
    };
    return statusMap[status] || 'status-pending';
  };

  const getStatusProgress = (status: string): number => {
    const index = THESIS_STATUSES.findIndex(s => s.value === status);
    return index >= 0 ? ((index + 1) / THESIS_STATUSES.length) * 100 : 0;
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando información de tesis...</p>
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
              <h1>Gestión de Tesis</h1>
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

      {thesis ? (
        <>
          <div className="card">
            <div className="thesis-header">
              <h2 className="thesis-title">{thesis.title}</h2>
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
                <p>{thesis.advisor_name || 'No asignado'}</p>
              </div>
              <div className="info-item">
                <label>Fecha de Inicio</label>
                <p>{new Date(thesis.start_date).toLocaleDateString('es-ES')}</p>
              </div>
              {thesis.defense_date && (
                <div className="info-item">
                  <label>Fecha de Defensa</label>
                  <p>{new Date(thesis.defense_date).toLocaleDateString('es-ES')}</p>
                </div>
              )}
            </div>

            <div className="progress-section">
              <div className="progress-header">
                <h3>Progreso de la Tesis</h3>
                <span className={`status-badge ${getStatusClass(thesis.status)}`}>
                  {thesis.status_display}
                </span>
              </div>
              <div className="progress-bar-container">
                <div 
                  className="progress-bar"
                  style={{ width: `${getStatusProgress(thesis.status)}%` }}
                >
                  {Math.round(getStatusProgress(thesis.status))}%
                </div>
              </div>
            </div>

            <div className="status-timeline">
              {THESIS_STATUSES.map((status, index) => {
                const isCompleted = THESIS_STATUSES.findIndex(s => s.value === thesis.status) >= index;
                const isCurrent = status.value === thesis.status;
                
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
                    {THESIS_STATUSES.map(status => (
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
                    placeholder="Agregar notas sobre el estado de la tesis..."
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
                        status: thesis.status,
                        notes: thesis.notes || '',
                      });
                    }}
                  >
                    <FiXCircle /> Cancelar
                  </button>
                </div>
              </div>
            )}

            {thesis.notes && (
              <div className="notes-section">
                <h3>Notas</h3>
                <p>{thesis.notes}</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="card">
          <div className="empty-state">
            <FiBook className="empty-icon" />
            <h3>No hay tesis registrada</h3>
            <p>Este estudiante aún no ha iniciado su proceso de tesis.</p>
            <p className="info-text">
              Para iniciar una tesis, el estudiante debe haber cerrado su pensum.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThesisManagement;

