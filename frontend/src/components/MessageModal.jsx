import { useEffect, useRef, useState } from 'react';
import { MessageSquare, Send, X } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

export default function MessageModal({ vehicle, open, onClose, onSent }) {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (open) {
      setMessage('');
      setError('');
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [open, vehicle?.vehicle_id]);

  if (!open || !vehicle) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = message.trim();
    if (!text) return;

    setSending(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/fleet/${vehicle.vehicle_id}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error('Failed to send message');
      const data = await res.json();
      onSent?.(data);
      onClose();
    } catch {
      setError('Could not send message. Try again.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div
        className="w-full max-w-md glass-panel p-4 space-y-3"
        role="dialog"
        aria-labelledby="message-modal-title"
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 id="message-modal-title" className="text-sm font-semibold text-white flex items-center gap-2">
              <MessageSquare size={16} className="text-brand-blue" />
              Message passengers
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {vehicle.vehicle_id} · {vehicle.passenger_count} passenger(s) on board
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-white p-1"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="e.g. Your driver is 2 minutes away. Please be ready at pickup."
            maxLength={500}
            rows={4}
            className="w-full resize-none rounded-lg bg-dark-900 border border-dark-600 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-600 focus:outline-none focus:border-brand-blue"
          />
          <div className="flex items-center justify-between text-[10px] text-gray-500">
            <span>{message.length}/500</span>
            {error && <span className="text-red-400">{error}</span>}
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs rounded-lg border border-dark-600 text-gray-400 hover:text-white hover:border-dark-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={sending || !message.trim()}
              className="px-3 py-1.5 text-xs rounded-lg bg-brand-blue text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              <Send size={12} />
              {sending ? 'Sending...' : 'Send to passengers'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
