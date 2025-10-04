import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './Header.css';

const Header: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="header">
      <div className="header-content">
        <Link to="/" className="logo">
          📚 Reading List
        </Link>

        {isAuthenticated ? (
          <div className="header-actions">
            <span className="user-info">
              {user?.email} ({user?.role === 'admin' ? 'Администратор' : 'Пользователь'})
            </span>
            <button onClick={handleLogout} className="logout-button">
              Выйти
            </button>
          </div>
        ) : (
          <div className="header-actions">
            <Link to="/login" className="auth-link">
              Войти
            </Link>
            <Link to="/register" className="auth-link register">
              Регистрация
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
