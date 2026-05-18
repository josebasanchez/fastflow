import { useState } from "react";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, PointElement, LineElement } from "chart.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Tooltip, Legend, PointElement, LineElement);

export default function AdminDashboard({
  stats,
  platos = [],
  ingredientes = [],
  onCreatePlato,
  onCreateIngrediente,
  onCreateReceta,
}) {
  const [platoForm, setPlatoForm] = useState({
    nombre: "",
    descripcion: "",
    precio: "",
    disponible: true,
    es_vegano: false,
    es_halal: false,
  });
  const [ingredienteForm, setIngredienteForm] = useState({
    nombre: "",
    stock_actual: "0",
    unidad: "ud",
    stock_minimo: "0",
    umbral_alerta: "0",
  });
  const [recetaForm, setRecetaForm] = useState({
    plato: "",
    ingrediente: "",
    cantidad: "1",
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  if (!stats) return null;

  const ordersData = {
    labels: ["Abiertos", "Entregados"],
    datasets: [{ label: "Pedidos", data: [stats.pedidos_abiertos, stats.pedidos_entregados], backgroundColor: ["#f59e0b", "#10b981"] }],
  };

  const topData = {
    labels: stats.top_platos.map((p) => p.plato_texto),
    datasets: [{ label: "Top platos", data: stats.top_platos.map((p) => p.total), backgroundColor: "#6366f1" }],
  };

  const reservasHistorico = stats.reservas_historico_14d || [];
  const ingresosHistorico = stats.ingresos_historico_14d || [];
  const pedidosHistorico = stats.pedidos_historico_14d || [];

  const reservasTrendData = {
    labels: reservasHistorico.map((d) => d.fecha.slice(5)),
    datasets: [{ label: "Reservas (14 dias)", data: reservasHistorico.map((d) => d.total), borderColor: "#2563eb", backgroundColor: "rgba(37,99,235,0.15)", tension: 0.25 }],
  };

  const ingresosTrendData = {
    labels: ingresosHistorico.map((d) => d.fecha.slice(5)),
    datasets: [{ label: "Ingresos aprobados (14 dias)", data: ingresosHistorico.map((d) => Number(d.total || 0)), borderColor: "#059669", backgroundColor: "rgba(5,150,105,0.15)", tension: 0.25 }],
  };

  const pedidosTrendData = {
    labels: pedidosHistorico.map((d) => d.fecha.slice(5)),
    datasets: [{ label: "Pedidos creados (14 dias)", data: pedidosHistorico.map((d) => d.total), borderColor: "#7c3aed", backgroundColor: "rgba(124,58,237,0.15)", tension: 0.25 }],
  };

  const pedidosPorEstado = stats.pedidos_por_estado || [];
  const pedidosEstadoData = {
    labels: pedidosPorEstado.map((row) => row.estado),
    datasets: [{ label: "Pedidos por estado", data: pedidosPorEstado.map((row) => row.total), backgroundColor: ["#f59e0b", "#94a3b8", "#10b981", "#6366f1"] }],
  };

  const topEmpleadoPorDia = stats.top_empleado_por_dia_14d || [];
  const rankingEmpleados = stats.ranking_empleados_14d || [];
  const empleadosTopDiaData = {
    labels: topEmpleadoPorDia.map((row) => row.fecha.slice(5)),
    datasets: [{ label: "Platos por top empleado del dia", data: topEmpleadoPorDia.map((row) => row.platos), backgroundColor: "#0ea5e9" }],
  };

  const prepSeconds = stats.tiempo_medio_preparacion_segundos;
  const prepMinutes = prepSeconds != null ? Math.round(prepSeconds / 60) : null;

  async function submitPlato() {
    if (!platoForm.nombre.trim() || !platoForm.precio) {
      setMsg("Nombre y precio son obligatorios.");
      return;
    }
    setSaving(true);
    setMsg("");
    try {
      const creado = await onCreatePlato?.({
        nombre: platoForm.nombre.trim(),
        descripcion: platoForm.descripcion.trim(),
        precio: platoForm.precio,
        disponible: Boolean(platoForm.disponible),
        es_vegano: Boolean(platoForm.es_vegano),
        es_halal: Boolean(platoForm.es_halal),
      });
      setPlatoForm({ nombre: "", descripcion: "", precio: "", disponible: true, es_vegano: false, es_halal: false });
      if (creado?.id) {
        setRecetaForm((prev) => ({ ...prev, plato: String(creado.id) }));
      }
      setMsg("Plato creado correctamente. Ya esta seleccionado para anadir receta.");
    } catch (e) {
      setMsg(String(e));
    } finally {
      setSaving(false);
    }
  }

  async function submitIngrediente() {
    if (!ingredienteForm.nombre.trim()) {
      setMsg("Nombre de ingrediente obligatorio.");
      return;
    }
    setSaving(true);
    setMsg("");
    try {
      await onCreateIngrediente?.({
        nombre: ingredienteForm.nombre.trim(),
        stock_actual: ingredienteForm.stock_actual || "0",
        unidad: ingredienteForm.unidad || "ud",
        stock_minimo: ingredienteForm.stock_minimo || "0",
        umbral_alerta: ingredienteForm.umbral_alerta || ingredienteForm.stock_minimo || "0",
      });
      setIngredienteForm({ nombre: "", stock_actual: "0", unidad: "ud", stock_minimo: "0", umbral_alerta: "0" });
      setMsg("Ingrediente creado correctamente.");
    } catch (e) {
      setMsg(String(e));
    } finally {
      setSaving(false);
    }
  }

  async function submitReceta() {
    if (!recetaForm.plato || !recetaForm.ingrediente || !recetaForm.cantidad) {
      setMsg("Selecciona plato, ingrediente y cantidad.");
      return;
    }
    setSaving(true);
    setMsg("");
    try {
      await onCreateReceta?.({
        plato: Number(recetaForm.plato),
        ingrediente: Number(recetaForm.ingrediente),
        cantidad: recetaForm.cantidad,
      });
      setRecetaForm((prev) => ({ ...prev, cantidad: "1" }));
      setMsg("Receta añadida correctamente al plato.");
    } catch (e) {
      setMsg(String(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Dashboard admin</h2>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950">Reservas totales: <b>{stats.total_reservas}</b></div>
        <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950">Reservas hoy: <b>{stats.reservas_hoy}</b></div>
        <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950">Ingresos: <b>{stats.ingresos_totales} EUR</b></div>
        <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950">Alertas stock: <b>{stats.alertas_stock}</b></div>
        <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-950">Tiempo medio preparacion: <b>{prepMinutes != null ? `${prepMinutes} min` : "-"}</b></div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-3"><Doughnut data={ordersData} /></div>
        <div className="rounded-xl border border-slate-200 p-3"><Bar data={topData} /></div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-3"><Line data={reservasTrendData} /></div>
        <div className="rounded-xl border border-slate-200 p-3"><Line data={ingresosTrendData} /></div>
        <div className="rounded-xl border border-slate-200 p-3"><Line data={pedidosTrendData} /></div>
        <div className="rounded-xl border border-slate-200 p-3"><Bar data={pedidosEstadoData} /></div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-3"><Bar data={empleadosTopDiaData} /></div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <p className="text-sm font-semibold text-slate-800">Empleado que mas prepara por dia (14 dias)</p>
          <div className="mt-2 max-h-56 overflow-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-slate-100 text-left text-slate-700">
                <tr>
                  <th className="px-3 py-2">Fecha</th>
                  <th className="px-3 py-2">Empleado</th>
                  <th className="px-3 py-2">Platos</th>
                </tr>
              </thead>
              <tbody>
                {topEmpleadoPorDia.map((row) => (
                  <tr key={row.fecha} className="border-t border-slate-100">
                    <td className="px-3 py-2">{row.fecha}</td>
                    <td className="px-3 py-2">{row.empleado}</td>
                    <td className="px-3 py-2">{row.platos}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-800">Ranking empleados (ultimos 14 dias)</p>
          <div className="mt-2 space-y-1">
            {rankingEmpleados.map((row) => (
              <div key={row.username} className="flex items-center justify-between rounded bg-white px-3 py-2 text-sm ring-1 ring-slate-200">
                <span>{row.empleado}</span>
                <b>{row.platos} platos</b>
              </div>
            ))}
            {rankingEmpleados.length === 0 ? <p className="text-xs text-slate-500">Aun no hay pedidos en preparacion registrados.</p> : null}
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <h3 className="font-medium">Gestion de platos</h3>
        <div className="mt-3 grid gap-2 md:grid-cols-2">
          <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Nombre" value={platoForm.nombre} onChange={(e) => setPlatoForm({ ...platoForm, nombre: e.target.value })} />
          <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Precio (ej. 12.50)" value={platoForm.precio} onChange={(e) => setPlatoForm({ ...platoForm, precio: e.target.value })} />
          <textarea className="md:col-span-2 rounded-lg border border-slate-300 px-3 py-2" rows="2" placeholder="Descripcion" value={platoForm.descripcion} onChange={(e) => setPlatoForm({ ...platoForm, descripcion: e.target.value })} />
        </div>
        <div className="mt-2 flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={platoForm.disponible} onChange={(e) => setPlatoForm({ ...platoForm, disponible: e.target.checked })} /> Disponible</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={platoForm.es_vegano} onChange={(e) => setPlatoForm({ ...platoForm, es_vegano: e.target.checked })} /> Vegano</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={platoForm.es_halal} onChange={(e) => setPlatoForm({ ...platoForm, es_halal: e.target.checked })} /> Halal</label>
        </div>
        <button className="mt-3 rounded-lg bg-indigo-600 px-4 py-2 text-white disabled:opacity-60" disabled={saving} onClick={submitPlato}>
          {saving ? "Guardando..." : "Crear plato"}
        </button>

        <h4 className="mt-5 font-medium">Mini formulario de ingredientes y receta</h4>
        <div className="mt-2 grid gap-2 md:grid-cols-4">
          <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Ingrediente" value={ingredienteForm.nombre} onChange={(e) => setIngredienteForm({ ...ingredienteForm, nombre: e.target.value })} />
          <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Stock" value={ingredienteForm.stock_actual} onChange={(e) => setIngredienteForm({ ...ingredienteForm, stock_actual: e.target.value })} />
          <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Unidad (ud/kg/l)" value={ingredienteForm.unidad} onChange={(e) => setIngredienteForm({ ...ingredienteForm, unidad: e.target.value })} />
          <button className="rounded-lg bg-slate-800 px-4 py-2 text-white disabled:opacity-60" disabled={saving} onClick={submitIngrediente}>Crear ingrediente</button>
        </div>

        <div className="mt-3 grid gap-2 md:grid-cols-4">
          <select className="rounded-lg border border-slate-300 px-3 py-2" value={recetaForm.plato} onChange={(e) => setRecetaForm({ ...recetaForm, plato: e.target.value })}>
            <option value="">Selecciona plato</option>
            {platos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
          </select>
          <select className="rounded-lg border border-slate-300 px-3 py-2" value={recetaForm.ingrediente} onChange={(e) => setRecetaForm({ ...recetaForm, ingrediente: e.target.value })}>
            <option value="">Selecciona ingrediente</option>
            {ingredientes.map((i) => <option key={i.id} value={i.id}>{i.nombre}</option>)}
          </select>
          <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Cantidad receta" value={recetaForm.cantidad} onChange={(e) => setRecetaForm({ ...recetaForm, cantidad: e.target.value })} />
          <button className="rounded-lg bg-emerald-600 px-4 py-2 text-white disabled:opacity-60" disabled={saving} onClick={submitReceta}>Anadir a receta</button>
        </div>

        {msg ? <p className="mt-2 text-sm text-slate-700">{msg}</p> : null}

        <div className="mt-4 rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-sm font-medium">Platos actuales ({platos.length})</p>
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {platos.slice(0, 20).map((p) => (
              <div key={p.id} className="rounded border border-slate-200 px-3 py-2 text-sm">
                <p><b>{p.nombre}</b> - {p.precio} EUR</p>
                <p className="text-slate-600">{p.descripcion || "Sin descripcion"}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
