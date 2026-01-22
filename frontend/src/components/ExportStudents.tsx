import React, { useState, useEffect, useCallback } from 'react';
import { exportsApi, academicsApi } from '../services/api';
import { FiDownload, FiUsers, FiCheck, FiX, FiFilter } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import Pagination from './Pagination';
import './shared.css';
import './ExportStudents.css';

interface Student {
  id: string;
  carnet: string;
  first_name: string;
  first_last_name?: string;
  second_last_name?: string;
  email: string;
  career_name: string;
  is_active: boolean;
  full_name?: string;
  moodle_username?: string;
  moodle_password?: string;
}

interface Career {
  id: string;
  name: string;
  code: number;
}

const ExportStudents: React.FC = () => {
  const { success, error, warning } = useToast();
  const [students, setStudents] = useState<Student[]>([]);
  const [careers, setCareers] = useState<Career[]>([]);
  const [selectedStudents, setSelectedStudents] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 50;

  // Filtros
  const [filters, setFilters] = useState({
    career: '',
    is_active: '',
    search: '',
    has_moodle_credentials: '', // Por defecto mostrar todos
  });

  const loadCareers = useCallback(async () => {
    try {
      const response = await academicsApi.getCareers();
      setCareers(response.data.results || response.data || []);
    } catch (err) {
      console.error('Error loading careers:', err);
    }
  }, []);

  const loadStudents = useCallback(async (page: number = 1, filterParams: any = {}) => {
    setLoading(true);
    try {
      const params: any = {
        page,
        page_size: itemsPerPage,
        ...filterParams,
      };

      const response = await exportsApi.listStudents(params);
      console.log('Students response:', response.data);
      const data = response.data;
      
      // Debug: verificar qué datos recibimos
      console.log('Total count:', data.count);
      console.log('Results:', data.results);

      if (data.results) {
        setStudents(data.results);
        setTotalPages(Math.ceil(data.count / itemsPerPage));
        setTotalItems(data.count);
      } else {
        const studentsArray = Array.isArray(data) ? data : [];
        setStudents(studentsArray);
        setTotalPages(1);
        setTotalItems(studentsArray.length);
      }
    } catch (err: any) {
      console.error('Error loading students:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || err.message || 'Error al cargar estudiantes';
      console.error('Error details:', errorMessage);
      error(errorMessage);
      // En caso de error, mostrar array vacío
      setStudents([]);
      setTotalPages(1);
      setTotalItems(0);
    } finally {
      setLoading(false);
    }
  }, [itemsPerPage, error]);

  useEffect(() => {
    loadCareers();
  }, [loadCareers]);

  useEffect(() => {
    loadStudents(currentPage, filters);
    // Limpiar selección al cambiar filtros o página
    setSelectedStudents(new Set());
  }, [currentPage, filters, loadStudents]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const handleSelectAll = () => {
    if (selectedStudents.size === students.length) {
      setSelectedStudents(new Set());
    } else {
      setSelectedStudents(new Set(students.map(s => s.id)));
    }
  };

  const handleSelectStudent = (studentId: string) => {
    setSelectedStudents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(studentId)) {
        newSet.delete(studentId);
      } else {
        newSet.add(studentId);
      }
      return newSet;
    });
  };

  const handleExport = async () => {
    if (selectedStudents.size === 0) {
      warning('Debe seleccionar al menos un estudiante para exportar');
      return;
    }

    // Verificar que los estudiantes seleccionados tengan credenciales de Moodle
    const studentsWithoutCredentials = students.filter(
      s => selectedStudents.has(s.id) && (!s.moodle_username || !s.moodle_password)
    );

    if (studentsWithoutCredentials.length > 0) {
      warning(
        `${studentsWithoutCredentials.length} estudiante(s) seleccionado(s) no tienen credenciales de Moodle. Solo se exportarán los que tengan credenciales.`
      );
    }

    setExporting(true);
    try {
      const response = await exportsApi.exportStudents(Array.from(selectedStudents));
      
      // Crear blob y descargar
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `moodle_export_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      success(`Exportación exitosa: ${selectedStudents.size} estudiante(s) exportado(s)`);
      setSelectedStudents(new Set());
    } catch (err: any) {
      console.error('Error exporting students:', err);
      error(err.response?.data?.error || 'Error al exportar estudiantes');
    } finally {
      setExporting(false);
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const allSelected = students.length > 0 && selectedStudents.size === students.length;
  const someSelected = selectedStudents.size > 0 && selectedStudents.size < students.length;

  if (loading && students.length === 0) {
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
            <FiDownload className="header-icon" />
            <div>
              <h1>Exportación para Moodle</h1>
              <p className="header-subtitle">Seleccione estudiantes para exportar a formato CSV</p>
            </div>
          </div>
          <button
            className="btn btn-primary btn-large"
            onClick={handleExport}
            disabled={exporting || selectedStudents.size === 0}
          >
            <FiDownload />
            {exporting ? 'Exportando...' : `Exportar (${selectedStudents.size})`}
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="filters-section">
        {/* Búsqueda principal */}
        <div className="search-section">
          <div className="search-group">
            <label htmlFor="search-input">
              <FiFilter />
              Búsqueda rápida
            </label>
            <input
              id="search-input"
              type="text"
              placeholder="Buscar por nombre, email, carnet..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        {/* Filtros agrupados */}
        <div className="filters-content">
          <div className="filters-grid">
            <div className="filter-group filter-group-career">
              <label htmlFor="career-filter">Carrera</label>
              <select
                id="career-filter"
                value={filters.career}
                onChange={(e) => handleFilterChange('career', e.target.value)}
              >
                <option value="">Todas las carreras</option>
                {careers.map(career => (
                  <option key={career.id} value={career.id}>
                    {career.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label htmlFor="status-filter">Estado</label>
              <select
                id="status-filter"
                value={filters.is_active}
                onChange={(e) => handleFilterChange('is_active', e.target.value)}
              >
                <option value="">Todos los estados</option>
                <option value="true">Activos</option>
                <option value="false">Inactivos</option>
              </select>
            </div>

            <div className="filter-group">
              <label htmlFor="moodle-filter">Credenciales Moodle</label>
              <select
                id="moodle-filter"
                value={filters.has_moodle_credentials}
                onChange={(e) => handleFilterChange('has_moodle_credentials', e.target.value)}
              >
                <option value="">Todos</option>
                <option value="true">Con credenciales</option>
                <option value="false">Sin credenciales</option>
              </select>
            </div>
          </div>

          {/* Botón para limpiar filtros */}
          {(filters.career || filters.is_active || filters.search || filters.has_moodle_credentials) && (
            <div className="filters-actions">
              <button
                className="btn btn-secondary btn-small"
                onClick={() => {
                  setFilters({
                    career: '',
                    is_active: '',
                    search: '',
                    has_moodle_credentials: '',
                  });
                  setCurrentPage(1);
                }}
              >
                <FiX />
                Limpiar filtros
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Información de selección */}
      {selectedStudents.size > 0 && (
        <div className="selection-info">
          <span>
            {selectedStudents.size} estudiante(s) seleccionado(s)
          </span>
          <button
            className="btn btn-secondary btn-small"
            onClick={() => setSelectedStudents(new Set())}
          >
            Limpiar selección
          </button>
        </div>
      )}

      {/* Tabla de estudiantes */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '50px' }}>
                <button
                  className="checkbox-button"
                  onClick={handleSelectAll}
                  title={allSelected ? 'Deseleccionar todos' : 'Seleccionar todos'}
                >
                  {allSelected ? <FiCheck className="checkbox-checked" /> : <span className="checkbox-empty">☐</span>}
                </button>
              </th>
              <th>Carnet</th>
              <th>Nombre</th>
              <th>Email</th>
              <th>Carrera</th>
              <th>Usuario Moodle</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {students.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2rem' }}>
                  No se encontraron estudiantes
                </td>
              </tr>
            ) : (
              students.map(student => {
                const isSelected = selectedStudents.has(student.id);
                const hasCredentials = student.moodle_username && student.moodle_password;

                return (
                  <tr
                    key={student.id}
                    className={isSelected ? 'selected' : ''}
                    onClick={() => handleSelectStudent(student.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <button
                        className="checkbox-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectStudent(student.id);
                        }}
                      >
                        {isSelected ? <FiCheck className="checkbox-checked" /> : <span className="checkbox-empty">☐</span>}
                      </button>
                    </td>
                    <td>{student.carnet || 'N/A'}</td>
                    <td>{student.full_name || `${student.first_name} ${student.first_last_name || ''}`.trim()}</td>
                    <td>{student.email}</td>
                    <td>{student.career_name || 'N/A'}</td>
                    <td>
                      {hasCredentials ? (
                        <span className="badge badge-success">{student.moodle_username}</span>
                      ) : (
                        <span className="badge badge-warning">Sin credenciales</span>
                      )}
                    </td>
                    <td>
                      <span className={`badge ${student.is_active ? 'badge-success' : 'badge-danger'}`}>
                        {student.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}

      <div className="page-footer">
        <p>Total: {totalItems} estudiante(s)</p>
      </div>
    </div>
  );
};

export default ExportStudents;
