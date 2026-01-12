import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  academicsApi,
  getCareers,
  getStudent
} from '../services/api';
import { 
  FiUpload, FiFileText, FiCheckCircle, FiXCircle, FiDownload,
  FiArrowLeft, FiSearch, FiRefreshCw
} from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './GradeUpload.css';

interface Career {
  id: string;
  name: string;
  code: number;
}

interface Cuatrimestre {
  id: string;
  name: string;
  number: number;
}

interface CuatrimestreEnrollment {
  id: string;
  student: string;
  student_name: string;
  student_carnet: string;
  cuatrimestre: string;
  cuatrimestre_name: string;
  academic_year: number;
  status: string;
}

interface Course {
  id: string;
  code: string;
  name: string;
  cuatrimestre: string;
}

interface CourseEnrollment {
  id: string;
  student: string;
  student_name: string;
  course: string;
  course_id: string;
  course_name: string;
  course_code: string;
  final_grade: number | null;
  status: string;
  status_display: string;
}

interface GradeItem {
  student_id: string;
  course_id: string;
  final_grade: number;
  student_name?: string;
  course_name?: string;
  course_code?: string;
}

const GradeUpload: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { success, error } = useToast();
  
  const [careers, setCareers] = useState<Career[]>([]);
  const [selectedCareer, setSelectedCareer] = useState<string>('');
  const [cuatrimestres, setCuatrimestres] = useState<Cuatrimestre[]>([]);
  const [selectedCuatrimestre, setSelectedCuatrimestre] = useState<string>('');
  const [academicYear, setAcademicYear] = useState<number>(new Date().getFullYear());
  
  const [enrollments, setEnrollments] = useState<CourseEnrollment[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMode, setUploadMode] = useState<'manual' | 'file'>('manual');
  
  const [grades, setGrades] = useState<Map<string, number>>(new Map());
  const [uploadResults, setUploadResults] = useState<any>(null);

  useEffect(() => {
    loadCareers();
  }, []);

  useEffect(() => {
    if (selectedCareer) {
      loadCuatrimestres();
    }
  }, [selectedCareer]);

  useEffect(() => {
    if (selectedCuatrimestre && academicYear) {
      loadEnrollments();
    }
  }, [selectedCuatrimestre, academicYear]);

  const loadCareers = async () => {
    try {
      const response = await getCareers();
      const careersData = response.data.results || response.data;
      setCareers(careersData);
    } catch (err: any) {
      error('Error al cargar carreras');
    }
  };

  const loadCuatrimestres = async () => {
    try {
      const response = await academicsApi.getCuatrimestres({ career: selectedCareer });
      const cuatrimestresData = response.data.results || response.data;
      setCuatrimestres(cuatrimestresData);
    } catch (err: any) {
      error('Error al cargar cuatrimestres');
    }
  };

  const loadEnrollments = async () => {
    if (!selectedCuatrimestre || !academicYear) return;
    
    setLoading(true);
    try {
      // Primero obtener las inscripciones al cuatrimestre
      const cuatrimestreEnrollmentsRes = await academicsApi.getCuatrimestreEnrollments({
        cuatrimestre_id: selectedCuatrimestre,
        academic_year: academicYear
      });
      
      const cuatrimestreEnrollments = cuatrimestreEnrollmentsRes.data.results || cuatrimestreEnrollmentsRes.data;
      
      if (cuatrimestreEnrollments.length === 0) {
        setEnrollments([]);
        setLoading(false);
        return;
      }
      
      // Obtener todas las matrículas de cursos para estos cuatrimestres
      const allEnrollments: CourseEnrollment[] = [];
      
      for (const ce of cuatrimestreEnrollments) {
        try {
          const enrollmentsRes = await academicsApi.getEnrollmentsByCuatrimestre({
            cuatrimestre_enrollment_id: ce.id
          });
          const courseEnrollments = enrollmentsRes.data || [];
          allEnrollments.push(...courseEnrollments);
        } catch (err) {
          console.error(`Error loading enrollments for cuatrimestre enrollment ${ce.id}:`, err);
        }
      }
      
      setEnrollments(allEnrollments);
      
      // Inicializar el mapa de notas con las notas existentes
      const gradesMap = new Map<string, number>();
      allEnrollments.forEach(enrollment => {
        if (enrollment.final_grade !== null && enrollment.final_grade !== undefined) {
          const key = `${enrollment.student}-${enrollment.course_id}`;
          gradesMap.set(key, enrollment.final_grade);
        }
      });
      setGrades(gradesMap);
      
    } catch (err: any) {
      console.error('Error loading enrollments:', err);
      error('Error al cargar matrículas');
    } finally {
      setLoading(false);
    }
  };

  const handleGradeChange = (studentId: string, courseId: string, value: string) => {
    const numValue = parseFloat(value);
    const key = `${studentId}-${courseId}`;
    
    if (isNaN(numValue) || value === '') {
      const newGrades = new Map(grades);
      newGrades.delete(key);
      setGrades(newGrades);
    } else if (numValue >= 0 && numValue <= 100) {
      const newGrades = new Map(grades);
      newGrades.set(key, numValue);
      setGrades(newGrades);
    }
  };

  const handleBulkUpload = async () => {
    if (grades.size === 0) {
      error('No hay notas para subir');
      return;
    }

    setUploading(true);
    try {
      const gradesArray: GradeItem[] = [];
      
      grades.forEach((finalGrade, key) => {
        const [studentId, courseId] = key.split('-');
        const enrollment = enrollments.find(
          e => e.student === studentId && e.course_id === courseId
        );
        
        if (enrollment) {
          gradesArray.push({
            student_id: studentId,
            course_id: courseId,
            final_grade: finalGrade,
            student_name: enrollment.student_name,
            course_name: enrollment.course_name,
            course_code: enrollment.course_code
          });
        }
      });

      const response = await academicsApi.bulkUploadGrades(gradesArray);
      setUploadResults(response.data);
      
      success(`Notas subidas: ${response.data.results.updated} actualizadas, ${response.data.results.created} creadas`);
      
      // Recargar matrículas para ver los cambios
      await loadEnrollments();
      
    } catch (err: any) {
      console.error('Error uploading grades:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'Error al subir notas';
      error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Leer el archivo CSV
    const text = await file.text();
    const lines = text.split('\n').filter(line => line.trim());
    
    // Asumir que la primera línea es el encabezado
    // Formato esperado: student_id,course_id,final_grade o carnet,course_code,final_grade
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const isCarnetFormat = headers.includes('carnet') || headers.includes('carné');
    
    const gradesArray: GradeItem[] = [];
    const errors: string[] = [];
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      
      if (values.length < 3) continue;
      
      try {
        let studentId: string;
        let courseId: string;
        const finalGrade = parseFloat(values[2]);
        
        if (isNaN(finalGrade) || finalGrade < 0 || finalGrade > 100) {
          errors.push(`Línea ${i + 1}: Nota inválida (${values[2]})`);
          continue;
        }
        
        if (isCarnetFormat) {
          // Buscar estudiante por carnet
          // Buscar curso por código
          // Por ahora, mostrar error
          errors.push(`Línea ${i + 1}: Formato con carnet no implementado aún. Use student_id y course_id.`);
          continue;
        } else {
          studentId = values[0];
          courseId = values[1];
        }
        
        gradesArray.push({
          student_id: studentId,
          course_id: courseId,
          final_grade: finalGrade
        });
      } catch (err) {
        errors.push(`Línea ${i + 1}: Error al procesar`);
      }
    }
    
    if (errors.length > 0) {
      error(`Errores en el archivo: ${errors.slice(0, 5).join(', ')}${errors.length > 5 ? '...' : ''}`);
    }
    
    if (gradesArray.length > 0) {
      setUploading(true);
      try {
        const response = await academicsApi.bulkUploadGrades(gradesArray);
        setUploadResults(response.data);
        success(`Notas subidas: ${response.data.results.updated} actualizadas, ${response.data.results.created} creadas`);
        await loadEnrollments();
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'Error al subir notas';
        error(errorMessage);
      } finally {
        setUploading(false);
      }
    }
  };

  const exportToCSV = () => {
    if (enrollments.length === 0) {
      error('No hay datos para exportar');
      return;
    }

    const headers = ['student_id', 'student_name', 'student_carnet', 'course_id', 'course_code', 'course_name', 'final_grade', 'status'];
    const rows = enrollments.map(e => [
      e.student,
      e.student_name || '',
      '', // carnet - necesitaríamos cargarlo
      e.course_id,
      e.course_code || '',
      e.course_name || '',
      e.final_grade?.toString() || '',
      e.status || ''
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notas_${selectedCareer}_${academicYear}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Agrupar enrollments por estudiante y curso
  const groupedEnrollments = enrollments.reduce((acc, enrollment) => {
    const key = `${enrollment.student}-${enrollment.course_id}`;
    if (!acc.has(key)) {
      acc.set(key, enrollment);
    }
    return acc;
  }, new Map<string, CourseEnrollment>());

  const enrollmentsList = Array.from(groupedEnrollments.values());

  return (
    <div className="grade-upload-container">
      <div className="page-header">
        <h1>
          <FiFileText /> Subir Notas de Estudiantes
        </h1>
        <p className="page-description">
          Sube las notas de los estudiantes al finalizar el cuatrimestre. 
          Los cursos aprobados no se pueden reasignar, pero los reprobados sí.
        </p>
      </div>

      <div className="filters-section">
        <div className="filter-group">
          <label>Carrera</label>
          <select
            value={selectedCareer}
            onChange={(e) => {
              setSelectedCareer(e.target.value);
              setSelectedCuatrimestre('');
              setEnrollments([]);
            }}
            className="form-control"
          >
            <option value="">Seleccionar carrera</option>
            {careers.map(career => (
              <option key={career.id} value={career.id}>
                {career.code} - {career.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Cuatrimestre</label>
          <select
            value={selectedCuatrimestre}
            onChange={(e) => {
              setSelectedCuatrimestre(e.target.value);
              setEnrollments([]);
            }}
            className="form-control"
            disabled={!selectedCareer}
          >
            <option value="">Seleccionar cuatrimestre</option>
            {cuatrimestres.map(cuatrimestre => (
              <option key={cuatrimestre.id} value={cuatrimestre.id}>
                {cuatrimestre.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Año Académico</label>
          <input
            type="number"
            value={academicYear}
            onChange={(e) => setAcademicYear(parseInt(e.target.value) || new Date().getFullYear())}
            className="form-control"
            min="2000"
            max="2100"
          />
        </div>

        <button
          onClick={loadEnrollments}
          className="btn btn-primary"
          disabled={!selectedCuatrimestre || loading}
        >
          <FiRefreshCw /> Cargar Matrículas
        </button>
      </div>

      {enrollmentsList.length > 0 && (
        <div className="actions-bar">
          <button onClick={exportToCSV} className="btn btn-secondary">
            <FiDownload /> Exportar CSV
          </button>
          <button
            onClick={handleBulkUpload}
            className="btn btn-primary"
            disabled={uploading || grades.size === 0}
          >
            <FiUpload /> {uploading ? 'Subiendo...' : `Subir ${grades.size} Nota(s)`}
          </button>
        </div>
      )}

      {uploadResults && (
        <div className={`upload-results ${uploadResults.results.errors.length > 0 ? 'has-errors' : ''}`}>
          <h3>Resultados de la carga</h3>
          <p>{uploadResults.message}</p>
          {uploadResults.results.errors.length > 0 && (
            <div className="errors-list">
              <h4>Errores:</h4>
              <ul>
                {uploadResults.results.errors.slice(0, 10).map((err: any, idx: number) => (
                  <li key={idx}>{err.error || JSON.stringify(err)}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <p>Cargando matrículas...</p>
        </div>
      ) : enrollmentsList.length === 0 ? (
        <div className="empty-state">
          <p>No hay matrículas para mostrar. Selecciona un cuatrimestre y año académico.</p>
        </div>
      ) : (
        <div className="enrollments-table-container">
          <table className="enrollments-table">
            <thead>
              <tr>
                <th>Estudiante</th>
                <th>Curso</th>
                <th>Estado</th>
                <th>Nota Actual</th>
                <th>Nueva Nota</th>
              </tr>
            </thead>
            <tbody>
              {enrollmentsList.map((enrollment) => {
                const key = `${enrollment.student}-${enrollment.course_id}`;
                const currentGrade = grades.get(key) ?? enrollment.final_grade ?? '';
                const isApproved = enrollment.status === 'APROBADO';
                
                return (
                  <tr key={enrollment.id} className={isApproved ? 'approved-row' : ''}>
                    <td>
                      <div className="student-info">
                        <strong>{enrollment.student_name}</strong>
                      </div>
                    </td>
                    <td>
                      <div className="course-info">
                        <strong>{enrollment.course_code}</strong> - {enrollment.course_name}
                      </div>
                    </td>
                    <td>
                      <span className={`status-badge status-${enrollment.status.toLowerCase().replace('_', '-')}`}>
                        {enrollment.status_display}
                      </span>
                    </td>
                    <td>
                      {enrollment.final_grade !== null && enrollment.final_grade !== undefined
                        ? enrollment.final_grade.toFixed(2)
                        : '-'}
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={typeof currentGrade === 'number' ? currentGrade : ''}
                        onChange={(e) => handleGradeChange(enrollment.student, enrollment.course_id, e.target.value)}
                        className="grade-input"
                        disabled={isApproved}
                        placeholder="0-100"
                      />
                      {isApproved && (
                        <span className="help-text">Aprobado - no editable</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="file-upload-section">
        <h3>O subir desde archivo CSV</h3>
        <p>Formato: student_id,course_id,final_grade</p>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          className="file-input"
        />
      </div>
    </div>
  );
};

export default GradeUpload;

