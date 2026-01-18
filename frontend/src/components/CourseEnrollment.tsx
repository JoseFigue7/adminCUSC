import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  getStudent, 
  getCareerPensum, 
  getCourseEnrollments, 
  createCourseEnrollment,
  getCourses,
  academicsApi
} from '../services/api';
import { 
  FiBook, FiCheckCircle, FiXCircle, FiPlus, FiArrowLeft, 
  FiSearch, FiFilter, FiClock, FiAlertTriangle, FiDollarSign,
  FiDownload, FiInfo, FiX
} from '../utils/icons';
import { useToast } from '../hooks/useToast';
import { getAcademicPeriod, getCuatrimestresByPeriod, getPeriodName } from '../utils/academicPeriod';
import './shared.css';
import './CourseEnrollment.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
  career: string;
  career_name: string;
}

interface CourseSchedule {
  id: string;
  day: string;
  start_time: string;
  end_time: string;
}

interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  is_required: boolean;
  cuatrimestre_name: string;
  cuatrimestre_number?: number;
  prerequisite: string | null;
  schedules?: CourseSchedule[];
}

interface Enrollment {
  id: string;
  course_id?: string;
  course?: string;
  course_code: string;
  course_name: string;
  status: string;
}

const CourseEnrollment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const studentId = searchParams.get('studentId');
  const cuatrimestreEnrollmentId = searchParams.get('cuatrimestreEnrollmentId');
  const { success, error } = useToast();

  const [student, setStudent] = useState<Student | null>(null);
  const [cuatrimestreEnrollment, setCuatrimestreEnrollment] = useState<any>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCourses, setSelectedCourses] = useState<Set<string>>(new Set());
  const [filterCuatrimestre, setFilterCuatrimestre] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [enrolling, setEnrolling] = useState(false);
  const [tuitionData, setTuitionData] = useState<any>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showBoletaModal, setShowBoletaModal] = useState(false);
  const [boletaUrl, setBoletaUrl] = useState<string | null>(null);
  const [paymentOption, setPaymentOption] = useState<'monthly' | 'full'>('monthly');
  const [loadingTuition, setLoadingTuition] = useState(false);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (studentId || cuatrimestreEnrollmentId) {
      loadData();
    }
  }, [studentId, cuatrimestreEnrollmentId]);

  useEffect(() => {
    // Cargar datos de colegiatura cuando hay cursos asignados y el estado permite confirmar
    if (cuatrimestreEnrollmentId && cuatrimestreEnrollment && 
        (cuatrimestreEnrollment.status === 'PENDIENTE_PAGO' || 
         cuatrimestreEnrollment.status === 'PENDIENTE_CONFIRMACION') && 
        enrollments.length > 0) {
      loadTuitionData();
    }
  }, [cuatrimestreEnrollmentId, cuatrimestreEnrollment?.status, enrollments.length]);

  const loadData = async () => {
    if (!studentId && !cuatrimestreEnrollmentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      let studentData;
      let enrollmentData;

      if (cuatrimestreEnrollmentId) {
        // Cargar datos desde cuatrimestre enrollment
        const [cuatEnrollmentRes, coursesRes, availableCoursesRes] = await Promise.all([
          academicsApi.getCuatrimestreEnrollment(cuatrimestreEnrollmentId),
          academicsApi.getCoursesInCuatrimestre(cuatrimestreEnrollmentId),
          academicsApi.getAvailableCourses(cuatrimestreEnrollmentId)
        ]);

        enrollmentData = cuatEnrollmentRes.data;
        setCuatrimestreEnrollment(enrollmentData);
        studentData = { data: await getStudent(enrollmentData.student).then(r => r.data) };
        
        const courseEnrollments = coursesRes.data.results || coursesRes.data;
        setEnrollments(courseEnrollments);
        
        // Usar el nuevo endpoint que filtra automáticamente por período académico
        // El endpoint devuelve { courses: [...], enrollment_period: 1, period_cuatrimestres: [1,4,7], total_available: X }
        const availableCourses = availableCoursesRes.data.courses || availableCoursesRes.data;
        setCourses(Array.isArray(availableCourses) ? availableCourses : []);
      } else if (studentId) {
        // Modo normal sin cuatrimestre enrollment
        const [studentRes, enrollmentsRes] = await Promise.all([
          getStudent(studentId),
          getCourseEnrollments(studentId)
        ]);

        studentData = studentRes;
        const enrollments = enrollmentsRes.data.results || enrollmentsRes.data;
        setEnrollments(enrollments);

        // Cargar cursos de la carrera
        if (studentRes.data.career) {
          const coursesRes = await getCourses({ career: studentRes.data.career });
          const allCourses = coursesRes.data.results || coursesRes.data;
          setCourses(allCourses);
        }
      }

      if (studentData) {
        setStudent(studentData.data);
      }
    } catch (err: any) {
      console.error('Error loading data:', err);
      console.error('Error response:', err.response);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al cargar los datos';
      error(errorMessage);
      setStudent(null);
    } finally {
      setLoading(false);
    }
  };

  const enrolledCourseIds = new Set(enrollments.map(e => e.course_id || (e as any).course || ''));

  // Filtrar cursos aprobados (no se pueden volver a inscribir)
  const approvedCourseIds = new Set(
    enrollments
      .filter(e => e.status === 'APROBADO')
      .map(e => e.course_id || (e as any).course || '')
  );

  const availableCourses = courses.filter(course => {
    // Filtrar cursos ya matriculados en este cuatrimestre
    if (enrolledCourseIds.has(course.id)) return false;
    
    // Filtrar cursos ya aprobados (no se pueden volver a inscribir)
    if (approvedCourseIds.has(course.id)) return false;
    
    // Si hay cuatrimestreEnrollment, los cursos ya están filtrados por período en loadData
    // Solo aplicar filtro de búsqueda si existe
    
    // Filtrar por cuatrimestre (si no hay cuatrimestreEnrollment)
    if (!cuatrimestreEnrollment && filterCuatrimestre !== 'ALL' && course.cuatrimestre_name !== filterCuatrimestre) {
      return false;
    }
    
    // Filtrar por búsqueda
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        course.code.toLowerCase().includes(search) ||
        course.name.toLowerCase().includes(search)
      );
    }
    
    return true;
  });

  const cuatrimestres = Array.from(new Set(courses.map(c => c.cuatrimestre_name))).sort();

  // Función para verificar si dos horarios se traslapan
  const schedulesOverlap = (schedule1: CourseSchedule, schedule2: CourseSchedule): boolean => {
    if (schedule1.day !== schedule2.day) return false;
    
    const start1 = new Date(`2000-01-01T${schedule1.start_time}`);
    const end1 = new Date(`2000-01-01T${schedule1.end_time}`);
    const start2 = new Date(`2000-01-01T${schedule2.start_time}`);
    const end2 = new Date(`2000-01-01T${schedule2.end_time}`);
    
    return start1 < end2 && start2 < end1;
  };

  // Función para verificar traslapes entre cursos seleccionados
  const checkScheduleOverlaps = (selectedCourseIds: Set<string>): { hasOverlap: boolean; overlapDetails: string[] } => {
    const overlaps: string[] = [];
    const selectedCoursesList = courses.filter(c => selectedCourseIds.has(c.id));
    
    for (let i = 0; i < selectedCoursesList.length; i++) {
      const course1 = selectedCoursesList[i];
      const schedules1 = course1.schedules || [];
      
      if (schedules1.length === 0) continue;
      
      for (let j = i + 1; j < selectedCoursesList.length; j++) {
        const course2 = selectedCoursesList[j];
        const schedules2 = course2.schedules || [];
        
        if (schedules2.length === 0) continue;
        
        // Verificar traslapes entre todos los horarios de course1 y course2
        for (const s1 of schedules1) {
          for (const s2 of schedules2) {
            if (schedulesOverlap(s1, s2)) {
              const time1 = `${s1.start_time.substring(0, 5)}-${s1.end_time.substring(0, 5)}`;
              const time2 = `${s2.start_time.substring(0, 5)}-${s2.end_time.substring(0, 5)}`;
              overlaps.push(`${course1.code} (${s1.day} ${time1}) y ${course2.code} (${s2.day} ${time2})`);
            }
          }
        }
      }
    }
    
    return {
      hasOverlap: overlaps.length > 0,
      overlapDetails: overlaps
    };
  };

  const toggleCourseSelection = (courseId: string) => {
    const newSelected = new Set(selectedCourses);
    
    if (newSelected.has(courseId)) {
      newSelected.delete(courseId);
    } else {
      // Validar máximo 7 cursos
      if (cuatrimestreEnrollmentId && newSelected.size >= 7) {
        error('No se pueden seleccionar más de 7 cursos por cuatrimestre');
        return;
      }
      
      // Validar traslapes antes de agregar
      newSelected.add(courseId);
      const overlapCheck = checkScheduleOverlaps(newSelected);
      
      if (overlapCheck.hasOverlap) {
        newSelected.delete(courseId);
        error(`Los horarios se traslapan: ${overlapCheck.overlapDetails[0]}`);
        return;
      }
    }
    
    setSelectedCourses(newSelected);
  };

  const handleEnroll = async () => {
    if ((!studentId && !cuatrimestreEnrollmentId) || selectedCourses.size === 0) return;
    
    setEnrolling(true);
    try {
      if (cuatrimestreEnrollmentId) {
        // Pre-asignar cursos (flujo presencial guiado)
        await academicsApi.preAssignCourses(
          cuatrimestreEnrollmentId,
          Array.from(selectedCourses)
        );
        
        // Recargar datos para obtener el nuevo estado
        await loadData();
        
        // Generar y mostrar boleta de preview
        await handlePreviewBoleta();
        
        success(`Se pre-asignaron ${selectedCourses.size} curso(s). Revise la boleta antes de confirmar.`);
      } else if (studentId) {
        // Modo normal: matricular sin cuatrimestre enrollment
        await Promise.all(
          Array.from(selectedCourses).map(courseId => 
            createCourseEnrollment({
              student: studentId,
              course: courseId,
              status: 'MATRICULADO'
            })
          )
        );
        success(`Se matricularon ${selectedCourses.size} curso(s) exitosamente`);
      }
      
      setSelectedCourses(new Set());
      await loadData();
    } catch (err: any) {
      // Solo loggear en desarrollo, no en producción
      if (process.env.NODE_ENV === 'development') {
        console.error('Error enrolling courses:', err);
        console.error('Error response:', err.response?.data);
      }
      
      let errorMessage = 'Error al matricular cursos';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // Manejar errores de traslape de horarios de forma especial
        // Verificar tanto en español como en inglés, y diferentes variaciones
        const isOverlapError = errorData.error && (
          errorData.error.toLowerCase().includes('traslape') ||
          errorData.error.toLowerCase().includes('traslapan') ||
          errorData.error.toLowerCase().includes('horario') ||
          errorData.error.toLowerCase().includes('overlap')
        );
        
        if (isOverlapError && errorData.errors && Array.isArray(errorData.errors) && errorData.errors.length > 0) {
          errorMessage = '⚠️ HAY TRASLAPES DE HORARIOS\n\nLos siguientes cursos tienen horarios que se traslapan:\n\n';
          
          // Formatear los errores de traslape de forma clara
          const overlapErrors = errorData.errors.map((errMsg: string) => {
            return `• ${errMsg}`;
          });
          
          errorMessage += overlapErrors.join('\n\n');
          errorMessage += '\n\nPor favor, deseleccione algunos cursos o elija cursos con horarios diferentes.';
          
          error(errorMessage);
          return;
        }
        
        // Si hay errores detallados, mostrarlos
        if (errorData.errors && Array.isArray(errorData.errors) && errorData.errors.length > 0) {
          errorMessage = errorData.error || 'Error al matricular cursos';
          
          // Formatear errores de forma más legible
          const errorsList = errorData.errors.map((errMsg: string, index: number) => {
            return `${index + 1}. ${errMsg}`;
          }).join('\n\n');
          
          error(`${errorMessage}\n\n${errorsList}`);
          return;
        }
        
        // Si hay un error simple
        errorMessage = errorData.detail || errorData.error || errorMessage;
      }
      
      error(errorMessage);
    } finally {
      setEnrolling(false);
    }
  };

  const loadTuitionData = async () => {
    if (!cuatrimestreEnrollmentId) return;
    
    setLoadingTuition(true);
    try {
      const res = await academicsApi.calculateTuition(cuatrimestreEnrollmentId);
      setTuitionData(res.data);
    } catch (err: any) {
      console.error('Error loading tuition:', err);
    } finally {
      setLoadingTuition(false);
    }
  };

  useEffect(() => {
    if (cuatrimestreEnrollmentId && cuatrimestreEnrollment && 
        cuatrimestreEnrollment.status === 'PENDIENTE_CONFIRMACION' && enrollments.length > 0) {
      loadTuitionData();
    }
  }, [cuatrimestreEnrollmentId, cuatrimestreEnrollment, enrollments.length]);

  const handleDownloadAssignmentSheet = async () => {
    if (!cuatrimestreEnrollmentId) return;
    
    try {
      const res = await academicsApi.getAssignmentSheet(cuatrimestreEnrollmentId);
      // Por ahora solo mostramos los datos, más adelante podemos generar PDF
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hoja-asignacion-${cuatrimestreEnrollmentId}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      success('Hoja de asignación descargada');
    } catch (err: any) {
      console.error('Error downloading assignment sheet:', err);
      error('Error al descargar la hoja de asignación');
    }
  };

  const handlePreviewBoleta = async () => {
    if (!cuatrimestreEnrollmentId) return;
    
    try {
      const response = await academicsApi.previewBoleta(cuatrimestreEnrollmentId);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      setBoletaUrl(url);
      setShowBoletaModal(true);
    } catch (err: any) {
      console.error('Error generating boleta:', err);
      error(err.response?.data?.error || 'Error al generar la boleta');
    }
  };

  const handlePrintBoleta = () => {
    if (boletaUrl) {
      const printWindow = window.open(boletaUrl, '_blank');
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print();
        };
      }
    }
  };

  const handleConfirmAssignment = async () => {
    if (!cuatrimestreEnrollmentId) return;
    
    if (!window.confirm(`¿Está seguro de confirmar la asignación? Una vez confirmada, no se podrá modificar para este cuatrimestre.`)) {
      return;
    }
    
    setConfirming(true);
    try {
      await academicsApi.confirmCourseAssignment(cuatrimestreEnrollmentId);
      success('Asignación confirmada exitosamente. El plan de pagos ha sido generado.');
      setShowBoletaModal(false);
      setShowConfirmModal(false);
      setBoletaUrl(null);
      setSelectedCourses(new Set());
      await loadData();
      // Recargar para obtener el nuevo estado
      const res = await academicsApi.getCuatrimestreEnrollment(cuatrimestreEnrollmentId);
      setCuatrimestreEnrollment(res.data);
    } catch (err: any) {
      console.error('Error confirming assignment:', err);
      error(err.response?.data?.error || 'Error al confirmar la asignación');
    } finally {
      setConfirming(false);
    }
  };

  const handleBackToSelection = () => {
    setShowBoletaModal(false);
    setBoletaUrl(null);
    // El estado ya está en CURSOS_PREASIGNADOS, el usuario puede modificar
  };

  const canEnrollInCourse = (course: Course): boolean => {
    if (!course.prerequisite) return true;
    
    // Verificar si el prerequisito está aprobado
    const prerequisiteEnrollment = enrollments.find(
      e => (e.course_id || (e as any).course) === course.prerequisite && e.status === 'APROBADO'
    );
    
    return !!prerequisiteEnrollment;
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando cursos disponibles...</p>
        </div>
      </div>
    );
  }

  if (!student && !cuatrimestreEnrollment) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiBook className="empty-icon" />
          <h3>{studentId || cuatrimestreEnrollmentId ? 'Estudiante no encontrado' : 'No se especificó un estudiante'}</h3>
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
              <h1>Matrícula de Cursos</h1>
              <p className="header-subtitle">
                {student.first_name} {student.last_name} - {student.carnet} | {student.career_name}
                {cuatrimestreEnrollment && (
                  <>
                    {' | '}{cuatrimestreEnrollment.cuatrimestre_name} {cuatrimestreEnrollment.academic_year}
                    {cuatrimestreEnrollment.cuatrimestre_number && (
                      <> ({getPeriodName(getAcademicPeriod(cuatrimestreEnrollment.cuatrimestre_number) || 0)})</>
                    )}
                  </>
                )}
              </p>
            </div>
          </div>
          <div className="header-actions">
            <button 
              onClick={() => {
                if (cuatrimestreEnrollmentId && cuatrimestreEnrollment) {
                  navigate(`/cuatrimestre-enrollments?studentId=${cuatrimestreEnrollment.student}`);
                } else if (studentId) {
                  navigate(`/students/${studentId}`);
                } else {
                  navigate('/students');
                }
              }} 
              className="btn btn-secondary btn-large"
            >
              <FiArrowLeft /> Volver
            </button>
            {selectedCourses.size > 0 && (
              <>
                {cuatrimestreEnrollmentId && selectedCourses.size > 7 && (
                  <div className="warning-message" style={{ 
                    background: '#fed7d7', 
                    color: '#742a2a', 
                    padding: '0.5rem 1rem', 
                    borderRadius: '4px',
                    marginRight: '1rem'
                  }}>
                    <FiAlertTriangle style={{ marginRight: '0.5rem' }} />
                    Máximo 7 cursos permitidos
                  </div>
                )}
                <button 
                  onClick={handleEnroll} 
                  className="btn btn-primary btn-large"
                  disabled={enrolling || (cuatrimestreEnrollmentId && selectedCourses.size > 7)}
                >
                  {enrolling ? (
                    <>Cargando...</>
                  ) : (
                    <>
                      <FiPlus /> Matricular {selectedCourses.size} curso(s)
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-toolbar">
          <div className="search-box">
            <FiSearch className="search-icon" />
            <input
              type="text"
              placeholder="Buscar por código o nombre de curso..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          {!cuatrimestreEnrollment && (
            <div className="filter-group">
              <FiFilter className="filter-icon" />
              <select
                value={filterCuatrimestre}
                onChange={(e) => setFilterCuatrimestre(e.target.value)}
                className="filter-select"
              >
                <option value="ALL">Todos los cuatrimestres</option>
                {cuatrimestres.map(cuat => (
                  <option key={cuat} value={cuat}>{cuat}</option>
                ))}
              </select>
            </div>
          )}
          <div className="stats-badge">
            {availableCourses.length} curso(s) disponible(s)
            {cuatrimestreEnrollmentId && (
              <span style={{ marginLeft: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                | Máximo 7 cursos | {selectedCourses.size} seleccionado(s)
              </span>
            )}
          </div>
        </div>

        {availableCourses.length > 0 ? (
          <div className="courses-grid">
            {availableCourses.map((course) => {
              const canEnroll = canEnrollInCourse(course);
              const isSelected = selectedCourses.has(course.id);
              
              return (
                <div
                  key={course.id}
                  className={`course-card ${isSelected ? 'selected' : ''} ${!canEnroll ? 'disabled' : ''}`}
                  onClick={() => canEnroll && toggleCourseSelection(course.id)}
                >
                  <div className="course-header">
                    <div className="course-code">{course.code}</div>
                    <div className="course-checkbox">
                      {isSelected ? (
                        <FiCheckCircle className="check-icon" />
                      ) : (
                        <div className="check-placeholder" />
                      )}
                    </div>
                  </div>
                  <h3 className="course-name">{course.name}</h3>
                  <div className="course-info">
                    <span className="course-cuatrimestre">{course.cuatrimestre_name}</span>
                    <span className="course-credits">{course.credits} créditos</span>
                  </div>
                  
                  {/* Mostrar horarios */}
                  {course.schedules && course.schedules.length > 0 && (
                    <div className="course-schedules" style={{ marginTop: '0.75rem', fontSize: '0.875rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem', color: '#6b7280' }}>
                        <FiClock style={{ marginRight: '0.5rem' }} />
                        <strong>Horarios:</strong>
                      </div>
                      {course.schedules.map((schedule) => (
                        <div key={schedule.id} style={{ 
                          marginLeft: '1.5rem', 
                          marginBottom: '0.25rem',
                          color: '#4b5563'
                        }}>
                          {schedule.day}: {schedule.start_time.substring(0, 5)} - {schedule.end_time.substring(0, 5)}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {course.prerequisite && !canEnroll && (
                    <div className="prerequisite-warning">
                      Requiere aprobar el prerequisito
                    </div>
                  )}
                  {course.is_required && (
                    <span className="required-badge">Obligatorio</span>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="empty-state">
            <FiBook className="empty-icon" />
            <h3>No hay cursos disponibles</h3>
            <p>
              {searchTerm || filterCuatrimestre !== 'ALL'
                ? 'No hay cursos que coincidan con los filtros aplicados'
                : 'El estudiante ya está matriculado en todos los cursos disponibles'}
            </p>
          </div>
        )}
      </div>

      {enrollments.length > 0 && (
        <div className="card">
          <h2 className="card-title">
            <FiCheckCircle className="card-title-icon" />
            Cursos Matriculados ({enrollments.length})
          </h2>
          <div className="enrolled-courses-list">
            {enrollments.map((enrollment) => (
              <div key={enrollment.id} className="enrolled-course-item">
                <div>
                  <strong>{enrollment.course_code}</strong> - {enrollment.course_name}
                </div>
                <span className={`status-badge status-${enrollment.status.toLowerCase()}`}>
                  {enrollment.status}
                </span>
              </div>
            ))}
          </div>
          
          {/* Mostrar información de colegiatura y opciones de confirmación */}
          {cuatrimestreEnrollmentId && cuatrimestreEnrollment && 
           (cuatrimestreEnrollment.status === 'PENDIENTE_PAGO' || 
            cuatrimestreEnrollment.status === 'PENDIENTE_CONFIRMACION') && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
              {loadingTuition ? (
                <div style={{ textAlign: 'center', padding: '1rem' }}>
                  <div className="spinner" style={{ margin: '0 auto' }}></div>
                  <p>Cargando información de colegiatura...</p>
                </div>
              ) : tuitionData ? (
                <>
                  <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center' }}>
                    <FiDollarSign style={{ marginRight: '0.5rem' }} />
                    Información de Colegiatura
                  </h3>
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <strong>Costo total de colegiatura:</strong>
                      <strong style={{ fontSize: '1.25rem', color: '#059669' }}>
                        ${parseFloat(tuitionData.total_tuition).toFixed(2)}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
                      <span>Pago mensual (4 meses):</span>
                      <span>${parseFloat(tuitionData.payment_plan.monthly_payment).toFixed(2)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
                      <span>Pago completo con descuento (10%):</span>
                      <span>${parseFloat(tuitionData.payment_plan.full_payment_total).toFixed(2)} 
                        <span style={{ color: '#059669', marginLeft: '0.5rem' }}>
                          (Ahorra ${parseFloat(tuitionData.payment_plan.full_payment_discount).toFixed(2)})
                        </span>
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    <button
                      onClick={handleDownloadAssignmentSheet}
                      className="btn btn-secondary"
                    >
                      <FiDownload /> Descargar Hoja de Asignación
                    </button>
                    <button
                      onClick={() => setShowConfirmModal(true)}
                      className="btn btn-primary"
                    >
                      <FiCheckCircle /> Confirmar Asignación
                    </button>
                    <button
                      onClick={() => navigate(`/cuatrimestre-enrollments?studentId=${student?.id}`)}
                      className="btn btn-secondary"
                    >
                      <FiArrowLeft /> Volver Atrás
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          )}
        </div>
      )}

      {/* Modal de boleta de asignación (preview) */}
      {showBoletaModal && boletaUrl && (
        <div className="modal-overlay" onClick={() => setShowBoletaModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '90%', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
            <div className="modal-header">
              <h2>Boleta de Asignación Académica (Preview)</h2>
              <button className="modal-close" onClick={() => setShowBoletaModal(false)}>
                <FiX />
              </button>
            </div>
            <div style={{ padding: '1.5rem', flex: 1, overflow: 'auto' }}>
              <div style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '8px' }}>
                <FiInfo style={{ marginRight: '0.5rem', color: '#d97706' }} />
                <span style={{ color: '#92400e' }}>
                  Esta es una boleta informativa. La asignación NO está confirmada hasta que presione "Confirmar asignación".
                </span>
              </div>
              <iframe 
                src={boletaUrl} 
                style={{ width: '100%', height: '70vh', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                title="Boleta de Asignación"
              />
            </div>
            <div className="modal-actions" style={{ padding: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
              <button 
                type="button" 
                onClick={handleBackToSelection} 
                className="btn btn-secondary"
              >
                <FiArrowLeft /> Regresar a Selección
              </button>
              <button 
                type="button" 
                onClick={handlePrintBoleta} 
                className="btn btn-secondary"
              >
                <FiDownload /> Imprimir Boleta
              </button>
              <button 
                onClick={handleConfirmAssignment} 
                className="btn btn-primary"
                disabled={confirming}
              >
                {confirming ? 'Confirmando...' : (
                  <>
                    <FiCheckCircle /> Confirmar Asignación
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de confirmación de asignación */}
      {showConfirmModal && tuitionData && (
        <div className="modal-overlay" onClick={() => setShowConfirmModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <h2>Confirmar Asignación de Cursos</h2>
              <button className="modal-close" onClick={() => setShowConfirmModal(false)}>
                <FiX />
              </button>
            </div>
            <div style={{ padding: '1.5rem' }}>
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '1rem', padding: '1rem', backgroundColor: '#fef3c7', borderRadius: '8px' }}>
                  <FiInfo style={{ marginRight: '0.5rem', color: '#d97706' }} />
                  <span style={{ color: '#92400e' }}>
                    Una vez confirmada, la asignación no podrá modificarse para este cuatrimestre.
                  </span>
                </div>
                <h3 style={{ marginBottom: '1rem' }}>Seleccione la opción de pago:</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', padding: '1rem', border: '2px solid #e5e7eb', borderRadius: '8px', cursor: 'pointer' }}
                    className={paymentOption === 'monthly' ? 'selected' : ''}>
                    <input
                      type="radio"
                      name="paymentOption"
                      value="monthly"
                      checked={paymentOption === 'monthly'}
                      onChange={(e) => setPaymentOption(e.target.value as 'monthly' | 'full')}
                      style={{ marginRight: '0.75rem' }}
                    />
                    <div style={{ flex: 1 }}>
                      <strong>Pago Mensual (4 pagos)</strong>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem' }}>
                        ${parseFloat(tuitionData.payment_plan.monthly_payment).toFixed(2)} por mes
                      </div>
                    </div>
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', padding: '1rem', border: '2px solid #e5e7eb', borderRadius: '8px', cursor: 'pointer' }}
                    className={paymentOption === 'full' ? 'selected' : ''}>
                    <input
                      type="radio"
                      name="paymentOption"
                      value="full"
                      checked={paymentOption === 'full'}
                      onChange={(e) => setPaymentOption(e.target.value as 'monthly' | 'full')}
                      style={{ marginRight: '0.75rem' }}
                    />
                    <div style={{ flex: 1 }}>
                      <strong>Pago Completo (10% descuento)</strong>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem' }}>
                        ${parseFloat(tuitionData.payment_plan.full_payment_total).toFixed(2)} 
                        <span style={{ color: '#059669', marginLeft: '0.5rem' }}>
                          (Ahorra ${parseFloat(tuitionData.payment_plan.full_payment_discount).toFixed(2)})
                        </span>
                      </div>
                    </div>
                  </label>
                </div>
              </div>
              <div className="modal-actions">
                <button 
                  type="button" 
                  onClick={() => setShowConfirmModal(false)} 
                  className="btn btn-secondary"
                  disabled={confirming}
                >
                  Cancelar
                </button>
                <button 
                  onClick={handleConfirmAssignment} 
                  className="btn btn-primary"
                  disabled={confirming}
                >
                  {confirming ? 'Confirmando...' : 'Confirmar Asignación'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourseEnrollment;

