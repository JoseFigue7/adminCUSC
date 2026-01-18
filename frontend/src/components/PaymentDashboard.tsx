import React, { useState, useEffect } from 'react';
import { paymentsApi } from '../services/api';
import { FiDollarSign, FiTrendingUp, FiCalendar, FiCreditCard } from '../utils/icons';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './PaymentDashboard.css';

interface Statistics {
  periods: {
    today: { total: number; count: number; average: number };
    week: { total: number; count: number; average: number };
    last_15_days: { total: number; count: number; average: number };
    month: { total: number; count: number; average: number };
    last_month: { total: number; count: number; average: number };
  };
  tuition: {
    today: { total: number; count: number; average: number };
    week: { total: number; count: number; average: number };
    last_15_days: { total: number; count: number; average: number };
    month: { total: number; count: number; average: number };
  };
  charts: {
    daily: Array<{ date: string; total: number; count: number }>;
    by_method: Array<{ method: string; method_display: string; total: number; count: number }>;
    by_type: Array<{ code: string; name: string; total: number; count: number }>;
  };
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
  }).format(value);
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('es-MX', {
    day: '2-digit',
    month: '2-digit',
  }).format(date);
};

const PaymentDashboard: React.FC = () => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await paymentsApi.getStatistics();
      setStatistics(response.data);
    } catch (err: any) {
      console.error('Error loading statistics:', err);
      setError('Error al cargar las estadísticas');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="payment-dashboard-loading">
        <div className="spinner"></div>
        <p>Cargando estadísticas...</p>
      </div>
    );
  }

  if (error || !statistics) {
    return (
      <div className="payment-dashboard-error">
        <p>{error || 'No se pudieron cargar las estadísticas'}</p>
        <button onClick={loadStatistics} className="btn btn-primary">
          Reintentar
        </button>
      </div>
    );
  }

  // Preparar datos para la gráfica diaria
  const dailyData = statistics.charts.daily.map(item => ({
    date: formatDate(item.date),
    total: item.total,
    count: item.count,
  }));

  // Preparar datos para gráfica por método
  const methodData = statistics.charts.by_method.map(item => ({
    name: item.method_display,
    total: item.total,
    count: item.count,
  }));

  // Preparar datos para gráfica por tipo
  const typeData = statistics.charts.by_type.slice(0, 6).map(item => ({
    name: item.name || item.code,
    value: item.total,
    count: item.count,
  }));

  // Calcular cambio porcentual entre mes actual y anterior
  const monthChange = statistics.periods.last_month.total > 0
    ? ((statistics.periods.month.total - statistics.periods.last_month.total) / statistics.periods.last_month.total) * 100
    : 0;

  return (
    <div className="payment-dashboard">
      <div className="dashboard-header">
        <h2>
          <FiDollarSign /> Dashboard de Pagos
        </h2>
        <button onClick={loadStatistics} className="btn btn-secondary btn-sm">
          Actualizar
        </button>
      </div>

      {/* Tarjetas de resumen por período */}
      <div className="stats-cards">
        <div className="stat-card">
          <div className="stat-card-header">
            <FiCalendar />
            <span>Hoy</span>
          </div>
          <div className="stat-card-content">
            <div className="stat-value">{formatCurrency(statistics.periods.today.total)}</div>
            <div className="stat-label">{statistics.periods.today.count} pagos</div>
            {statistics.periods.today.average > 0 && (
              <div className="stat-average">Promedio: {formatCurrency(statistics.periods.today.average)}</div>
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <FiCalendar />
            <span>Última Semana</span>
          </div>
          <div className="stat-card-content">
            <div className="stat-value">{formatCurrency(statistics.periods.week.total)}</div>
            <div className="stat-label">{statistics.periods.week.count} pagos</div>
            {statistics.periods.week.average > 0 && (
              <div className="stat-average">Promedio: {formatCurrency(statistics.periods.week.average)}</div>
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <FiTrendingUp />
            <span>Últimos 15 Días</span>
          </div>
          <div className="stat-card-content">
            <div className="stat-value">{formatCurrency(statistics.periods.last_15_days.total)}</div>
            <div className="stat-label">{statistics.periods.last_15_days.count} pagos</div>
            {statistics.periods.last_15_days.average > 0 && (
              <div className="stat-average">Promedio: {formatCurrency(statistics.periods.last_15_days.average)}</div>
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <FiDollarSign />
            <span>Mes Actual</span>
          </div>
          <div className="stat-card-content">
            <div className="stat-value">{formatCurrency(statistics.periods.month.total)}</div>
            <div className="stat-label">{statistics.periods.month.count} pagos</div>
            {statistics.periods.month.average > 0 && (
              <div className="stat-average">Promedio: {formatCurrency(statistics.periods.month.average)}</div>
            )}
            {statistics.periods.last_month.total > 0 && (
              <div className={`stat-change ${monthChange >= 0 ? 'positive' : 'negative'}`}>
                {monthChange >= 0 ? '+' : ''}{monthChange.toFixed(1)}% vs mes anterior
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tarjetas de Colegiaturas */}
      <div className="dashboard-section">
        <h3>
          <FiCreditCard /> Estadísticas de Colegiaturas
        </h3>
        <div className="stats-cards">
          <div className="stat-card stat-card-tuition">
            <div className="stat-card-header">
              <FiCalendar />
              <span>Hoy</span>
            </div>
            <div className="stat-card-content">
              <div className="stat-value">{formatCurrency(statistics.tuition.today.total)}</div>
              <div className="stat-label">{statistics.tuition.today.count} colegiaturas</div>
            </div>
          </div>

          <div className="stat-card stat-card-tuition">
            <div className="stat-card-header">
              <FiCalendar />
              <span>Última Semana</span>
            </div>
            <div className="stat-card-content">
              <div className="stat-value">{formatCurrency(statistics.tuition.week.total)}</div>
              <div className="stat-label">{statistics.tuition.week.count} colegiaturas</div>
            </div>
          </div>

          <div className="stat-card stat-card-tuition">
            <div className="stat-card-header">
              <FiTrendingUp />
              <span>Últimos 15 Días</span>
            </div>
            <div className="stat-card-content">
              <div className="stat-value">{formatCurrency(statistics.tuition.last_15_days.total)}</div>
              <div className="stat-label">{statistics.tuition.last_15_days.count} colegiaturas</div>
            </div>
          </div>

          <div className="stat-card stat-card-tuition">
            <div className="stat-card-header">
              <FiDollarSign />
              <span>Mes Actual</span>
            </div>
            <div className="stat-card-content">
              <div className="stat-value">{formatCurrency(statistics.tuition.month.total)}</div>
              <div className="stat-label">{statistics.tuition.month.count} colegiaturas</div>
            </div>
          </div>
        </div>
      </div>

      {/* Gráficas */}
      <div className="charts-container">
        {/* Gráfica de pagos diarios */}
        <div className="chart-card">
          <h3>Pagos Diarios (Últimos 15 Días)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip 
                formatter={(value: number) => formatCurrency(value)}
                labelFormatter={(label) => `Fecha: ${label}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="total" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="Monto Total"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfica por método de pago */}
        <div className="chart-card">
          <h3>Pagos por Método (Últimos 30 Días)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={methodData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip 
                formatter={(value: number) => formatCurrency(value)}
              />
              <Legend />
              <Bar dataKey="total" fill="#10b981" name="Monto Total" />
              <Bar dataKey="count" fill="#f59e0b" name="Cantidad" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfica por tipo de pago */}
        {typeData.length > 0 && (
          <div className="chart-card">
            <h3>Pagos por Tipo (Últimos 30 Días)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentDashboard;
