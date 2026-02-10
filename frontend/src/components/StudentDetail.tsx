import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  getStudent, 
  getStudentDocuments, 
  uploadDocument,
  updateDocumentStatus,
  enrollmentsApi
} from '../services/api';
import { 
  FiUser, FiFileText, FiDownload, FiUpload, FiCheckCircle, 
  FiXCircle, FiEdit, FiTrendingUp, FiArrowLeft, FiBook, FiCalendar
} from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './StudentDetail.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  first_last_name?: string;
  second_last_name?: string;
  last_name?: string; // Para compatibilidad con código existente
  full_name?: string;
  email: string;
  phone: string;
  date_of_birth: string;
  gender: string;
  curp: string;
  address: string;
  career?: string;
  career_name: string;
  is_active: boolean;
  scholarship_type: string;
}

interface Document {
  id: string;
  document_type: string;
  document_type_display: string;
  file: string | null;
  status: string;
  status_display: string;
  notes: string;
}

interface Enrollment {
  id: string;
  status: string;
  status_display: string;
  enrollment_status?: string;
  enrollment_status_display?: string;
  enrollment_date: string;
  school_year?: number | null;
  contract_generated: boolean;
  contract_file_url?: string | null;
  contract_scanned_url?: string | null;
  contract_uploaded_at?: string | null;
  is_officially_enrolled?: boolean;
  institutional_id?: string | null;
  career_name?: string;
  student_name?: string;
  student_carnet?: string;
}

const StudentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { success, error } = useToast();
  const [student, setStudent] = useState<Student | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string | null>(null);
  const [uploadingContract, setUploadingContract] = useState(false);

  const loadData = React.useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [studentRes, docsRes] = await Promise.all([
        getStudent(id),
        getStudentDocuments(id)
      ]);
      
      setStudent(studentRes.data);
      
      // Manejar diferentes formatos de respuesta de documentos
      let docsData = [];
      if (Array.isArray(docsRes.data)) {
        docsData = docsRes.data;
      } else if (docsRes.data?.results) {
        docsData = docsRes.data.results;
      } else if (docsRes.data?.data) {
        docsData = docsRes.data.data;
      }
      
      console.log('Documentos cargados:', docsData.length, docsData);
      setDocuments(docsData);
      
      // Si el estudiante tiene inscripción en la respuesta (creado recientemente)
      if (studentRes.data.enrollment) {
        console.log('Enrollment encontrado en respuesta del estudiante:', studentRes.data.enrollment);
        setEnrollment(studentRes.data.enrollment);
      } else {
        // Si no, buscar las inscripciones del estudiante
        try {
          console.log('Buscando inscripciones para estudiante:', id);
          const enrollRes = await enrollmentsApi.list({ student: id });
          const enrollments = enrollRes.data.results || enrollRes.data;
          console.log('Inscripciones encontradas:', enrollments);
          if (Array.isArray(enrollments) && enrollments.length > 0) {
            // Obtener la inscripción más reciente (ordenar por fecha si es posible)
            const sortedEnrollments = enrollments.sort((a: Enrollment, b: Enrollment) => {
              const dateA = new Date(a.enrollment_date).getTime();
              const dateB = new Date(b.enrollment_date).getTime();
              return dateB - dateA; // Más reciente primero
            });
            setEnrollment(sortedEnrollments[0]);
          } else {
            console.log('No se encontraron inscripciones para este estudiante');
          }
        } catch (err) {
          console.error('Error loading enrollments:', err);
        }
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id, loadData]);

  const handleFileUpload = async (documentType: string, file: File) => {
    if (!id) return;
    
    // Validar tamaño del archivo (máximo 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      error('El archivo es demasiado grande. El tamaño máximo es 10MB.');
      return;
    }

    // Validar tipo de archivo
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      error('Tipo de archivo no permitido. Solo se permiten PDF, JPG y PNG.');
      return;
    }

    setUploading(documentType);
    try {
      const response = await uploadDocument(id, documentType, file);
      await loadData();
      const successMessage = response.data?.message || 'Documento subido exitosamente';
      success(successMessage);
    } catch (err: any) {
      console.error('Error uploading document:', err);
      console.error('Error response:', err.response?.data);
      
      let errorMessage = 'Error al subir el documento';
      if (err.response?.data) {
        if (err.response.data.error) {
          errorMessage = err.response.data.error;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        } else if (Array.isArray(err.response.data)) {
          errorMessage = err.response.data.join(', ');
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      error(errorMessage);
    } finally {
      setUploading(null);
    }
  };

  const handleDownloadContract = async () => {
    if (!enrollment) return;
    try {
      const response = await enrollmentsApi.generateContract(enrollment.id);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `contrato_${student?.carnet}_${enrollment.school_year || new Date().getFullYear()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      success('Contrato descargado exitosamente');
    } catch (err: any) {
      console.error('Error downloading contract:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al descargar el contrato';
      error(errorMessage);
    }
  };

  const handleViewContract = () => {
    if (!enrollment?.contract_file_url) return;
    window.open(enrollment.contract_file_url, '_blank');
  };

  const handleUploadScannedContract = async (file: File) => {
    if (!enrollment) return;

    // Validar tamaño del archivo (máximo 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      error('El archivo es demasiado grande. El tamaño máximo es 10MB.');
      return;
    }

    // Validar tipo de archivo
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      error('Tipo de archivo no permitido. Solo se permiten PDF, JPG y PNG.');
      return;
    }

    setUploadingContract(true);
    try {
      await enrollmentsApi.uploadScannedContract(enrollment.id, file);
      await loadData();
      success('Contrato firmado subido exitosamente');
    } catch (err: any) {
      console.error('Error uploading scanned contract:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al subir el contrato firmado';
      error(errorMessage);
    } finally {
      setUploadingContract(false);
    }
  };

  const handleDocumentStatusChange = async (docId: string, status: string) => {
    try {
      const response = await updateDocumentStatus(docId, status);
      await loadData();
      const successMessage = response.data?.message || 
        (status === 'APROBADO' ? 'Documento aprobado exitosamente' : 
         status === 'RECHAZADO' ? 'Documento rechazado exitosamente' : 
         'Estado del documento actualizado exitosamente');
      success(successMessage);
    } catch (err: any) {
      console.error('Error updating document status:', err);
      console.error('Error response:', err.response?.data);
      
      let errorMessage = 'Error al actualizar el estado del documento';
      if (err.response?.data) {
        if (err.response.data.error) {
          errorMessage = err.response.data.error;
        } else if (err.response.data.detail) {
          errorMessage = err.response.data.detail;
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      error(errorMessage);
    }
  };

  const getDocumentStatusClass = (status: string): string => {
    switch (status) {
      case 'APROBADO':
        return 'status-approved';
      case 'RECHAZADO':
        return 'status-rejected';
      case 'RECIBIDO':
        return 'status-received';
      default:
        return 'status-pending';
    }
  };

  // Todos los documentos son subibles ahora
  const isDocumentUploadable = (documentType: string): boolean => {
    return true;
  };

  // Ya no hay documentos solo para registro físico
  const isPhysicalRecordOnly = (documentType: string): boolean => {
    return false;
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando información del estudiante...</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiUser className="empty-icon" />
          <h3>Estudiante no encontrado</h3>
          <Link to="/students" className="btn btn-primary">
            <FiArrowLeft /> Volver a estudiantes
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <FiUser className="header-icon" />
            <div>
              <h1>{student.full_name || `${student.first_name} ${student.first_last_name || student.last_name || ''} ${student.second_last_name || ''}`.trim()}</h1>
              <p className="header-subtitle">Carnet: {student.carnet} | {student.career_name}</p>
            </div>
          </div>
          <div className="header-actions">
            <Link to={`/students/${id}/edit`} className="btn btn-primary btn-large">
              <FiEdit /> Editar
            </Link>
            <Link to={`/academics?studentId=${id}`} className="btn btn-success btn-large">
              <FiTrendingUp /> Progreso Académico
            </Link>
            <Link to={`/cuatrimestre-enrollments?studentId=${id}`} className="btn btn-primary btn-large">
              <FiCalendar /> Inscripciones a Cuatrimestres
            </Link>
            <Link to={`/careers/${student.career}/pensum`} className="btn btn-secondary btn-large">
              <FiBook /> Ver Pensum
            </Link>
            <Link to={`/graduation-method?studentId=${id}`} className="btn btn-info btn-large">
              <FiBook /> Método de Graduación
            </Link>
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="card">
          <h2 className="card-title">Información Personal</h2>
          <div className="info-grid">
            <div className="info-item">
              <label>Email</label>
              <p>{student.email}</p>
            </div>
            <div className="info-item">
              <label>Teléfono</label>
              <p>{student.phone}</p>
            </div>
            <div className="info-item">
              <label>Fecha de Nacimiento</label>
              <p>{new Date(student.date_of_birth).toLocaleDateString('es-ES')}</p>
            </div>
            <div className="info-item">
              <label>CURP</label>
              <p>{student.curp}</p>
            </div>
            <div className="info-item">
              <label>Dirección</label>
              <p>{student.address}</p>
            </div>
            <div className="info-item">
              <label>Beca</label>
              <p>
                {student.scholarship_type === 'NINGUNA' ? 'Sin Beca' :
                 student.scholarship_type === 'COMPLETA' ? 'Beca Completa' : 'Media Beca'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="card-title">Contrato de Inscripción</h2>
          {enrollment ? (
            <div className="enrollment-info">
              <div className="enrollment-status">
                <span className={`status-badge status-${enrollment.status.toLowerCase()}`}>
                  {enrollment.status_display}
                </span>
                <p className="enrollment-date">
                  Fecha de inscripción: {new Date(enrollment.enrollment_date).toLocaleDateString('es-ES')}
                </p>
                {enrollment.school_year && (
                  <p className="enrollment-date">
                    Ciclo escolar: {enrollment.school_year}
                  </p>
                )}
                {enrollment.is_officially_enrolled && (
                  <p className="enrollment-official">
                    <FiCheckCircle style={{ color: 'var(--success-color)', marginRight: '0.5rem' }} />
                    Oficialmente inscrito
                  </p>
                )}
              </div>

              {/* Contrato Generado */}
              <div className="contract-section">
                <h3>Contrato Generado</h3>
                {enrollment.contract_generated ? (
                  <div className="contract-actions">
                    {enrollment.contract_file_url && (
                      <button 
                        className="btn btn-primary" 
                        onClick={handleViewContract}
                        title="Ver contrato en nueva ventana"
                      >
                        <FiFileText /> Ver Contrato
                      </button>
                    )}
                    <button 
                      className="btn btn-secondary" 
                      onClick={handleDownloadContract}
                      title="Descargar contrato para imprimir"
                    >
                      <FiDownload /> Descargar/Imprimir
                    </button>
                    <p className="contract-help-text">
                      Descargue el contrato, imprímalo, haga que el estudiante lo firme y luego súbalo más abajo.
                    </p>
                  </div>
                ) : (
                  <div className="contract-status-message">
                    <p style={{ marginBottom: '1rem' }}>
                      El contrato aún no ha sido generado. Para generar el contrato, el estudiante debe tener cursos asignados.
                    </p>
                    <button 
                      className="btn btn-primary" 
                      onClick={async () => {
                        try {
                          await enrollmentsApi.generateContract(enrollment.id);
                          await loadData();
                          success('Contrato generado exitosamente');
                        } catch (err: any) {
                          console.error('Error generating contract:', err);
                          const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al generar el contrato';
                          error(errorMessage);
                        }
                      }}
                    >
                      <FiFileText /> Generar Contrato Ahora
                    </button>
                  </div>
                )}
              </div>

              {/* Contrato Firmado */}
              <div className="contract-section">
                <h3>Contrato Firmado (Escaneado)</h3>
                {enrollment.contract_scanned_url ? (
                  <div className="contract-scanned-info">
                    <a 
                      href={enrollment.contract_scanned_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-success"
                    >
                      <FiFileText /> Ver Contrato Firmado
                    </a>
                    {enrollment.contract_uploaded_at && (
                      <p className="contract-upload-date">
                        Subido el: {new Date(enrollment.contract_uploaded_at).toLocaleDateString('es-ES', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    )}
                    {enrollment.is_officially_enrolled ? (
                      <p className="contract-official-status">
                        <FiCheckCircle style={{ color: 'var(--success-color)', marginRight: '0.5rem' }} />
                        Contrato aprobado - Estudiante oficialmente inscrito
                      </p>
                    ) : (
                      <p className="contract-pending-status">
                        Contrato subido - Pendiente de aprobación
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="contract-upload-section">
                    <input
                      type="file"
                      id="scanned-contract-upload"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          handleUploadScannedContract(file);
                          // Resetear el input para permitir subir el mismo archivo otra vez
                          e.target.value = '';
                        }
                      }}
                      style={{ display: 'none' }}
                      disabled={uploadingContract || !enrollment.contract_generated}
                    />
                    <label 
                      htmlFor="scanned-contract-upload" 
                      className={`btn btn-primary ${(uploadingContract || !enrollment.contract_generated) ? 'disabled' : ''}`}
                      style={{ 
                        cursor: (uploadingContract || !enrollment.contract_generated) ? 'not-allowed' : 'pointer',
                        opacity: (uploadingContract || !enrollment.contract_generated) ? 0.6 : 1
                      }}
                    >
                      {uploadingContract ? (
                        <>Cargando...</>
                      ) : (
                        <>
                          <FiUpload /> Subir Contrato Firmado
                        </>
                      )}
                    </label>
                    {!enrollment.contract_generated && (
                      <p className="contract-help-text" style={{ color: 'var(--warning-color)', marginTop: '0.5rem' }}>
                        Primero debe generarse el contrato para poder subir el contrato firmado.
                      </p>
                    )}
                    <p className="contract-help-text">
                      Formatos aceptados: PDF, JPG, PNG (máximo 10MB)
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="contract-status-message">
              <p>No hay inscripción registrada para este estudiante.</p>
              <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--gray-600)' }}>
                La inscripción y el contrato se generan automáticamente al registrar un nuevo estudiante. 
                Si este estudiante fue creado antes de implementar esta funcionalidad, puede crear una inscripción manualmente.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">
          <FiFileText className="card-title-icon" />
          Documentos Requeridos
        </h2>
        
        <div className="documents-grid">
          {documents.length > 0 ? (
            documents.map((doc) => {
              const isUploadable = isDocumentUploadable(doc.document_type);
              const isPhysicalOnly = isPhysicalRecordOnly(doc.document_type);
              
              return (
                <div key={doc.id} className="document-card">
                  <div className="document-header">
                    <h4>{doc.document_type_display}</h4>
                    <span className={`status-badge ${getDocumentStatusClass(doc.status)}`}>
                      {doc.status_display}
                    </span>
                  </div>
                  
                {isPhysicalOnly ? (
                  // Documentos solo para registro físico (copias)
                  <div className="document-physical-record">
                    <div style={{ 
                      padding: '1rem', 
                      background: doc.status === 'APROBADO' ? 'var(--success-light)' : 'var(--gray-100)', 
                      borderRadius: 'var(--radius-sm)',
                      textAlign: 'center',
                      border: doc.status === 'APROBADO' ? '2px solid var(--success-color)' : '1px solid var(--gray-200)'
                    }}>
                      <FiFileText style={{ 
                        fontSize: '2rem', 
                        color: doc.status === 'APROBADO' ? 'var(--success-color)' : 'var(--gray-400)', 
                        marginBottom: '0.5rem' 
                      }} />
                      <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--gray-600)' }}>
                        Registro físico solamente
                      </p>
                      <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem', color: 'var(--gray-500)' }}>
                        Este documento se registra físicamente en el expediente del estudiante
                      </p>
                      
                      {doc.status === 'APROBADO' ? (
                        // Documento físico aprobado - solo lectura
                        <div style={{ 
                          marginTop: '1rem',
                          padding: '0.75rem',
                          background: 'rgba(34, 197, 94, 0.1)',
                          borderRadius: 'var(--radius-sm)'
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                            <FiCheckCircle style={{ color: 'var(--success-color)' }} />
                            <span style={{ color: 'var(--success-color)', fontWeight: 600, fontSize: '0.875rem' }}>
                              Documento Aprobado
                            </span>
                          </div>
                          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--gray-600)' }}>
                            Este documento ha sido aprobado y no puede ser modificado
                          </p>
                        </div>
                      ) : (
                        // Documento físico pendiente - permite aprobar/rechazar
                        <div className="status-buttons" style={{ marginTop: '1rem', justifyContent: 'center' }}>
                          <button
                            className="btn-icon btn-icon-success"
                            onClick={() => handleDocumentStatusChange(doc.id, 'APROBADO')}
                            title="Marcar como recibido y aprobado"
                            disabled={doc.status === 'APROBADO'}
                          >
                            <FiCheckCircle />
                          </button>
                          <button
                            className="btn-icon btn-icon-danger"
                            onClick={() => handleDocumentStatusChange(doc.id, 'RECHAZADO')}
                            title="Marcar como rechazado"
                            disabled={doc.status === 'RECHAZADO' || doc.status === 'APROBADO'}
                          >
                            <FiXCircle />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ) : doc.file ? (
                  // Documento subido
                  <div className="document-actions">
                    <a 
                      href={doc.file} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-primary"
                      style={{ width: '100%', marginBottom: doc.status === 'APROBADO' ? '0' : '0.5rem' }}
                    >
                      <FiDownload /> Ver Documento
                    </a>
                    
                    {doc.status === 'APROBADO' ? (
                      // Documento aprobado - solo lectura, no se puede modificar
                      <div style={{ 
                        marginTop: '0.75rem',
                        padding: '0.75rem',
                        background: 'var(--success-light)',
                        borderRadius: 'var(--radius-sm)',
                        textAlign: 'center'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          <FiCheckCircle style={{ color: 'var(--success-color)' }} />
                          <span style={{ color: 'var(--success-color)', fontWeight: 600, fontSize: '0.875rem' }}>
                            Documento Aprobado
                          </span>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--gray-600)' }}>
                          Este documento ha sido aprobado y no puede ser modificado
                        </p>
                      </div>
                    ) : (
                      // Documento subido pero no aprobado - permite acciones
                      <>
                        <div className="status-buttons" style={{ marginTop: '0.5rem', justifyContent: 'center' }}>
                          <button
                            className="btn-icon btn-icon-success"
                            onClick={() => handleDocumentStatusChange(doc.id, 'APROBADO')}
                            title="Aprobar documento"
                            disabled={doc.status === 'APROBADO' || uploading === doc.document_type}
                          >
                            <FiCheckCircle />
                          </button>
                          <button
                            className="btn-icon btn-icon-danger"
                            onClick={() => handleDocumentStatusChange(doc.id, 'RECHAZADO')}
                            title="Rechazar documento"
                            disabled={doc.status === 'RECHAZADO' || uploading === doc.document_type}
                          >
                            <FiXCircle />
                          </button>
                        </div>
                        
                        {/* Input oculto para reemplazar documento */}
                        <input
                          type="file"
                          id={`replace-file-${doc.id}`}
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) {
                              handleFileUpload(doc.document_type, file);
                            }
                            // Resetear el input
                            e.target.value = '';
                          }}
                          accept=".pdf,.jpg,.jpeg,.png"
                          style={{ display: 'none' }}
                          disabled={uploading === doc.document_type || doc.status === 'APROBADO'}
                        />
                        
                        <button
                          className="btn btn-sm btn-secondary"
                          style={{ 
                            marginTop: '0.75rem', 
                            width: '100%',
                            cursor: (uploading === doc.document_type || doc.status === 'APROBADO') ? 'not-allowed' : 'pointer',
                            opacity: (uploading === doc.document_type || doc.status === 'APROBADO') ? 0.6 : 1
                          }}
                          onClick={() => {
                            if (doc.status === 'APROBADO') {
                              error('No se puede reemplazar un documento que ha sido aprobado');
                              return;
                            }
                            const input = document.getElementById(`replace-file-${doc.id}`) as HTMLInputElement;
                            if (input && !input.disabled) {
                              input.click();
                            }
                          }}
                          disabled={uploading === doc.document_type || doc.status === 'APROBADO'}
                          title={doc.status === 'APROBADO' ? 'No se puede reemplazar un documento aprobado' : 'Reemplazar documento'}
                        >
                          {uploading === doc.document_type ? (
                            <>⏳ Cargando...</>
                          ) : (
                            <>
                              <FiUpload /> Reemplazar Documento
                            </>
                          )}
                        </button>
                      </>
                    )}
                  </div>
                ) : (
                    // Documento pendiente de subir (solo si es subible)
                    <div className="document-upload">
                      <input
                        type="file"
                        id={`file-${doc.id}`}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            handleFileUpload(doc.document_type, file);
                          }
                          // Resetear el input
                          e.target.value = '';
                        }}
                        accept=".pdf,.jpg,.jpeg,.png"
                        style={{ display: 'none' }}
                        disabled={uploading === doc.document_type || !isUploadable}
                      />
                      <label 
                        htmlFor={`file-${doc.id}`} 
                        className={`btn btn-sm btn-primary ${!isUploadable ? 'disabled' : ''}`}
                        style={{ 
                          cursor: (uploading === doc.document_type || !isUploadable) ? 'not-allowed' : 'pointer',
                          opacity: (uploading === doc.document_type || !isUploadable) ? 0.6 : 1,
                          width: '100%',
                          textAlign: 'center'
                        }}
                      >
                        {uploading === doc.document_type ? (
                          <>⏳ Cargando...</>
                        ) : (
                          <>
                            <FiUpload /> Subir Documento
                          </>
                        )}
                      </label>
                      {isUploadable && (
                        <p style={{ 
                          marginTop: '0.75rem', 
                          fontSize: '0.75rem', 
                          color: 'var(--gray-600)',
                          textAlign: 'center',
                          lineHeight: '1.4'
                        }}>
                          Formatos aceptados: PDF, JPG, PNG<br/>
                          Tamaño máximo: 10MB
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="empty-state" style={{ padding: '2rem', textAlign: 'center' }}>
              <FiFileText style={{ fontSize: '3rem', color: 'var(--gray-400)', marginBottom: '1rem' }} />
              <p>No hay documentos registrados para este estudiante.</p>
              <p style={{ fontSize: '0.875rem', color: 'var(--gray-600)', marginTop: '0.5rem' }}>
                Los documentos requeridos se crean automáticamente al registrar un estudiante. Si no aparecen, puede crearlos manualmente.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentDetail;

