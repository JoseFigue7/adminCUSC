import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reportsApi } from '../services/api';
import { FiDownload, FiCalendar, FiTrendingUp, FiDollarSign, FiBarChart2, FiUsers, FiFileText, FiFile } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';

interface PaymentByType {
  codigo: string;
  nombre: string;
  cantidad: number;
  monto_total: number;
  porcentaje_del_total: number;
}

interface PaymentByMethod {
  metodo: string;
  metodo_display: string;
  cantidad: number;
  monto_total: number;
  porcentaje_del_total: number;
}

interface PaymentByMonth {
  año: number;
  mes: number;
  mes_nombre: string;
  cantidad: number;
  monto_total: number;
}

interface TopStudent {
  carnet: string;
  nombre_completo: string;
  cantidad_pagos: number;
  monto_total: number;
}

interface ExecutiveReportData {
  resumen_general: {
    total_pagos: number;
    monto_total: number;
    promedio_por_pago: number;
    rango_fechas: {
      inicio: string | null;
      fin: string | null;
    };
  };
  pagos_por_tipo: { [key: string]: PaymentByType };
  pagos_por_metodo: { [key: string]: PaymentByMethod };
  pagos_por_mes: { [key: string]: PaymentByMonth };
  top_estudiantes: TopStudent[];
}

const ExecutiveReport: React.FC = () => {
  const { success, error } = useToast();
  const [reportData, setReportData] = useState<ExecutiveReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  useEffect(() => {
    // Establecer fechas por defecto (año actual)
    const today = new Date();
    const yearStart = new Date(today.getFullYear(), 0, 1);
    
    setEndDate(today.toISOString().split('T')[0]);
    setStartDate(yearStart.toISOString().split('T')[0]);
  }, []);

  const loadReport = async () => {
    if (!startDate || !endDate) {
      error('Por favor, selecciona un rango de fechas');
      return;
    }

    setLoading(true);
    try {
      const response = await reportsApi.executive({
        start_date: startDate,
        end_date: endDate,
      });
      setReportData(response.data);
      success('Reporte ejecutivo cargado exitosamente');
    } catch (err: any) {
      console.error('Error loading executive report:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al cargar el reporte ejecutivo';
      error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const exportToPDF = async () => {
    if (!startDate || !endDate) {
      error('Por favor, selecciona un rango de fechas antes de exportar');
      return;
    }

    try {
      const response = await reportsApi.exportExecutivePDF({
        start_date: startDate,
        end_date: endDate,
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `reporte_ejecutivo_${startDate}_${endDate}.pdf`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      success('Reporte ejecutivo exportado a PDF exitosamente');
    } catch (err: any) {
      console.error('Error exporting to PDF:', err);
      error('Error al exportar el reporte a PDF');
    }
  };

  const exportToCSV = () => {
    if (!reportData) {
      error('No hay datos para exportar');
      return;
    }

    const lines: string[] = [];
    
    // Resumen General
    lines.push('REPORTE EJECUTIVO DE PAGOS');
    lines.push(`Período: ${startDate} a ${endDate}`);
    lines.push('');
    lines.push('RESUMEN GENERAL');
    lines.push(`Total de Pagos,${reportData.resumen_general.total_pagos}`);
    lines.push(`Monto Total,${reportData.resumen_general.monto_total.toFixed(2)}`);
    lines.push(`Promedio por Pago,${reportData.resumen_general.promedio_por_pago.toFixed(2)}`);
    lines.push('');
    
    // Pagos por Tipo
    lines.push('PAGOS POR TIPO DE PAGO');
    lines.push('Código,Nombre,Cantidad,Monto Total,Porcentaje');
    Object.values(reportData.pagos_por_tipo).forEach((tipo) => {
      lines.push(`${tipo.codigo},"${tipo.nombre}",${tipo.cantidad},${tipo.monto_total.toFixed(2)},${tipo.porcentaje_del_total.toFixed(2)}%`);
    });
    lines.push('');
    
    // Pagos por Método
    lines.push('PAGOS POR MÉTODO DE PAGO');
    lines.push('Método,Cantidad,Monto Total,Porcentaje');
    Object.values(reportData.pagos_por_metodo).forEach((metodo) => {
      lines.push(`"${metodo.metodo_display}",${metodo.cantidad},${metodo.monto_total.toFixed(2)},${metodo.porcentaje_del_total.toFixed(2)}%`);
    });
    lines.push('');
    
    // Pagos por Mes
    lines.push('PAGOS POR MES');
    lines.push('Año,Mes,Cantidad,Monto Total');
    Object.values(reportData.pagos_por_mes)
      .sort((a, b) => {
        if (a.año !== b.año) return a.año - b.año;
        return a.mes - b.mes;
      })
      .forEach((mes) => {
        lines.push(`${mes.año},"${mes.mes_nombre}",${mes.cantidad},${mes.monto_total.toFixed(2)}`);
      });
    lines.push('');
    
    // Top Estudiantes
    lines.push('TOP 10 ESTUDIANTES POR MONTO PAGADO');
    lines.push('Carnet,Nombre Completo,Cantidad Pagos,Monto Total');
    reportData.top_estudiantes.forEach((estudiante) => {
      lines.push(`${estudiante.carnet},"${estudiante.nombre_completo}",${estudiante.cantidad_pagos},${estudiante.monto_total.toFixed(2)}`);
    });

    const csvContent = lines.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `reporte_ejecutivo_${startDate}_${endDate}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    success('Reporte ejecutivo exportado exitosamente');
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>
          <FiTrendingUp /> Reporte Ejecutivo
        </h1>
        <p>Estadísticas y análisis de pagos para gerencia</p>
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
          <Link to="/reports/payments-detailed" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
            <FiFileText /> Detallado
          </Link>
          <Link to="/reports/executive" className="btn btn-primary" style={{ textDecoration: 'none' }}>
            <FiTrendingUp /> Ejecutivo
          </Link>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Filtros</h2>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label htmlFor="startDate">Fecha Inicio</label>
            <input
              type="date"
              id="startDate"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="form-input"
            />
          </div>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label htmlFor="endDate">Fecha Fin</label>
            <input
              type="date"
              id="endDate"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="form-input"
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={loadReport}
            disabled={loading || !startDate || !endDate}
          >
            <FiCalendar /> {loading ? 'Cargando...' : 'Generar Reporte'}
          </button>
        </div>
      </div>

      {reportData && (
        <>
          {/* Resumen General */}
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>
                <FiBarChart2 /> Resumen General
              </h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button 
                  className="btn btn-primary" 
                  onClick={exportToPDF}
                  disabled={!startDate || !endDate}
                  title={!startDate || !endDate ? 'Selecciona un rango de fechas para exportar' : `Exportar reporte ejecutivo a PDF del ${startDate} al ${endDate}`}
                >
                  <FiFile /> Exportar PDF
                </button>
                <button 
                  className="btn btn-secondary" 
                  onClick={exportToCSV}
                  disabled={!startDate || !endDate}
                  title={!startDate || !endDate ? 'Selecciona un rango de fechas para exportar' : `Exportar reporte ejecutivo del ${startDate} al ${endDate}`}
                >
                  <FiDownload /> Exportar CSV
                </button>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem' }}>
              <div className="stat-card" style={{ background: 'linear-gradient(135deg, var(--primary), var(--primary-dark))', color: 'white' }}>
                <div className="stat-label" style={{ color: 'rgba(255,255,255,0.9)' }}>Total de Pagos</div>
                <div className="stat-value" style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>
                  {reportData.resumen_general.total_pagos}
                </div>
              </div>
              <div className="stat-card" style={{ background: 'linear-gradient(135deg, var(--success), #28a745)', color: 'white' }}>
                <div className="stat-label" style={{ color: 'rgba(255,255,255,0.9)' }}>Monto Total</div>
                <div className="stat-value" style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>
                  ${reportData.resumen_general.monto_total.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
              <div className="stat-card" style={{ background: 'linear-gradient(135deg, var(--info), #17a2b8)', color: 'white' }}>
                <div className="stat-label" style={{ color: 'rgba(255,255,255,0.9)' }}>Promedio por Pago</div>
                <div className="stat-value" style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>
                  ${reportData.resumen_general.promedio_por_pago.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          </div>

          {/* Pagos por Tipo */}
          <div className="card">
            <div className="card-header">
              <h2>
                <FiBarChart2 /> Pagos por Tipo de Pago
              </h2>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Código</th>
                    <th>Nombre</th>
                    <th>Cantidad</th>
                    <th>Monto Total</th>
                    <th>% del Total</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.values(reportData.pagos_por_tipo)
                    .sort((a, b) => b.monto_total - a.monto_total)
                    .map((tipo, index) => (
                      <tr key={tipo.codigo}>
                        <td>
                          <span className="carnet-badge">{tipo.codigo}</span>
                        </td>
                        <td><strong>{tipo.nombre}</strong></td>
                        <td>{tipo.cantidad}</td>
                        <td>
                          <strong>${tipo.monto_total.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ 
                              flex: 1, 
                              height: '20px', 
                              backgroundColor: 'var(--bg-secondary)', 
                              borderRadius: '10px',
                              overflow: 'hidden'
                            }}>
                              <div style={{
                                width: `${tipo.porcentaje_del_total}%`,
                                height: '100%',
                                backgroundColor: `hsl(${index * 60}, 70%, 50%)`,
                                transition: 'width 0.3s ease'
                              }} />
                            </div>
                            <span style={{ minWidth: '50px', textAlign: 'right' }}>
                              {tipo.porcentaje_del_total.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagos por Método */}
          <div className="card">
            <div className="card-header">
              <h2>
                <FiDollarSign /> Pagos por Método de Pago
              </h2>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Método</th>
                    <th>Cantidad</th>
                    <th>Monto Total</th>
                    <th>% del Total</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.values(reportData.pagos_por_metodo)
                    .sort((a, b) => b.monto_total - a.monto_total)
                    .map((metodo, index) => (
                      <tr key={metodo.metodo}>
                        <td><strong>{metodo.metodo_display}</strong></td>
                        <td>{metodo.cantidad}</td>
                        <td>
                          <strong>${metodo.monto_total.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ 
                              flex: 1, 
                              height: '20px', 
                              backgroundColor: 'var(--bg-secondary)', 
                              borderRadius: '10px',
                              overflow: 'hidden'
                            }}>
                              <div style={{
                                width: `${metodo.porcentaje_del_total}%`,
                                height: '100%',
                                backgroundColor: `hsl(${120 + index * 60}, 70%, 50%)`,
                                transition: 'width 0.3s ease'
                              }} />
                            </div>
                            <span style={{ minWidth: '50px', textAlign: 'right' }}>
                              {metodo.porcentaje_del_total.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagos por Mes */}
          <div className="card">
            <div className="card-header">
              <h2>
                <FiCalendar /> Pagos por Mes
              </h2>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Año</th>
                    <th>Mes</th>
                    <th>Cantidad</th>
                    <th>Monto Total</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.values(reportData.pagos_por_mes)
                    .sort((a, b) => {
                      if (a.año !== b.año) return a.año - b.año;
                      return a.mes - b.mes;
                    })
                    .map((mes) => (
                      <tr key={`${mes.año}-${mes.mes}`}>
                        <td>{mes.año}</td>
                        <td><strong>{mes.mes_nombre}</strong></td>
                        <td>{mes.cantidad}</td>
                        <td>
                          <strong>${mes.monto_total.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Estudiantes */}
          <div className="card">
            <div className="card-header">
              <h2>
                <FiUsers /> Top 10 Estudiantes por Monto Pagado
              </h2>
            </div>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Carnet</th>
                    <th>Estudiante</th>
                    <th>Cantidad Pagos</th>
                    <th>Monto Total</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.top_estudiantes.map((estudiante, index) => (
                    <tr key={estudiante.carnet}>
                      <td>
                        <span className="carnet-badge" style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
                          {index + 1}
                        </span>
                      </td>
                      <td>
                        <span className="carnet-badge">{estudiante.carnet}</span>
                      </td>
                      <td><strong>{estudiante.nombre_completo}</strong></td>
                      <td>{estudiante.cantidad_pagos}</td>
                      <td>
                        <strong style={{ color: 'var(--success)', fontSize: '1.1rem' }}>
                          ${estudiante.monto_total.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ExecutiveReport;
