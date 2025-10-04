import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Entry, EntryCreate, EntryUpdate, EntryKind, EntryStatus } from '../../types/api';
import { apiClient } from '../../api/client';
import './EntryModal.css';

interface EntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  entry?: Entry | null;
}

interface EntryFormData {
  title: string;
  kind: EntryKind;
  link: string;
  status: EntryStatus;
}

const EntryModal: React.FC<EntryModalProps> = ({ isOpen, onClose, onSuccess, entry }) => {
  const isEdit = !!entry;
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<EntryFormData>({
    defaultValues: {
      title: '',
      kind: 'book',
      link: '',
      status: 'planned',
    },
  });

  useEffect(() => {
    if (isOpen) {
      if (entry) {
        reset({
          title: entry.title,
          kind: entry.kind,
          link: entry.link || '',
          status: entry.status,
        });
      } else {
        reset({
          title: '',
          kind: 'book',
          link: '',
          status: 'planned',
        });
      }
      setError(null);
    }
  }, [isOpen, entry, reset]);

  const onSubmit = async (data: EntryFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      if (isEdit && entry) {
        const updateData: EntryUpdate = {
          title: data.title,
          kind: data.kind,
          link: data.link || null,
          status: data.status,
        };
        await apiClient.updateEntry(entry.id, updateData);
      } else {
        const createData: EntryCreate = {
          title: data.title,
          kind: data.kind,
          link: data.link || null,
          status: data.status,
        };
        await apiClient.createEntry(createData);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      if (apiClient.isValidationError(err)) {
        setError(apiClient.getValidationErrors(err).join(', '));
      } else {
        setError(err.response?.data?.detail || 'Operation failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{isEdit ? 'Редактировать запись' : 'Добавить запись'}</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="modal-form">
          <div className="form-group">
            <label htmlFor="title">Название *</label>
            <input
              type="text"
              id="title"
              {...register('title', {
                required: 'Название обязательно',
                minLength: {
                  value: 1,
                  message: 'Название не может быть пустым',
                },
              })}
              className={errors.title ? 'error' : ''}
              placeholder="Введите название книги или статьи"
            />
            {errors.title && <span className="error-message">{errors.title.message}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="kind">Тип *</label>
            <select
              id="kind"
              {...register('kind', { required: 'Тип обязателен' })}
              className={errors.kind ? 'error' : ''}
            >
              <option value="book">Книга</option>
              <option value="article">Статья</option>
            </select>
            {errors.kind && <span className="error-message">{errors.kind.message}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="link">Ссылка</label>
            <input
              type="url"
              id="link"
              {...register('link', {
                pattern: {
                  value: /^https?:\/\/.+/,
                  message: 'Введите корректную ссылку (начинающуюся с http:// или https://)',
                },
              })}
              className={errors.link ? 'error' : ''}
              placeholder="https://example.com"
            />
            {errors.link && <span className="error-message">{errors.link.message}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="status">Статус *</label>
            <select
              id="status"
              {...register('status', { required: 'Статус обязателен' })}
              className={errors.status ? 'error' : ''}
            >
              <option value="planned">Запланировано</option>
              <option value="in_progress">В процессе</option>
              <option value="finished">Завершено</option>
            </select>
            {errors.status && <span className="error-message">{errors.status.message}</span>}
          </div>

          {error && <div className="error-message global-error">{error}</div>}

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Отмена
            </button>
            <button type="submit" disabled={isLoading} className="submit-button">
              {isLoading ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Добавить'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EntryModal;
