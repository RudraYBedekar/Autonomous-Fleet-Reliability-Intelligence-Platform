import { useState, useRef, useEffect } from 'react';
import {
  Bot, X, Send, Sparkles, MapPin, Users, Battery, HeartPulse, Gauge, Wrench, ShieldAlert, Navigation, Phone, MessageSquare, AlertTriangle, RefreshCw
} from 'lucide-react';
import { apiUrl } from '../utils/format';

const SUGGESTIONS = [
  { label: '🚗 Search car-003', query: 'Search car-003' },
  { label: '👥 Passenger Summary', query: 'Show passenger summary across fleet' },
  { label: '⚡ Low Battery EVs', query: 'Which cars have low battery?' },
  { label: '🚨 Active Alerts', query: 'Show active fleet alerts' },
  { label: '📊 Fleet Brief', query: 'Give me fleet executive brief' },
];

export default function CopilotPanel({ isOpen, onClose, onSelect, selectedId }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Hello! I am **FleetGuard AI Copilot**. Search any vehicle (e.g. `car-001` through `car-015`) to get its description, passenger info, live telemetry metrics, route details, and diagnostics!',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [diagnosingId, setDiagnosingId] = useState(null);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (queryText) => {
    const text = (queryText || input).trim();
    if (!text || loading) return;

    const userMsg = { id: Date.now().toString(), sender: 'user', text };
    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiUrl('/api/ai/ask'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text }),
      });
      const data = await res.json();

      const botMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.response || 'No response received from AI.',
        matchedVehicle: data.matched_vehicle,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: '⚠️ Failed to connect to AI backend service. Please ensure API server is running.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDiagnose = async (vehicleId) => {
    setDiagnosingId(vehicleId);
    try {
      const res = await fetch(apiUrl(`/api/ai/diagnose/${vehicleId}`));
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: 'bot',
          text: data.ai_report || `Diagnostic for ${vehicleId} completed.`,
          matchedVehicle: data.vehicle,
        },
      ]);
    } catch (err) {
      console.error('Diagnosis failed', err);
    } finally {
      setDiagnosingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[450px] bg-slate-900/95 backdrop-blur-xl border-l border-slate-700/60 shadow-2xl flex flex-col transition-all duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800 bg-slate-950/60">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-brand-blue to-purple-600 shadow-lg shadow-brand-blue/20">
            <Bot className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              FleetGuard AI Assistant
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </h2>
            <p className="text-xs text-slate-400">Search cars, telemetry, passengers & RCA</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Quick Suggestion Chips */}
      <div className="px-4 py-2 bg-slate-950/40 border-b border-slate-800/50 flex gap-2 overflow-x-auto scrollbar-none">
        {SUGGESTIONS.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(chip.query)}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 rounded-full whitespace-nowrap transition-all duration-150 flex items-center gap-1 shrink-0"
          >
            <Sparkles className="w-3 h-3 text-purple-400" />
            {chip.label}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-brand-blue text-white rounded-br-none shadow-md'
                  : 'bg-slate-800/90 text-slate-200 border border-slate-700/50 rounded-bl-none shadow-md'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.text}</div>

              {/* Matched Vehicle Detailed Card */}
              {msg.matchedVehicle && (
                <div className="mt-3 p-3.5 bg-slate-950/70 border border-slate-700/80 rounded-xl space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-brand-blue/30 text-brand-blue border border-brand-blue/40 font-mono font-bold text-xs">
                        {msg.matchedVehicle.vehicle_id}
                      </span>
                      <span className="text-xs font-semibold text-slate-300">
                        {msg.matchedVehicle.driver_name}
                      </span>
                    </div>
                    {msg.matchedVehicle.driver_phone && (
                      <a
                        href={`tel:${msg.matchedVehicle.driver_phone}`}
                        className="text-xs text-brand-blue hover:underline flex items-center gap-1"
                      >
                        <Phone className="w-3 h-3" />
                        {msg.matchedVehicle.driver_phone}
                      </a>
                    )}
                  </div>

                  {/* Passengers & Route */}
                  <div className="space-y-1 text-xs text-slate-300">
                    <div className="flex items-center gap-1.5 font-medium text-emerald-400">
                      <Users className="w-3.5 h-3.5" />
                      <span>{msg.matchedVehicle.passenger_count} Passengers onboard</span>
                    </div>
                    <div className="flex items-start gap-1.5 text-slate-400 pl-0.5">
                      <MapPin className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
                      <div className="line-clamp-2">
                        <span className="text-slate-200 font-medium">
                          {msg.matchedVehicle.pickup_address?.split(',')[0]}
                        </span>{' '}
                        ➔{' '}
                        <span className="text-slate-200 font-medium">
                          {msg.matchedVehicle.destination_address?.split(',')[0]}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Telemetry Metrics Grid */}
                  <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                      <Gauge className="w-4 h-4 text-cyan-400 shrink-0" />
                      <div>
                        <div className="text-[10px] text-slate-400">Speed</div>
                        <div className="font-semibold text-slate-200">
                          {msg.matchedVehicle.speed_kmh ?? 0} km/h
                        </div>
                      </div>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                      <Battery className="w-4 h-4 text-yellow-400 shrink-0" />
                      <div>
                        <div className="text-[10px] text-slate-400">Battery</div>
                        <div className="font-semibold text-slate-200">
                          {msg.matchedVehicle.battery_pct ?? 90}%
                        </div>
                      </div>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                      <HeartPulse className="w-4 h-4 text-emerald-400 shrink-0" />
                      <div>
                        <div className="text-[10px] text-slate-400">Health Score</div>
                        <div className="font-semibold text-slate-200">
                          {msg.matchedVehicle.health_score ?? 95}%
                        </div>
                      </div>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800/80 flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-purple-400 shrink-0" />
                      <div>
                        <div className="text-[10px] text-slate-400">Maint RUL</div>
                        <div className="font-semibold text-slate-200">
                          {msg.matchedVehicle.maintenance_rul_pct ?? 100}%
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Active Alert Banner */}
                  {msg.matchedVehicle.active_alert && (
                    <div className="p-2 rounded-lg bg-red-500/15 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                      <span>{msg.matchedVehicle.active_alert}</span>
                    </div>
                  )}

                  {/* Interactive Action Buttons */}
                  <div className="flex gap-2 pt-1">
                    <button
                      onClick={() => onSelect?.(msg.matchedVehicle.vehicle_id)}
                      className="flex-1 py-1.5 px-2 bg-brand-blue/20 hover:bg-brand-blue/30 border border-brand-blue/40 rounded-lg text-brand-blue font-semibold text-xs transition-colors flex items-center justify-center gap-1.5"
                    >
                      <Navigation className="w-3.5 h-3.5" />
                      Focus on Map
                    </button>
                    <button
                      onClick={() => handleDiagnose(msg.matchedVehicle.vehicle_id)}
                      disabled={diagnosingId === msg.matchedVehicle.vehicle_id}
                      className="flex-1 py-1.5 px-2 bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/40 rounded-lg text-purple-300 font-semibold text-xs transition-colors flex items-center justify-center gap-1.5"
                    >
                      {diagnosingId === msg.matchedVehicle.vehicle_id ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Sparkles className="w-3.5 h-3.5" />
                      )}
                      Run RCA
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-slate-400 text-xs py-2 px-1">
            <Bot className="w-4 h-4 animate-spin text-brand-blue" />
            <span>FleetGuard AI is analyzing telemetry & passenger data...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Footer Input Bar */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Search vehicle ID (e.g. car-003) or ask AI..."
            className="flex-1 bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-brand-blue hover:bg-blue-600 disabled:opacity-50 text-white font-medium shadow-md shadow-brand-blue/20 transition-colors shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
