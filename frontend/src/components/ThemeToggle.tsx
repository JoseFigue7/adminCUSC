import React from 'react';
import { useTheme } from '../context/ThemeContext';
import { FiSun, FiMoon } from '../utils/icons';
import './ThemeToggle.css';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button className="theme-toggle" onClick={toggleTheme} title={theme === 'light' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro'}>
      {theme === 'light' ? <FiMoon /> : <FiSun />}
    </button>
  );
};

export default ThemeToggle;







