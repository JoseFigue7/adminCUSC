import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  getStudent,
  academicsApi
} from '../services/api';
import { 
  FiCalendar, FiPlus, FiArrowLeft, FiCheckCircle, FiXCircle,
  FiX, FiEdit, FiDollarSign, FiDownload, FiClock, FiAlertCircle
} from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './CuatrimestreEnrollment.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
  career: string;
  career_name: string;
}

interface Cuatrimestre {
  id: string;
  number: number;
  name: string;
  career: string;
}

interface CuatrimestreEnrollment {
  id: string;
  student: string;
  cuatrimestre: string;
  cuatrimestre_name: string;
  cuatrimestre_number: number;
  academic_year: number;
  status: string;
  status_display: string;
  enrollment_date: string;
  courses_count: number;
  career_name: string;
}

interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  cuatrimestre: string;
}

const CuatrimestreEnrollment: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const studentId = searchParams.get('studentId');
  const { success, error } = useToast();

  const [student, setStudent] = useState<Student | null>(null);
  const [cuatrimestres, setCuatrimestres] = useState<Cuatrimestre[]>([]);
  const [enrollments, setEnrollments] = useState<CuatrimestreEnrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    cuatrimestre: '',
    academic_year: new Date().getFullYear(),
    notes: ''
  });
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedEnrollment, setSelectedEnrollment] = useState<CuatrimestreEnrollment | null>(null);
  const [paymentData, setPaymentData] = useState({
    payment_method: 'EFECTIVO',
    payment_reference: '',
    transfer_receipt: null as File | null
  });

  useEffect(() => {
    if (studentId) {
      loadData();
    }
  }, [studentId]);

  const loadData = async () => {
    if (!studentId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [studentRes, enrollmentsRes] = await Promise.all([
        getStudent(studentId),
        academicsApi.getCuatrimestreEnrollments({ student_id: studentId })
      ]);

      setStudent(studentRes.data);
      const enrollments = enrollmentsRes.data.results || enrollmentsRes.data;
      setEnrollments(enrollments);

      // Cargar cuatrimestres de la carrera
      if (studentRes.data.career) {
        const cuatrimestresRes = await academicsApi.getCuatrimestres({ career: studentRes.data.career });
        const allCuatrimestres = cuatrimestresRes.data.results || cuatrimestresRes.data;
        setCuatrimestres(allCuatrimestres);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId) return;

    try {
      // Preparar datos: no enviar status al crear (usará el default 'PENDIENTE_PAGO' del backend)
      // Al editar, tampoco permitimos cambiar el status desde el formulario
      const enrollmentData = {
        cuatrimestre: formData.cuatrimestre,
        academic_year: formData.academic_year,
        notes: formData.notes,
        student: studentId
      };

      if (editingId) {
        await academicsApi.updateCuatrimestreEnrollment(editingId, enrollmentData);
        success('Inscripción actualizada exitosamente');
        setShowForm(false);
        setEditingId(null);
        setFormData({
          cuatrimestre: '',
          academic_year: new Date().getFullYear(),
          notes: ''
        });
        await loadData();
      } else {
        // Crear inscripción y redirigir inmediatamente a selección de cursos
        const response = await academicsApi.createCuatrimestreEnrollment(enrollmentData);
        const newEnrollmentId = response.data.id;
        success('Inscripción creada. Ahora seleccione los cursos.');
        // Redirigir a la selección de cursos
        navigate(`/courses/enroll?cuatrimestreEnrollmentId=${newEnrollmentId}`);
      }
    } catch (err: any) {
      console.error('Error saving enrollment:', err);
      error(err.response?.data?.detail || 'Error al guardar la inscripción');
    }
  };

  const handleEdit = (enrollment: CuatrimestreEnrollment) => {
    setEditingId(enrollment.id);
    setFormData({
      cuatrimestre: enrollment.cuatrimestre,
      academic_year: enrollment.academic_year,
      notes: ''
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('¿Está seguro de que desea eliminar esta inscripción?')) {
      return;
    }

    try {
      await academicsApi.deleteCuatrimestreEnrollment(id);
      success('Inscripción eliminada exitosamente');
      await loadData();
    } catch (err: any) {
      console.error('Error deleting enrollment:', err);
      error(err.response?.data?.detail || 'Error al eliminar la inscripción');
    }
  };

  const handleViewCourses = (enrollmentId: string) => {
    navigate(`/courses/enroll?cuatrimestreEnrollmentId=${enrollmentId}`);
  };

  const handleProcessPayment = (enrollment: CuatrimestreEnrollment) => {
    setSelectedEnrollment(enrollment);
    setPaymentData({
      payment_method: 'EFECTIVO',
      payment_reference: '',
      transfer_receipt: null
    });
    setShowPaymentModal(true);
  };

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEnrollment) return;

    try {
      await academicsApi.processEnrollmentPayment(selectedEnrollment.id, paymentData);
      success('Pago de inscripción procesado. Debe ser aprobado para continuar.');
      setShowPaymentModal(false);
      setSelectedEnrollment(null);
      await loadData();
    } catch (err: any) {
      console.error('Error processing payment:', err);
      error(err.response?.data?.error || 'Error al procesar el pago');
    }
  };

  const handleApprovePayment = async (enrollmentId: string) => {
    if (!window.confirm('¿Está seguro de aprobar este pago? Esto permitirá al estudiante asignar cursos.')) {
      return;
    }

    try {
      await academicsApi.approveEnrollmentPayment(enrollmentId);
      success('Pago aprobado. El estudiante ahora puede asignar cursos.');
      await loadData();
    } catch (err: any) {
      console.error('Error approving payment:', err);
      error(err.response?.data?.error || 'Error al aprobar el pago');
    }
  };

  const handleRejectPayment = async (enrollmentId: string) => {
    if (!window.confirm('¿Está seguro de rechazar este pago? El estudiante deberá crear un nuevo pago.')) {
      return;
    }

    try {
      await academicsApi.rejectEnrollmentPayment(enrollmentId);
      success('Pago rechazado. El estudiante puede crear un nuevo pago.');
      await loadData();
    } catch (err: any) {
      console.error('Error rejecting payment:', err);
      error(err.response?.data?.error || 'Error al rechazar el pago');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!student) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiXCircle className="empty-icon" />
          <h3>Estudiante no encontrado</h3>
          <p>No se pudo cargar la información del estudiante. Por favor, verifique el ID o intente nuevamente.</p>
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
            <FiCalendar className="header-icon" />
            <div>
              <h1>Inscripciones a Cuatrimestres</h1>
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
            <button 
              onClick={() => {
                setShowForm(!showForm);
                setEditingId(null);
                setFormData({
                  cuatrimestre: '',
                  academic_year: new Date().getFullYear(),
                  notes: ''
                });
              }}
              className="btn btn-primary btn-large"
            >
              <FiPlus /> {showForm ? 'Cancelar' : 'Nueva Inscripción'}
            </button>
          </div>
        </div>
      </div>

      {showForm && (
        <div className="card">
          <h2 className="card-title">
            {editingId ? 'Editar Inscripción' : 'Nueva Inscripción a Cuatrimestre'}
          </h2>
          <form onSubmit={handleSubmit} className="form">
            <div className="form-group">
              <label htmlFor="cuatrimestre">Cuatrimestre *</label>
              <select
                id="cuatrimestre"
                value={formData.cuatrimestre}
                onChange={(e) => setFormData({ ...formData, cuatrimestre: e.target.value })}
                required
              >
                <option value="">Seleccionar cuatrimestre</option>
                {cuatrimestres.map(cuat => (
                  <option key={cuat.id} value={cuat.id}>
                    {cuat.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="academic_year">Año Académico *</label>
              <input
                type="number"
                id="academic_year"
                value={formData.academic_year}
                onChange={(e) => setFormData({ ...formData, academic_year: parseInt(e.target.value) })}
                min="1900"
                max="9999"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="notes">Notas</label>
              <textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
              />
            </div>

            <div className="form-actions">
              <button type="button" onClick={() => {
                setShowForm(false);
                setEditingId(null);
              }} className="btn btn-secondary">
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary">
                {editingId ? 'Actualizar' : 'Crear'} Inscripción
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">
          <FiCalendar className="card-title-icon" />
          Inscripciones ({enrollments.length})
        </h2>

        {enrollments.length === 0 ? (
          <div className="empty-state">
            <FiCalendar className="empty-icon" />
            <h3>No hay inscripciones registradas</h3>
            <p>Crea una nueva inscripción para comenzar</p>
          </div>
        ) : (
          <div className="enrollments-list">
            {enrollments.map((enrollment) => (
              <div key={enrollment.id} className="enrollment-card">
                <div className="enrollment-header">
                  <div className="enrollment-info">
                    <h3>{enrollment.cuatrimestre_name}</h3>
                    <p className="enrollment-year">Año: {enrollment.academic_year}</p>
                    <p className="enrollment-career">{enrollment.career_name}</p>
                  </div>
                  <div className="enrollment-status">
                    <span className={`status-badge status-${enrollment.status.toLowerCase().replace('_', '-')}`}>
                      {enrollment.status_display}
                    </span>
                  </div>
                </div>
                
                <div className="enrollment-details">
                  <div className="enrollment-meta">
                    <span className="enrollment-date">
                      Fecha de inscripción: {new Date(enrollment.enrollment_date).toLocaleDateString()}
                    </span>
                    <span className="enrollment-courses-count">
                      {enrollment.courses_count} curso(s) inscrito(s)
                    </span>
                  </div>
                  
                  <div className="enrollment-actions">
                    {enrollment.status === 'PENDIENTE_PAGO' && (
                      <>
                        <button
                          onClick={() => handleProcessPayment(enrollment)}
                          className="btn btn-primary btn-sm"
                        >
                          <FiDollarSign /> Procesar Pago
                        </button>
                        <button
                          onClick={() => handleEdit(enrollment)}
                          className="btn btn-secondary btn-sm"
                        >
                          <FiEdit /> Editar
                        </button>
                      </>
                    )}
                    {enrollment.status === 'PENDIENTE_CONFIRMACION' && (
                      <>
                        <button
                          onClick={() => handleViewCourses(enrollment.id)}
                          className="btn btn-primary btn-sm"
                        >
                          <FiCheckCircle /> Asignar Cursos
                        </button>
                        <button
                          onClick={() => handleApprovePayment(enrollment.id)}
                          className="btn btn-success btn-sm"
                        >
                          <FiCheckCircle /> Aprobar Pago
                        </button>
                        <button
                          onClick={() => handleRejectPayment(enrollment.id)}
                          className="btn btn-warning btn-sm"
                        >
                          <FiXCircle /> Rechazar Pago
                        </button>
                      </>
                    )}
                    {enrollment.status === 'EN_CURSO' && (
                      <button
                        onClick={() => handleViewCourses(enrollment.id)}
                        className="btn btn-primary btn-sm"
                      >
                        <FiCheckCircle /> Ver Cursos
                      </button>
                    )}
                    {(enrollment.status === 'FINALIZADO' || enrollment.status === 'CANCELADO') && (
                      <button
                        onClick={() => handleViewCourses(enrollment.id)}
                        className="btn btn-secondary btn-sm"
                      >
                        <FiCheckCircle /> Ver Cursos
                      </button>
                    )}
                    {enrollment.status !== 'EN_CURSO' && enrollment.status !== 'FINALIZADO' && (
                      <button
                        onClick={() => handleDelete(enrollment.id)}
                        className="btn btn-danger btn-sm"
                      >
                        <FiX /> Eliminar
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showPaymentModal && selectedEnrollment && (
        <div className="modal-overlay" onClick={() => setShowPaymentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Procesar Pago de Inscripción</h2>
              <button className="modal-close" onClick={() => setShowPaymentModal(false)}>
                <FiX />
              </button>
            </div>
            <form onSubmit={handleSubmitPayment} className="form">
              <div className="form-group">
                <label htmlFor="payment_method">Método de Pago *</label>
                <select
                  id="payment_method"
                  value={paymentData.payment_method}
                  onChange={(e) => setPaymentData({ ...paymentData, payment_method: e.target.value })}
                  required
                >
                  <option value="EFECTIVO">Efectivo</option>
                  <option value="TRANSFERENCIA">Transferencia</option>
                  <option value="TARJETA">Tarjeta</option>
                </select>
              </div>

              {paymentData.payment_method === 'TRANSFERENCIA' && (
                <>
                  <div className="form-group">
                    <label htmlFor="payment_reference">Referencia de Pago</label>
                    <input
                      type="text"
                      id="payment_reference"
                      value={paymentData.payment_reference}
                      onChange={(e) => setPaymentData({ ...paymentData, payment_reference: e.target.value })}
                      placeholder="Número de referencia de transferencia"
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="transfer_receipt">Comprobante de Pago</label>
                    <input
                      type="file"
                      id="transfer_receipt"
                      accept="image/*,.pdf"
                      onChange={(e) => setPaymentData({ 
                        ...paymentData, 
                        transfer_receipt: e.target.files?.[0] || null 
                      })}
                    />
                  </div>
                </>
              )}

              {paymentData.payment_method === 'EFECTIVO' && (
                <div className="form-group">
                  <label htmlFor="payment_reference">Número de Recibo</label>
                  <input
                    type="text"
                    id="payment_reference"
                    value={paymentData.payment_reference}
                    onChange={(e) => setPaymentData({ ...paymentData, payment_reference: e.target.value })}
                    placeholder="Número de recibo (opcional)"
                  />
                </div>
              )}

              <div className="modal-actions">
                <button type="button" onClick={() => setShowPaymentModal(false)} className="btn btn-secondary">
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary">
                  Procesar Pago
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CuatrimestreEnrollment;

