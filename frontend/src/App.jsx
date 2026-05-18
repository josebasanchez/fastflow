import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { apiWithRefresh, requestApi } from "./api";
import AuthForms from "./components/AuthForms";
import MesasDisponibles from "./components/MesasDisponibles";
import ReservaCliente from "./components/ReservaCliente";
import PagoCliente from "./components/PagoCliente";
import PedidosCola from "./components/PedidosCola";
import AdminDashboard from "./components/AdminDashboard";
import logo from "./assets/logo.jpg";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000/restaurante";
const STORAGE_KEY = "fastflow_auth";

function normalizeRole(user) {
  const rawRole = String(user?.rol || "").toLowerCase().trim();
  const username = String(user?.username || "").toLowerCase().trim();
  if (Boolean(user?.is_staff) || rawRole === "administrador" || rawRole === "admin" || username === "admin") return "administrador";
  if (rawRole === "empleado" || rawRole.includes("empleado") || username.includes("empleado")) return "empleado";
  return "cliente";
}

function getDefaultPathForAuth(auth) {
  const role = normalizeRole(auth?.user);
  if (role === "administrador") return "/admin";
  if (role === "empleado") return "/empleado";
  return "/cliente";
}

function todayInput() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getNombreCliente(auth) {
  return auth?.user?.nombre_mostrar || auth?.user?.first_name || auth?.user?.username || "";
}

function AppShell({ auth, onLogout, children }) {
  const role = normalizeRole(auth?.user);
  return (
    <main className="min-h-screen bg-[#f5f0e8] p-4 md:p-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4">
        <header className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-[#d9cdb8]">
          <div className="flex items-center gap-3">
            <img src={logo} alt="Logo Fast Flow" className="h-12 w-12 rounded-full object-cover ring-2 ring-[#c89a58]" />
            <div>
              <h1 className="text-2xl font-bold text-[#5c3d1e]">Fast Flow</h1>
              <p className="text-xs text-[#8c6a43]">Llega, come y vete.</p>
              <p className="text-sm text-[#7a5c3a]">{auth ? `${auth.user.username} · ${role}` : "Invitado"}</p>
            </div>
          </div>
          <nav className="flex flex-wrap gap-2 text-sm">
            {!auth ? <NavLink className="rounded-lg bg-[#5c3d1e] px-3 py-2 text-white" to="/auth">Entrar</NavLink> : null}
            {auth ? <button className="rounded-lg bg-[#5c3d1e] px-3 py-2 text-white" onClick={onLogout}>Salir</button> : null}
          </nav>
        </header>
        {children}
        <footer className="rounded-2xl bg-white p-4 text-sm text-[#7a5c3a] shadow-sm ring-1 ring-[#d9cdb8]">
          <p><b>Contacto</b> · Tel: 912 345 678 · Email: info@fastflow.es · Dirección: Calle Gran Vía 123, Madrid</p>
        </footer>
      </div>
    </main>
  );
}

function RoleRoute({ auth, roles, children }) {
  if (!auth) return <Navigate to="/auth" replace />;
  const role = normalizeRole(auth?.user);
  if (!roles.includes(role)) return <Navigate to={getDefaultPathForAuth(auth)} replace />;
  return children;
}

function ClientPage({ auth, onRequireLogin, mesas, platos, mesasFiltros, setMesasFiltros, reservaState, setReservaState, crearReservaCliente, dietaFiltros, setDietaFiltros, onRate, onComment, onVote, comentariosByPlato, occupiedSlotsByMesa, loadCommentsPage, onSuccess }) {
  const [step, setStep] = useState(1);
  const selectedMesa = mesas.find((m) => m.id === Number(reservaState.mesa_id));
  const total = reservaState.pedidos.reduce((acc, item) => {
    const plato = platos.find((p) => p.id === item.plato_id);
    if (!plato) return acc;
    return acc + Number(plato.precio) * Number(item.cantidad);
  }, 0);

  function onSelectMesa(mesa) {
    setReservaState((prev) => ({ ...prev, mesa_id: String(mesa.id) }));
  }

  function onContinueFromMesas() {
    if (!selectedMesa || !mesasFiltros.hora) return;
    if (!auth || normalizeRole(auth.user) !== "cliente") {
      onRequireLogin();
      return;
    }
    setStep(2);
  }

  return (
    <>
      {step === 1 ? (
        <MesasDisponibles
          auth={auth}
          onRequireLogin={onRequireLogin}
          mesas={mesas}
          filtros={mesasFiltros}
          setFiltros={setMesasFiltros}
          selectedMesaId={reservaState.mesa_id}
          onSelectMesa={onSelectMesa}
          occupiedSlotsByMesa={occupiedSlotsByMesa}
          onContinue={onContinueFromMesas}
          apiBaseUrl={API_BASE_URL}
        />
      ) : null}
      {step === 2 ? (
        <ReservaCliente
          platos={platos}
          state={reservaState}
          setState={setReservaState}
          auth={auth}
          onRequireLogin={onRequireLogin}
          onNextStep={() => {
            if (!auth) {
              onRequireLogin();
              return;
            }
            setStep(3);
          }}
          dietaFiltros={dietaFiltros}
          setDietaFiltros={setDietaFiltros}
          onRate={onRate}
          onComment={onComment}
          onVote={onVote}
          comentariosByPlato={comentariosByPlato}
          selectedMesa={selectedMesa}
          onBackToMesas={() => setStep(1)}
          loadCommentsPage={loadCommentsPage}
          onAddToCart={() => onSuccess({ msg: "Producto añadido al carrito" })}
        />
      ) : null}
      {step === 3 ? (
        <PagoCliente
          state={reservaState}
          setState={setReservaState}
          selectedMesa={selectedMesa}
          fecha={mesasFiltros.fecha}
          hora={mesasFiltros.hora}
          total={total}
          onBack={() => setStep(2)}
          auth={auth}
          onRequireLogin={onRequireLogin}
          onConfirm={() => {
            if (!auth) {
              onRequireLogin();
              return;
            }
            Promise.resolve(crearReservaCliente()).then(() => setStep(1));
          }}
        />
      ) : null}
    </>
  );
}

function EmpleadoPage({ pedidos, onStartPreparing, onMarkReady, currentUser }) {
  return (
    <PedidosCola
      pedidos={pedidos}
      onStartPreparing={onStartPreparing}
      onMarkReady={onMarkReady}
      currentUserId={currentUser?.id}
      currentUsername={currentUser?.username}
    />
  );
}

function AdminPage({ stats, platos, ingredientes, onCreatePlato, onCreateIngrediente, onCreateReceta }) {
  return (
    <AdminDashboard
      stats={stats}
      platos={platos}
      ingredientes={ingredientes}
      onCreatePlato={onCreatePlato}
      onCreateIngrediente={onCreateIngrediente}
      onCreateReceta={onCreateReceta}
    />
  );
}

function AuthPage({ onLogin, onRegister, auth }) {
  const location = useLocation();
  if (auth) {
    const from = location.state?.from?.pathname || getDefaultPathForAuth(auth);
    return <Navigate to={from} replace />;
  }
  return <AuthForms onLogin={onLogin} onRegister={onRegister} />;
}

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const [auth, setAuth] = useState(() => JSON.parse(localStorage.getItem(STORAGE_KEY) || "null"));
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);
  const [mesasFiltros, setMesasFiltros] = useState({ fecha: todayInput(), hora: "", capacidad: 2 });
  const [mesas, setMesas] = useState([]);
  const [occupiedSlotsByMesa, setOccupiedSlotsByMesa] = useState({});
  const [platos, setPlatos] = useState([]);
  const [dietaFiltros, setDietaFiltros] = useState({ vegano: false, halal: false });
  const [comentariosByPlato, setComentariosByPlato] = useState({});
  const [reservaState, setReservaState] = useState({
    nombre_cliente: getNombreCliente(auth),
    email_cliente: auth?.user?.email || "",
    mesa_id: "",
    pedido_anticipado: true,
    metodo_pago: "establecimiento",
    referencia_pago: "",
    pedidos: [],
  });
  const [pedidos, setPedidos] = useState([]);
  const [stats, setStats] = useState(null);
  const [adminPlatos, setAdminPlatos] = useState([]);
  const [adminIngredientes, setAdminIngredientes] = useState([]);
  const mesasRequestInFlight = useRef(false);
  const privateRequestInFlight = useRef(false);

  const currentRole = useMemo(() => normalizeRole(auth?.user), [auth]);
  const isAdmin = useMemo(() => currentRole === "administrador", [currentRole]);
  const canAccessPrivate = useMemo(() => currentRole === "empleado" || currentRole === "administrador", [currentRole]);

  async function onLogin(form) {
    const data = await requestApi(API_BASE_URL, "auth/login/", { method: "POST", body: { username: form.username, password: form.password } });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    setAuth(data);
    setError("");
    setSuccess("");
    navigate(getDefaultPathForAuth(data));
  }

  async function onRegister(form) {
    const data = await requestApi(API_BASE_URL, "auth/register/", { method: "POST", body: form });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    setAuth(data);
    setError("");
    setSuccess("");
    navigate(getDefaultPathForAuth(data));
  }

  const buscarMesas = useCallback(async () => {
    if (mesasRequestInFlight.current) return;
    if (!mesasFiltros.fecha) {
      throw new Error("Selecciona fecha antes de buscar mesas");
    }
    mesasRequestInFlight.current = true;
    try {
      const q = `fecha=${mesasFiltros.fecha}`;
      setMesas(await requestApi(API_BASE_URL, `cliente/mesas-disponibles/?${q}`));
      setError("");
    } finally {
      mesasRequestInFlight.current = false;
    }
  }, [mesasFiltros.fecha]);

  async function cargarPlatos() {
    const params = new URLSearchParams();
    if (dietaFiltros.vegano) params.append("vegano", "true");
    if (dietaFiltros.halal) params.append("halal", "true");
    const suffix = params.toString() ? `?${params.toString()}` : "";
    const data = await requestApi(API_BASE_URL, `cliente/platos/${suffix}`);
    setPlatos(data);
    await Promise.all(
      data.map(async (plato) => {
        // Cargar primera página de comentarios (5 por página)
        const comentariosResp = await requestApi(API_BASE_URL, `cliente/platos/${plato.id}/comentarios/?page=1&page_size=5`);
        // La respuesta ahora incluye pagination metadata
        const { results, total, page, page_size, total_pages } = comentariosResp;
        setComentariosByPlato((prev) => ({ ...prev, [plato.id]: { results, total, page, page_size, total_pages } }));
      })
    );
  }

  async function onRate(platoId, puntuacion) {
    if (!reservaState.email_cliente || !puntuacion) throw new Error("Indica email y puntuacion");
    await requestApi(API_BASE_URL, `cliente/platos/${platoId}/valoraciones/`, { method: "POST", body: { email_cliente: reservaState.email_cliente, puntuacion } });
    await cargarPlatos();
  }

  async function onComment(platoId, comentario) {
    if (!reservaState.email_cliente || !reservaState.nombre_cliente || !comentario.trim()) throw new Error("Nombre, email y comentario son obligatorios");
    await requestApi(API_BASE_URL, `cliente/platos/${platoId}/comentarios/`, { method: "POST", body: { nombre_cliente: reservaState.nombre_cliente, email_cliente: reservaState.email_cliente, comentario } });
    // Recargar la página actual de comentarios
    const current = comentariosByPlato[platoId] || { page: 1, page_size: 5 };
    const resp = await requestApi(API_BASE_URL, `cliente/platos/${platoId}/comentarios/?page=${current.page}&page_size=${current.page_size}`);
    setComentariosByPlato((prev) => ({ ...prev, [platoId]: resp }));
  }

  async function onVote(comentarioId, tipo) {
    if (!reservaState.email_cliente) throw new Error("Indica email para votar");
    const actualizado = await requestApi(API_BASE_URL, `cliente/comentarios/${comentarioId}/voto/`, { method: "POST", body: { email_cliente: reservaState.email_cliente, tipo } });
    // Recargar la página actual del plato al que pertenece el comentario
    // Encontrar el platoId del comentario (asumimos que está en comentariosByPlato)
    const platoId = Object.keys(comentariosByPlato).find((pid) =>
      (comentariosByPlato[pid].results || []).some((c) => c.id === comentarioId)
    );
    if (platoId) {
      const current = comentariosByPlato[platoId] || { page: 1, page_size: 5 };
      const resp = await requestApi(API_BASE_URL, `cliente/platos/${platoId}/comentarios/?page=${current.page}&page_size=${current.page_size}`);
      setComentariosByPlato((prev) => ({ ...prev, [platoId]: resp }));
    } else {
      // fallback: actualizar directamente
      setComentariosByPlato((prev) => {
        const next = { ...prev };
        Object.keys(next).forEach((pid) => {
          next[pid] = next[pid].map((c) => (c.id === actualizado.id ? actualizado : c));
        });
        return next;
      });
    }
  }

  async function crearReservaCliente() {
    if (!auth) throw new Error("Debes iniciar sesion para reservar");
    const payload = {
      nombre_cliente: reservaState.nombre_cliente,
      email_cliente: reservaState.email_cliente,
      mesa_id: Number(reservaState.mesa_id),
      fecha: mesasFiltros.fecha,
      hora: mesasFiltros.hora,
      pedido_anticipado: reservaState.pedido_anticipado,
      metodo_pago: reservaState.metodo_pago,
      referencia_pago: reservaState.referencia_pago,
      pedidos: reservaState.pedidos.map((item) => ({ plato_id: Number(item.plato_id), cantidad: Number(item.cantidad) })),
    };

    await apiWithRefresh(API_BASE_URL, "cliente/reserva/", { method: "POST", body: payload }, auth, setAuth, STORAGE_KEY);
    await buscarMesas();
    setReservaState((prev) => ({ ...prev, pedidos: [], referencia_pago: "", mesa_id: "" }));
    setError("");
    setSuccess({ msg: "Reserva creada correctamente" })
  }

  // Load a page of comments for a plato (used by child components)
  async function loadCommentsPage(platoId, page = 1, pageSize = 5) {
    const resp = await requestApi(API_BASE_URL, `cliente/platos/${platoId}/comentarios/?page=${page}&page_size=${pageSize}`);
    setComentariosByPlato((prev) => ({ ...prev, [platoId]: resp }));
  }

  const loadPrivate = useCallback(async () => {
    if (!auth || !canAccessPrivate || privateRequestInFlight.current) return;
    privateRequestInFlight.current = true;
    try {
      const cola = await apiWithRefresh(API_BASE_URL, "pedidos/cola_preparacion/", {}, auth, setAuth, STORAGE_KEY);
      setPedidos(cola);
      if (isAdmin) {
        setStats(await apiWithRefresh(API_BASE_URL, "admin/dashboard-stats/", {}, auth, setAuth, STORAGE_KEY));
        setAdminPlatos(await apiWithRefresh(API_BASE_URL, "platos/", {}, auth, setAuth, STORAGE_KEY));
        setAdminIngredientes(await apiWithRefresh(API_BASE_URL, "ingredientes/", {}, auth, setAuth, STORAGE_KEY));
      }
    } finally {
      privateRequestInFlight.current = false;
    }
  }, [auth, isAdmin, canAccessPrivate]);

  const setPedidoEnPreparacion = useCallback(async (pedidoId) => {
    if (!auth) throw new Error("Debes iniciar sesion");
    await apiWithRefresh(API_BASE_URL, `pedidos/${pedidoId}/iniciar_preparacion/`, { method: "POST" }, auth, setAuth, STORAGE_KEY);
    await loadPrivate();
  }, [auth, loadPrivate]);

  const setPedidoListo = useCallback(async (pedidoId) => {
    if (!auth) throw new Error("Debes iniciar sesion");
    await apiWithRefresh(API_BASE_URL, `pedidos/${pedidoId}/marcar_listo/`, { method: "POST" }, auth, setAuth, STORAGE_KEY);
    await loadPrivate();
  }, [auth, loadPrivate]);

  const crearPlatoAdmin = useCallback(async (payload) => {
    if (!auth || !isAdmin) throw new Error("Solo administradores");
    const creado = await apiWithRefresh(API_BASE_URL, "platos/", { method: "POST", body: payload }, auth, setAuth, STORAGE_KEY);
    setAdminPlatos(await apiWithRefresh(API_BASE_URL, "platos/", {}, auth, setAuth, STORAGE_KEY));
    await cargarPlatos();
    return creado;
  }, [auth, isAdmin]);

  const crearIngredienteAdmin = useCallback(async (payload) => {
    if (!auth || !isAdmin) throw new Error("Solo administradores");
    await apiWithRefresh(API_BASE_URL, "ingredientes/", { method: "POST", body: payload }, auth, setAuth, STORAGE_KEY);
    setAdminIngredientes(await apiWithRefresh(API_BASE_URL, "ingredientes/", {}, auth, setAuth, STORAGE_KEY));
  }, [auth, isAdmin]);

  const crearRecetaAdmin = useCallback(async (payload) => {
    if (!auth || !isAdmin) throw new Error("Solo administradores");
    await apiWithRefresh(API_BASE_URL, "recetas/", { method: "POST", body: payload }, auth, setAuth, STORAGE_KEY);
  }, [auth, isAdmin]);

  useEffect(() => {
    const nombreCliente = getNombreCliente(auth);
    const emailCliente = auth?.user?.email || "";
    setReservaState((prev) => ({
      ...prev,
      nombre_cliente: nombreCliente,
      email_cliente: emailCliente,
    }));
  }, [auth]);

  useEffect(() => {
    if (!success) return;
    const handle = setTimeout(() => setSuccess(null), 3000);
    return () => clearTimeout(handle);
  }, [success]);

  useEffect(() => {
    cargarPlatos().catch((e) => setError(String(e)));
  }, [dietaFiltros]);

  useEffect(() => {
    if (!mesasFiltros.fecha) return;
    buscarMesas().catch((e) => setError(String(e)));
  }, [mesasFiltros.fecha, mesasFiltros.capacidad, buscarMesas]);

  useEffect(() => {
    if (location.pathname !== "/cliente" || !mesasFiltros.fecha) {
      setOccupiedSlotsByMesa({});
      return;
    }
    const params = new URLSearchParams({ fecha: mesasFiltros.fecha, capacidad: String(mesasFiltros.capacidad || 1) });
    const streamUrl = `${API_BASE_URL}/stream/cliente-updates/?${params.toString()}`;
    const es = new EventSource(streamUrl);
    let gotMessage = false;
    const fetchOccupiedFallback = async () => {
      if (mesas.length === 0) return;
      try {
        const entries = await Promise.all(
          mesas.map(async (mesa) => {
            const data = await requestApi(API_BASE_URL, `cliente/mesas/${mesa.id}/horas-ocupadas/?fecha=${mesasFiltros.fecha}`);
            return [String(mesa.id), data.horas_ocupadas || []];
          })
        );
        setOccupiedSlotsByMesa(Object.fromEntries(entries));
      } catch (_) {
        // ignore fallback errors
      }
    };

    es.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        gotMessage = true;
        if (Array.isArray(payload.mesas)) setMesas(payload.mesas);
        if (payload.occupied_slots_by_mesa && typeof payload.occupied_slots_by_mesa === "object") {
          setOccupiedSlotsByMesa(payload.occupied_slots_by_mesa);
        }
      } catch (_) {
        // ignore malformed payloads
      }
    };
    es.onerror = () => {
      if (!gotMessage) fetchOccupiedFallback();
    };
    return () => es.close();
  }, [location.pathname, mesas, mesasFiltros.fecha, mesasFiltros.capacidad]);

  useEffect(() => {
    if (!auth || !canAccessPrivate || !auth.access) return;
    const streamUrl = `${API_BASE_URL}/stream/private-updates/?token=${encodeURIComponent(auth.access)}`;
    const es = new EventSource(streamUrl);
    es.onmessage = (evt) => {
      try {
        const payload = JSON.parse(evt.data);
        if (Array.isArray(payload.pedidos)) setPedidos(payload.pedidos);
        if (isAdmin && payload.stats) setStats(payload.stats);
        if (isAdmin && Array.isArray(payload.adminPlatos)) setAdminPlatos(payload.adminPlatos);
        if (isAdmin && Array.isArray(payload.adminIngredientes)) setAdminIngredientes(payload.adminIngredientes);
      } catch (_) {
        // ignore malformed payloads
      }
    };
    es.onerror = () => {
      // browser auto-reconnects SSE
    };
    return () => es.close();
  }, [auth, canAccessPrivate, isAdmin]);

  useEffect(() => {
    loadPrivate().catch((e) => {
      if (!String(e).includes("token_not_valid") && !String(e).includes("Token is expired")) {
        setError(String(e));
      }
    });
  }, [loadPrivate]);

  function onLogout() {
    localStorage.removeItem(STORAGE_KEY);
    setAuth(null);
    navigate("/auth");
  }

  return (
    <AppShell auth={auth} onLogout={onLogout}>
      <Routes>
        <Route path="/" element={<Navigate to={auth ? getDefaultPathForAuth(auth) : "/cliente"} replace />} />
        <Route path="/auth" element={<AuthPage auth={auth} onLogin={(f) => onLogin(f).catch((e) => setError(String(e)))} onRegister={(f) => onRegister(f).catch((e) => setError(String(e)))} />} />
        <Route
          path="/cliente"
          element={
            auth && currentRole !== "cliente" ? (
              <Navigate to={getDefaultPathForAuth(auth)} replace />
            ) : (
              <ClientPage
                mesas={mesas}
                auth={auth}
                onRequireLogin={() => navigate("/auth", { state: { from: { pathname: "/cliente" } } })}
                platos={platos}
                mesasFiltros={mesasFiltros}
                setMesasFiltros={setMesasFiltros}
                reservaState={reservaState}
                setReservaState={setReservaState}
                crearReservaCliente={() => crearReservaCliente().catch((e) => setError(String(e)))}
                dietaFiltros={dietaFiltros}
                setDietaFiltros={setDietaFiltros}
                onRate={(platoId, puntuacion) => onRate(platoId, puntuacion).catch((e) => setError(String(e)))}
                onComment={(platoId, comentario) => onComment(platoId, comentario).catch((e) => setError(String(e)))}
                onVote={(comentarioId, tipo) => onVote(comentarioId, tipo).catch((e) => setError(String(e)))}
                comentariosByPlato={comentariosByPlato}
                occupiedSlotsByMesa={occupiedSlotsByMesa}
                loadCommentsPage={loadCommentsPage}
                onSuccess={(msg) => setSuccess(msg)}
              />
            )
          }
        />
        <Route
          path="/empleado"
          element={
            <RoleRoute auth={auth} roles={["empleado"]}>
              <EmpleadoPage
                pedidos={pedidos}
                onStartPreparing={(pedidoId) => setPedidoEnPreparacion(pedidoId).catch((e) => { setError(String(e)); throw e; })}
                onMarkReady={(pedidoId) => setPedidoListo(pedidoId).catch((e) => { setError(String(e)); throw e; })}
                currentUser={auth?.user}
              />
            </RoleRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <RoleRoute auth={auth} roles={["administrador"]}>
              <AdminPage
                stats={stats}
                platos={adminPlatos}
                ingredientes={adminIngredientes}
                onCreatePlato={(p) => crearPlatoAdmin(p).catch((e) => { setError(String(e)); throw e; })}
                onCreateIngrediente={(i) => crearIngredienteAdmin(i).catch((e) => { setError(String(e)); throw e; })}
                onCreateReceta={(r) => crearRecetaAdmin(r).catch((e) => { setError(String(e)); throw e; })}
              />
            </RoleRoute>
          }
        />
        <Route path="*" element={<Navigate to={auth ? getDefaultPathForAuth(auth) : "/cliente"} replace />} />
      </Routes>
      {success ? (
        <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
          <div className="bg-emerald-500 text-white text-lg font-semibold px-8 py-5 rounded-2xl shadow-2xl">
            {success.msg}
          </div>
        </div>
      ) : null}
      {error ? <div className="mx-auto mt-3 w-full max-w-7xl rounded-lg bg-rose-100 px-4 py-3 text-rose-800">{error}</div> : null}
    </AppShell>
  );
}
