import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { FiHome, FiUsers, FiDollarSign, FiBook, FiAward, FiLogOut, FiUser, FiDownload, FiTrendingUp, FiFileText } from './utils/icons';
import Dashboard from './components/Dashboard';
import StudentList from './components/StudentList';
import StudentForm from './components/StudentForm';
import StudentDetail from './components/StudentDetail';
import EnrollmentForm from './components/EnrollmentForm';
import ContractManagement from './components/ContractManagement';
import PaymentList from './components/PaymentList';
import PaymentForm from './components/PaymentForm';
import PendingTransfers from './components/PendingTransfers';
import AcademicProgress from './components/AcademicProgress';
import CourseEnrollment from './components/CourseEnrollment';
import CuatrimestreEnrollment from './components/CuatrimestreEnrollment';
import CareerPensum from './components/CareerPensum';
import GraduationMethodManagement from './components/GraduationMethodManagement';
import GradeUpload from './components/GradeUpload';
import ScholarshipManagement from './components/ScholarshipManagement';
import ExportStudents from './components/ExportStudents';
import ReportsIndex from './components/ReportsIndex';
import PaymentsDetailedReport from './components/PaymentsDetailedReport';
import ExecutiveReport from './components/ExecutiveReport';
import Login from './components/Login';
import Register from './components/Register';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import UserProfile from './components/UserProfile';
import StudentAccounting from './components/StudentAccounting';
import PublicPayment from './components/PublicPayment';
import ProtectedRoute from './components/ProtectedRoute';
import Toast from './components/Toast';
import ThemeToggle from './components/ThemeToggle';
import { useAuth } from './context/AuthContext';
import { useToastContext } from './context/ToastContext';
import './App.css';

const Navigation: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav>
      <Link to="/" className={isActive('/') && location.pathname === '/' ? 'active' : ''}>
        <FiHome /> Inicio
      </Link>
      <Link to="/students" className={isActive('/students') ? 'active' : ''}>
        <FiUsers /> Estudiantes
      </Link>
      <Link to="/payments" className={isActive('/payments') ? 'active' : ''}>
        <FiDollarSign /> Pagos
      </Link>
      <Link to="/academics" className={isActive('/academics') ? 'active' : ''}>
        <FiBook /> Académico
      </Link>
      <Link to="/scholarships" className={isActive('/scholarships') ? 'active' : ''}>
        <FiAward /> Becas
      </Link>
      <Link to="/exports" className={isActive('/exports') ? 'active' : ''}>
        <FiDownload /> Exportación
      </Link>
      <Link to="/reports" className={isActive('/reports') ? 'active' : ''}>
        <FiFileText /> Reportes
      </Link>
    </nav>
  );
};

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="app-container">
      {isAuthenticated && (
        <header className="app-header">
          <div className="app-header-content">
            <div className="app-header-brand">
              <img src="/SC Logo.png" alt="AdminCUSC Logo" className="app-logo" />
            </div>
            <Navigation />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {user && (
              <Link 
                to="/profile" 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem', 
                  marginRight: '1rem',
                  textDecoration: 'none',
                  color: 'var(--text-secondary)',
                  fontSize: '0.9rem',
                  transition: 'color 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--primary-color)'}
                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
              >
                <FiUser />
                <span>
                  {user.first_name && user.last_name 
                    ? `${user.first_name} ${user.last_name}` 
                    : user.username}
                </span>
                {user.role && (
                  <span style={{ 
                    background: 'var(--primary-color-alpha)', 
                    color: 'var(--primary-color)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.85rem',
                    fontWeight: 500
                  }}>
                    {user.role.description || user.role.name}
                  </span>
                )}
              </Link>
            )}
            <button 
              onClick={handleLogout}
              className="btn btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              title="Cerrar sesión"
            >
              <FiLogOut /> Salir
            </button>
            <ThemeToggle />
          </div>
        </header>
      )}
      <main className="app-main">
        {children}
      </main>
    </div>
  );
};

function AppContent() {
  const { toasts, removeToast } = useToastContext();
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  
  // Detectar si estamos en la página pública de pagos
  const isPublicPaymentPage = location.pathname === '/pagos';

  return (
    <>
      {isPublicPaymentPage ? (
        <Routes>
          <Route path="/pagos" element={<PublicPayment />} />
        </Routes>
      ) : (
        <AppLayout>
          <Routes>
            <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} />
            <Route path="/register" element={isAuthenticated ? <Navigate to="/" replace /> : <Register />} />
            <Route path="/forgot-password" element={isAuthenticated ? <Navigate to="/" replace /> : <ForgotPassword />} />
            <Route path="/reset-password" element={isAuthenticated ? <Navigate to="/" replace /> : <ResetPassword />} />
            <Route path="/profile" element={<ProtectedRoute><UserProfile /></ProtectedRoute>} />
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/students" element={<ProtectedRoute requirePermission="manage_students"><StudentList /></ProtectedRoute>} />
            <Route path="/students/new" element={<ProtectedRoute requirePermission="manage_students"><StudentForm /></ProtectedRoute>} />
            <Route path="/students/:id/edit" element={<ProtectedRoute requirePermission="manage_students"><StudentForm /></ProtectedRoute>} />
            <Route path="/enrollments/new" element={<ProtectedRoute requirePermission="manage_students"><EnrollmentForm /></ProtectedRoute>} />
            <Route path="/enrollments/:id/edit" element={<ProtectedRoute requirePermission="manage_students"><EnrollmentForm /></ProtectedRoute>} />
            <Route path="/enrollments/:id/contract" element={<ProtectedRoute requirePermission="manage_students"><ContractManagement /></ProtectedRoute>} />
            <Route path="/students/:id" element={<ProtectedRoute requirePermission="manage_students"><StudentDetail /></ProtectedRoute>} />
            <Route path="/students/:id/accounting" element={<ProtectedRoute requirePermission="manage_payments"><StudentAccounting /></ProtectedRoute>} />
            <Route path="/payments" element={<ProtectedRoute requirePermission="manage_payments"><PaymentList /></ProtectedRoute>} />
            <Route path="/payments/pending-transfers" element={<ProtectedRoute requirePermission="manage_payments"><PendingTransfers /></ProtectedRoute>} />
            <Route path="/payments/new" element={<ProtectedRoute requirePermission="manage_payments"><PaymentForm /></ProtectedRoute>} />
            <Route path="/academics" element={<ProtectedRoute requirePermission="manage_academics"><AcademicProgress /></ProtectedRoute>} />
            <Route path="/courses/enroll" element={<ProtectedRoute requirePermission="manage_academics"><CourseEnrollment /></ProtectedRoute>} />
            <Route path="/cuatrimestre-enrollments" element={<ProtectedRoute requirePermission="manage_academics"><CuatrimestreEnrollment /></ProtectedRoute>} />
            <Route path="/grades/upload" element={<ProtectedRoute requirePermission="manage_academics"><GradeUpload /></ProtectedRoute>} />
            <Route path="/careers/:id/pensum" element={<ProtectedRoute requirePermission="manage_academics"><CareerPensum /></ProtectedRoute>} />
            <Route path="/graduation-method" element={<ProtectedRoute requirePermission="manage_thesis"><GraduationMethodManagement /></ProtectedRoute>} />
            <Route path="/scholarships" element={<ProtectedRoute requirePermission="manage_scholarships"><ScholarshipManagement /></ProtectedRoute>} />
            <Route path="/exports" element={<ProtectedRoute requirePermission="manage_students"><ExportStudents /></ProtectedRoute>} />
            <Route path="/reports" element={<ProtectedRoute requirePermission="view_reports"><ReportsIndex /></ProtectedRoute>} />
            <Route path="/reports/payments-detailed" element={<ProtectedRoute requirePermission="view_reports"><PaymentsDetailedReport /></ProtectedRoute>} />
            <Route path="/reports/executive" element={<ProtectedRoute requirePermission="view_reports"><ExecutiveReport /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      )}
      <div className="toast-container">
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
