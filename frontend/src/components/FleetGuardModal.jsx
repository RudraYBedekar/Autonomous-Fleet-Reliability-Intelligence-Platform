import React, { useState, useEffect } from 'react';
import { apiUrl } from '../api';

export default function FleetGuardModal({ vehicleId, alertType, onClose, onComplete }) {
  const [loading, setLoading] = useState(true);
  const [agentData, setAgentData] = useState(null);
  const [error, setError] = useState(null);
  const [activeStageIndex, setActiveStageIndex] = useState(0);

  useEffect(() => {
    let isMounted = true;
    const runAgentLoop = async () => {
      try {
        setLoading(true);
        const res = await fetch(apiUrl('/api/fleetguard/investigate'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vehicle_id: vehicleId || 'car-001',
            alert_type: alertType || null,
          }),
        });

        if (!res.ok) {
          throw new Error(`Agent loop request failed with status ${res.status}`);
        }

        const data = await res.json();
        if (isMounted) {
          setAgentData(data);
          setLoading(false);
          // Animate stages sequentially
          for (let i = 0; i < (data.stages?.length || 5); i++) {
            await new Promise(r => setTimeout(r, 600));
            if (isMounted) setActiveStageIndex(i);
          }
          if (onComplete) onComplete(data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      }
    };

    runAgentLoop();

    return () => { isMounted = false; };
  }, [vehicleId, alertType]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-md p-4 animate-fade-in">
      <div className="bg-slate-900 border border-cyan-500/30 rounded-2xl max-w-3xl w-full p-6 shadow-2xl shadow-cyan-500/20 text-slate-100 flex flex-col max-h-[90vh] overflow-y-auto">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/30">
              🤖
            </div>
            <div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                FleetGuard Autonomous AI Agent Loop
              </h2>
              <p className="text-xs text-slate-400">
                DataHub Context Injection • ML Lineage Blast Radius • Auto-Mitigation • GMS Write-Back
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 w-8 h-8 rounded-lg flex items-center justify-center transition"
          >
            ✕
          </button>
        </div>

        {/* Loading Spinner */}
        {loading && !agentData && (
          <div className="flex flex-col items-center justify-center py-16 space-y-4">
            <div className="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-400 rounded-full animate-spin"></div>
            <p className="text-cyan-400 font-medium text-sm animate-pulse">
              Initializing Autonomous Agent Loop & Querying DataHub...
            </p>
          </div>
        )}

        {/* Error View */}
        {error && (
          <div className="p-4 bg-red-950/50 border border-red-500/40 rounded-xl text-red-300 text-sm mb-4">
            ⚠️ Agent Execution Error: {error}
          </div>
        )}

        {/* Agent 5-Stage Execution Flow */}
        {agentData && (
          <div className="space-y-6">
            
            {/* Top Summary Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block">Target Vehicle</span>
                <span className="font-semibold text-cyan-300">{agentData.vehicle_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Metadata Origin</span>
                <a
                  href={`http://${window.location.hostname}:9002/dataset/urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`font-semibold hover:underline flex items-center gap-1 ${agentData.metadata_source === 'live' ? 'text-cyan-300' : 'text-amber-400'}`}
                >
                  {agentData.metadata_source === 'live' ? '⚡ LIVE DataHub ↗' : '⚡ Offline Demo Fallback ↗'}
                </a>
              </div>
              <div>
                <span className="text-slate-500 block">Execution Speed</span>
                <span className="font-semibold text-emerald-400">{agentData.execution_time_ms} ms</span>
              </div>
              <div>
                <span className="text-slate-500 block">DataHub Write-Back</span>
                <a
                  href={`http://${window.location.hostname}:9002/dataset/urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`font-semibold hover:underline flex items-center gap-1 ${agentData.writeback?.datahub_written ? 'text-emerald-400' : 'text-amber-400'}`}
                >
                  {agentData.writeback?.datahub_written ? '✓ Synced to GMS ↗' : '⚠ Offline Local Record ↗'}
                </a>
              </div>
            </div>

            {/* Stages Vertical Timeline */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Autonomous 5-Stage Reasoning Trajectory
              </h3>

              {agentData.stages?.map((stage, idx) => {
                const isActive = idx <= activeStageIndex;
                return (
                  <div
                    key={stage.stage}
                    className={`p-4 rounded-xl border transition-all duration-300 ${
                      isActive
                        ? 'bg-slate-800/80 border-cyan-500/40 shadow-lg shadow-cyan-950/20'
                        : 'bg-slate-950/40 border-slate-800/50 opacity-40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${
                            stage.status === 'COMPLETED'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30'
                              : stage.status === 'IN_PROGRESS'
                              ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/30 animate-pulse'
                              : stage.status === 'OFFLINE'
                              ? 'bg-amber-950 text-amber-400 border border-amber-500/30'
                              : 'bg-slate-900 text-slate-500 border border-slate-800'
                          }`}
                        >
                          {stage.stage}
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-slate-200">
                            {stage.name}
                          </h4>
                          <p className="text-xs text-slate-400">{stage.description}</p>
                        </div>
                      </div>
                      <span
                        className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full ${
                          stage.status === 'COMPLETED'
                            ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50'
                            : stage.status === 'IN_PROGRESS'
                            ? 'bg-cyan-900/50 text-cyan-300 border border-cyan-700/50 animate-pulse'
                            : stage.status === 'OFFLINE'
                            ? 'bg-amber-900/50 text-amber-300 border border-amber-700/50'
                            : 'bg-slate-900 text-slate-600 border border-slate-800'
                        }`}
                      >
                        {stage.status}
                      </span>
                    </div>

                    {/* Stage 2 DataHub Context Payload Details */}
                    {stage.stage === 2 && stage.datahub_payload && isActive && (
                      <div className="mt-3 p-3 bg-slate-950/80 rounded-lg border border-slate-800 text-xs space-y-1.5 font-mono text-slate-300">
                        <div className="flex justify-between text-cyan-400 font-bold border-b border-slate-800 pb-1">
                          <span>Asset URN: {stage.datahub_payload.asset}</span>
                          <span className={stage.datahub_payload.metadata_source === 'live' ? 'text-cyan-300' : 'text-amber-400'}>
                            Source: {stage.datahub_payload.metadata_source || 'live'}
                          </span>
                        </div>
                        <div><span className="text-slate-500">Owners:</span> {stage.datahub_payload.owners?.join(', ') || 'fleet_ops'}</div>
                        <div><span className="text-slate-500">Upstream Sensors:</span> {stage.datahub_payload.upstream?.map(u => u.urn).join(', ')}</div>
                        <div><span className="text-slate-500">Downstream Impact Radius:</span> {stage.datahub_payload.downstream?.map(d => d.urn).join(', ')}</div>
                      </div>
                    )}

                    {/* Stage 3 AI Reasoning Text */}
                    {stage.stage === 3 && stage.reasoning_summary && isActive && (
                      <div className="mt-3 p-3 bg-slate-950/90 rounded-lg border border-slate-700 text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
                        {stage.reasoning_summary}
                      </div>
                    )}

                    {/* Stage 5 Writeback Tags */}
                    {stage.stage === 5 && stage.writeback_data && isActive && (
                      <div className="mt-3 p-3 bg-slate-950/80 rounded-lg border border-emerald-900/30 text-xs flex flex-wrap gap-2 items-center">
                        <span className="text-emerald-400 font-medium mr-1">DataHub Tags Emitted:</span>
                        {stage.writeback_data.details?.tags?.map(tag => (
                          <span key={tag} className="px-2 py-0.5 bg-emerald-900/50 text-emerald-200 border border-emerald-700/50 rounded-full font-mono text-[10px]">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Footer Actions */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
              <a
                href={`http://${window.location.hostname}:9002/dataset/urn:li:dataset:(urn:li:dataPlatform:kafka,vehicle_health_features,PROD)`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-500/30 font-semibold text-xs flex items-center gap-1.5 transition"
              >
                📊 Open Entity & Lineage in DataHub Core ↗
              </a>
              <button
                onClick={onClose}
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition"
              >
                Close Agent Loop Report
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
