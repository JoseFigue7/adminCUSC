import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { reportsApi } from '../services/api';
import { FiDownload, FiCalendar, FiDollarSign, FiUser, FiCheckCircle, FiClock, FiXCircle, FiTrendingUp, FiFile } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';

interface PaymentDetail {
  id: string;
  fecha_pago: string | null;
  fecha_creacion: string | null;
  estudiante: {
    id: string;
    carnet: string;
    nombre_completo: string;
    email: string;
  };
  tipo_pago: {
    codigo: string;
    nombre: string;
  };
  monto: {
    original: number;
    descuento_beca: number;
    mora: number;
    final: number;
  };
  estado: string;
  estado_display: string;
  metodo_pago: string;
  metodo_pago_display: string;
  referencia: string;
  mes: number | null;
  año: number | null;
  creado_por: string | null;
  aprobado_por: string | null;
  fecha_aprobacion: string | null;
}

interface ReportData {
  resumen: {
    total_pagos: number;
    aprobados: number;
    pendientes: number;
    rechazados: number;
    monto_total_aprobados: number;
    rango_fechas: {
      inicio: string | null;
      fin: string | null;
    };
  };
  pagos: PaymentDetail[];
}

const PaymentsDetailedReport: React.FC = () => {
  const { success, error } = useToast();
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  useEffect(() => {
    // Establecer fechas por defecto (último año)
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    
    setEndDate(today.toISOString().split('T')[0]);
    setStartDate(oneYearAgo.toISOString().split('T')[0]);
  }, []);

  const loadReport = async () => {
    if (!startDate || !endDate) {
      error('Por favor, selecciona un rango de fechas');
      return;
    }

    setLoading(true);
    try {
      const response = await reportsApi.paymentsDetailed({
        start_date: startDate,
        end_date: endDate,
      });
      setReportData(response.data);
      success('Reporte cargado exitosamente');
    } catch (err: any) {
      console.error('Error loading report:', err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || 'Error al cargar el reporte';
      error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const exportToExcel = async () => {
    if (!startDate || !endDate) {
      error('Por favor, selecciona un rango de fechas antes de exportar');
      return;
    }

    try {
      const response = await reportsApi.exportPaymentsExcel({
        start_date: startDate,
        end_date: endDate,
      });
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `reporte_pagos_detallado_${startDate}_${endDate}.xlsx`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      success('Reporte exportado a Excel exitosamente');
    } catch (err: any) {
      console.error('Error exporting to Excel:', err);
      error('Error al exportar el reporte a Excel');
    }
  };

  const exportToCSV = async () => {
    if (!startDate || !endDate) {
      error('Por favor, selecciona un rango de fechas antes de exportar');
      return;
    }

    try {
      // Exportar usando el endpoint del backend que respeta las fechas
      const response = await reportsApi.exportPayments({
        start_date: startDate,
        end_date: endDate,
      });
      
      // Crear blob desde la respuesta
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `reporte_pagos_detallado_${startDate}_${endDate}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      success('Reporte exportado exitosamente');
    } catch (err: any) {
      console.error('Error exporting report:', err);
      // Si falla el endpoint del backend, exportar desde los datos cargados
      if (!reportData || !reportData.pagos.length) {
        error('No hay datos para exportar. Por favor, genera el reporte primero.');
        return;
      }

      const headers = [
        'Fecha Pago',
        'Fecha Creación',
        'Carnet',
        'Estudiante',
        'Email',
        'Tipo de Pago',
        'Monto Original',
        'Descuento Beca',
        'Mora',
        'Monto Final',
        'Estado',
        'Método de Pago',
        'Referencia',
        'Mes',
        'Año',
        'Creado Por',
        'Aprobado Por',
        'Fecha Aprobación',
      ];

      const rows = reportData.pagos.map((pago) => [
        pago.fecha_pago || '',
        pago.fecha_creacion || '',
        pago.estudiante.carnet,
        pago.estudiante.nombre_completo,
        pago.estudiante.email,
        pago.tipo_pago.nombre,
        pago.monto.original.toFixed(2),
        pago.monto.descuento_beca.toFixed(2),
        pago.monto.mora.toFixed(2),
        pago.monto.final.toFixed(2),
        pago.estado_display,
        pago.metodo_pago_display,
        pago.referencia,
        pago.mes?.toString() || '',
        pago.año?.toString() || '',
        pago.creado_por || '',
        pago.aprobado_por || '',
        pago.fecha_aprobacion || '',
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `reporte_pagos_detallado_${startDate}_${endDate}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      success('Reporte exportado exitosamente (desde datos cargados)');
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'APROBADO':
        return 'status-badge status-approved';
      case 'PENDIENTE':
      case 'EN_REVISION':
        return 'status-badge status-pending';
      case 'RECHAZADO':
        return 'status-badge status-rejected';
      default:
        return 'status-badge';
    }
  };

  return (
    <div className="container">
      <div className="page-header">
        <h1>
          <FiDollarSign /> Reporte Detallado de Pagos
        </h1>
        <p>Consulta todos los pagos recibidos con información detallada</p>
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
          <Link to="/reports/payments-detailed" className="btn btn-primary" style={{ textDecoration: 'none' }}>
            <FiDollarSign /> Detallado
          </Link>
          <Link to="/reports/executive" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
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
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>Resumen</h2>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn btn-primary" onClick={exportToExcel}>
                  <FiFile /> Exportar Excel
                </button>
                <button className="btn btn-secondary" onClick={exportToCSV}>
                  <FiDownload /> Exportar CSV
                </button>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
              <div className="stat-card">
                <div className="stat-label">Total Pagos</div>
                <div className="stat-value">{reportData.resumen.total_pagos}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Aprobados</div>
                <div className="stat-value" style={{ color: 'var(--success)' }}>
                  <FiCheckCircle /> {reportData.resumen.aprobados}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Pendientes</div>
                <div className="stat-value" style={{ color: 'var(--warning)' }}>
                  <FiClock /> {reportData.resumen.pendientes}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Rechazados</div>
                <div className="stat-value" style={{ color: 'var(--danger)' }}>
                  <FiXCircle /> {reportData.resumen.rechazados}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Monto Total Aprobados</div>
                <div className="stat-value" style={{ color: 'var(--primary)' }}>
                  ${reportData.resumen.monto_total_aprobados.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2>Detalle de Pagos ({reportData.pagos.length})</h2>
            </div>
            {reportData.pagos.length === 0 ? (
              <div className="empty-state">
                <p>No hay pagos en el rango de fechas seleccionado</p>
              </div>
            ) : (
              <div className="table-container" style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Fecha Pago</th>
                      <th>Estudiante</th>
                      <th>Carnet</th>
                      <th>Tipo Pago</th>
                      <th>Monto Original</th>
                      <th>Descuento</th>
                      <th>Mora</th>
                      <th>Monto Final</th>
                      <th>Estado</th>
                      <th>Método</th>
                      <th>Referencia</th>
                      <th>Mes/Año</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportData.pagos.map((pago) => (
                      <tr key={pago.id}>
                        <td>
                          {pago.fecha_pago ? new Date(pago.fecha_pago).toLocaleDateString('es-MX') : '-'}
                        </td>
                        <td>
                          <strong>{pago.estudiante.nombre_completo}</strong>
                          {pago.estudiante.email && (
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                              {pago.estudiante.email}
                            </div>
                          )}
                        </td>
                        <td>
                          <span className="carnet-badge">{pago.estudiante.carnet || '-'}</span>
                        </td>
                        <td>
                          <div>
                            <strong>{pago.tipo_pago.nombre}</strong>
                            <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                              {pago.tipo_pago.codigo}
                            </div>
                          </div>
                        </td>
                        <td>${pago.monto.original.toFixed(2)}</td>
                        <td style={{ color: 'var(--success)' }}>
                          {pago.monto.descuento_beca > 0 ? `-$${pago.monto.descuento_beca.toFixed(2)}` : '-'}
                        </td>
                        <td style={{ color: 'var(--danger)' }}>
                          {pago.monto.mora > 0 ? `+$${pago.monto.mora.toFixed(2)}` : '-'}
                        </td>
                        <td>
                          <strong>${pago.monto.final.toFixed(2)}</strong>
                        </td>
                        <td>
                          <span className={getStatusBadgeClass(pago.estado)}>
                            {pago.estado_display}
                          </span>
                        </td>
                        <td>{pago.metodo_pago_display}</td>
                        <td>{pago.referencia || '-'}</td>
                        <td>
                          {pago.mes && pago.año ? `${pago.mes}/${pago.año}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default PaymentsDetailedReport;
