import React from 'react';

export default function Modal({ open, title, onClose, children, maxWidth = 'max-w-4xl' }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className={`relative bg-white rounded-xl shadow-2xl w-full ${maxWidth} mx-4 overflow-hidden`}>
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-3 text-white flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-white/90 hover:text-white">✕</button>
        </div>
        <div className="p-0">
          {children}
        </div>
      </div>
    </div>
  );
}

