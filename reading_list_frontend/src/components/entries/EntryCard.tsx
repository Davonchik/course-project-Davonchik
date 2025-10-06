import React, { useState } from 'react';
import { Entry, EntryStatus } from '../../types/api';
import { apiClient } from '../../api/client';
import './EntryCard.css';

interface EntryCardProps {
  entry: Entry;
  onUpdate: () => void;
  onDelete: () => void;
  onEdit: (entry: Entry) => void;
  canEdit: boolean;
}

const EntryCard: React.FC<EntryCardProps> = ({ entry, onUpdate, onDelete, onEdit, canEdit }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const getStatusColor = (status: EntryStatus) => {
    switch (status) {
      case 'planned':
        return '#f39c12';
      case 'in_progress':
        return '#3498db';
      case 'finished':
        return '#27ae60';
      default:
        return '#95a5a6';
    }
  };

  const getStatusText = (status: EntryStatus) => {
    switch (status) {
      case 'planned':
        return 'Запланировано';
      case 'in_progress':
        return 'В процессе';
      case 'finished':
        return 'Завершено';
      default:
        return status;
    }
  };

  const getKindText = (kind: string) => {
    switch (kind) {
      case 'book':
        return 'Книга';
      case 'article':
        return 'Статья';
      default:
        return kind;
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить эту запись?')) {
      return;
    }

    setIsDeleting(true);
    try {
      await apiClient.deleteEntry(entry.id);
      onDelete();
    } catch (error) {
      console.error('Failed to delete entry:', error);
      alert('Не удалось удалить запись');
    } finally {
      setIsDeleting(false);
    }
  };


  return (
    <div className="entry-card">
      <div className="entry-header">
        <div className="entry-title">{entry.title}</div>
        <div className="entry-actions">
          {canEdit && (
            <>
              <button
                className="edit-button"
                onClick={() => onEdit(entry)}
                title="Редактировать"
              >
                ✏️
              </button>
              <button
                className="delete-button"
                onClick={handleDelete}
                disabled={isDeleting}
                title="Удалить"
              >
                {isDeleting ? '⏳' : '🗑️'}
              </button>
            </>
          )}
        </div>
      </div>

      <div className="entry-meta">
        <div className="entry-kind">{getKindText(entry.kind)}</div>
        <div
          className="entry-status"
          style={{ backgroundColor: getStatusColor(entry.status) }}
        >
          {getStatusText(entry.status)}
        </div>
      </div>

      {entry.link && (
        <div className="entry-link">
          <a
            href={entry.link}
            target="_blank"
            rel="noopener noreferrer"
            className="link-button"
          >
            🔗 Открыть ссылку
          </a>
        </div>
      )}

    </div>
  );
};

export default EntryCard;
