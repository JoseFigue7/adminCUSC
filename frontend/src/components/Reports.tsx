import React, { useState, useEffect } from 'react';
import { reportsApi, getStudents, getPayments } from '../services/api';
import { 
  FiBarChart2, FiDownload, FiFileText, FiTrendingUp, FiUsers, 
  FiDollarSign, FiBook, FiAward, FiCalendar, FiFilter 
} from '../utils/icons';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import './shared.css';
import './Reports.css';

interface ReportData {
  students: {
    total: number;
    active: number;
    byCareer: Record<string, number>;
    byScholarship: Record<string, number>;
  };
  payments: {
    total: number;
    approved: number;
    pending: number;
    rejected: number;
    totalAmount: number;
    byMonth: Record<string, number>;
  };
  academics: {
    totalEnrollments: number;
    approvedCourses: number;
    averageGrade: number;
    pensumCompletion: number;
  };
  scholarships: {
    total: number;
    active: number;
    completa: number;
    media: number;
  };
}

const Reports: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [selectedReport, setSelectedReport] = useState<string>('overview');
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    loadReportData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateRange.start, dateRange.end]);

  const loadReportData = async () => {
    setLoading(true);
    try {
      // Usar el endpoint consolidado de reportes
      const response = await reportsApi.getOverview({
        start_date: dateRange.start,
        end_date: dateRange.end,
      });

      console.log('Reports API Response:', response.data);

      const data = response.data;
      
      // Validar que los datos existen
      if (!data || !data.students || !data.payments || !data.academics || !data.scholarships) {
        console.error('Invalid data structure from API:', data);
        setReportData(null);
        return;
      }
      
      // Mapear los datos del backend al formato esperado por el componente
      const reportData = {
        students: {
          total: data.students.total || 0,
          active: data.students.active || 0,
          byCareer: data.students.by_career || {},
          byScholarship: data.students.by_scholarship || {},
        },
        payments: {
          total: data.payments.total || 0,
          approved: data.payments.approved || 0,
          pending: data.payments.pending || 0,
          rejected: data.payments.rejected || 0,
          totalAmount: parseFloat(data.payments.total_amount || '0'),
          byMonth: data.payments.by_month || {},
        },
        academics: {
          totalEnrollments: data.academics.total_enrollments || 0,
          approvedCourses: data.academics.approved_courses || 0,
          averageGrade: parseFloat(String(data.academics.average_grade || '0')),
          pensumCompletion: Math.min(parseFloat(String(data.academics.pensum_completion || '0')), 100),
        },
        scholarships: {
          total: data.scholarships.total || 0,
          active: data.scholarships.active || 0,
          completa: data.scholarships.completa || 0,
          media: data.scholarships.media || 0,
        },
      };
      
      setReportData(reportData);
    } catch (error: any) {
      console.error('Error loading report data:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      
      // Mostrar mensaje de error más específico
      if (error.response?.status === 403) {
        console.error('Permiso denegado para ver reportes');
      } else if (error.response?.status === 404) {
        console.error('Endpoint de reportes no encontrado');
      } else if (error.response?.status >= 500) {
        console.error('Error del servidor al cargar reportes');
      } else {
        console.error('Error desconocido al cargar reportes');
      }
      
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) {
      alert('No hay datos para exportar');
      return;
    }

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
      }).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleExportStudents = async () => {
    try {
      // Usar endpoint de exportación del backend
      const response = await reportsApi.getOverview({ 
        start_date: dateRange.start, 
        end_date: dateRange.end 
      });
      const data = response.data;
      
      // Crear datos para CSV desde el reporte consolidado
      const students = await getStudents();
      const studentsList = students.data.results || students.data;
      exportToCSV(studentsList, 'estudiantes');
    } catch (error) {
      console.error('Error exporting students:', error);
    }
  };

  const handleExportPayments = async () => {
    try {
      // Usar endpoint de exportación del backend
      const payments = await getPayments({ 
        start_date: dateRange.start, 
        end_date: dateRange.end 
      });
      const paymentsList = payments.data.results || payments.data;
      exportToCSV(paymentsList, 'pagos');
    } catch (error) {
      console.error('Error exporting payments:', error);
    }
  };

  const exportToPDF = () => {
    if (!reportData) return;

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    let yPosition = margin;

    // Título
    doc.setFontSize(20);
    doc.setFont('helvetica', 'bold');
    doc.text('Reporte General del Sistema', pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 15;

    // Fecha
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const dateStr = `Generado el: ${new Date().toLocaleDateString('es-ES', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })}`;
    doc.text(dateStr, pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 20;

    // Resumen General
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Resumen General', margin, yPosition);
    yPosition += 10;

    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const summaryData = [
      ['Total Estudiantes', reportData.students.total.toString()],
      ['Estudiantes Activos', reportData.students.active.toString()],
      ['Total Pagos', reportData.payments.total.toString()],
      ['Pagos Aprobados', reportData.payments.approved.toString()],
      ['Monto Total', `MX$${reportData.payments.totalAmount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}`],
      ['Cursos Aprobados', reportData.academics.approvedCourses.toString()],
      ['Promedio General', reportData.academics.averageGrade.toFixed(1)],
      ['Becas Activas', reportData.scholarships.active.toString()],
    ];

    (doc as any).autoTable({
      startY: yPosition,
      head: [['Métrica', 'Valor']],
      body: summaryData,
      theme: 'striped',
      headStyles: { fillColor: [66, 153, 225], textColor: 255, fontStyle: 'bold' },
      margin: { left: margin, right: margin },
    });

    yPosition = (doc as any).lastAutoTable.finalY + 15;

    // Estudiantes por Carrera
    if (Object.keys(reportData.students.byCareer).length > 0) {
      if (yPosition > 250) {
        doc.addPage();
        yPosition = margin;
      }

      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Estudiantes por Carrera', margin, yPosition);
      yPosition += 10;

      const careerData = Object.entries(reportData.students.byCareer).map(([career, count]) => [
        career,
        count.toString(),
        `${((count as number / reportData.students.total) * 100).toFixed(1)}%`
      ]);

      (doc as any).autoTable({
        startY: yPosition,
        head: [['Carrera', 'Cantidad', 'Porcentaje']],
        body: careerData,
        theme: 'striped',
        headStyles: { fillColor: [66, 153, 225], textColor: 255, fontStyle: 'bold' },
        margin: { left: margin, right: margin },
      });

      yPosition = (doc as any).lastAutoTable.finalY + 15;
    }

    // Pagos por Mes
    if (Object.keys(reportData.payments.byMonth).length > 0) {
      if (yPosition > 250) {
        doc.addPage();
        yPosition = margin;
      }

      doc.setFontSize(14);
      doc.setFont('helvetica', 'bold');
      doc.text('Pagos por Mes', margin, yPosition);
      yPosition += 10;

      const paymentsData = Object.entries(reportData.payments.byMonth)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([month, amount]) => [
          month,
          `MX$${(amount as number).toLocaleString('es-ES', { minimumFractionDigits: 2 })}`
        ]);

      (doc as any).autoTable({
        startY: yPosition,
        head: [['Mes', 'Monto']],
        body: paymentsData,
        theme: 'striped',
        headStyles: { fillColor: [72, 187, 120], textColor: 255, fontStyle: 'bold' },
        margin: { left: margin, right: margin },
      });
    }

    // Guardar PDF
    doc.save(`reporte_general_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Generando reportes...</p>
        </div>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiBarChart2 className="empty-icon" />
          <h3>No se pudieron cargar los datos</h3>
          <p>Por favor, verifica la consola del navegador para más detalles del error.</p>
          <button 
            className="btn btn-primary" 
            onClick={() => loadReportData()}
            style={{ marginTop: '1rem' }}
          >
            Reintentar
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
            <FiBarChart2 className="header-icon" />
            <div>
              <h1>Reportes y Estadísticas</h1>
              <p className="header-subtitle">Análisis completo del sistema</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div className="date-range-selector">
              <FiCalendar className="calendar-icon" />
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                className="date-input"
              />
              <span>a</span>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                className="date-input"
              />
            </div>
            <button className="btn btn-primary btn-large" onClick={exportToPDF}>
              <FiFileText /> Exportar PDF
            </button>
          </div>
        </div>
      </div>

      <div className="report-tabs">
        <button
          className={`tab-button ${selectedReport === 'overview' ? 'active' : ''}`}
          onClick={() => setSelectedReport('overview')}
        >
          <FiTrendingUp /> Resumen General
        </button>
        <button
          className={`tab-button ${selectedReport === 'students' ? 'active' : ''}`}
          onClick={() => setSelectedReport('students')}
        >
          <FiUsers /> Estudiantes
        </button>
        <button
          className={`tab-button ${selectedReport === 'payments' ? 'active' : ''}`}
          onClick={() => setSelectedReport('payments')}
        >
          <FiDollarSign /> Pagos
        </button>
        <button
          className={`tab-button ${selectedReport === 'academics' ? 'active' : ''}`}
          onClick={() => setSelectedReport('academics')}
        >
          <FiBook /> Académico
        </button>
        <button
          className={`tab-button ${selectedReport === 'scholarships' ? 'active' : ''}`}
          onClick={() => setSelectedReport('scholarships')}
        >
          <FiAward /> Becas
        </button>
      </div>

      {selectedReport === 'overview' && (
        <div className="overview-grid">
          <div className="stat-card stat-primary">
            <div className="stat-icon">
              <FiUsers />
            </div>
            <div className="stat-content">
              <h3>Total Estudiantes</h3>
              <p className="stat-value">{reportData.students.total}</p>
              <p className="stat-subtitle">{reportData.students.active} activos</p>
            </div>
          </div>

          <div className="stat-card stat-success">
            <div className="stat-icon">
              <FiDollarSign />
            </div>
            <div className="stat-content">
              <h3>Pagos Totales</h3>
              <p className="stat-value">MX${reportData.payments.totalAmount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}</p>
              <p className="stat-subtitle">{reportData.payments.approved} aprobados</p>
            </div>
          </div>

          <div className="stat-card stat-info">
            <div className="stat-icon">
              <FiBook />
            </div>
            <div className="stat-content">
              <h3>Cursos Aprobados</h3>
              <p className="stat-value">{reportData.academics.approvedCourses}</p>
              <p className="stat-subtitle">Promedio: {reportData.academics.averageGrade.toFixed(1)}</p>
            </div>
          </div>

          <div className="stat-card stat-warning">
            <div className="stat-icon">
              <FiAward />
            </div>
            <div className="stat-content">
              <h3>Becas Activas</h3>
              <p className="stat-value">{reportData.scholarships.active}</p>
              <p className="stat-subtitle">{reportData.scholarships.completa} completas, {reportData.scholarships.media} medias</p>
            </div>
          </div>
        </div>
      )}

      {selectedReport === 'students' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <FiUsers className="card-title-icon" />
              Reporte de Estudiantes
            </h2>
            <button className="btn btn-primary" onClick={handleExportStudents}>
              <FiDownload /> Exportar CSV
            </button>
          </div>
          
          <div className="report-content">
            <div className="chart-container">
              <h3>Estudiantes por Carrera</h3>
              <div className="bar-chart">
                {Object.entries(reportData.students.byCareer).map(([career, count]) => (
                  <div key={career} className="bar-item">
                    <div className="bar-label">{career}</div>
                    <div className="bar-wrapper">
                      <div 
                        className="bar-fill"
                        style={{ 
                          width: `${(count / reportData.students.total) * 100}%`,
                          backgroundColor: `hsl(${(Object.keys(reportData.students.byCareer).indexOf(career) * 60) % 360}, 70%, 50%)`
                        }}
                      >
                        <span className="bar-value">{count}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="chart-container">
              <h3>Distribución de Becas</h3>
              <div className="pie-chart">
                {Object.entries(reportData.students.byScholarship).map(([type, count], index) => {
                  const percentage = (count / reportData.students.total) * 100;
                  const colors = ['#4299e1', '#48bb78', '#ed8936', '#e53e3e'];
                  return (
                    <div key={type} className="pie-item">
                      <div 
                        className="pie-color"
                        style={{ backgroundColor: colors[index % colors.length] }}
                      />
                      <span className="pie-label">
                        {type === 'NINGUNA' ? 'Sin Beca' : type === 'COMPLETA' ? 'Beca Completa' : 'Media Beca'}
                      </span>
                      <span className="pie-value">{count} ({percentage.toFixed(1)}%)</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedReport === 'payments' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <FiDollarSign className="card-title-icon" />
              Reporte de Pagos
            </h2>
            <button className="btn btn-primary" onClick={handleExportPayments}>
              <FiDownload /> Exportar CSV
            </button>
          </div>
          
          <div className="report-content">
            <div className="stats-row">
              <div className="mini-stat">
                <h4>Total Pagos</h4>
                <p>{reportData.payments.total}</p>
              </div>
              <div className="mini-stat">
                <h4>Aprobados</h4>
                <p className="text-success">{reportData.payments.approved}</p>
              </div>
              <div className="mini-stat">
                <h4>Pendientes</h4>
                <p className="text-warning">{reportData.payments.pending}</p>
              </div>
              <div className="mini-stat">
                <h4>Rechazados</h4>
                <p className="text-danger">{reportData.payments.rejected}</p>
              </div>
            </div>

            <div className="chart-container">
              <h3>Pagos por Mes</h3>
              <div className="bar-chart">
                {Object.entries(reportData.payments.byMonth)
                  .sort(([a], [b]) => a.localeCompare(b))
                  .map(([month, amount]) => (
                    <div key={month} className="bar-item">
                      <div className="bar-label">{month}</div>
                      <div className="bar-wrapper">
                        <div 
                          className="bar-fill"
                          style={{ 
                            width: `${(amount / reportData.payments.totalAmount) * 100}%`,
                            backgroundColor: '#48bb78'
                          }}
                        >
                          <span className="bar-value">MX${amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}</span>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedReport === 'academics' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <FiBook className="card-title-icon" />
              Reporte Académico
            </h2>
          </div>
          
          <div className="report-content">
            <div className="stats-row">
              <div className="mini-stat">
                <h4>Total Matrículas</h4>
                <p>{reportData.academics.totalEnrollments}</p>
              </div>
              <div className="mini-stat">
                <h4>Cursos Aprobados</h4>
                <p className="text-success">{reportData.academics.approvedCourses}</p>
              </div>
              <div className="mini-stat">
                <h4>Promedio General</h4>
                <p className="text-info">{reportData.academics.averageGrade.toFixed(1)}</p>
              </div>
              <div className="mini-stat">
                <h4>Completitud Pensum</h4>
                <p className="text-primary">{reportData.academics.pensumCompletion.toFixed(1)}%</p>
              </div>
            </div>

            <div className="progress-card">
              <h3>Progreso General del Sistema</h3>
              <div className="progress-bar-large">
                <div 
                  className="progress-fill"
                  style={{ width: `${reportData.academics.pensumCompletion}%` }}
                >
                  {reportData.academics.pensumCompletion.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedReport === 'scholarships' && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <FiAward className="card-title-icon" />
              Reporte de Becas
            </h2>
          </div>
          
          <div className="report-content">
            <div className="stats-row">
              <div className="mini-stat">
                <h4>Total Becas</h4>
                <p>{reportData.scholarships.total}</p>
              </div>
              <div className="mini-stat">
                <h4>Becas Activas</h4>
                <p className="text-success">{reportData.scholarships.active}</p>
              </div>
              <div className="mini-stat">
                <h4>Becas Completas</h4>
                <p className="text-warning">{reportData.scholarships.completa}</p>
              </div>
              <div className="mini-stat">
                <h4>Medias Becas</h4>
                <p className="text-info">{reportData.scholarships.media}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;




