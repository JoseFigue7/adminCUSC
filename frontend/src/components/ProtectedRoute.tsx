import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiLoader } from '../utils/icons';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requirePermission?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requirePermission }) => {
  const { isAuthenticated, loading, hasPermission } = useAuth();

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requirePermission && !hasPermission(requirePermission)) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <FiLoader className="empty-icon" />
          <h3>Acceso Denegado</h3>
          <p>No tienes permisos para acceder a esta sección.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;




