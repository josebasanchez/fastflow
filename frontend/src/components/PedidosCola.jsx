import { useMemo, useState } from "react";

function getRemainingMinutes(fechaLimite) {
  const deadline = new Date(fechaLimite).getTime();
  const now = Date.now();
  return Math.round((deadline - now) / 60000);
}

function getUrgencyLevel(minutesLeft) {
  if (minutesLeft < 0) return "late";
  if (minutesLeft <= 60) return "lt1h";
  if (minutesLeft <= 120) return "lt2h";
  if (minutesLeft <= 180) return "lt3h";
  return "normal";
}

function getCardClass(estado, urgencyLevel) {
  if (estado === "listo") return "border-emerald-300 bg-emerald-50";
  if (urgencyLevel === "late") return "border-slate-900 bg-slate-900 text-white";
  if (urgencyLevel === "lt1h") return "border-rose-300 bg-rose-50";
  if (urgencyLevel === "lt2h") return "border-orange-300 bg-orange-50";
  if (urgencyLevel === "lt3h") return "border-amber-300 bg-amber-50";
  return "border-slate-200 bg-white";
}

function getStateRank(estado) {
  if (estado === "pendiente") return 0;
  if (estado === "preparando") return 1;
  if (estado === "listo") return 2;
  return 3;
}

function formatRemaining(minutesLeft) {
  if (minutesLeft < 0) return `Retraso ${Math.abs(minutesLeft)} min`;
  if (minutesLeft < 60) return `${minutesLeft} min restantes`;
  const hours = Math.floor(minutesLeft / 60);
  const mins = minutesLeft % 60;
  return `${hours}h ${mins}m restantes`;
}

function formatReservaSlot(pedido) {
  if (!pedido?.reserva_fecha || !pedido?.reserva_hora) return "-";
  return `${pedido.reserva_fecha} ${String(pedido.reserva_hora).slice(0, 5)}`;
}

export default function PedidosCola({ pedidos = [], onStartPreparing, onMarkReady, currentUserId, currentUsername }) {
  const [busyId, setBusyId] = useState(null);

  const prioritized = useMemo(() => {
    return [...pedidos]
      .map((pedido) => {
        const minutesLeft = getRemainingMinutes(pedido.fecha_limite);
        const urgencyLevel = getUrgencyLevel(minutesLeft);
        return { ...pedido, minutesLeft, urgencyLevel };
      })
      .sort((a, b) => {
        const byState = getStateRank(a.estado) - getStateRank(b.estado);
        if (byState !== 0) return byState;
        if (a.minutesLeft !== b.minutesLeft) return a.minutesLeft - b.minutesLeft;
        return a.id - b.id;
      });
  }, [pedidos]);

  async function handleStartPreparing(pedidoId) {
    if (!onStartPreparing) return;
    setBusyId(pedidoId);
    try {
      await onStartPreparing(pedidoId);
    } finally {
      setBusyId(null);
    }
  }

  async function handleMarkReady(pedidoId) {
    if (!onMarkReady) return;
    setBusyId(pedidoId);
    try {
      await onMarkReady(pedidoId);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-lg font-semibold">Cola de preparacion por prioridad</h2>
      <p className="mt-1 text-sm text-slate-600">Ordenado por urgencia de servicio. Los pedidos mas urgentes salen arriba.</p>

      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-slate-900 px-3 py-1 text-white">Fuera de tiempo</span>
        <span className="rounded-full bg-rose-100 px-3 py-1 text-rose-700">Menos de 1h</span>
        <span className="rounded-full bg-orange-100 px-3 py-1 text-orange-700">Menos de 2h</span>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-700">Menos de 3h</span>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700">Listo para servir</span>
      </div>

      <ul className="mt-3 space-y-2">
        {prioritized.map((p) => {
          const isBusy = busyId === p.id;
          const cardClass = getCardClass(p.estado, p.urgencyLevel);
          const isLate = p.urgencyLevel === "late" && p.estado !== "listo";
          const ownerById = currentUserId != null && p.preparado_por != null && Number(p.preparado_por) === Number(currentUserId);
          const ownerByUsername = Boolean(currentUsername && p.preparado_por_username && p.preparado_por_username === currentUsername);
          const canMarkReady = p.estado === "preparando" && (ownerById || ownerByUsername || !p.preparado_por);
          return (
            <li key={p.id} className={`rounded-lg border p-3 ${cardClass}`}>
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className={`font-medium ${isLate ? "text-white" : "text-slate-900"}`}>
                    #{p.id} · {p.plato_nombre} x{p.cantidad}
                  </p>
                  <p className={`text-sm ${isLate ? "text-slate-100" : "text-slate-700"}`}>Mesa: {p.mesa_nombre || "-"} · Servicio: {formatReservaSlot(p)}</p>
                  <p className={`text-sm ${isLate ? "text-slate-100" : "text-slate-700"}`}>Limite: {new Date(p.fecha_limite).toLocaleString()} · {formatRemaining(p.minutesLeft)}</p>
                  {p.preparado_por_nombre ? (
                    <p className={`text-sm ${isLate ? "text-slate-100" : "text-slate-700"}`}>Preparando: {p.preparado_por_nombre}</p>
                  ) : null}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`rounded-full px-2 py-1 text-xs font-medium uppercase tracking-wide ${isLate ? "bg-slate-700 text-white" : "bg-white/70 text-slate-700"}`}>
                    {p.estado}
                  </span>
                  {p.estado === "pendiente" ? (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleStartPreparing(p.id)}
                      className="rounded-lg bg-slate-700 px-3 py-1.5 text-sm text-white disabled:opacity-60"
                    >
                      {isBusy ? "Actualizando..." : "Poner en preparacion"}
                    </button>
                  ) : null}
                  {canMarkReady ? (
                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleMarkReady(p.id)}
                      className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm text-white disabled:opacity-60"
                    >
                      {isBusy ? "Actualizando..." : "Marcar listo para servir"}
                    </button>
                  ) : null}
                  {p.estado === "preparando" && !canMarkReady ? (
                    <p className={`text-xs ${isLate ? "text-slate-100" : "text-slate-600"}`}>Lo esta preparando {p.preparado_por_nombre || p.preparado_por_username || "otro empleado"}.</p>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
