import { useMemo, useState } from "react";

function onlyDigits(value) {
  return String(value || "").replace(/[^\d]/g, "");
}

function generateRef(prefix = "FF") {
  const lastDigit = String(Math.floor(Math.random() * 10));
  const middle = String(Math.floor(Math.random() * 90000000) + 10000000);
  return `${prefix}-${middle}${lastDigit}`;
}

export default function PagoCliente({ auth, onRequireLogin, state, setState, selectedMesa, fecha, hora, total, onBack, onConfirm }) {
  const [processing, setProcessing] = useState(false);
  const [gatewayMsg, setGatewayMsg] = useState("");
  const metodo = state.metodo_pago;

  const hint = useMemo(() => {
    if (metodo === "establecimiento") return "El pago quedará pendiente y se realizará en el local.";
    if (metodo === "bizum") return "Simulación: referencia que termina en número par = aprobado; impar = rechazado.";
    if (metodo === "tarjeta") return "Simulación: referencia que termina en número par = aprobado; impar = rechazado.";
    return "";
  }, [metodo]);

  async function simulateAndConfirm() {
    if (!auth) return onRequireLogin?.();
    if (processing) return;

    setGatewayMsg("");
    setProcessing(true);
    try {
      if (metodo !== "establecimiento") {
        const nextRef = state.referencia_pago?.trim()
          ? state.referencia_pago.trim()
          : generateRef(metodo === "bizum" ? "BZM" : "CARD");
        setState((prev) => ({ ...prev, referencia_pago: nextRef }));
        setGatewayMsg("Procesando pago...");
        await new Promise((r) => setTimeout(r, 900));
      }
      await onConfirm?.();
    } finally {
      setProcessing(false);
    }
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Paso 3 · Pago y confirmacion</h2>
        <button className="rounded-lg bg-slate-200 px-3 py-2 text-sm dark:bg-slate-800 dark:text-slate-100" onClick={onBack}>Volver a productos</button>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-800 dark:bg-slate-950">
        <p><b>Mesa:</b> {selectedMesa?.nombre || "-"}</p>
        <p><b>Fecha:</b> {fecha || "-"}</p>
        <p><b>Hora:</b> {hora || "-"} (reserva de 1 hora)</p>
        <p className="mt-2 text-base"><b>Total:</b> {total.toFixed(2)} EUR</p>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-2">
        <select className="rounded-lg border border-slate-300 px-2 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" value={state.metodo_pago} onChange={(e) => setState({ ...state, metodo_pago: e.target.value })}>
          <option value="establecimiento">Pago en establecimiento</option>
          <option value="bizum">Bizum</option>
          <option value="tarjeta">Tarjeta</option>
        </select>
        <input
          className="rounded-lg border border-slate-300 px-2 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
          placeholder={metodo === "establecimiento" ? "Referencia (opcional)" : "Referencia simulada (opcional)"}
          value={state.referencia_pago}
          onChange={(e) => setState({ ...state, referencia_pago: e.target.value })}
        />
      </div>

      <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-200">
        <p className="font-semibold text-slate-900 dark:text-slate-100">Pasarela (simulada)</p>
        <p className="mt-1">{hint}</p>
        {metodo === "tarjeta" ? (
          <div className="mt-3 grid gap-2 md:grid-cols-3">
            <input
              className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              placeholder="Numero tarjeta (simulado)"
              inputMode="numeric"
              value={onlyDigits(state.tarjeta_numero)}
              onChange={(e) => setState((prev) => ({ ...prev, tarjeta_numero: e.target.value }))}
            />
            <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" placeholder="MM/AA" value={state.tarjeta_exp || ""} onChange={(e) => setState((prev) => ({ ...prev, tarjeta_exp: e.target.value }))} />
            <input
              className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              placeholder="CVV"
              inputMode="numeric"
              value={onlyDigits(state.tarjeta_cvv)}
              onChange={(e) => setState((prev) => ({ ...prev, tarjeta_cvv: e.target.value }))}
            />
          </div>
        ) : null}
        {metodo === "bizum" ? (
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" placeholder="Telefono Bizum (simulado)" inputMode="tel" value={state.bizum_telefono || ""} onChange={(e) => setState((prev) => ({ ...prev, bizum_telefono: e.target.value }))} />
            <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" placeholder="Codigo Bizum (simulado)" inputMode="numeric" value={state.bizum_codigo || ""} onChange={(e) => setState((prev) => ({ ...prev, bizum_codigo: e.target.value }))} />
          </div>
        ) : null}
        {gatewayMsg ? <p className="mt-3 text-slate-600 dark:text-slate-300">{gatewayMsg}</p> : null}
      </div>

      <button className="mt-4 rounded-lg bg-indigo-600 px-3 py-2 text-white disabled:opacity-60" disabled={processing} onClick={simulateAndConfirm}>
        {!auth ? "Inicia sesion para confirmar" : processing ? "Procesando..." : metodo === "establecimiento" ? "Confirmar reserva (pago en local)" : "Pagar y confirmar reserva"}
      </button>
    </section>
  );
}
