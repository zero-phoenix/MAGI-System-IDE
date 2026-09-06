import React from 'react';
import { useMagiStore } from '../store';

export const CancelReportCard: React.FC = () => {
  const cancelReport = useMagiStore((state) => state.cancelReport);
  const setCancelReport = useMagiStore((state) => state.setCancelReport);

  if (!cancelReport) return null;

  const hasWarnings = (cancelReport.processes_failed || 0) > 0 || (cancelReport.loops_failed || 0) > 0;

  return (
    <div
      style={{
        margin: '10px 16px',
        padding: '12px 16px',
        borderRadius: '6px',
        border: hasWarnings ? '1px solid #ef4444' : '1px solid #f59e0b',
        backgroundColor: hasWarnings ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
        color: '#f3f4f6',
        fontSize: '13px',
        fontFamily: 'monospace',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold' }}>
          <span style={{ color: hasWarnings ? '#ef4444' : '#f59e0b', fontSize: '16px' }}>🛑</span>
          <span>PARADA DE EMERGENCIA — INFORME</span>
        </div>
        <button
          onClick={() => setCancelReport(null)}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            fontSize: '14px',
            padding: '2px 6px',
          }}
          title="Cerrar aviso"
        >
          ✕
        </button>
      </div>

      <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>
        {cancelReport.detail || (
          cancelReport.nothing_running
            ? 'No había tareas ni procesos en marcha. El sistema ya estaba en reposo.'
            : `Cancelación completada: ${cancelReport.loops_cancelled || 0} tarea(s) canceladas · ${cancelReport.processes_killed || 0} proceso(s) terminados`
        )}
      </div>

      {hasWarnings && (
        <div style={{ marginTop: '8px', color: '#fca5a5', fontWeight: 600 }}>
          ⚠️ ATENCIÓN: Procesos o bucles no respondieron a la señal. Compruébelos manualmente.
        </div>
      )}
    </div>
  );
};
