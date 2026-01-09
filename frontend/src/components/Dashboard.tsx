import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getStudents, getPayments, getCareers } from '../services/api';
import { FiUsers, FiDollarSign, FiBook, FiTrendingUp, FiAlertCircle, FiCheckCircle, FiHome } from '../utils/icons';
import './shared.css';
import './Dashboard.css';

interface DashboardStats {
  totalStudents: number;
  activeStudents: number;
  totalPayments: number;
  pendingPayments: number;
  totalCareers: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalStudents: 0,
    activeStudents: 0,
    totalPayments: 0,
    pendingPayments: 0,
    totalCareers: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentStudents, setRecentStudents] = useState<any[]>([]);
  const [recentPayments, setRecentPayments] = useState<any[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [studentsRes, paymentsRes, careersRes] = await Promise.all([
        getStudents(),
        getPayments(),
        getCareers(),
      ]);

      const students = studentsRes.data.results || studentsRes.data;
      const payments = paymentsRes.data.results || paymentsRes.data;
      const careers = careersRes.data.results || careersRes.data;

      const activeStudents = students.filter((s: any) => s.is_active).length;
      const pendingPayments = payments.filter((p: any) => 
        p.status === 'PENDIENTE' || p.status === 'EN_REVISION'
      ).length;

      setStats({
        totalStudents: students.length,
        activeStudents,
        totalPayments: payments.length,
        pendingPayments,
        totalCareers: careers.length,
      });

      setRecentStudents(students.slice(0, 5));
      setRecentPayments(payments.slice(0, 5));
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando datos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Panel de Control</h1>
        <p className="dashboard-subtitle">Bienvenido al sistema de gestión estudiantil</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">
            <FiUsers />
          </div>
          <div className="stat-content">
            <h3>Total Estudiantes</h3>
            <p className="stat-number">{stats.totalStudents}</p>
            <span className="stat-label">Activos: {stats.activeStudents}</span>
          </div>
        </div>

        <div className="stat-card stat-card-success">
          <div className="stat-icon">
            <FiDollarSign />
          </div>
          <div className="stat-content">
            <h3>Pagos Totales</h3>
            <p className="stat-number">{stats.totalPayments}</p>
            <span className="stat-label">Pendientes: {stats.pendingPayments}</span>
          </div>
        </div>

        <div className="stat-card stat-card-info">
          <div className="stat-icon">
            <FiBook />
          </div>
          <div className="stat-content">
            <h3>Carreras</h3>
            <p className="stat-number">{stats.totalCareers}</p>
            <span className="stat-label">Disponibles</span>
          </div>
        </div>

        <div className="stat-card stat-card-warning">
          <div className="stat-icon">
            <FiAlertCircle />
          </div>
          <div className="stat-content">
            <h3>Pagos Pendientes</h3>
            <p className="stat-number">{stats.pendingPayments}</p>
            <span className="stat-label">Requieren atención</span>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="card-header">
            <h2>
              <FiUsers className="card-icon" />
              Estudiantes Recientes
            </h2>
            <Link to="/students" className="view-all-link">
              Ver todos <FiTrendingUp />
            </Link>
          </div>
          <div className="card-content">
            {recentStudents.length > 0 ? (
              <table className="recent-table">
                <thead>
                  <tr>
                    <th>Carnet</th>
                    <th>Nombre</th>
                    <th>Carrera</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {recentStudents.map((student) => (
                    <tr key={student.id}>
                      <td className="carnet-cell">{student.carnet}</td>
                      <td>{student.full_name || `${student.first_name} ${student.last_name}`}</td>
                      <td>{student.career_name}</td>
                      <td>
                        <span className={`status-badge ${student.is_active ? 'active' : 'inactive'}`}>
                          {student.is_active ? (
                            <>
                              <FiCheckCircle /> Activo
                            </>
                          ) : (
                            <>
                              <FiAlertCircle /> Inactivo
                            </>
                          )}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="empty-state">No hay estudiantes registrados</p>
            )}
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <h2>
              <FiDollarSign className="card-icon" />
              Pagos Recientes
            </h2>
            <Link to="/payments" className="view-all-link">
              Ver todos <FiTrendingUp />
            </Link>
          </div>
          <div className="card-content">
            {recentPayments.length > 0 ? (
              <table className="recent-table">
                <thead>
                  <tr>
                    <th>Estudiante</th>
                    <th>Monto</th>
                    <th>Mes</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {recentPayments.map((payment) => {
                    // Convertir amount a número si viene como string
                    const amount = typeof payment.amount === 'string' 
                      ? parseFloat(payment.amount) 
                      : payment.amount;
                    const formattedAmount = isNaN(amount) || amount === null || amount === undefined
                      ? '0.00'
                      : amount.toFixed(2);
                    
                    return (
                      <tr key={payment.id}>
                        <td>{payment.student_name}</td>
                        <td className="amount-cell">MX${formattedAmount}</td>
                        <td>{payment.month_display} {payment.year}</td>
                        <td>
                          <span className={`status-badge status-${payment.status.toLowerCase()}`}>
                            {payment.status_display}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <p className="empty-state">No hay pagos registrados</p>
            )}
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <h2>Acciones Rápidas</h2>
        <div className="actions-grid">
          <Link to="/students/new" className="action-card">
            <FiUsers className="action-icon" />
            <h3>Nuevo Estudiante</h3>
            <p>Registrar un nuevo estudiante en el sistema</p>
          </Link>
          <Link to="/payments" className="action-card">
            <FiDollarSign className="action-icon" />
            <h3>Gestionar Pagos</h3>
            <p>Ver y aprobar pagos pendientes</p>
          </Link>
          <Link to="/academics" className="action-card">
            <FiBook className="action-icon" />
            <h3>Progreso Académico</h3>
            <p>Revisar el progreso de los estudiantes</p>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

