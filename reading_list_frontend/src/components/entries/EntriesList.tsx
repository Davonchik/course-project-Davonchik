import React, { useState, useEffect } from 'react';
import { Entry, ListEntriesParams } from '../../types/api';
import { apiClient } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import EntryCard from './EntryCard';
import EntryFilters from './EntryFilters';
import Pagination from './Pagination';
import EntryModal from './EntryModal';
import './EntriesList.css';

const EntriesList: React.FC = () => {
  const { user } = useAuth();
  const [entries, setEntries] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<ListEntriesParams>({
    limit: 10,
    offset: 0,
    entry_status: null,
    owner_id: null,
  });

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<Entry | null>(null);

  const fetchEntries = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.getEntries(filters);
      setEntries(response.data.items);
      setTotal(response.data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch entries');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleFilterChange = (newFilters: Partial<ListEntriesParams>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
      offset: 0, // Reset to first page when filters change
    }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({
      ...prev,
      offset: (page - 1) * (prev.limit || 10),
    }));
  };

  const handleEntryUpdate = () => {
    fetchEntries();
  };

  const handleEntryDelete = () => {
    fetchEntries();
  };

  const handleCreateEntry = () => {
    setEditingEntry(null);
    setIsModalOpen(true);
  };

  const handleEditEntry = (entry: Entry) => {
    setEditingEntry(entry);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setEditingEntry(null);
  };

  const handleModalSuccess = () => {
    fetchEntries();
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Загрузка записей...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-message">{error}</div>
        <button onClick={fetchEntries} className="retry-button">
          Попробовать снова
        </button>
      </div>
    );
  }

  const totalPages = Math.ceil(total / (filters.limit || 10));
  const currentPage = Math.floor((filters.offset || 0) / (filters.limit || 10)) + 1;

  return (
    <div className="entries-list">
      <div className="entries-header">
        <h1>Список для чтения</h1>
        <button
          className="add-entry-button"
          onClick={handleCreateEntry}
        >
          + Добавить запись
        </button>
      </div>

      <EntryFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        isAdmin={user?.role === 'admin'}
      />

      {entries.length === 0 ? (
        <div className="empty-state">
          <p>Записи не найдены</p>
          <button
            className="add-entry-button"
            onClick={handleCreateEntry}
          >
            Добавить первую запись
          </button>
        </div>
      ) : (
        <>
          <div className="entries-grid">
            {entries.map((entry) => (
              <EntryCard
                key={entry.id}
                entry={entry}
                onUpdate={handleEntryUpdate}
                onDelete={handleEntryDelete}
                onEdit={handleEditEntry}
                canEdit={user?.role === 'admin' || entry.owner_id === user?.id}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </>
      )}

      <EntryModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        onSuccess={handleModalSuccess}
        entry={editingEntry}
      />
    </div>
  );
};

export default EntriesList;
