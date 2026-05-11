import React, { useState, useEffect } from 'react';
import { FiSearch, FiFilter, FiX } from '../utils/icons';
import './AdvancedSearch.css';

export interface FilterParams {
  search?: string;
  [key: string]: any;
}

interface PaymentType {
  id: string;
  code: string;
  name: string;
}

interface AdvancedSearchProps {
  onFilterChange: (filters: FilterParams) => void;
  filters: FilterParams;
  type: 'students' | 'payments';
  onReset?: () => void;
  paymentTypes?: PaymentType[];
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({ onFilterChange, filters, type, onReset, paymentTypes = [] }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState<FilterParams>(filters);
  const [searchInputValue, setSearchInputValue] = useState<string>(filters.search || '');
  
  // Sincronizar filtros locales cuando cambien los filtros externos
  useEffect(() => {
    setLocalFilters(filters);
    setSearchInputValue(filters.search || '');
  }, [filters]);

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...localFilters, [key]: value || undefined };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const trimmedValue = searchInputValue.trim();
      const newFilters: FilterParams = { ...localFilters };
      
      // Limpiar propiedades undefined y vacías
      Object.keys(newFilters).forEach(key => {
        if (newFilters[key] === undefined || newFilters[key] === '') {
          delete newFilters[key];
        }
      });
      
      // Agregar o eliminar el filtro de búsqueda
      if (trimmedValue) {
        newFilters.search = trimmedValue;
      } else {
        delete newFilters.search;
      }
      
      setLocalFilters(newFilters);
      onFilterChange(newFilters);
    }
  };

  const handleReset = () => {
    const emptyFilters: FilterParams = {};
    setLocalFilters(emptyFilters);
    setSearchInputValue('');
    onFilterChange(emptyFilters);
    if (onReset) onReset();
  };

  const hasActiveFilters = Object.keys(localFilters).some(key => localFilters[key] !== undefined && localFilters[key] !== '');

  if (type === 'students') {
    return (
      <div className="advanced-search">
        <div className="search-header">
          <div className="search-input-container">
            <FiSearch className="search-icon" />
            <input
              type="text"
              placeholder="Buscar por carnet, nombre, apellido, email... (Presiona Enter para buscar)"
              value={searchInputValue}
              onChange={(e) => setSearchInputValue(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="search-input"
            />
            {hasActiveFilters && (
              <button onClick={handleReset} className="clear-filters-btn" title="Limpiar filtros">
                <FiX />
              </button>
            )}
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`filter-toggle-btn ${isExpanded ? 'active' : ''}`}
            title="Filtros avanzados"
          >
            <FiFilter />
            {hasActiveFilters && <span className="filter-badge"></span>}
          </button>
        </div>

        {isExpanded && (
          <div className="advanced-filters">
            <div className="filters-grid">
              <div className="filter-group">
                <label>Carnet</label>
                <input
                  type="text"
                  value={localFilters.carnet || ''}
                  onChange={(e) => handleFilterChange('carnet', e.target.value)}
                  placeholder="Buscar por carnet"
                />
              </div>

              <div className="filter-group">
                <label>Nombre</label>
                <input
                  type="text"
                  value={localFilters.first_name || ''}
                  onChange={(e) => handleFilterChange('first_name', e.target.value)}
                  placeholder="Buscar por nombre"
                />
              </div>

              <div className="filter-group">
                <label>Primer Apellido</label>
                <input
                  type="text"
                  value={localFilters.first_last_name || ''}
                  onChange={(e) => handleFilterChange('first_last_name', e.target.value)}
                  placeholder="Buscar por primer apellido"
                />
              </div>

              <div className="filter-group">
                <label>Segundo Apellido</label>
                <input
                  type="text"
                  value={localFilters.second_last_name || ''}
                  onChange={(e) => handleFilterChange('second_last_name', e.target.value)}
                  placeholder="Buscar por segundo apellido"
                />
              </div>

              <div className="filter-group">
                <label>Email</label>
                <input
                  type="email"
                  value={localFilters.email || ''}
                  onChange={(e) => handleFilterChange('email', e.target.value)}
                  placeholder="Buscar por email"
                />
              </div>

              <div className="filter-group">
                <label>Estado</label>
                <select
                  value={localFilters.is_active !== undefined ? String(localFilters.is_active) : ''}
                  onChange={(e) => handleFilterChange('is_active', e.target.value === '' ? undefined : e.target.value === 'true')}
                >
                  <option value="">Todos</option>
                  <option value="true">Activo</option>
                  <option value="false">Inactivo</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Tiene Beca</label>
                <select
                  value={localFilters.has_scholarship !== undefined ? String(localFilters.has_scholarship) : ''}
                  onChange={(e) => handleFilterChange('has_scholarship', e.target.value === '' ? undefined : e.target.value === 'true')}
                >
                  <option value="">Todos</option>
                  <option value="true">Sí</option>
                  <option value="false">No</option>
                </select>
              </div>

              <div className="filter-group">
                <label>Fecha de Inscripción Desde</label>
                <input
                  type="date"
                  value={localFilters.enrollment_date_from || ''}
                  onChange={(e) => handleFilterChange('enrollment_date_from', e.target.value)}
                />
              </div>

              <div className="filter-group">
                <label>Fecha de Inscripción Hasta</label>
                <input
                  type="date"
                  value={localFilters.enrollment_date_to || ''}
                  onChange={(e) => handleFilterChange('enrollment_date_to', e.target.value)}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Payment filters
  return (
    <div className="advanced-search">
      <div className="search-header">
        <div className="search-input-container">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por estudiante, carnet, número de recibo... (Presiona Enter para buscar)"
            value={searchInputValue}
            onChange={(e) => setSearchInputValue(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            className="search-input"
          />
          {hasActiveFilters && (
            <button onClick={handleReset} className="clear-filters-btn" title="Limpiar filtros">
              <FiX />
            </button>
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`filter-toggle-btn ${isExpanded ? 'active' : ''}`}
          title="Filtros avanzados"
        >
          <FiFilter />
          {hasActiveFilters && <span className="filter-badge"></span>}
        </button>
      </div>

      {isExpanded && (
        <div className="advanced-filters">
          <div className="filters-grid">
            <div className="filter-group">
              <label>Carnet del Estudiante</label>
              <input
                type="text"
                value={localFilters.student_carnet || ''}
                onChange={(e) => handleFilterChange('student_carnet', e.target.value)}
                placeholder="Buscar por carnet"
              />
            </div>

            <div className="filter-group">
              <label>Nombre del Estudiante</label>
              <input
                type="text"
                value={localFilters.student_name || ''}
                onChange={(e) => handleFilterChange('student_name', e.target.value)}
                placeholder="Buscar por nombre"
              />
            </div>

            <div className="filter-group">
              <label>Estado</label>
              <select
                value={localFilters.status || ''}
                onChange={(e) => {
                  const newFilters = { ...localFilters };
                  // Limpiar pending si se selecciona un estado único
                  delete newFilters.pending;
                  delete newFilters.status__in; // Limpiar el antiguo filtro si existe
                  if (e.target.value) {
                    newFilters.status = e.target.value;
                  } else {
                    delete newFilters.status;
                  }
                  setLocalFilters(newFilters);
                  onFilterChange(newFilters);
                }}
              >
                <option value="">Todos</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="EN_REVISION">En Revisión</option>
                <option value="APROBADO">Aprobado</option>
                <option value="RECHAZADO">Rechazado</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Tipo de Pago</label>
              <select
                value={localFilters.payment_type || ''}
                onChange={(e) => handleFilterChange('payment_type', e.target.value || undefined)}
              >
                <option value="">Todos</option>
                {paymentTypes.map((pt) => (
                  <option key={pt.id} value={pt.id}>
                    {pt.name} ({pt.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Método de Pago</label>
              <select
                value={localFilters.payment_method || ''}
                onChange={(e) => handleFilterChange('payment_method', e.target.value || undefined)}
              >
                <option value="">Todos</option>
                <option value="TRANSFERENCIA">Transferencia</option>
                <option value="TARJETA">Tarjeta</option>
                <option value="EFECTIVO">Efectivo</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Mes</label>
              <select
                value={localFilters.month || ''}
                onChange={(e) => handleFilterChange('month', e.target.value ? parseInt(e.target.value) : undefined)}
              >
                <option value="">Todos</option>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(m => (
                  <option key={m} value={m}>
                    {new Date(2000, m - 1).toLocaleString('es-ES', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Año</label>
              <input
                type="number"
                value={localFilters.year || ''}
                onChange={(e) => handleFilterChange('year', e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder="Ej: 2024"
                min="2000"
                max="2100"
              />
            </div>

            <div className="filter-group">
              <label>Fecha Desde</label>
              <input
                type="date"
                value={localFilters.payment_date_from || ''}
                onChange={(e) => handleFilterChange('payment_date_from', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Fecha Hasta</label>
              <input
                type="date"
                value={localFilters.payment_date_to || ''}
                onChange={(e) => handleFilterChange('payment_date_to', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>Monto Mínimo</label>
              <input
                type="number"
                value={localFilters.amount_min || ''}
                onChange={(e) => handleFilterChange('amount_min', e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="0.00"
                step="0.01"
                min="0"
              />
            </div>

            <div className="filter-group">
              <label>Monto Máximo</label>
              <input
                type="number"
                value={localFilters.amount_max || ''}
                onChange={(e) => handleFilterChange('amount_max', e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="0.00"
                step="0.01"
                min="0"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedSearch;

