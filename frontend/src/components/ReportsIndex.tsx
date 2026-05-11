import React from 'react';
import { Link } from 'react-router-dom';
import { FiFileText, FiTrendingUp, FiDollarSign, FiBarChart2 } from '../utils/icons';
import './shared.css';

const ReportsIndex: React.FC = () => {
  return (
    <div className="container">
      <div className="page-header">
        <h1>
          <FiBarChart2 /> Reportes
        </h1>
        <p>Selecciona el tipo de reporte que deseas generar</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
        {/* Reporte Detallado de Pagos */}
        <Link 
          to="/reports/payments-detailed" 
          className="card"
          style={{ 
            textDecoration: 'none', 
            color: 'inherit',
            transition: 'transform 0.2s, box-shadow 0.2s',
            cursor: 'pointer'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
            e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}
        >
          <div style={{ padding: '2rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'var(--primary)' }}>
              <FiFileText />
            </div>
            <h2 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              Reporte Detallado de Pagos
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Consulta todos los pagos recibidos con información detallada: fechas, estudiantes, montos, estados y métodos de pago.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)', fontWeight: '500' }}>
              Ver reporte <FiDollarSign />
            </div>
          </div>
        </Link>

        {/* Reporte Ejecutivo */}
        <Link 
          to="/reports/executive" 
          className="card"
          style={{ 
            textDecoration: 'none', 
            color: 'inherit',
            transition: 'transform 0.2s, box-shadow 0.2s',
            cursor: 'pointer'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-5px)';
            e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}
        >
          <div style={{ padding: '2rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem', color: 'var(--success)' }}>
              <FiTrendingUp />
            </div>
            <h2 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
              Reporte Ejecutivo
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Estadísticas y análisis de pagos para gerencia: agrupados por tipo, método, mes y top estudiantes.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontWeight: '500' }}>
              Ver reporte <FiTrendingUp />
            </div>
          </div>
        </Link>
      </div>

      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header">
          <h3>Información</h3>
        </div>
        <div style={{ padding: '1rem' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>Nota:</strong> Todos los reportes permiten filtrar por rango de fechas y exportar los resultados a CSV.
          </p>
          <ul style={{ marginLeft: '1.5rem', color: 'var(--text-secondary)' }}>
            <li>Selecciona un rango de fechas antes de generar el reporte</li>
            <li>Los reportes se generan en tiempo real basados en los datos del sistema</li>
            <li>Puedes exportar los resultados a CSV para análisis externos</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ReportsIndex;
