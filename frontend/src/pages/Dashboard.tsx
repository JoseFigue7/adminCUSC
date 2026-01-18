import React from 'react';
import { useAuth } from '../context/AuthContext';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div style={{ padding: '20px' }}>
      <h1>Dashboard - AdminCUSC</h1>
      <div>
        <h2>Bienvenido, {user?.first_name || user?.username}</h2>
        <p>Rol: {user?.role?.name || 'Sin rol asignado'}</p>
        <p>Email: {user?.email}</p>
      </div>
      <div style={{ marginTop: '40px' }}>
        <h3>Módulos Disponibles</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '20px' }}>
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h4>Estudiantes</h4>
            <p>Gestión de estudiantes</p>
          </div>
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h4>Pagos</h4>
            <p>Gestión de pagos</p>
          </div>
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h4>Académico</h4>
            <p>Gestión académica</p>
          </div>
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h4>Reportes</h4>
            <p>Ver reportes</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;








