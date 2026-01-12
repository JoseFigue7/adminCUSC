import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getStudents } from '../services/api';
import { FiUsers, FiPlus, FiEdit, FiTrendingUp, FiCheckCircle, FiXCircle, FiUser } from '../utils/icons';
import Pagination from './Pagination';
import AdvancedSearch, { FilterParams } from './AdvancedSearch';
import './shared.css';
import './StudentList.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  last_name?: string;
  first_last_name?: string;
  second_last_name?: string;
  email: string;
  career_name: string;
  is_active: boolean;
  full_name?: string;
}

const StudentList: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterParams>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 20;

  const loadStudents = useCallback(async (page: number = 1, filterParams: FilterParams = {}) => {
    setLoading(true);
    try {
      const response = await getStudents(page, itemsPerPage, filterParams);
      const data = response.data;
      
      // Manejar respuesta paginada o no paginada
      if (data.results) {
        setStudents(data.results);
        setTotalPages(Math.ceil(data.count / itemsPerPage));
        setTotalItems(data.count);
      } else {
        // Si no hay paginación, tratar como array
        const studentsArray = Array.isArray(data) ? data : [];
        setStudents(studentsArray);
        setTotalPages(1);
        setTotalItems(studentsArray.length);
      }
    } catch (error) {
      console.error('Error loading students:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStudents(currentPage, filters);
  }, [currentPage, filters, loadStudents]);

  const handleFilterChange = (newFilters: FilterParams) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleResetFilters = () => {
    setFilters({});
    setCurrentPage(1);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando estudiantes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-content">
          <div className="header-title">
            <FiUsers className="header-icon" />
            <div>
              <h1>Gestión de Estudiantes</h1>
              <p className="header-subtitle">Administra los estudiantes del sistema</p>
            </div>
          </div>
          <Link to="/students/new" className="btn btn-primary btn-large">
            <FiPlus /> Nuevo Estudiante
          </Link>
        </div>
      </div>

      <div className="card">
        <AdvancedSearch
          type="students"
          filters={filters}
          onFilterChange={handleFilterChange}
          onReset={handleResetFilters}
        />
        
        <div className="card-toolbar">
          <div className="stats-badge">
            {totalItems} estudiante{totalItems !== 1 ? 's' : ''}
          </div>
        </div>

        {students.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Carnet</th>
                  <th>Nombre Completo</th>
                  <th>Email</th>
                  <th>Carrera</th>
                  <th>Estado</th>
                  <th className="actions-column">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.id} className="table-row">
                    <td className="carnet-cell">
                      <span className="carnet-badge">{student.carnet}</span>
                    </td>
                    <td>
                      <div className="student-name">
                        <strong>{student.full_name || `${student.first_name} ${student.first_last_name || student.last_name || ''} ${student.second_last_name || ''}`.trim()}</strong>
                      </div>
                    </td>
                    <td className="email-cell">{student.email}</td>
                    <td>
                      <span className="career-badge">{student.career_name}</span>
                    </td>
                    <td>
                      <span className={`status-badge ${student.is_active ? 'active' : 'inactive'}`}>
                        {student.is_active ? (
                          <>
                            <FiCheckCircle /> Activo
                          </>
                        ) : (
                          <>
                            <FiXCircle /> Inactivo
                          </>
                        )}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <div className="action-buttons">
                        <Link 
                          to={`/students/${student.id}`} 
                          className="btn-icon btn-icon-primary"
                          title="Ver Detalles"
                        >
                          <FiUser />
                        </Link>
                        <Link 
                          to={`/students/${student.id}/edit`} 
                          className="btn-icon btn-icon-secondary"
                          title="Editar"
                        >
                          <FiEdit />
                        </Link>
                        <Link 
                          to={`/academics?studentId=${student.id}`} 
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
        ) : null}
        
        {totalPages > 1 && (
          <div style={{ marginTop: '2rem' }}>
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
              totalItems={totalItems}
              itemsPerPage={itemsPerPage}
            />
          </div>
        )}

        {students.length === 0 && !loading ? (
          <div className="empty-state">
            <FiUsers className="empty-icon" />
            <h3>No se encontraron estudiantes</h3>
            <p>
              {Object.keys(filters).length > 0
                ? 'No hay estudiantes que coincidan con los filtros aplicados' 
                : 'Comienza agregando tu primer estudiante'}
            </p>
            {Object.keys(filters).length === 0 && (
              <Link to="/students/new" className="btn btn-primary">
                <FiPlus /> Agregar Estudiante
              </Link>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default StudentList;
