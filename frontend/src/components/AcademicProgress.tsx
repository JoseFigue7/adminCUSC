import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { getStudentProgress, getCourseEnrollments, updateCourseGrade, getStudent, getStudents } from '../services/api';
import { FiBook, FiTrendingUp, FiCheckCircle, FiXCircle, FiEdit2, FiSave, FiLoader, FiSearch, FiArrowLeft, FiUpload } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './AcademicProgress.css';

interface Progress {
  total_courses: number;
  approved_courses: number;
  progress_percentage: number;
  pensum_closed: boolean;
  thesis_started: boolean;
}

interface Enrollment {
  id: string;
  course_code: string;
  course_name: string;
  course_id?: string;
  final_grade: number | null;
  status_display: string;
  temp_grade?: number;
  cuatrimestre?: string;
}

interface StudentOption {
  id: string;
  carnet: string;
  first_name: string;
  last_name?: string;
  first_last_name?: string;
  second_last_name?: string;
  full_name?: string;
  career_name: string;
}

const AcademicProgress: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const studentId = searchParams.get('studentId');
  const { success, error } = useToast();

  const [student, setStudent] = useState<any>(null);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);
  const [students, setStudents] = useState<StudentOption[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (studentId) {
      setLoading(true);
      loadStudentData();
      loadProgress(studentId);
      loadEnrollments(studentId);
    } else {
      setLoading(false);
      loadStudentsList();
    }
  }, [studentId]);

  const loadStudentsList = async () => {
    setLoadingStudents(true);
    try {
      const response = await getStudents({ page_size: 100 });
      const data = response.data.results || response.data;
      setStudents(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading students:', err);
      error('Error al cargar la lista de estudiantes');
    } finally {
      setLoadingStudents(false);
    }
  };

  const handleStudentSelect = (selectedStudentId: string) => {
    if (selectedStudentId) {
      setSearchParams({ studentId: selectedStudentId });
    }
  };

  const handleChangeStudent = () => {
    setSearchParams({});
    setStudent(null);
    setProgress(null);
    setEnrollments([]);
  };

  const loadStudentData = async () => {
    if (!studentId) return;
    try {
      const response = await getStudent(studentId);
      setStudent(response.data);
    } catch (error) {
      console.error('Error loading student:', error);
    }
  };

  const loadProgress = async (id: string) => {
    try {
      const response = await getStudentProgress(id);
      setProgress(response.data);
    } catch (error) {
      console.error('Error loading progress:', error);
    }
  };

  const loadEnrollments = async (id: string) => {
    try {
      const response = await getCourseEnrollments(id);
      const data = response.data.results || response.data;
      setEnrollments(data.map((e: Enrollment) => ({ ...e, temp_grade: undefined })));
    } catch (error) {
      console.error('Error loading enrollments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateGrade = async (enrollment: Enrollment) => {
    if (enrollment.temp_grade !== undefined &&
      enrollment.temp_grade >= 0 &&
      enrollment.temp_grade <= 100) {
      setSavingId(enrollment.id);
      try {
        await updateCourseGrade(enrollment.id, enrollment.temp_grade);
        const updated = enrollments.map(e =>
          e.id === enrollment.id
            ? { ...e, final_grade: enrollment.temp_grade || null, temp_grade: undefined }
            : e
        );
        setEnrollments(updated);
        setEditingId(null);
        if (studentId) {
          loadProgress(studentId);
        }
        success('Nota actualizada exitosamente');
      } catch (err: any) {
        console.error('Error updating grade:', err);
        const errorMessage = err.response?.data?.detail || 'Error al actualizar la nota';
        error(errorMessage);
      } finally {
        setSavingId(null);
      }
    }
  };

  const startEditing = (id: string) => {
    setEditingId(id);
  };

  const cancelEditing = (id: string) => {
    setEditingId(null);
    setEnrollments(enrollments.map(e =>
      e.id === id ? { ...e, temp_grade: undefined } : e
    ));
  };

  const getGradeColor = (grade: number | null): string => {
    if (grade === null) return 'gray';
    if (grade >= 90) return 'excellent';
    if (grade >= 80) return 'good';
    if (grade >= 70) return 'pass';
    return 'fail';
  };

  const getStudentDisplayName = (student: StudentOption): string => {
    if (student.full_name) return student.full_name;
    const lastName = student.first_last_name || student.last_name || '';
    const secondLastName = student.second_last_name || '';
    return `${student.first_name} ${lastName} ${secondLastName}`.trim();
  };

  const filteredStudents = students.filter(s => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    const fullName = getStudentDisplayName(s).toLowerCase();
    return (
      s.carnet.toLowerCase().includes(search) ||
      fullName.includes(search) ||
      s.career_name.toLowerCase().includes(search)
    );
  });

  if (!studentId) {
    return (
      <div className="page-container">
        <div className="page-header">
          <div className="header-title">
            <FiBook className="header-icon" />
            <div>
              <h1>Progreso Académico</h1>
              <p className="header-subtitle">Selecciona un estudiante para ver su progreso académico</p>
            </div>
          </div>
          <div className="header-actions">
            <Link 
              to="/grades/upload" 
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <FiUpload /> Subir Notas Masivamente
            </Link>
          </div>
        </div>

        <div className="card">
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label htmlFor="student-search">Buscar Estudiante</label>
            <div style={{ position: 'relative' }}>
              <FiSearch 
                style={{ 
                  position: 'absolute', 
                  left: '12px', 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: 'var(--text-secondary)'
                }} 
              />
              <input
                id="student-search"
                type="text"
                placeholder="Buscar por carnet, nombre o carrera..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="form-input"
                style={{ paddingLeft: '40px' }}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="student-select">Seleccionar Estudiante *</label>
            {loadingStudents ? (
              <div className="loading-spinner" style={{ padding: '2rem' }}>
                <div className="spinner"></div>
                <p>Cargando estudiantes...</p>
              </div>
            ) : (
              <>
                <select
                  id="student-select"
                  value=""
                  onChange={(e) => handleStudentSelect(e.target.value)}
                  className="form-input"
                  style={{ marginBottom: '1rem' }}
                >
                  <option value="">Seleccione un estudiante</option>
                  {filteredStudents.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.carnet} - {getStudentDisplayName(student)} ({student.career_name})
                    </option>
                  ))}
                </select>
                {searchTerm && filteredStudents.length === 0 && (
                  <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                    No se encontraron estudiantes que coincidan con la búsqueda.
                  </p>
                )}
                {!searchTerm && filteredStudents.length === 0 && (
                  <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                    No hay estudiantes disponibles.
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando progreso académico...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {student && (
        <div className="page-header">
          <div className="header-content">
            <div className="header-title">
              <FiBook className="header-icon" />
              <div>
                <h1>Progreso Académico</h1>
                <p className="header-subtitle">
                  {student.full_name || `${student.first_name} ${student.last_name}`} - {student.carnet}
                </p>
              </div>
            </div>
            <div className="header-actions">
              <button 
                onClick={handleChangeStudent}
                className="btn btn-secondary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <FiArrowLeft /> Cambiar Estudiante
              </button>
            </div>
          </div>
        </div>
      )}

      {progress && (
        <div className="card progress-card">
          <h2 className="card-title">
            <FiTrendingUp className="card-title-icon" />
            Resumen del Progreso
          </h2>

          <div className="progress-summary">
            <div className="progress-info">
              <div className="progress-bar-container">
                <div
                  className="progress-bar"
                  style={{ width: `${progress.progress_percentage}%` }}
                >
                  {progress.approved_courses} / {progress.total_courses} cursos aprobados
                </div>
              </div>
              <div className="progress-stats">
                <div className="stat-item">
                  <span className="stat-label">Progreso Total</span>
                  <span className="stat-value">{progress.progress_percentage.toFixed(1)}%</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Cursos Aprobados</span>
                  <span className="stat-value">{progress.approved_courses}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Total de Cursos</span>
                  <span className="stat-value">{progress.total_courses}</span>
                </div>
              </div>
            </div>

            <div className="status-cards">
              <div className={`status-card ${progress.pensum_closed ? 'status-active' : 'status-inactive'}`}>
                <FiCheckCircle className="status-card-icon" />
                <div>
                  <h4>Pensum</h4>
                  <p>{progress.pensum_closed ? 'Cerrado' : 'En Progreso'}</p>
                </div>
              </div>
              <div className={`status-card ${progress.thesis_started ? 'status-active' : 'status-inactive'}`}>
                <FiBook className="status-card-icon" />
                <div>
                  <h4>Tesis</h4>
                  <p>{progress.thesis_started ? 'Iniciada' : 'No Iniciada'}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">
          <FiBook className="card-title-icon" />
          Cursos Matriculados
        </h2>

        {enrollments.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Curso</th>
                  <th>Nota Final</th>
                  <th>Estado</th>
                  <th className="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {enrollments.map((enrollment) => {
                  const isEditing = editingId === enrollment.id;
                  const isSaving = savingId === enrollment.id;

                  return (
                    <tr key={enrollment.id} className="table-row">
                      <td className="code-cell">
                        <span className="code-badge">{enrollment.course_code}</span>
                      </td>
                      <td className="course-name">{enrollment.course_name}</td>
                      <td className="grade-cell">
                        {isEditing ? (
                          <div className="grade-input-group">
                            <input
                              type="number"
                              value={enrollment.temp_grade || ''}
                              onChange={(e) => {
                                const value = parseFloat(e.target.value);
                                setEnrollments(enrollments.map(e =>
                                  e.id === enrollment.id
                                    ? { ...e, temp_grade: isNaN(value) ? undefined : value }
                                    : e
                                ));
                              }}
                              min="0"
                              max="100"
                              className="grade-input"
                              autoFocus
                            />
                            <div className="grade-actions">
                              <button
                                className="btn-icon btn-icon-success btn-small"
                                onClick={() => handleUpdateGrade(enrollment)}
                                disabled={isSaving || enrollment.temp_grade === undefined}
                                title="Guardar"
                              >
                                {isSaving ? <FiLoader className="spinning" /> : <FiSave />}
                              </button>
                              <button
                                className="btn-icon btn-icon-danger btn-small"
                                onClick={() => cancelEditing(enrollment.id)}
                                disabled={isSaving}
                                title="Cancelar"
                              >
                                <FiXCircle />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="grade-display">
                            {enrollment.final_grade !== null ? (
                              <span className={`grade-badge grade-${getGradeColor(enrollment.final_grade)}`}>
                                {enrollment.final_grade}
                              </span>
                            ) : (
                              <span className="grade-placeholder">Sin calificar</span>
                            )}
                          </div>
                        )}
                      </td>
                      <td>
                        <span className={`status-badge status-${enrollment.status_display.toLowerCase().replace(' ', '-')}`}>
                          {enrollment.status_display}
                        </span>
                      </td>
                      <td className="actions-cell">
                        {!enrollment.final_grade && !isEditing && (
                          <button
                            className="btn-icon btn-icon-primary"
                            onClick={() => startEditing(enrollment.id)}
                            title="Editar Nota"
                          >
                            <FiEdit2 />
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <FiBook className="empty-icon" />
            <h3>No hay cursos matriculados</h3>
            <p>Este estudiante aún no tiene cursos registrados</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AcademicProgress;
