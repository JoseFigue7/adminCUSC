import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  getStudent, 
  getStudentDocuments, 
  getEnrollment, 
  generateContract,
  uploadDocument,
  updateDocumentStatus 
} from '../services/api';
import { 
  FiUser, FiFileText, FiDownload, FiUpload, FiCheckCircle, 
  FiXCircle, FiEdit, FiTrendingUp, FiArrowLeft, FiBook, FiPlus
} from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './StudentDetail.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
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
  enrollment_date: string;
  contract_generated: boolean;
}

const StudentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success, error } = useToast();
  const [student, setStudent] = useState<Student | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string | null>(null);
  const [selectedDocType, setSelectedDocType] = useState<string>('');

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [studentRes, docsRes, enrollRes] = await Promise.all([
        getStudent(id),
        getStudentDocuments(id),
        getEnrollment(id)
      ]);
      
      setStudent(studentRes.data);
      setDocuments(docsRes.data.results || docsRes.data);
      
      const enrollments = enrollRes.data.results || enrollRes.data;
      if (enrollments.length > 0) {
        setEnrollment(enrollments[0]);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

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
      await uploadDocument(id, documentType, file);
      await loadData();
      success('Documento subido exitosamente');
    } catch (err: any) {
      console.error('Error uploading document:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al subir el documento';
      error(errorMessage);
    } finally {
      setUploading(null);
    }
  };

  const handleDownloadContract = async () => {
    if (!enrollment) return;
    try {
      const response = await generateContract(enrollment.id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `contrato_${student?.carnet}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      success('Contrato descargado exitosamente');
    } catch (err: any) {
      console.error('Error downloading contract:', err);
      const errorMessage = err.response?.data?.detail || 'Error al descargar el contrato';
      error(errorMessage);
    }
  };

  const handleDocumentStatusChange = async (docId: string, status: string) => {
    try {
      await updateDocumentStatus(docId, status);
      await loadData();
      const statusText = status === 'APROBADO' ? 'aprobado' : status === 'RECHAZADO' ? 'rechazado' : 'actualizado';
      success(`Documento ${statusText} exitosamente`);
    } catch (err: any) {
      console.error('Error updating document status:', err);
      const errorMessage = err.response?.data?.detail || 'Error al actualizar el estado del documento';
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
              <h1>{student.first_name} {student.last_name}</h1>
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
            <Link to={`/courses/enroll?studentId=${id}`} className="btn btn-primary btn-large">
              <FiPlus /> Matricular Cursos
            </Link>
            <Link to={`/careers/${student.career}/pensum`} className="btn btn-secondary btn-large">
              <FiBook /> Ver Pensum
            </Link>
            <Link to={`/thesis?studentId=${id}`} className="btn btn-info btn-large">
              <FiBook /> Gestión de Tesis
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
          <h2 className="card-title">Estado de Inscripción</h2>
          {enrollment ? (
            <div className="enrollment-info">
              <div className="enrollment-status">
                <span className={`status-badge status-${enrollment.status.toLowerCase()}`}>
                  {enrollment.status_display}
                </span>
                <p className="enrollment-date">
                  Fecha: {new Date(enrollment.enrollment_date).toLocaleDateString('es-ES')}
                </p>
              </div>
              {enrollment.contract_generated && (
                <button 
                  className="btn btn-primary btn-large" 
                  onClick={handleDownloadContract}
                >
                  <FiDownload /> Descargar Contrato
                </button>
              )}
            </div>
          ) : (
            <p>No hay inscripción registrada</p>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">
          <FiFileText className="card-title-icon" />
          Documentos Requeridos
        </h2>
        
        <div className="documents-grid">
          {documents.map((doc) => (
            <div key={doc.id} className="document-card">
              <div className="document-header">
                <h4>{doc.document_type_display}</h4>
                <span className={`status-badge ${getDocumentStatusClass(doc.status)}`}>
                  {doc.status_display}
                </span>
              </div>
              
              {doc.file ? (
                <div className="document-actions">
                  <a 
                    href={doc.file} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn btn-sm btn-primary"
                  >
                    <FiDownload /> Ver Documento
                  </a>
                  <div className="status-buttons">
                    <button
                      className="btn-icon btn-icon-success"
                      onClick={() => handleDocumentStatusChange(doc.id, 'APROBADO')}
                      title="Aprobar"
                    >
                      <FiCheckCircle />
                    </button>
                    <button
                      className="btn-icon btn-icon-danger"
                      onClick={() => handleDocumentStatusChange(doc.id, 'RECHAZADO')}
                      title="Rechazar"
                    >
                      <FiXCircle />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="document-upload">
                  <input
                    type="file"
                    id={`file-${doc.id}`}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        handleFileUpload(doc.document_type, file);
                      }
                    }}
                    style={{ display: 'none' }}
                    disabled={uploading === doc.document_type}
                  />
                  <label 
                    htmlFor={`file-${doc.id}`} 
                    className="btn btn-sm btn-secondary"
                  >
                    {uploading === doc.document_type ? (
                      <>Cargando...</>
                    ) : (
                      <>
                        <FiUpload /> Subir Documento
                      </>
                    )}
                  </label>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StudentDetail;

