import { useState } from "react";

export default function AuthForms({ onLogin, onRegister }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", password: "", email: "", nombre_mostrar: "", first_name: "", rol: "cliente", idioma: "es" });

  return (
    <section className="mx-auto w-full max-w-md rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">FastFlow</h1>
      <div className="mt-4 flex gap-2">
        <button className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white" onClick={() => setMode("login")}>Login</button>
        <button className="rounded-lg bg-slate-200 px-3 py-2 text-sm font-medium text-slate-900" onClick={() => setMode("register")}>Registro</button>
      </div>
      <div className="mt-4 grid gap-3">
        <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" placeholder="Usuario" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
        <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        {mode === "register" ? (
          <>
            <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" placeholder="Nombre" value={form.nombre_mostrar} onChange={(e) => setForm({ ...form, nombre_mostrar: e.target.value, first_name: e.target.value })} />
            <input className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <select className="rounded-lg border border-slate-300 px-3 py-2 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100" value={form.idioma} onChange={(e) => setForm({ ...form, idioma: e.target.value })}><option value="es">Espanol</option><option value="en">English</option></select>
          </>
        ) : null}
        <button className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white" onClick={() => mode === "login" ? onLogin(form) : onRegister(form)}>{mode === "login" ? "Entrar" : "Crear cuenta"}</button>
      </div>
    </section>
  );
}
