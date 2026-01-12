import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { enrollmentsApi, getStudent, getCareers, catalogosApi } from '../services/api';
import { FiFileText, FiSave, FiX, FiLoader } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './EnrollmentForm.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  first_last_name: string;
  second_last_name?: string;
  full_name: string;
  career: string;
  career_name: string;
}

interface Career {
  id: string;
  name: string;
  cct?: string;
  rvoe_agreement_number?: string;
  rvoe_agreement_date?: string;
}

interface CatalogoItem {
  id: string;
  codigo?: string;
  nombre: string;
}

const EnrollmentForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const studentId = searchParams.get('student');
  const { success, error } = useToast();
  const isEdit = !!id;

  const currentYear = new Date().getFullYear();

  const [enrollment, setEnrollment] = useState({
    student: studentId || '',
    enrollment_status: 'INSCRIPCION',
    school_year: currentYear,
    institutional_id: '',
    cct: '',
    career: '',
    educational_level: '',
    shift: '',
    educational_modality: '',
    rvoe_agreement_number: '',
    rvoe_agreement_date: '',
    status: 'PENDIENTE',
  });

  const [student, setStudent] = useState<Student | null>(null);
  const [careers, setCareers] = useState<Career[]>([]);
  const [catalogos, setCatalogos] = useState({
    niveles: [] as CatalogoItem[],
    modalidades: [] as CatalogoItem[],
    turnos: [] as CatalogoItem[],
  });

  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadInitialData();
    if (studentId) {
      loadStudent(studentId);
    }
    if (isEdit && id) {
      loadEnrollment(id);
    }
  }, [id, studentId, isEdit]);

  const loadInitialData = async () => {
    try {
      await Promise.all([
        loadCareers(),
        loadCatalogos(),
      ]);
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  const loadCareers = async () => {
    try {
      const response = await getCareers();
      const data = response.data.results || response.data;
      setCareers(data);
      // Si hay un estudiante con carrera, seleccionarla por defecto
      if (student && student.career) {
        const studentCareer = data.find((c: Career) => c.id === student.career);
        if (studentCareer) {
          setEnrollment(prev => ({
            ...prev,
            career: studentCareer.id,
            cct: studentCareer.cct || '',
            rvoe_agreement_number: studentCareer.rvoe_agreement_number || '',
            rvoe_agreement_date: studentCareer.rvoe_agreement_date || '',
          }));
        }
      }
    } catch (err) {
      console.error('Error loading careers:', err);
    }
  };

  const loadCatalogos = async () => {
    try {
      const [nivelesRes, modalidadesRes, turnosRes] = await Promise.all([
        catalogosApi.getNivelesEducativos(),
        catalogosApi.getModalidadesEducativas(),
        catalogosApi.getTurnos(),
      ]);

      setCatalogos({
        niveles: nivelesRes.data.results || nivelesRes.data || [],
        modalidades: modalidadesRes.data.results || modalidadesRes.data || [],
        turnos: turnosRes.data.results || turnosRes.data || [],
      });
    } catch (err) {
      console.error('Error loading catalogos:', err);
    }
  };

  const loadStudent = async (studentId: string) => {
    try {
      const response = await getStudent(studentId);
      const data = response.data;
      setStudent(data);
      setEnrollment(prev => ({
        ...prev,
        student: studentId,
        institutional_id: data.carnet || '',
        career: data.career || '',
      }));
      
      // Cargar datos de carrera si existe
      if (data.career) {
        const career = careers.find(c => c.id === data.career);
        if (career) {
          setEnrollment(prev => ({
            ...prev,
            cct: career.cct || '',
            rvoe_agreement_number: career.rvoe_agreement_number || '',
            rvoe_agreement_date: career.rvoe_agreement_date || '',
          }));
        }
      }
    } catch (err: any) {
      console.error('Error loading student:', err);
      error('Error al cargar estudiante');
    }
  };

  const loadEnrollment = async (enrollmentId: string) => {
    setLoadingData(true);
    try {
      const response = await enrollmentsApi.get(enrollmentId);
      const data = response.data;
      setEnrollment({
        student: data.student || data.student_id || '',
        enrollment_status: data.enrollment_status || 'INSCRIPCION',
        school_year: data.school_year || currentYear,
        institutional_id: data.institutional_id || '',
        cct: data.cct || '',
        career: data.career || '',
        educational_level: data.educational_level || '',
        shift: data.shift || '',
        educational_modality: data.educational_modality || '',
        rvoe_agreement_number: data.rvoe_agreement_number || '',
        rvoe_agreement_date: data.rvoe_agreement_date || '',
        status: data.status || 'PENDIENTE',
      });
      
      if (data.student || data.student_id) {
        await loadStudent(data.student || data.student_id);
      }
    } catch (err: any) {
      console.error('Error loading enrollment:', err);
      error('Error al cargar inscripción');
    } finally {
      setLoadingData(false);
    }
  };

  const handleCareerChange = (careerId: string) => {
    const career = careers.find(c => c.id === careerId);
    setEnrollment(prev => ({
      ...prev,
      career: careerId,
      cct: career?.cct || prev.cct,
      rvoe_agreement_number: career?.rvoe_agreement_number || prev.rvoe_agreement_number,
      rvoe_agreement_date: career?.rvoe_agreement_date || prev.rvoe_agreement_date,
    }));
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!enrollment.student) {
      newErrors.student = 'El estudiante es requerido';
    }
    
    if (!enrollment.enrollment_status) {
      newErrors.enrollment_status = 'El estatus de inscripción es requerido';
    }
    
    if (!enrollment.school_year) {
      newErrors.school_year = 'El año del ciclo escolar es requerido';
    } else if (enrollment.school_year < 1900 || enrollment.school_year > 9999) {
      newErrors.school_year = 'El año debe estar entre 1900 y 9999';
    }
    
    if (!enrollment.institutional_id || enrollment.institutional_id.trim() === '') {
      newErrors.institutional_id = 'La matrícula institucional es requerida';
    } else if (enrollment.institutional_id.length > 20) {
      newErrors.institutional_id = 'La matrícula no debe exceder 20 caracteres';
    }
    
    if (!enrollment.cct || enrollment.cct.trim() === '') {
      newErrors.cct = 'El CCT es requerido';
    } else if (enrollment.cct.length !== 10) {
      newErrors.cct = 'El CCT debe tener exactamente 10 caracteres';
    }
    
    if (!enrollment.career) {
      newErrors.career = 'La carrera es requerida';
    }
    
    if (!enrollment.rvoe_agreement_number || enrollment.rvoe_agreement_number.trim() === '') {
      newErrors.rvoe_agreement_number = 'El número de acuerdo RVOE es requerido';
    } else if (enrollment.rvoe_agreement_number.length > 70) {
      newErrors.rvoe_agreement_number = 'El número de acuerdo no debe exceder 70 caracteres';
    }
    
    if (!enrollment.rvoe_agreement_date || enrollment.rvoe_agreement_date.trim() === '') {
      newErrors.rvoe_agreement_date = 'La fecha del acuerdo RVOE es requerida';
    } else if (!/^\d{8}$/.test(enrollment.rvoe_agreement_date)) {
      newErrors.rvoe_agreement_date = 'La fecha debe tener 8 dígitos en formato aaaammdd';
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
      const submitData: any = {
        ...enrollment,
        educational_level: enrollment.educational_level || null,
        shift: enrollment.shift || null,
        educational_modality: enrollment.educational_modality || null,
      };

      if (isEdit && id) {
        await enrollmentsApi.update(id, submitData);
        success('Inscripción actualizada exitosamente');
        setTimeout(() => navigate(`/enrollments/${id}/contract`), 1000);
      } else {
        const response = await enrollmentsApi.create(submitData);
        const enrollmentId = response.data.id;
        success('Inscripción creada exitosamente. Ahora puede generar el contrato.');
        setTimeout(() => navigate(`/enrollments/${enrollmentId}/contract`), 1000);
      }
    } catch (err: any) {
      console.error('Error saving enrollment:', err);
      if (err.response?.data) {
        setErrors(err.response.data);
        const errorMessage = err.response.data.detail || Object.values(err.response.data)[0] || 'Error al guardar inscripción';
        error(Array.isArray(errorMessage) ? errorMessage[0] : errorMessage);
      } else {
        error('Error al guardar inscripción');
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
          <p>Cargando datos de la inscripción...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-title">
          <FiFileText className="header-icon" />
          <div>
            <h1>{isEdit ? 'Editar Inscripción' : 'Nueva Inscripción/Reinscripción'}</h1>
            <p className="header-subtitle">
              {isEdit 
                ? 'Modifica la información de la inscripción' 
                : student 
                  ? `Registra una nueva inscripción para ${student.full_name}` 
                  : 'Registra una nueva inscripción con datos SEP'}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="enrollment-form">
          {/* Sección 1: Estudiante y Estatus - SEP */}
          <div className="form-section">
            <h3 className="section-title">Estudiante y Estatus - SEP</h3>
            {!studentId && (
              <div className="form-group">
                <label>Estudiante *</label>
                <input
                  type="text"
                  value={enrollment.student}
                  onChange={(e) => setEnrollment({ ...enrollment, student: e.target.value })}
                  className={errors.student ? 'error' : ''}
                  placeholder="ID del estudiante"
                  required
                />
                {errors.student && <span className="error-message">{errors.student}</span>}
              </div>
            )}
            
            <div className="form-row">
              <div className="form-group">
                <label>Estatus del alumno *</label>
                <select
                  value={enrollment.enrollment_status}
                  onChange={(e) => setEnrollment({ ...enrollment, enrollment_status: e.target.value })}
                  className={errors.enrollment_status ? 'error' : ''}
                  required
                >
                  <option value="INSCRIPCION">Inscripción</option>
                  <option value="REINSCRIPCION">Reinscripción</option>
                </select>
                {errors.enrollment_status && <span className="error-message">{errors.enrollment_status}</span>}
              </div>
              
              <div className="form-group">
                <label>Año del ciclo escolar *</label>
                <input
                  type="number"
                  value={enrollment.school_year}
                  onChange={(e) => setEnrollment({ ...enrollment, school_year: parseInt(e.target.value) || currentYear })}
                  className={errors.school_year ? 'error' : ''}
                  min="1900"
                  max="9999"
                  required
                  placeholder="Ej: 2024"
                />
                {errors.school_year && <span className="error-message">{errors.school_year}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Matrícula institucional del alumno * (máx. 20 caracteres)</label>
                <input
                  type="text"
                  value={enrollment.institutional_id}
                  onChange={(e) => setEnrollment({ ...enrollment, institutional_id: e.target.value })}
                  className={errors.institutional_id ? 'error' : ''}
                  maxLength={20}
                  required
                  placeholder={student?.carnet || 'Matrícula institucional'}
                />
                {errors.institutional_id && <span className="error-message">{errors.institutional_id}</span>}
                {student?.carnet && <small>Por defecto se usa el carnet: {student.carnet}</small>}
              </div>
            </div>
          </div>

          {/* Sección 2: Información Institucional - SEP */}
          <div className="form-section">
            <h3 className="section-title">Información Institucional - SEP</h3>
            <div className="form-row">
              <div className="form-group">
                <label>CCT (Clave del Centro de Trabajo) * (10 caracteres)</label>
                <input
                  type="text"
                  value={enrollment.cct}
                  onChange={(e) => setEnrollment({ ...enrollment, cct: e.target.value.toUpperCase() })}
                  className={errors.cct ? 'error' : ''}
                  maxLength={10}
                  required
                  placeholder="Ej: 12PCT0001X"
                />
                {errors.cct && <span className="error-message">{errors.cct}</span>}
                <small>Se completa automáticamente desde la carrera si no se especifica</small>
              </div>
              
              <div className="form-group">
                <label>Carrera *</label>
                <select
                  value={enrollment.career}
                  onChange={(e) => handleCareerChange(e.target.value)}
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
                {student?.career_name && <small>Carrera del estudiante: {student.career_name}</small>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Nivel educativo</label>
                <select
                  value={enrollment.educational_level}
                  onChange={(e) => setEnrollment({ ...enrollment, educational_level: e.target.value })}
                >
                  <option value="">Seleccione un nivel</option>
                  {catalogos.niveles.map((nivel) => (
                    <option key={nivel.id} value={nivel.id}>
                      {nivel.nombre}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Turno</label>
                <select
                  value={enrollment.shift}
                  onChange={(e) => setEnrollment({ ...enrollment, shift: e.target.value })}
                >
                  <option value="">Seleccione un turno</option>
                  {catalogos.turnos.map((turno) => (
                    <option key={turno.id} value={turno.id}>
                      {turno.nombre}
                    </option>
                  ))}
                </select>
                <small>Conforme al CCT</small>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Modalidad educativa</label>
                <select
                  value={enrollment.educational_modality}
                  onChange={(e) => setEnrollment({ ...enrollment, educational_modality: e.target.value })}
                >
                  <option value="">Seleccione una modalidad</option>
                  {catalogos.modalidades.map((modalidad) => (
                    <option key={modalidad.id} value={modalidad.id}>
                      {modalidad.nombre}
                    </option>
                  ))}
                </select>
                <small>Escolar, no escolarizada o mixta</small>
              </div>
            </div>
          </div>

          {/* Sección 3: RVOE - SEP */}
          <div className="form-section">
            <h3 className="section-title">Información RVOE - SEP</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Número de Acuerdo de RVOE * (máx. 70 caracteres)</label>
                <input
                  type="text"
                  value={enrollment.rvoe_agreement_number}
                  onChange={(e) => setEnrollment({ ...enrollment, rvoe_agreement_number: e.target.value })}
                  className={errors.rvoe_agreement_number ? 'error' : ''}
                  maxLength={70}
                  required
                  placeholder="Número de acuerdo RVOE"
                />
                {errors.rvoe_agreement_number && <span className="error-message">{errors.rvoe_agreement_number}</span>}
                <small>Se completa automáticamente desde la carrera si no se especifica</small>
              </div>
              
              <div className="form-group">
                <label>Fecha del Acuerdo de RVOE * (formato: aaaammdd)</label>
                <input
                  type="text"
                  value={enrollment.rvoe_agreement_date}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '');
                    if (value.length <= 8) {
                      setEnrollment({ ...enrollment, rvoe_agreement_date: value });
                    }
                  }}
                  className={errors.rvoe_agreement_date ? 'error' : ''}
                  maxLength={8}
                  required
                  placeholder="20240101"
                  pattern="\d{8}"
                />
                {errors.rvoe_agreement_date && <span className="error-message">{errors.rvoe_agreement_date}</span>}
                <small>8 dígitos: año (4), mes (2), día (2). Ej: 20240101</small>
              </div>
            </div>
          </div>

          {/* Sección 4: Estado Administrativo */}
          {isEdit && (
            <div className="form-section">
              <h3 className="section-title">Estado Administrativo</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Estado</label>
                  <select
                    value={enrollment.status}
                    onChange={(e) => setEnrollment({ ...enrollment, status: e.target.value })}
                  >
                    <option value="PENDIENTE">Pendiente</option>
                    <option value="EN_REVISION">En Revisión</option>
                    <option value="APROBADA">Aprobada</option>
                    <option value="RECHAZADA">Rechazada</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-large" disabled={loading}>
              {loading ? (
                <>
                  <FiLoader className="spinning" /> Guardando...
                </>
              ) : (
                <>
                  <FiSave /> {isEdit ? 'Actualizar' : 'Crear'} Inscripción
                </>
              )}
            </button>
            <button 
              type="button" 
              className="btn btn-secondary btn-large" 
              onClick={() => navigate(studentId ? `/students/${studentId}` : '/students')}
            >
              <FiX /> Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EnrollmentForm;

