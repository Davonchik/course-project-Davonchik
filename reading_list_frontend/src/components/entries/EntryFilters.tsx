import React, { useState, useEffect } from 'react';
import { EntryStatus, ListEntriesParams, UserListItem } from '../../types/api';
import { apiClient } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import './EntryFilters.css';

interface EntryFiltersProps {
  filters: ListEntriesParams;
  onFilterChange: (filters: Partial<ListEntriesParams>) => void;
  isAdmin: boolean;
}

const EntryFilters: React.FC<EntryFiltersProps> = ({ filters, onFilterChange, isAdmin }) => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);

  useEffect(() => {
    if (isAdmin) {
      loadUsers();
    }
  }, [isAdmin]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await apiClient.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
      // Если API не поддерживает получение пользователей, показываем только текущего пользователя
      if (currentUser) {
        setUsers([{ id: currentUser.id, email: currentUser.email }]);
      } else {
        setUsers([]);
      }
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleStatusChange = (status: EntryStatus | null) => {
    onFilterChange({ entry_status: status });
  };

  const handleLimitChange = (limit: number) => {
    onFilterChange({ limit });
  };

  const handleOwnerChange = (ownerId: number | null) => {
    onFilterChange({ owner_id: ownerId });
  };

  return (
    <div className="entry-filters">
      <div className="filter-group">
        <label htmlFor="status-filter">Статус:</label>
        <select
          id="status-filter"
          value={filters.entry_status || ''}
          onChange={(e) => handleStatusChange(e.target.value as EntryStatus || null)}
        >
          <option value="">Все статусы</option>
          <option value="planned">Запланировано</option>
          <option value="in_progress">В процессе</option>
          <option value="finished">Завершено</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="limit-filter">Записей на странице:</label>
        <select
          id="limit-filter"
          value={filters.limit || 10}
          onChange={(e) => handleLimitChange(Number(e.target.value))}
        >
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
        </select>
      </div>

      {isAdmin && (
        <div className="filter-group">
          <label htmlFor="owner-filter">Владелец:</label>
          <select
            id="owner-filter"
            value={filters.owner_id || ''}
            onChange={(e) => handleOwnerChange(e.target.value ? Number(e.target.value) : null)}
            disabled={isLoadingUsers}
          >
            <option value="">Все пользователи</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.email}
              </option>
            ))}
          </select>
          {isLoadingUsers && <span className="loading-text">Загрузка...</span>}
        </div>
      )}

      <button
        className="clear-filters-button"
        onClick={() => onFilterChange({
          entry_status: null,
          owner_id: null,
          offset: 0
        })}
      >
        Очистить фильтры
      </button>
    </div>
  );
};

export default EntryFilters;
