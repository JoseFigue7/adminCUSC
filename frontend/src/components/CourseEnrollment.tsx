import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  getStudent, 
  getCareerPensum, 
  getCourseEnrollments, 
  createCourseEnrollment,
  getCourses 
} from '../services/api';
import { 
  FiBook, FiCheckCircle, FiXCircle, FiPlus, FiArrowLeft, 
  FiSearch, FiFilter 
} from '../utils/icons';
import { useToast } from '../hooks/useToast';
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

interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  is_required: boolean;
  cuatrimestre_name: string;
  prerequisite: string | null;
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
  const { success, error } = useToast();

  const [student, setStudent] = useState<Student | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCourses, setSelectedCourses] = useState<Set<string>>(new Set());
  const [filterCuatrimestre, setFilterCuatrimestre] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [enrolling, setEnrolling] = useState(false);

  useEffect(() => {
    if (studentId) {
      loadData();
    }
  }, [studentId]);

  const loadData = async () => {
    if (!studentId) return;
    setLoading(true);
    try {
      const [studentRes, enrollmentsRes] = await Promise.all([
        getStudent(studentId),
        getCourseEnrollments(studentId)
      ]);

      setStudent(studentRes.data);
      const enrollments = enrollmentsRes.data.results || enrollmentsRes.data;
      setEnrollments(enrollments);

      // Cargar cursos de la carrera
      if (studentRes.data.career) {
        const coursesRes = await getCourses(studentRes.data.career);
        const allCourses = coursesRes.data.results || coursesRes.data;
        setCourses(allCourses);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const enrolledCourseIds = new Set(enrollments.map(e => e.course_id || (e as any).course || ''));

  const availableCourses = courses.filter(course => {
    // Filtrar cursos ya matriculados
    if (enrolledCourseIds.has(course.id)) return false;
    
    // Filtrar por cuatrimestre
    if (filterCuatrimestre !== 'ALL' && course.cuatrimestre_name !== filterCuatrimestre) {
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

  const toggleCourseSelection = (courseId: string) => {
    const newSelected = new Set(selectedCourses);
    if (newSelected.has(courseId)) {
      newSelected.delete(courseId);
    } else {
      newSelected.add(courseId);
    }
    setSelectedCourses(newSelected);
  };

  const handleEnroll = async () => {
    if (!studentId || selectedCourses.size === 0) return;
    
    setEnrolling(true);
    try {
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
      setSelectedCourses(new Set());
      await loadData();
    } catch (err: any) {
      console.error('Error enrolling courses:', err);
      const errorMessage = err.response?.data?.detail || 'Error al matricular cursos';
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
              <h1>Matrícula de Cursos</h1>
              <p className="header-subtitle">
                {student.first_name} {student.last_name} - {student.carnet} | {student.career_name}
              </p>
            </div>
          </div>
          <div className="header-actions">
            <button 
              onClick={() => navigate(`/students/${studentId}`)} 
              className="btn btn-secondary btn-large"
            >
              <FiArrowLeft /> Volver
            </button>
            {selectedCourses.size > 0 && (
              <button 
                onClick={handleEnroll} 
                className="btn btn-primary btn-large"
                disabled={enrolling}
              >
                {enrolling ? (
                  <>Cargando...</>
                ) : (
                  <>
                    <FiPlus /> Matricular {selectedCourses.size} curso(s)
                  </>
                )}
              </button>
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
          <div className="stats-badge">
            {availableCourses.length} curso(s) disponible(s)
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

