import { useMemo, useState } from "react";
import burgerClasicaImg from "../assets/platos/burger_clasica.png";
import burgerVeganaImg from "../assets/platos/burger_vegana.png";
import ensaladaCesarImg from "../assets/platos/ensalada_cesar.png";
import pizzaMargaritaImg from "../assets/platos/pizza_margarita.png";

const CATEGORY_RULES = [
  { id: "burgers", label: "Burgers", test: /(burger|hamburguesa)/i },
  { id: "pizza", label: "Pizzas", test: /(pizza)/i },
  { id: "salads", label: "Ensaladas", test: /(ensalada|salad)/i },
  { id: "menu", label: "Menus", test: /(menu|combo)/i },
  { id: "sides", label: "Acompañamientos", test: /(patata|fries|nugget|alita)/i },
  { id: "drinks", label: "Bebidas", test: /(cola|agua|zumo|fanta|nestea|cafe|cerveza)/i },
];

const PLATO_IMAGE_MAP = {
  burgerclasica: burgerClasicaImg,
  burgervegana: burgerVeganaImg,
  ensaladacesar: ensaladaCesarImg,
  pizzamargarita: pizzaMargaritaImg,
};

function normalizeKey(value) {
  return (value || "").toLowerCase().replace(/\s+/g, "").replace(/[^a-z0-9]/g, "");
}

function getCategory(plato) {
  const byName = `${plato.nombre} ${plato.descripcion || ""}`;
  const found = CATEGORY_RULES.find((rule) => rule.test.test(byName));
  return found ? found.id : "otros";
}

export default function ReservaCliente({ auth, onRequireLogin, platos, state, setState, onNextStep, dietaFiltros, setDietaFiltros, onRate, onComment, onVote, comentariosByPlato, selectedMesa, onBackToMesas, loadCommentsPage }) {
  const [activeCategory, setActiveCategory] = useState("burgers");
  const [draftComments, setDraftComments] = useState({});
  const [draftRatings, setDraftRatings] = useState({});

  const grouped = useMemo(() => {
    const base = { burgers: [], pizza: [], salads: [], menu: [], sides: [], drinks: [], otros: [] };
    for (const plato of platos) base[getCategory(plato)].push(plato);
    return base;
  }, [platos]);

  const total = useMemo(() => state.pedidos.reduce((acc, item) => {
    const plato = platos.find((p) => p.id === item.plato_id);
    if (!plato) return acc;
    return acc + Number(plato.precio) * Number(item.cantidad);
  }, 0), [state.pedidos, platos]);

  function addToCart(platoId) {
    const existing = state.pedidos.find((item) => item.plato_id === platoId);
    const next = existing
      ? state.pedidos.map((item) => (item.plato_id === platoId ? { ...item, cantidad: item.cantidad + 1 } : item))
      : [...state.pedidos, { plato_id: platoId, cantidad: 1 }];
    setState({ ...state, pedidos: next });
  }

  function updateQty(platoId, delta) {
    const next = state.pedidos
      .map((item) => (item.plato_id === platoId ? { ...item, cantidad: Math.max(0, item.cantidad + delta) } : item))
      .filter((item) => item.cantidad > 0);
    setState({ ...state, pedidos: next });
  }

  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Paso 2 · Elegir productos</h2>
        <div className="flex gap-2">
          <button className="rounded-lg bg-slate-200 px-3 py-2 text-sm" onClick={onBackToMesas}>Cambiar mesa</button>
        </div>
      </div>
      {selectedMesa ? <p className="mt-2 text-sm text-slate-700">Mesa seleccionada: <b>{selectedMesa.nombre}</b> · {selectedMesa.capacidad} personas · {selectedMesa.disposicion}</p> : null}

      <div className="mt-4 rounded-xl border border-slate-200 p-3">
        <h3 className="font-medium">Filtros alimentarios</h3>
        <div className="mt-2 flex gap-4 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={dietaFiltros.vegano} onChange={(e) => setDietaFiltros({ ...dietaFiltros, vegano: e.target.checked })} /> Solo vegano</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={dietaFiltros.halal} onChange={(e) => setDietaFiltros({ ...dietaFiltros, halal: e.target.checked })} /> Solo halal</label>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-slate-200 p-3">
        <h3 className="font-medium">Menu y carrito</h3>
        <div className="mt-2 flex flex-wrap gap-2">
          {Object.keys(grouped).map((cat) => (
            <button key={cat} className={`rounded-lg px-3 py-2 text-sm ${activeCategory === cat ? "bg-slate-900 text-white" : "bg-slate-100"}`} onClick={() => setActiveCategory(cat)}>{cat}</button>
          ))}
        </div>
        <div className="mt-3 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
          {grouped[activeCategory]?.map((p) => (
            <article key={p.id} className="rounded-lg border border-slate-200 p-3">
              <img src={PLATO_IMAGE_MAP[normalizeKey(p.nombre)] || pizzaMargaritaImg} alt={p.nombre} className="mb-2 h-36 w-full rounded object-cover" />
              <h4 className="font-medium">{p.nombre}</h4>
              <p className="text-sm text-slate-600">{p.descripcion}</p>
              <p className="text-xs text-slate-500">Valoracion: {p.valoracion_media ?? "sin"} ({p.total_valoraciones})</p>
              <p className="mt-2 font-semibold">{p.precio} EUR</p>
              <div className="mt-2 flex gap-2 text-xs">
                {p.es_vegano ? <span className="rounded bg-emerald-100 px-2 py-1 text-emerald-700">Vegano</span> : null}
                {p.es_halal ? <span className="rounded bg-cyan-100 px-2 py-1 text-cyan-700">Halal</span> : null}
              </div>
              <button className="mt-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm text-white" onClick={() => addToCart(p.id)}>Añadir</button>
              <div className="mt-3 border-t border-slate-200 pt-2">
                <div className="flex items-center gap-2">
                  <select className="rounded border border-slate-300 px-2 py-1 text-sm" value={draftRatings[p.id] || ""} onChange={(e) => setDraftRatings({ ...draftRatings, [p.id]: e.target.value })}>
                    <option value="">Puntuar</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option>
                  </select>
                  <button className="rounded bg-slate-900 px-2 py-1 text-xs text-white" onClick={() => onRate(p.id, Number(draftRatings[p.id] || 0))}>Enviar</button>
                </div>
                <textarea className="mt-2 w-full rounded border border-slate-300 px-2 py-1 text-sm" rows="2" placeholder="Escribe un comentario" value={draftComments[p.id] || ""} onChange={(e) => setDraftComments({ ...draftComments, [p.id]: e.target.value })} />
                <button className="mt-1 rounded bg-slate-800 px-2 py-1 text-xs text-white" onClick={() => onComment(p.id, draftComments[p.id] || "")}>Comentar</button>
                <div className="mt-2 space-y-1">
                  {((comentariosByPlato[p.id] && comentariosByPlato[p.id].results) || []).map((c) => (
                    <div key={c.id} className="rounded bg-slate-50 p-2 text-xs">
                      <p><b>{c.nombre_cliente}</b>: {c.comentario}</p>
                      <div className="mt-1 flex gap-2">
                        <button className="rounded bg-emerald-100 px-2" onClick={() => onVote(c.id, "like")}>Like {c.likes}</button>
                        <button className="rounded bg-rose-100 px-2" onClick={() => onVote(c.id, "dislike")}>Dislike {c.dislikes}</button>
                      </div>
                    </div>
                  ))}
                  {/* Pagination controls */}
                  {comentariosByPlato[p.id] && (
                    <div className="flex justify-between mt-2 text-sm">
                      <button
                        disabled={comentariosByPlato[p.id].page <= 1}
                        onClick={() => loadCommentsPage(p.id, comentariosByPlato[p.id].page - 1, comentariosByPlato[p.id].page_size)}
                        className="px-2 py-1 bg-slate-200 rounded disabled:opacity-50"
                      >Anterior</button>
                      <span>Página {comentariosByPlato[p.id].page} de {comentariosByPlato[p.id].total_pages}</span>
                      <button
                        disabled={comentariosByPlato[p.id].page >= comentariosByPlato[p.id].total_pages}
                        onClick={() => loadCommentsPage(p.id, comentariosByPlato[p.id].page + 1, comentariosByPlato[p.id].page_size)}
                        className="px-2 py-1 bg-slate-200 rounded disabled:opacity-50"
                      >Siguiente</button>
                    </div>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="mt-4 rounded-lg bg-slate-50 p-3">
          <h4 className="font-medium">Tu pedido</h4>
          {state.pedidos.length === 0 ? <p className="text-sm text-slate-600">Sin productos.</p> : null}
          {state.pedidos.map((item) => {
            const plato = platos.find((p) => p.id === item.plato_id);
            if (!plato) return null;
            return (
              <div key={item.plato_id} className="mt-2 flex items-center justify-between gap-2 rounded border border-slate-200 bg-white px-3 py-2">
                <span>{plato.nombre}</span>
                <div className="flex items-center gap-2">
                  <button className="rounded bg-slate-200 px-2" onClick={() => updateQty(item.plato_id, -1)}>-</button>
                  <span>{item.cantidad}</span>
                  <button className="rounded bg-slate-200 px-2" onClick={() => updateQty(item.plato_id, 1)}>+</button>
                  <span className="w-20 text-right text-sm">{(Number(plato.precio) * Number(item.cantidad)).toFixed(2)} EUR</span>
                </div>
              </div>
            );
          })}
          <p className="mt-3 text-right font-semibold">Total: {total.toFixed(2)} EUR</p>
        </div>
      </div>

      <button className="mt-3 rounded-lg bg-indigo-600 px-3 py-2 text-white" onClick={auth ? onNextStep : onRequireLogin}>
        {auth ? "Continuar a pago" : "Inicia sesion para reservar"}
      </button>
    </section>
  );
}
