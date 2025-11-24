import { useState, useEffect, useCallback, useMemo } from 'react';
import { Play, Pause, X, RotateCcw, Clock, Zap } from 'lucide-react';

/**
 * TEMPLATE: modal component for notifications and actions
 * @param {object} props - Component props.
 * @param {string} props.title - Title of the modal.
 * @param {string} props.content - Body text of the modal.
 * @param {boolean} props.isOpen - Controls visibility.
 * @param {function} props.onClose - Function to close the modal.
 * @param {string} props.primaryActionLabel - Label for the main action button.
 * @param {function} props.onPrimaryAction - Handler for the main action button.
 */

export default function Modal({ title, isOpen, children }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3 className="modal-title">{title}</h3>
        <div className="modal-body">
            {children}
        </div>
      </div>
    </div>
  );
}