import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getScholarships, createScholarship, getStudents, getCareers } from '../services/api';
import { 
  FiAward, FiPlus, FiSearch, FiEdit, FiXCircle, FiCheckCircle, 
  FiUsers, FiFilter, FiTrendingUp 
} from '../utils/icons';
import './shared.css';
import './ScholarshipManagement.css';

interface Scholarship {
  id: string;
  student_name: string;
  student_carnet: string;
  student_id: string;
  student: string;
  career_name: string;
  scholarship_type: string;
  scholarship_type_display: string;
  start_date: string;
  end_date: string | null;
  status: string;
  status_display: string;
  notes: string;
}

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name: string;
  career_name: string;
  scholarship_type: string;
}

interface Career {
  id: string;
  name: string;
  code: string;
}

const ScholarshipManagement: React.FC = () => {
  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [filteredScholarships, setFilteredScholarships] = useState<Scholarship[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [careers, setCareers] = useState<Career[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [careerFilter, setCareerFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    student: '',
    scholarship_type: 'COMPLETA',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterScholarships();
  }, [searchTerm, typeFilter, careerFilter, statusFilter, scholarships]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [scholarshipsRes, studentsRes, careersRes] = await Promise.all([
        getScholarships(),
        getStudents(),
        getCareers()
      ]);

      const scholarshipsData = scholarshipsRes.data.results || scholarshipsRes.data;
      setScholarships(scholarshipsData);
      setFilteredScholarships(scholarshipsData);

      const studentsData = studentsRes.data.results || studentsRes.data;
      setStudents(studentsData);

      const careersData = careersRes.data.results || careersRes.data;
      setCareers(careersData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterScholarships = () => {
    let filtered = [...scholarships];

    if (searchTerm) {
      filtered = filtered.filter(scholarship =>
        scholarship.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        scholarship.student_carnet.toLowerCase().includes(searchTerm.toLowerCase()) ||
        scholarship.career_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== 'ALL') {
      filtered = filtered.filter(scholarship => scholarship.scholarship_type === typeFilter);
    }

    if (careerFilter !== 'ALL') {
      filtered = filtered.filter(scholarship => {
        return scholarship.career_name === careerFilter;
      });
    }

    if (statusFilter !== 'ALL') {
      filtered = filtered.filter(scholarship => {
        if (statusFilter === 'ACTIVE') return scholarship.status === 'ACTIVA';
        if (statusFilter === 'INACTIVE') return scholarship.status !== 'ACTIVA';
        return true;
      });
    }

    setFilteredScholarships(filtered);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createScholarship(formData);
      alert('Beca creada exitosamente');
      setShowForm(false);
      setFormData({
        student: '',
        scholarship_type: 'COMPLETA',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        notes: '',
      });
      await loadData();
    } catch (error) {
      console.error('Error creating scholarship:', error);
      alert('Error al crear la beca');
    } finally {
      setSubmitting(false);
    }
  };

  const getTypeClass = (type: string): string => {
    return type === 'COMPLETA' ? 'type-full' : 'type-half';
  };

  const getTypeIcon = (type: string) => {
    return type === 'COMPLETA' ? <FiAward /> : <FiAward />;
  };

  const stats = {
    total: scholarships.length,
    active: scholarships.filter(s => s.status === 'ACTIVA').length,
    completa: scholarships.filter(s => s.scholarship_type === 'COMPLETA' && s.status === 'ACTIVA').length,
    media: scholarships.filter(s => s.scholarship_type === 'MEDIA' && s.status === 'ACTIVA').length,
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando becas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <FiAward className="header-icon" />
            <div>
              <h1>Gestión de Becas</h1>
              <p className="header-subtitle">Administra las becas de los estudiantes</p>
            </div>
          </div>
          <button 
            className="btn btn-primary btn-large"
            onClick={() => setShowForm(!showForm)}
          >
            <FiPlus /> {showForm ? 'Cancelar' : 'Nueva Beca'}
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-total">
          <h3>Total de Becas</h3>
          <p className="stat-value">{stats.total}</p>
        </div>
        <div className="stat-card stat-active">
          <h3>Becas Activas</h3>
          <p className="stat-value">{stats.active}</p>
        </div>
        <div className="stat-card stat-full">
          <h3>Becas Completas</h3>
          <p className="stat-value">{stats.completa}</p>
        </div>
        <div className="stat-card stat-half">
          <h3>Medias Becas</h3>
          <p className="stat-value">{stats.media}</p>
        </div>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2 className="card-title">Nueva Beca</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Estudiante *</label>
                <select
                  value={formData.student}
                  onChange={(e) => setFormData({ ...formData, student: e.target.value })}
                  className="form-input"
                  required
                >
                  <option value="">Seleccionar estudiante...</option>
                  {students
                    .filter(s => !scholarships.find(sch => sch.student_id === s.id && sch.status === 'ACTIVA'))
                    .map(student => (
                      <option key={student.id} value={student.id}>
                        {student.carnet} - {student.first_name} {student.last_name} ({student.career_name})
                      </option>
                    ))}
                </select>
              </div>
              <div className="form-group">
                <label>Tipo de Beca *</label>
                <select
                  value={formData.scholarship_type}
                  onChange={(e) => setFormData({ ...formData, scholarship_type: e.target.value })}
                  className="form-input"
                  required
                >
                  <option value="COMPLETA">Beca Completa</option>
                  <option value="MEDIA">Media Beca</option>
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Fecha de Inicio *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="form-input"
                  required
                />
              </div>
              <div className="form-group">
                <label>Fecha de Fin (Opcional)</label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="form-input"
                />
              </div>
            </div>
            <div className="form-group">
              <label>Notas</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="form-input"
                rows={3}
                placeholder="Notas adicionales sobre la beca..."
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary btn-large" disabled={submitting}>
                {submitting ? 'Guardando...' : 'Crear Beca'}
              </button>
              <button 
                type="button" 
                className="btn btn-secondary btn-large"
                onClick={() => setShowForm(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="card-toolbar">
          <div className="search-box">
            <FiSearch className="search-icon" />
            <input
              type="text"
              placeholder="Buscar por estudiante, carnet o carrera..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
          <div className="filter-group">
            <FiFilter className="filter-icon" />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="filter-select"
            >
              <option value="ALL">Todos los tipos</option>
              <option value="COMPLETA">Beca Completa</option>
              <option value="MEDIA">Media Beca</option>
            </select>
          </div>
          <div className="filter-group">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="filter-select"
            >
              <option value="ALL">Todos los estados</option>
              <option value="ACTIVE">Activas</option>
              <option value="INACTIVE">Inactivas</option>
            </select>
          </div>
          <div className="stats-badge">
            {filteredScholarships.length} beca(s)
          </div>
        </div>

        {filteredScholarships.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Estudiante</th>
                  <th>Carnet</th>
                  <th>Carrera</th>
                  <th>Tipo de Beca</th>
                  <th>Fecha Inicio</th>
                  <th>Fecha Fin</th>
                  <th>Estado</th>
                  <th className="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filteredScholarships.map((scholarship) => (
                  <tr key={scholarship.id} className="table-row">
                    <td className="student-cell">
                      <strong>{scholarship.student_name}</strong>
                    </td>
                    <td>
                      <span className="carnet-badge">{scholarship.student_carnet}</span>
                    </td>
                    <td>{scholarship.career_name}</td>
                    <td>
                      <span className={`scholarship-type ${getTypeClass(scholarship.scholarship_type)}`}>
                        {getTypeIcon(scholarship.scholarship_type)}
                        {scholarship.scholarship_type_display}
                      </span>
                    </td>
                    <td className="date-cell">
                      {new Date(scholarship.start_date).toLocaleDateString('es-ES')}
                    </td>
                    <td className="date-cell">
                      {scholarship.end_date 
                        ? new Date(scholarship.end_date).toLocaleDateString('es-ES')
                        : 'Sin fecha límite'}
                    </td>
                    <td>
                      <span className={`status-badge ${scholarship.status === 'ACTIVA' ? 'status-active' : 'status-inactive'}`}>
                        {scholarship.status === 'ACTIVA' ? (
                          <>
                            <FiCheckCircle /> {scholarship.status_display}
                          </>
                        ) : (
                          <>
                            <FiXCircle /> {scholarship.status_display}
                          </>
                        )}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <div className="action-buttons">
                        <Link 
                          to={`/students/${scholarship.student_id}`} 
                          className="btn-icon btn-icon-primary"
                          title="Ver Estudiante"
                        >
                          <FiUsers />
                        </Link>
                        <Link 
                          to={`/academics?studentId=${scholarship.student_id}`} 
                          className="btn-icon btn-icon-success"
                          title="Ver Progreso"
                        >
                          <FiTrendingUp />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <FiAward className="empty-icon" />
            <h3>No se encontraron becas</h3>
            <p>
              {searchTerm || typeFilter !== 'ALL' || statusFilter !== 'ALL'
                ? 'No hay becas que coincidan con los filtros aplicados'
                : 'No hay becas registradas en el sistema'}
            </p>
            {!showForm && (
              <button 
                className="btn btn-primary"
                onClick={() => setShowForm(true)}
              >
                <FiPlus /> Crear Primera Beca
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ScholarshipManagement;

