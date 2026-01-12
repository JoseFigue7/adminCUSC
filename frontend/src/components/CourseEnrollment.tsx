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
  FiSearch, FiFilter, FiClock, FiAlertTriangle
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

  useEffect(() => {
    if (studentId || cuatrimestreEnrollmentId) {
      loadData();
    }
  }, [studentId, cuatrimestreEnrollmentId]);

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
        const [cuatEnrollmentRes, coursesRes] = await Promise.all([
          academicsApi.getCuatrimestreEnrollment(cuatrimestreEnrollmentId),
          academicsApi.getCoursesInCuatrimestre(cuatrimestreEnrollmentId)
        ]);

        enrollmentData = cuatEnrollmentRes.data;
        setCuatrimestreEnrollment(enrollmentData);
        studentData = { data: await getStudent(enrollmentData.student).then(r => r.data) };
        
        const courseEnrollments = coursesRes.data.results || coursesRes.data;
        setEnrollments(courseEnrollments);
        
        // Cargar cursos disponibles del mismo período académico (no solo del mismo cuatrimestre)
        const cuatrimestreRes = await academicsApi.getCuatrimestres({ id: enrollmentData.cuatrimestre });
        const cuatrimestre = (cuatrimestreRes.data.results || cuatrimestreRes.data)[0];
        
        if (cuatrimestre && enrollmentData.cuatrimestre_number) {
          // Obtener el período académico
          const period = getAcademicPeriod(enrollmentData.cuatrimestre_number);
          if (period && cuatrimestre.career) {
            // Obtener números de cuatrimestres del mismo período
            const periodCuatrimestres = getCuatrimestresByPeriod(period);
            
            // Cargar todos los cursos de la carrera con page_size grande para evitar paginación
            const allCoursesRes = await getCourses({ career: cuatrimestre.career, page_size: 1000 });
            const allCourses = allCoursesRes.data.results || allCoursesRes.data;
            
            // Filtrar cursos que pertenezcan al mismo período académico
            const periodCourses = allCourses.filter((course: Course) => 
              course.cuatrimestre_number && periodCuatrimestres.includes(course.cuatrimestre_number)
            );
            setCourses(periodCourses);
          }
        }
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
        // Inscribir cursos en el cuatrimestre específico
        await academicsApi.enrollCoursesInCuatrimestre(
          cuatrimestreEnrollmentId,
          Array.from(selectedCourses)
        );
        success(`Se matricularon ${selectedCourses.size} curso(s) exitosamente`);
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
      console.error('Error enrolling courses:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al matricular cursos';
      error(errorMessage);
    } finally {
      setEnrolling(false);
    }
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
        </div>
      )}
    </div>
  );
};

export default CourseEnrollment;

