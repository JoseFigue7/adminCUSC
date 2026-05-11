import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  academicsApi,
  getCareers,
  getStudent,
  getStudentByCarnet
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
  student_carnet?: string;
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
  
  // Estado para previsualización de CSV
  const [csvPreview, setCsvPreview] = useState<{
    grades: any[];
    errors: string[];
    fileName: string;
  } | null>(null);
  const [showPreview, setShowPreview] = useState(false);

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
      const gradesArray: any[] = [];
      
      grades.forEach((finalGrade, key) => {
        const [studentId, courseId] = key.split('-');
        const enrollment = enrollments.find(
          e => e.student === studentId && e.course_id === courseId
        );
        
        if (!enrollment) {
          return; // Saltar si no hay enrollment
        }
        
        // Solo enviar los campos que el backend espera
        // Asegurarse de que final_grade sea un número
        const gradeValue = typeof finalGrade === 'number' ? finalGrade : parseFloat(String(finalGrade));
        
        if (isNaN(gradeValue) || gradeValue < 0 || gradeValue > 100) {
          console.warn(`Nota inválida para estudiante ${studentId}, curso ${courseId}: ${finalGrade}`);
          return; // Saltar si la nota es inválida
        }
        
        gradesArray.push({
          student_id: studentId,
          course_id: courseId,
          final_grade: gradeValue
        });
      });

      if (gradesArray.length === 0) {
        error('No se encontraron matrículas válidas para las notas ingresadas');
        setUploading(false);
        return;
      }

      console.log('Enviando notas:', gradesArray);
      const response = await academicsApi.bulkUploadGrades(gradesArray);
      setUploadResults(response.data);
      
      success(`Notas subidas: ${response.data.results.updated} actualizadas, ${response.data.results.created} creadas`);
      
      // Limpiar el mapa de notas después de subir
      setGrades(new Map());
      
      // Recargar matrículas para ver los cambios
      await loadEnrollments();
      
    } catch (err: any) {
      console.error('Error uploading grades:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.response?.data?.error || 'Error al subir notas';
      error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const enrichPreviewData = async (gradesArray: any[]) => {
    // Enriquecer datos con información de estudiantes y cursos cuando sea posible
    const enrichedGrades = await Promise.all(
      gradesArray.map(async (grade) => {
        const enriched: any = { ...grade };
        
        // Si tenemos carnet, intentar obtener información del estudiante
        if (grade.student_carnet) {
          try {
            const studentRes = await getStudentByCarnet(grade.student_carnet);
            if (studentRes.data) {
              enriched.student_name = studentRes.data.first_name + ' ' + (studentRes.data.first_last_name || '');
              enriched.student_carnet_display = studentRes.data.carnet;
            }
          } catch (err) {
            // Si no se encuentra, mantener el identificador original
            enriched.student_name = 'No encontrado';
          }
        }
        
        // Si tenemos código de curso, intentar obtener información del curso
        if (grade.course_code) {
          try {
            const coursesRes = await academicsApi.getCourses({ code: grade.course_code });
            const courses = coursesRes.data.results || coursesRes.data;
            if (courses && courses.length > 0) {
              enriched.course_name = courses[0].name;
              enriched.course_code_display = courses[0].code;
            }
          } catch (err) {
            // Si no se encuentra, mantener el código original
            enriched.course_name = 'No encontrado';
          }
        }
        
        return enriched;
      })
    );
    
    return enrichedGrades;
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    
    // Leer el archivo CSV
    const text = await file.text();
    const lines = text.split('\n').filter(line => line.trim());
    
    if (lines.length < 2) {
      error('El archivo CSV debe tener al menos una línea de encabezado y una línea de datos');
      return;
    }
    
    // Asumir que la primera línea es el encabezado
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, '').toLowerCase());
    
    // Obtener índices de columnas con múltiples variantes
    const getIndex = (possibleNames: string[]) => {
      for (const name of possibleNames) {
        const idx = headers.findIndex(h => h === name.toLowerCase() || h.includes(name.toLowerCase()));
        if (idx !== -1) return idx;
      }
      return -1;
    };
    
    // Detectar formato Moodle 4.2
    const moodleIdIdx = getIndex(['id', 'student id', 'username', 'identificación', 'identificacion']);
    const moodleNameIdx = getIndex(['nombre completo', 'full name', 'firstname', 'nombre', 'apellido', 'lastname']);
    const moodleEmailIdx = getIndex(['email', 'correo', 'e-mail']);
    const moodleCourseNameIdx = getIndex(['nombre del curso', 'course name', 'curso', 'course']);
    const moodleCourseCodeIdx = getIndex(['código del curso', 'codigo del curso', 'course code', 'código', 'codigo']);
    
    // Detectar otros formatos
    const hasCarnet = getIndex(['student_carnet', 'carnet', 'carné']) !== -1;
    const hasCourseCode = getIndex(['course_code', 'codigo_curso', 'código_curso']) !== -1;
    const hasCareerCode = getIndex(['career_code', 'codigo_carrera', 'código_carrera']) !== -1;
    const hasCuatrimestre = getIndex(['cuatrimestre_number', 'cuatrimestre', 'cuatrimestre_numero']) !== -1;
    const hasAcademicYear = getIndex(['academic_year', 'año', 'ano', 'year']) !== -1;
    const hasStudentId = getIndex(['student_id']) !== -1;
    const hasCourseId = getIndex(['course_id']) !== -1;
    
    // Detectar formato de calificación
    const finalGradeIdx = getIndex(['calificación', 'calificacion', 'final_grade', 'nota', 'nota_final', 'grade', 'score', 'puntuación', 'puntuacion']);
    
    if (finalGradeIdx === -1) {
      error('No se encontró la columna de calificación. Busque columnas como: "Calificación", "Final grade", "Nota", "Grade"');
      return;
    }
    
    // Determinar formato
    // Moodle 4.2 típicamente tiene: ID/Username, Nombre completo, Email, Nombre del curso, Código del curso, Calificación
    const isMoodleFormat = moodleCourseCodeIdx !== -1 && (moodleIdIdx !== -1 || moodleNameIdx !== -1);
    const isCarnetFormat = hasCarnet && hasCourseCode;
    const isIdFormat = hasStudentId && hasCourseId;
    
    if (!isMoodleFormat && !isCarnetFormat && !isIdFormat) {
      error('Formato CSV no reconocido. Debe incluir columnas para identificar estudiante y curso. Use el ejemplo CSV como referencia.');
      return;
    }
    
    const gradesArray: any[] = [];
    const errors: string[] = [];
    
    // Obtener índices según el formato detectado
    let carnetIdx = -1;
    let courseCodeIdx = -1;
    
    if (isMoodleFormat) {
      // En formato Moodle, preferir ID si está disponible, sino usar nombre completo
      carnetIdx = moodleIdIdx !== -1 ? moodleIdIdx : moodleNameIdx;
      courseCodeIdx = moodleCourseCodeIdx;
    } else if (isCarnetFormat) {
      carnetIdx = getIndex(['student_carnet', 'carnet', 'carné']);
      courseCodeIdx = getIndex(['course_code', 'codigo_curso', 'código_curso']);
    }
    
    const careerCodeIdx = getIndex(['career_code', 'codigo_carrera', 'código_carrera']);
    const cuatrimestreIdx = getIndex(['cuatrimestre_number', 'cuatrimestre', 'cuatrimestre_numero']);
    const academicYearIdx = getIndex(['academic_year', 'año', 'ano', 'year']);
    const studentIdIdx = getIndex(['student_id']);
    const courseIdIdx = getIndex(['course_id']);
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''));
      
      if (values.length < 3) continue;
      
      try {
        const finalGrade = parseFloat(values[finalGradeIdx]);
        
        if (isNaN(finalGrade) || finalGrade < 0 || finalGrade > 100) {
          errors.push(`Línea ${i + 1}: Nota inválida (${values[finalGradeIdx]})`);
          continue;
        }
        
        if (isMoodleFormat || isCarnetFormat) {
          // Formato Moodle o con carnet
          const identifier = isMoodleFormat 
            ? (values[carnetIdx]?.trim() || values[moodleNameIdx]?.trim() || '')
            : values[carnetIdx]?.trim();
          const courseCode = values[courseCodeIdx]?.trim();
          
          if (!identifier || !courseCode) {
            errors.push(`Línea ${i + 1}: Faltan datos (identificador de estudiante o código de curso)`);
            continue;
          }
          
          const gradeItem: any = {
            student_carnet: identifier, // En Moodle puede ser ID, username o carnet
            course_code: courseCode,
            final_grade: finalGrade
          };
          
          // Agregar campos opcionales si están presentes
          if (careerCodeIdx !== -1 && values[careerCodeIdx]) {
            gradeItem.career_code = parseInt(values[careerCodeIdx]);
          }
          if (cuatrimestreIdx !== -1 && values[cuatrimestreIdx]) {
            gradeItem.cuatrimestre_number = parseInt(values[cuatrimestreIdx]);
          }
          if (academicYearIdx !== -1 && values[academicYearIdx]) {
            gradeItem.academic_year = parseInt(values[academicYearIdx]);
          } else if (selectedCareer && selectedCuatrimestre) {
            // Usar los valores seleccionados si no están en el CSV
            gradeItem.academic_year = academicYear;
            const career = careers.find(c => c.id === selectedCareer);
            if (career) {
              gradeItem.career_code = career.code;
            }
            const cuatrimestre = cuatrimestres.find(c => c.id === selectedCuatrimestre);
            if (cuatrimestre) {
              gradeItem.cuatrimestre_number = cuatrimestre.number;
            }
          }
          
          gradesArray.push(gradeItem);
        } else {
          // Formato con IDs
          const studentId = values[studentIdIdx]?.trim();
          const courseId = values[courseIdIdx]?.trim();
          
          if (!studentId || !courseId) {
            errors.push(`Línea ${i + 1}: Faltan datos (student_id o course_id)`);
            continue;
          }
          
          gradesArray.push({
            student_id: studentId,
            course_id: courseId,
            final_grade: finalGrade
          });
        }
      } catch (err) {
        errors.push(`Línea ${i + 1}: Error al procesar - ${err}`);
      }
    }
    
    if (errors.length > 0) {
      error(`Errores en el archivo (${errors.length}): ${errors.slice(0, 5).join(', ')}${errors.length > 5 ? '...' : ''}`);
    }
    
    if (gradesArray.length > 0) {
      try {
        // Enriquecer datos con información de estudiantes y cursos
        const enrichedGrades = await enrichPreviewData(gradesArray);
        
        // Mostrar previsualización en lugar de subir inmediatamente
        setCsvPreview({
          grades: enrichedGrades,
          errors: errors,
          fileName: file.name
        });
        setShowPreview(true);
        
        if (errors.length > 0) {
          error(`Se encontraron ${errors.length} errores en el archivo. Revise la previsualización.`);
        } else {
          success(`CSV procesado correctamente. Se importarán ${gradesArray.length} notas. Revise la previsualización antes de confirmar.`);
        }
      } catch (err) {
        console.error('Error enriqueciendo datos:', err);
        // Mostrar previsualización básica si falla el enriquecimiento
        setCsvPreview({
          grades: gradesArray,
          errors: errors,
          fileName: file.name
        });
        setShowPreview(true);
        success(`CSV procesado. Se importarán ${gradesArray.length} notas. Revise la previsualización antes de confirmar.`);
      }
    } else {
      error('No se pudieron procesar notas del archivo CSV. Verifique el formato.');
    }
    
    setLoading(false);
    
    // Limpiar el input para permitir subir el mismo archivo de nuevo
    event.target.value = '';
  };

  const handleConfirmImport = async () => {
    if (!csvPreview || csvPreview.grades.length === 0) {
      error('No hay notas para importar');
      return;
    }

    setUploading(true);
    try {
      const response = await academicsApi.bulkUploadGrades(csvPreview.grades);
      setUploadResults(response.data);
      success(`Notas importadas: ${response.data.results.updated} actualizadas, ${response.data.results.created} creadas`);
      await loadEnrollments();
      // Limpiar previsualización
      setCsvPreview(null);
      setShowPreview(false);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || 'Error al importar notas';
      error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleCancelImport = () => {
    setCsvPreview(null);
    setShowPreview(false);
  };

  const downloadExampleCSV = () => {
    // Formato compatible con Moodle 4.2 - exportación de notas
    // Moodle exporta con columnas: Nombre completo, Email, ID, Nombre del curso, Código del curso, Calificación
    const headers = ['Nombre completo', 'Email', 'ID', 'Nombre del curso', 'Código del curso', 'Calificación'];
    const exampleRows = [
      ['Juan Pérez García', 'juan.perez@example.com', '101240001', 'Matemáticas I', 'MAT101', '85.5'],
      ['María López Sánchez', 'maria.lopez@example.com', '101240002', 'Matemáticas I', 'MAT101', '92.0'],
      ['Carlos Ramírez Torres', 'carlos.ramirez@example.com', '101240003', 'Matemáticas I', 'MAT101', '78.5']
    ];
    
    const csv = [headers.join(','), ...exampleRows.map(r => r.map(cell => `"${cell}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ejemplo_notas_moodle_4.2.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    success('Ejemplo CSV descargado (formato Moodle 4.2)');
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

      {/* Sección de edición manual (opcional) - Solo se muestra si hay matrículas cargadas */}
      {enrollmentsList.length > 0 && !showPreview && (
        <div className="actions-bar">
          <p style={{ fontSize: '0.9rem', color: '#666', margin: '0.5rem 0' }}>
            <strong>Nota:</strong> También puede editar notas manualmente en la tabla de abajo, o subir un CSV masivamente usando el botón de abajo.
          </p>
          <button
            onClick={handleBulkUpload}
            className="btn btn-primary"
            disabled={uploading || grades.size === 0}
          >
            <FiUpload /> {uploading ? 'Subiendo...' : `Subir ${grades.size} Nota(s) Manualmente`}
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

      {/* Previsualización de CSV */}
      {showPreview && csvPreview && (
        <div className="csv-preview-section" style={{ 
          marginTop: '2rem', 
          padding: '1.5rem', 
          border: '2px solid #007bff', 
          borderRadius: '8px',
          backgroundColor: '#f8f9fa'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>
              <FiFileText /> Previsualización de Importación
            </h3>
            <span style={{ fontSize: '0.9rem', color: '#666' }}>
              Archivo: {csvPreview.fileName}
            </span>
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ margin: '0.5rem 0' }}>
              <strong>Total de notas a importar:</strong> {csvPreview.grades.length}
            </p>
            {csvPreview.errors.length > 0 && (
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#fff3cd', 
                border: '1px solid #ffc107', 
                borderRadius: '4px',
                marginTop: '0.5rem'
              }}>
                <strong>Advertencias ({csvPreview.errors.length}):</strong>
                <ul style={{ margin: '0.5rem 0 0 1.5rem', padding: 0 }}>
                  {csvPreview.errors.slice(0, 5).map((err, idx) => (
                    <li key={idx} style={{ fontSize: '0.9rem' }}>{err}</li>
                  ))}
                  {csvPreview.errors.length > 5 && (
                    <li style={{ fontSize: '0.9rem' }}>... y {csvPreview.errors.length - 5} más</li>
                  )}
                </ul>
              </div>
            )}
          </div>

          <div style={{ 
            maxHeight: '400px', 
            overflowY: 'auto', 
            border: '1px solid #dee2e6', 
            borderRadius: '4px',
            marginBottom: '1rem'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ backgroundColor: '#e9ecef', position: 'sticky', top: 0 }}>
                <tr>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Estudiante
                  </th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Carnet/ID
                  </th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Curso
                  </th>
                  <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Código
                  </th>
                  <th style={{ padding: '0.75rem', textAlign: 'center', borderBottom: '2px solid #dee2e6' }}>
                    Nota
                  </th>
                </tr>
              </thead>
              <tbody>
                {csvPreview.grades.map((grade, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #dee2e6' }}>
                    <td style={{ padding: '0.75rem' }}>
                      {grade.student_name || 'No encontrado'}
                    </td>
                    <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>
                      {grade.student_carnet_display || grade.student_carnet || grade.student_id || 'N/A'}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {grade.course_name || 'No encontrado'}
                    </td>
                    <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>
                      {grade.course_code_display || grade.course_code || grade.course_id || 'N/A'}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'center', fontWeight: 'bold', fontSize: '1.1em' }}>
                      {grade.final_grade}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              onClick={handleCancelImport}
              className="btn btn-secondary"
              disabled={uploading}
            >
              Cancelar
            </button>
            <button
              onClick={handleConfirmImport}
              className="btn btn-primary"
              disabled={uploading || csvPreview.grades.length === 0}
            >
              <FiUpload /> {uploading ? 'Importando...' : `Confirmar e Importar ${csvPreview.grades.length} Nota(s)`}
            </button>
          </div>
        </div>
      )}

      <div className="file-upload-section" style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3 style={{ marginTop: 0 }}>
          <FiUpload /> Subir Notas Masivamente desde CSV (Moodle)
        </h3>
        <div style={{ marginBottom: '1rem' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>Flujo de trabajo:</strong> Exporte las notas desde Moodle 4.2, seleccione el archivo CSV aquí, revise la previsualización y confirme la importación.
          </p>
          <p style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#666' }}>
            <strong>Formatos aceptados:</strong>
            <br />• Moodle 4.2: "Nombre completo", "Email", "ID", "Nombre del curso", "Código del curso", "Calificación"
            <br />• Simple: "student_carnet", "course_code", "final_grade"
            <br />• Con IDs: "student_id", "course_id", "final_grade"
          </p>
          <button
            onClick={downloadExampleCSV}
            className="btn btn-secondary"
            style={{ marginTop: '0.5rem' }}
            disabled={uploading || loading}
          >
            <FiDownload /> Descargar Ejemplo CSV (Formato Moodle 4.2)
          </button>
        </div>
        <div style={{ 
          padding: '1rem', 
          border: '2px dashed #007bff', 
          borderRadius: '4px',
          textAlign: 'center',
          backgroundColor: '#fff',
          position: 'relative'
        }}>
          <label 
            htmlFor="csv-file-input"
            style={{
              display: 'inline-block',
              padding: '0.75rem 1.5rem',
              backgroundColor: uploading || loading ? '#6c757d' : '#007bff',
              color: '#fff',
              borderRadius: '4px',
              cursor: uploading || loading ? 'not-allowed' : 'pointer',
              fontSize: '1rem',
              fontWeight: 'bold',
              width: '100%',
              textAlign: 'center'
            }}
          >
            {uploading || loading ? '⏳ Procesando...' : '📁 Seleccionar Archivo CSV'}
          </label>
          <input
            id="csv-file-input"
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            disabled={uploading || loading}
            style={{ 
              position: 'absolute',
              width: '100%',
              height: '100%',
              top: 0,
              left: 0,
              opacity: 0,
              cursor: uploading || loading ? 'not-allowed' : 'pointer',
              zIndex: 1
            }}
          />
          {loading && (
            <p style={{ marginTop: '0.5rem', color: '#007bff', fontWeight: 'bold' }}>
              ⏳ Procesando CSV y validando datos...
            </p>
          )}
          {uploading && (
            <p style={{ marginTop: '0.5rem', color: '#007bff', fontWeight: 'bold' }}>
              ⏳ Importando notas al sistema...
            </p>
          )}
          {showPreview && !uploading && !loading && (
            <p style={{ marginTop: '0.5rem', color: '#28a745', fontWeight: 'bold' }}>
              ✓ CSV procesado correctamente. Revise la previsualización arriba y confirme la importación.
            </p>
          )}
          {!showPreview && !uploading && !loading && (
            <p style={{ marginTop: '0.5rem', color: '#666', fontSize: '0.9rem' }}>
              Seleccione el archivo CSV exportado desde Moodle
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default GradeUpload;

