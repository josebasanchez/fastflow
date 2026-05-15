export default function PagoCliente({ auth, onRequireLogin, state, setState, selectedMesa, fecha, hora, total, onBack, onConfirm }) {
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Paso 3 · Pago y confirmacion</h2>
        <button className="rounded-lg bg-slate-200 px-3 py-2 text-sm" onClick={onBack}>Volver a productos</button>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
        <p><b>Mesa:</b> {selectedMesa?.nombre || "-"}</p>
        <p><b>Fecha:</b> {fecha || "-"}</p>
        <p><b>Hora:</b> {hora || "-"} (reserva de 1 hora)</p>
        <p className="mt-2 text-base"><b>Total:</b> {total.toFixed(2)} EUR</p>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-2">
        <select className="rounded-lg border border-slate-300 px-2 py-2" value={state.metodo_pago} onChange={(e) => setState({ ...state, metodo_pago: e.target.value })}>
          <option value="establecimiento">Pago en establecimiento</option>
          <option value="bizum">Bizum</option>
          <option value="tarjeta">Tarjeta</option>
        </select>
        <input className="rounded-lg border border-slate-300 px-2 py-2" placeholder="Referencia pago simulada" value={state.referencia_pago} onChange={(e) => setState({ ...state, referencia_pago: e.target.value })} />
      </div>

      <button className="mt-4 rounded-lg bg-indigo-600 px-3 py-2 text-white" onClick={auth ? onConfirm : onRequireLogin}>
        {auth ? "Confirmar reserva y pedido" : "Inicia sesion para confirmar"}
      </button>
    </section>
  );
}
