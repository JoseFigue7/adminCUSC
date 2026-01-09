import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCareerPensum, getCareers, getCourses } from '../services/api';
import { FiBook, FiArrowLeft, FiCheckCircle } from '../utils/icons';
import './shared.css';
import './CareerPensum.css';

interface Career {
  id: string;
  name: string;
  code: string;
}

interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  is_required: boolean;
  cuatrimestre_name: string;
  prerequisite: string | null;
  prerequisite_name: string | null;
}

interface Cuatrimestre {
  name: string;
  courses: Course[];
}

const CareerPensum: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [career, setCareer] = useState<Career | null>(null);
  const [cuatrimestres, setCuatrimestres] = useState<Cuatrimestre[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadPensum();
    }
  }, [id]);

  const loadPensum = async () => {
    setLoading(true);
    try {
      const [careersRes, coursesRes] = await Promise.all([
        getCareers(),
        getCourses(id!)
      ]);

      const careers = careersRes.data.results || careersRes.data;
      const selectedCareer = careers.find((c: Career) => c.id === id);
      setCareer(selectedCareer || null);

      // Obtener todos los cursos de la carrera
      const allCourses = coursesRes.data.results || coursesRes.data;
      
      // Organizar cursos por cuatrimestre
      const courses: Course[] = allCourses.map((course: any) => ({
        ...course,
        cuatrimestre_name: course.cuatrimestre_name || 'Sin Cuatrimestre'
      }));
      
      const cuatrimestreMap = new Map<string, Course[]>();

      courses.forEach(course => {
        const cuatName = course.cuatrimestre_name || 'Sin Cuatrimestre';
        if (!cuatrimestreMap.has(cuatName)) {
          cuatrimestreMap.set(cuatName, []);
        }
        cuatrimestreMap.get(cuatName)!.push(course);
      });

      const cuatrimestresArray = Array.from(cuatrimestreMap.entries())
        .map(([name, courses]) => ({
          name,
          courses: courses.sort((a, b) => a.code.localeCompare(b.code))
        }))
        .sort((a, b) => a.name.localeCompare(b.name));

      setCuatrimestres(cuatrimestresArray);
    } catch (error) {
      console.error('Error loading pensum:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalCourses = cuatrimestres.reduce((sum, cuat) => sum + cuat.courses.length, 0);
  const totalCredits = cuatrimestres.reduce(
    (sum, cuat) => sum + cuat.courses.reduce((s, c) => s + (c.credits || 0), 0),
    0
  );
  const requiredCourses = cuatrimestres.reduce(
    (sum, cuat) => sum + cuat.courses.filter(c => c.is_required).length,
    0
  );

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando pensum...</p>
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
              <h1>Pensum de Estudio</h1>
              <p className="header-subtitle">
                {career?.name || 'Carrera'} - Código: {career?.code || 'N/A'}
              </p>
            </div>
          </div>
          <button onClick={() => navigate('/students')} className="btn btn-secondary btn-large">
            <FiArrowLeft /> Volver
          </button>
        </div>
      </div>

      <div className="pensum-stats">
        <div className="stat-card">
          <h3>Total de Cursos</h3>
          <p className="stat-value">{totalCourses}</p>
        </div>
        <div className="stat-card">
          <h3>Créditos Totales</h3>
          <p className="stat-value">{totalCredits}</p>
        </div>
        <div className="stat-card">
          <h3>Cursos Obligatorios</h3>
          <p className="stat-value">{requiredCourses}</p>
        </div>
        <div className="stat-card">
          <h3>Cuatrimestres</h3>
          <p className="stat-value">{cuatrimestres.length}</p>
        </div>
      </div>

      <div className="cuatrimestres-container">
        {cuatrimestres.map((cuatrimestre, index) => (
          <div key={cuatrimestre.name} className="card cuatrimestre-card">
            <div className="cuatrimestre-header">
              <h2 className="cuatrimestre-title">
                {cuatrimestre.name}
              </h2>
              <span className="cuatrimestre-count">
                {cuatrimestre.courses.length} curso(s)
              </span>
            </div>
            
            <div className="courses-list">
              {cuatrimestre.courses.map((course) => (
                <div key={course.id} className="course-item">
                  <div className="course-main">
                    <div className="course-code-badge">{course.code}</div>
                    <div className="course-details">
                      <h4 className="course-title">{course.name}</h4>
                      <div className="course-meta">
                        <span className="course-credits">{course.credits} créditos</span>
                        {course.is_required && (
                          <span className="required-tag">Obligatorio</span>
                        )}
                        {course.prerequisite && (
                          <span className="prerequisite-tag">
                            Prereq: {course.prerequisite_name || course.prerequisite}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  {course.is_required && (
                    <FiCheckCircle className="required-icon" />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CareerPensum;

