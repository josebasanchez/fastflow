import { useEffect, useMemo, useRef, useState } from "react";
import { ReactComponent as VistaRealSvg } from "../assets/restaurante_vista_real.svg";
import { requestApi } from "../api";

const TABLE_POSITIONS = {
  m1: { x: 14.7, y: 25.0 },
  mesa1: { x: 14.7, y: 25.0 },
  m2: { x: 14.7, y: 69.5 },
  mesa2: { x: 14.7, y: 69.5 },
  m3: { x: 32.4, y: 45.0 },
  mesa3: { x: 32.4, y: 45.0 },
  m4: { x: 53.0, y: 26.0 },
  mesa4: { x: 53.0, y: 26.0 },
  m5: { x: 78.4, y: 26.0 },
  mesa5: { x: 78.4, y: 26.0 },
  m6: { x: 63.2, y: 67.8 },
  mesa6: { x: 63.2, y: 67.8 },
};

function normalizeMesaKey(nombre) {
  return nombre.toLowerCase().replace(/\s+/g, "").replace(/[^a-z0-9]/g, "");
}

function prettyMesaName(nombre) {
  const raw = String(nombre || "").trim();
  const match = raw.match(/^(m|mesa)\s*([0-9]+)$/i);
  if (match) return `Mesa ${Number(match[2])}`;
  return raw;
}

function formatDateInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function buildCalendarDays(monthDate) {
  const firstDay = startOfMonth(monthDate);
  const startOffset = (firstDay.getDay() + 6) % 7;
  const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
  const days = [];

  for (let i = 0; i < startOffset; i += 1) {
    days.push(null);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    days.push(new Date(monthDate.getFullYear(), monthDate.getMonth(), day));
  }

  while (days.length % 7 !== 0) {
    days.push(null);
  }

  return days;
}

function buildSlots() {
  const slots = [];
  const addRange = (startH, startM, endH, endM) => {
    const start = startH * 60 + startM;
    const end = endH * 60 + endM;
    for (let t = start; t <= end; t += 15) {
      const h = Math.floor(t / 60);
      const m = t % 60;
      slots.push(`${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`);
    }
  };
  addRange(14, 0, 16, 0);
  addRange(20, 0, 22, 30);
  return slots;
}

export default function MesasDisponibles({ auth, onRequireLogin, mesas, filtros, setFiltros, selectedMesaId, onSelectMesa, occupiedSlotsByMesa = {}, onContinue, apiBaseUrl }) {
  const [calendarMonth, setCalendarMonth] = useState(() => startOfMonth(new Date()));
  const [diasCompletos, setDiasCompletos] = useState(new Set());
  const [dragX, setDragX] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const franjas = useMemo(() => buildSlots(), []);
  const occupiedByMesa = useMemo(() => occupiedSlotsByMesa || {}, [occupiedSlotsByMesa]);
  const isCliente = Boolean(auth && auth.user?.rol === "cliente");
  const selectedDate = filtros.fecha || "";
  const todayInput = formatDateInput(new Date());
  const capacidad = Math.min(8, Math.max(1, Number(filtros.capacidad || 1)));
  const planoRef = useRef(null);
  const monthLabel = calendarMonth.toLocaleDateString("es-ES", { month: "long", year: "numeric" });
  const calendarDays = useMemo(() => buildCalendarDays(calendarMonth), [calendarMonth]);
  const allowedMesaKeys = useMemo(() => {
    return capacidad <= 2
      ? new Set(["m1", "mesa1", "m2", "mesa2"])
      : capacidad === 3
        ? new Set(["m3", "mesa3"])
        : capacidad === 4 || capacidad === 5
          ? new Set(["m4", "mesa4", "m5", "mesa5"])
          : new Set(["m6", "mesa6"]);
  }, [capacidad]);

  useEffect(() => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth() + 1;
    requestApi(apiBaseUrl, `cliente/mesas/dias-completos/?capacidad=${capacidad}&year=${year}&month=${month}`)
      .then((data) => setDiasCompletos(new Set(data?.dias_completos || [])))
      .catch(() => setDiasCompletos(new Set()));
  }, [calendarMonth, capacidad, apiBaseUrl]);


  const mesasVisibles = mesas.filter((mesa) => !normalizeMesaKey(mesa.nombre).includes("terraza"));

  const mesasConPosicion = mesasVisibles.map((mesa) => {
    const key = normalizeMesaKey(mesa.nombre);
    const position = TABLE_POSITIONS[key] || null;
    return { ...mesa, position };
  });

  const mesaByKey = useMemo(() => {
    const map = new Map();
    mesasConPosicion.forEach((mesa) => {
      const key = normalizeMesaKey(mesa.nombre);
      map.set(key, mesa);
      if (key.startsWith("m")) map.set(key.replace(/^m/, "mesa"), mesa);
      if (key.startsWith("mesa")) map.set(key.replace(/^mesa/, "m"), mesa);
    });
    return map;
  }, [mesasConPosicion]);

  useEffect(() => {
    const root = planoRef.current;
    if (!root) return;

    const mesaIds = ["mesa1", "mesa2", "mesa3", "mesa4", "mesa5", "mesa6"];
    const highlightMesaIds = new Set();
    mesaIds.forEach((mesaId) => {
      if (allowedMesaKeys.has(mesaId) || allowedMesaKeys.has(mesaId.replace("mesa", "m"))) {
        highlightMesaIds.add(mesaId);
      }
    });

    const highlightFill = "#ead9bf";
    const cleanups = [];

    mesaIds.forEach((mesaId) => {
      const el = root.querySelector(`#${mesaId}-top`);
      if (!el) return;

      // Ojo: en este SVG el color suele estar en el atributo `style="fill:rgb(...)"`,
      // asÃ­ que hay que tocar `el.style.fill` (tiene prioridad sobre `fill="..."`).
      if (!el.dataset.defaultStyleFill) el.dataset.defaultStyleFill = el.style.fill || "";
      el.style.transition = "fill 180ms ease, opacity 180ms ease";
      el.style.fill = highlightMesaIds.has(mesaId) ? highlightFill : el.dataset.defaultStyleFill;

      const enabled = allowedMesaKeys.has(mesaId) || allowedMesaKeys.has(mesaId.replace("mesa", "m"));
      el.style.cursor = enabled ? "pointer" : "not-allowed";
      el.style.opacity = enabled ? "1" : "0.75";
      el.style.pointerEvents = "all";

      const mesa = mesaByKey.get(mesaId) || mesaByKey.get(mesaId.replace("mesa", "m"));
      if (enabled && mesa && onSelectMesa) {
        const handler = (evt) => {
          evt.preventDefault();
          onSelectMesa(mesa);
        };
        el.addEventListener("click", handler);
        cleanups.push(() => el.removeEventListener("click", handler));
      }
    });

    return () => cleanups.forEach((fn) => fn());
  }, [allowedMesaKeys, mesaByKey, onSelectMesa]);

  const mesasPermitidas = useMemo(() => {
    return mesasConPosicion.filter((mesa) => allowedMesaKeys.has(normalizeMesaKey(mesa.nombre)));
  }, [mesasConPosicion, allowedMesaKeys]);

  const mesasSinPosicion = mesasPermitidas.filter((m) => !m.position);

  const now = new Date();
  const nowInput = formatDateInput(now);
  const nowMinutes = now.getHours() * 60 + now.getMinutes();

  function isSlotInTimeWindow(slot) {
    if (!selectedDate) return false;
    if (selectedDate < nowInput) return false;
    if (selectedDate > nowInput) return true;
    const [h, m] = slot.split(":").map(Number);
    return h * 60 + m >= nowMinutes;
  }

  function slotsForMesa(mesa) {
    return franjas.filter((slot) => isSlotInTimeWindow(slot));
  }

  function isOccupiedSlot(mesa, slot) {
    const occupied = new Set(occupiedByMesa[mesa.id] || []);
    return occupied.has(slot);
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-[#d9cdb8]">
      <h2 className="text-lg font-semibold text-[#5c3d1e]">Paso 1 · Buscar y elegir mesa</h2>
      {!auth ? <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">Sin login puedes consultar mesa y horarios. Para reservar, inicia sesion como cliente.</p> : null}

      <div className="mt-3 grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="relative overflow-hidden rounded-xl border border-slate-300 bg-white">
            <VistaRealSvg ref={planoRef} aria-label="Plano restaurante" className="h-auto w-full" />
          </div>

       

          {mesasSinPosicion.length > 0 ? (
            <div className="mt-3">
              <p className="mb-2 text-xs text-slate-600">Mesas sin posicion en el plano, puedes seleccionarlas aqui:</p>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {mesasSinPosicion.map((m) => (
                  <button key={m.id} type="button" onClick={() => onSelectMesa?.(m)} className={`rounded-lg border px-3 py-2 text-left text-sm ${Number(selectedMesaId) === m.id ? "border-indigo-600 bg-indigo-50" : "border-slate-300 bg-white"}`}>
                    {prettyMesaName(m.nombre)} · {m.capacidad} personas · {m.disposicion}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <aside className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => setCalendarMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))}
              className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700"
            >
              {"<"}
            </button>
            <p className="text-sm font-semibold capitalize text-[#5c3d1e]">{monthLabel}</p>
            <button
              type="button"
              onClick={() => setCalendarMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))}
              className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700"
            >
              {">"}
            </button>
          </div>
          <div className="mb-1 grid grid-cols-7 gap-1 text-center text-xs text-slate-500">
            {["L", "M", "X", "J", "V", "S", "D"].map((d) => (
              <span key={d}>{d}</span>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((date, idx) => {
              if (!date) {
                return <div key={`empty-${idx}`} className="h-8" />;
              }

              const value = formatDateInput(date);
              const isPast = value < todayInput;
              const isToday = value === todayInput;
              const isSelected = value === selectedDate;
              const isFullDay = diasCompletos.has(value);
              const dayClass = isPast
                ? "border-slate-200 bg-slate-200 text-slate-500 cursor-not-allowed"
                : isSelected
                  ? "border-indigo-600 bg-indigo-600 text-white"
                  : isFullDay
                    ? "border-red-300 bg-red-100 text-red-800"
                    : "border-transparent bg-white text-slate-700";

              return (
                <button
                  key={value}
                  type="button"
                  disabled={isPast}
                  onClick={() => setFiltros({ ...filtros, fecha: value, hora: "" })}
                  className={`h-8 rounded-md border text-sm ${dayClass} ${isToday ? "font-bold" : "font-normal"} ${isPast ? "" : "hover:bg-indigo-50"}`}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
          <div className="mt-3 flex items-end gap-2">
            <div className="flex flex-1 flex-col items-center">
              <div
                className="relative h-16 w-full max-w-[240px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md ring-1 ring-slate-100"
                style={{ touchAction: "pan-y" }}
                onPointerDown={(e) => {
                  setIsDragging(true);
                  setDragX(0);
                  e.currentTarget.setPointerCapture(e.pointerId);
                  e.currentTarget.dataset.startX = String(e.clientX);
                }}
                onPointerMove={(e) => {
                  if (!isDragging) return;
                  if (e.pointerType === "mouse" && e.buttons === 0) {
                    setIsDragging(false);
                    setDragX(0);
                    delete e.currentTarget.dataset.startX;
                    return;
                  }
                  const startX = Number(e.currentTarget.dataset.startX || e.clientX);
                  setDragX(e.clientX - startX);
                }}
                onPointerUp={(e) => {
                  if (!isDragging) return;
                  const threshold = 28;
                  const delta = dragX;
                  let next = capacidad;
                  if (delta <= -threshold) next = Math.min(8, capacidad + 1);
                  if (delta >= threshold) next = Math.max(1, capacidad - 1);
                  setIsDragging(false);
                  setDragX(0);
                  delete e.currentTarget.dataset.startX;
                  if (next !== capacidad) setFiltros({ ...filtros, capacidad: next, hora: "" });
                }}
          onPointerCancel={(e) => {
                  setIsDragging(false);
                  setDragX(0);
                  delete e.currentTarget.dataset.startX;
                }}
                onLostPointerCapture={(e) => {
                  setIsDragging(false);
                  setDragX(0);
                  delete e.currentTarget.dataset.startX;
                }}
              >
                <div className="pointer-events-none absolute left-3 top-1/2 z-20 -translate-y-1/2 text-slate-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M15 18l-6-6 6-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="pointer-events-none absolute right-3 top-1/2 z-20 -translate-y-1/2 text-slate-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M9 18l6-6-6-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
                <div className="pointer-events-none absolute left-3 top-2 z-20 text-slate-400">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M14.5 7.5a3 3 0 1 1 6 0a3 3 0 0 1-6 0Z" fill="currentColor" opacity="0.55" />
                    <path d="M3.5 8.5a3.5 3.5 0 1 0 7 0a3.5 3.5 0 0 0-7 0Z" fill="currentColor" opacity="0.85" />
                    <path d="M2.25 19.5c0-3.1 2.8-5.25 6-5.25s6 2.15 6 5.25v.25H2.25v-.25Z" fill="currentColor" opacity="0.85" />
                    <path d="M13.75 19.75v-.25c0-1.7-.7-3.17-1.84-4.2c.72-.36 1.58-.55 2.59-.55c2.88 0 5.25 1.66 5.25 4.75v.25h-6Z" fill="currentColor" opacity="0.55" />
                  </svg>
                </div>
                <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center pt-2 text-4xl font-semibold text-slate-800 drop-shadow-sm transition-transform" style={{ transform: `translateX(${dragX}px)` }}>
                  {capacidad}
                </div>
                <div
                  className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center pt-2 text-4xl font-semibold text-slate-800 opacity-40"
                  style={{
                    transform: `translateX(${dragX > 0 ? dragX - 70 : dragX + 70}px)`,
                    transition: isDragging ? "none" : "transform 160ms ease, opacity 160ms ease",
                    opacity: isDragging ? 0.35 : 0,
                  }}
                >
                  {dragX > 0 ? Math.max(1, capacidad - 1) : Math.min(8, capacidad + 1)}
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4 rounded-xl border border-slate-200 bg-white p-3">
            <div className="mt-3 space-y-3">
              {mesasPermitidas.map((mesa) => {
                const slots = slotsForMesa(mesa);
                const hasFreeSlot = slots.some((slot) => !isOccupiedSlot(mesa, slot));
                const loading = Object.keys(occupiedByMesa).length === 0 && slots.length > 0;
                return (
                  <div key={`slots-${mesa.id}`} className="rounded-lg border border-slate-200 p-2">
                    <p className="mb-2 text-sm font-medium text-[#5c3d1e]">{prettyMesaName(mesa.nombre)}</p>
                    {loading ? (
                      <p className="text-xs text-slate-500">Cargando...</p>
                    ) : slots.length === 0 ? (
                      <p className="text-xs text-slate-500">Sin huecos disponibles desde la hora actual.</p>
                    ) : (
                      <div className="grid max-h-36 grid-cols-3 gap-2 overflow-auto">
                        {slots.map((slot) => {
                          const selected = Number(selectedMesaId) === mesa.id && filtros.hora === slot;
                          const occupied = isOccupiedSlot(mesa, slot);
                          return (
                            <button
                              key={`${mesa.id}-${slot}`}
                              disabled={!isCliente || occupied}
                              onClick={() => {
                                onSelectMesa?.(mesa);
                                setFiltros({ ...filtros, hora: slot });
                              }}
                              className={`rounded-lg px-2 py-1 text-sm ${selected ? "bg-indigo-600 text-white" : "bg-slate-100"} ${occupied ? "line-through bg-slate-200 text-slate-500" : ""} ${!isCliente || occupied ? "cursor-not-allowed opacity-60" : ""}`}
                            >
                              {slot}
                            </button>
                          );
                        })}
                      </div>
                    )}
                    {!hasFreeSlot && slots.length > 0 ? (
                      <p className="mt-2 text-xs text-slate-500">Todos los horarios visibles estan ocupados.</p>
                    ) : null}
                  </div>
                );
              })}
            </div>
            {!isCliente ? <p className="mt-1 text-xs text-amber-700">Inicia sesion para seleccionar un horario.</p> : null}

            <button className="mt-3 w-full rounded-lg bg-indigo-600 px-3 py-2 text-white disabled:opacity-60" disabled={!filtros.hora || !selectedMesaId || !isCliente} onClick={isCliente ? onContinue : onRequireLogin}>
              Continuar
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}

