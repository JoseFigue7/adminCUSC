import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { enrollmentsApi } from '../services/api';
import { FiFileText, FiUpload, FiPrinter, FiCheckCircle, FiXCircle, FiLoader, FiDownload, FiArrowLeft } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './ContractManagement.css';

interface Enrollment {
  id: string;
  student_name: string;
  student_carnet: string;
  student_id: string;
  enrollment_status: string;
  enrollment_status_display: string;
  status: string;
  status_display: string;
  school_year: number;
  career_name: string;
  contract_generated: boolean;
  contract_file_url?: string;
  contract_scanned?: string;
  contract_scanned_url?: string;
  contract_uploaded_at?: string;
  is_officially_enrolled: boolean;
  enrollment_date: string;
}

const ContractManagement: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { success, error } = useToast();

  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState('');

  useEffect(() => {
    if (id) {
      loadEnrollment();
    }
  }, [id]);

  const loadEnrollment = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await enrollmentsApi.get(id);
      setEnrollment(response.data);
    } catch (err: any) {
      console.error('Error loading enrollment:', err);
      error('Error al cargar inscripción');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateContract = async () => {
    if (!id) return;
    setGenerating(true);
    try {
      const response = await enrollmentsApi.generateContract(id);
      
      // Crear URL del blob y abrir en nueva ventana para imprimir
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const printWindow = window.open(url, '_blank');
      
      if (printWindow) {
        printWindow.onload = () => {
          printWindow.print();
        };
      }
      
      // Actualizar la inscripción
      await loadEnrollment();
      success('Contrato generado e impreso exitosamente');
    } catch (err: any) {
      console.error('Error generating contract:', err);
      error('Error al generar contrato');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadContract = async () => {
    if (!id || !enrollment?.contract_file_url) return;
    
    try {
      const response = await enrollmentsApi.generateContract(id);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `contrato_${enrollment.student_carnet}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      success('Contrato descargado exitosamente');
    } catch (err: any) {
      console.error('Error downloading contract:', err);
      error('Error al descargar contrato');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setFileError('');
    
    if (!file) {
      setSelectedFile(null);
      return;
    }

    // Validar tipo de archivo
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      setFileError('Formato no permitido. Use PDF, JPG o PNG');
      setSelectedFile(null);
      return;
    }

    // Validar tamaño (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setFileError('El archivo no debe exceder 10MB');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  const handleUploadContract = async () => {
    if (!id || !selectedFile) return;

    setUploading(true);
    try {
      await enrollmentsApi.uploadScannedContract(id, selectedFile);
      success('Contrato escaneado subido exitosamente');
      setSelectedFile(null);
      // Limpiar input
      const fileInput = document.getElementById('contract-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      await loadEnrollment();
    } catch (err: any) {
      console.error('Error uploading contract:', err);
      const errorMessage = err.response?.data?.error || err.response?.data?.detail || 'Error al subir contrato escaneado';
      error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleViewScannedContract = () => {
    if (enrollment?.contract_scanned_url) {
      window.open(enrollment.contract_scanned_url, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando información de inscripción...</p>
        </div>
      </div>
    );
  }

  if (!enrollment) {
    return (
      <div className="page-container">
        <div className="card">
          <p>Inscripción no encontrada</p>
          <button className="btn btn-secondary" onClick={() => navigate('/students')}>
            Volver
          </button>
        </div>
      </div>
    );
  }

  const canUploadContract = enrollment.contract_generated && !enrollment.is_officially_enrolled;
  const isPendingApproval = enrollment.status === 'EN_REVISION' && enrollment.contract_scanned;

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-title">
          <FiFileText className="header-icon" />
          <div>
            <h1>Gestión de Contrato de Inscripción</h1>
            <p className="header-subtitle">
              Estudiante: {enrollment.student_name} ({enrollment.student_carnet})
            </p>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={() => navigate('/students')}>
          <FiArrowLeft /> Volver
        </button>
      </div>

      <div className="card contract-info">
        <h3>Información de la Inscripción</h3>
        <div className="info-grid">
          <div className="info-item">
            <label>Estado de Inscripción:</label>
            <span className={`status-badge status-${enrollment.status.toLowerCase()}`}>
              {enrollment.status_display}
            </span>
          </div>
          <div className="info-item">
            <label>Tipo:</label>
            <span>{enrollment.enrollment_status_display}</span>
          </div>
          <div className="info-item">
            <label>Ciclo Escolar:</label>
            <span>{enrollment.school_year}</span>
          </div>
          <div className="info-item">
            <label>Carrera:</label>
            <span>{enrollment.career_name}</span>
          </div>
          <div className="info-item">
            <label>Fecha de Inscripción:</label>
            <span>{new Date(enrollment.enrollment_date).toLocaleDateString('es-ES')}</span>
          </div>
          <div className="info-item">
            <label>Oficialmente Inscrito:</label>
            <span className={enrollment.is_officially_enrolled ? 'status-approved' : 'status-pending'}>
              {enrollment.is_officially_enrolled ? '✓ Sí' : '✗ No'}
            </span>
          </div>
        </div>
      </div>

      {/* Paso 1: Generar e Imprimir Contrato */}
      <div className="card contract-step">
        <div className="step-header">
          <div className="step-number">1</div>
          <div>
            <h3>Generar e Imprimir Contrato</h3>
            <p>Genere el contrato para que sea firmado por el estudiante</p>
          </div>
        </div>
        
        <div className="step-content">
          {enrollment.contract_generated ? (
            <div className="contract-generated">
              <FiCheckCircle className="icon-success" />
              <p>Contrato generado exitosamente</p>
              <div className="action-buttons">
                <button 
                  className="btn btn-primary" 
                  onClick={handleGenerateContract}
                  disabled={generating}
                >
                  {generating ? <FiLoader className="spinning" /> : <FiPrinter />}
                  {generating ? 'Generando...' : 'Imprimir Contrato'}
                </button>
                <button 
                  className="btn btn-secondary" 
                  onClick={handleDownloadContract}
                >
                  <FiDownload /> Descargar Contrato
                </button>
              </div>
            </div>
          ) : (
            <div className="contract-not-generated">
              <p>El contrato aún no ha sido generado</p>
              <button 
                className="btn btn-primary" 
                onClick={handleGenerateContract}
                disabled={generating}
              >
                {generating ? <FiLoader className="spinning" /> : <FiFileText />}
                {generating ? 'Generando...' : 'Generar Contrato'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Paso 2: Subir Contrato Escaneado */}
      {enrollment.contract_generated && (
        <div className="card contract-step">
          <div className="step-header">
            <div className="step-number">2</div>
            <div>
              <h3>Subir Contrato Escaneado</h3>
              <p>Suba el contrato firmado por ambas partes (PDF o imagen)</p>
            </div>
          </div>
          
          <div className="step-content">
            {enrollment.contract_scanned ? (
              <div className="contract-uploaded">
                <FiCheckCircle className="icon-success" />
                <p>Contrato escaneado subido exitosamente</p>
                {enrollment.contract_uploaded_at && (
                  <p className="upload-date">
                    Subido el: {new Date(enrollment.contract_uploaded_at).toLocaleString('es-ES')}
                  </p>
                )}
                <div className="action-buttons">
                  <button 
                    className="btn btn-secondary" 
                    onClick={handleViewScannedContract}
                  >
                    <FiDownload /> Ver Contrato Escaneado
                  </button>
                  {canUploadContract && (
                    <button 
                      className="btn btn-secondary" 
                      onClick={() => {
                        setSelectedFile(null);
                        const fileInput = document.getElementById('contract-file') as HTMLInputElement;
                        if (fileInput) fileInput.value = '';
                      }}
                    >
                      <FiUpload /> Subir Nueva Versión
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="contract-upload-form">
                <div className="file-upload-area">
                  <input
                    type="file"
                    id="contract-file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    className="file-input"
                    disabled={uploading || !canUploadContract}
                  />
                  <label 
                    htmlFor="contract-file" 
                    className={`file-label ${selectedFile ? 'has-file' : ''} ${!canUploadContract ? 'disabled' : ''}`}
                  >
                    {selectedFile ? (
                      <>
                        <FiFileText />
                        <span>{selectedFile.name}</span>
                      </>
                    ) : (
                      <>
                        <FiUpload />
                        <span>Seleccionar archivo (PDF, JPG o PNG - máximo 10MB)</span>
                      </>
                    )}
                  </label>
                </div>
                {fileError && <p className="error-message">{fileError}</p>}
                <button 
                  className="btn btn-primary" 
                  onClick={handleUploadContract}
                  disabled={!selectedFile || uploading || !canUploadContract}
                >
                  {uploading ? <FiLoader className="spinning" /> : <FiUpload />}
                  {uploading ? 'Subiendo...' : 'Subir Contrato Escaneado'}
                </button>
                {!canUploadContract && enrollment.is_officially_enrolled && (
                  <p className="info-message">
                    El estudiante ya está oficialmente inscrito. No se pueden realizar más cambios.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Paso 3: Estado Final */}
      {enrollment.is_officially_enrolled && (
        <div className="card contract-step success-step">
          <div className="step-header">
            <div className="step-number success">✓</div>
            <div>
              <h3>Inscripción Completada</h3>
              <p>El estudiante ha sido oficialmente inscrito</p>
            </div>
          </div>
        </div>
      )}

      {isPendingApproval && !enrollment.is_officially_enrolled && (
        <div className="card contract-step warning-step">
          <div className="step-header">
            <div className="step-number warning">!</div>
            <div>
              <h3>Esperando Aprobación</h3>
              <p>El contrato escaneado ha sido subido y está esperando revisión por parte del administrador</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractManagement;






