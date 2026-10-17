import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";

const EMPTY_FORM = { name: "", category: "Produce", quantity: 1, unit: "pcs", expiry_date: "" };

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((new Date(`${dateStr}T00:00:00`) - today) / 86_400_000);
}

function ExpiryBadge({ date }) {
  const d = daysUntil(date);
  if (d === null) return <span className="badge badge-none">No expiry</span>;
  if (d < 0) return <span className="badge badge-expired">Expired {-d}d ago</span>;
  if (d === 0) return <span className="badge badge-soon">Expires today</span>;
  if (d <= 3) return <span className="badge badge-soon">{d}d left</span>;
  return <span className="badge badge-ok">{d}d left</span>;
}

function StatCard({ label, value, tone }) {
  return (
    <div className={`stat stat-${tone}`}>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

function ItemForm({ categories, initial, onSubmit, onCancel, submitLabel }) {
  const [form, setForm] = useState(initial);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = (e) => {
    e.preventDefault();
    onSubmit({ ...form, quantity: Number(form.quantity), expiry_date: form.expiry_date || null });
  };

  return (
    <form className="item-form" onSubmit={submit}>
      <label>
        Name
        <input required maxLength={120} value={form.name} onChange={set("name")} placeholder="e.g. Basmati rice" />
      </label>
      <label>
        Category
        <select value={form.category} onChange={set("category")}>
          {categories.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </label>
      <label className="narrow">
        Qty
        <input type="number" min="0" step="any" value={form.quantity} onChange={set("quantity")} />
      </label>
      <label className="narrow">
        Unit
        <input required maxLength={20} value={form.unit} onChange={set("unit")} />
      </label>
      <label>
        Expires
        <input type="date" value={form.expiry_date ?? ""} onChange={set("expiry_date")} />
      </label>
      <div className="form-actions">
        <button type="submit" className="btn btn-primary">{submitLabel}</button>
        {onCancel && (
          <button type="button" className="btn" onClick={onCancel}>Cancel</button>
        )}
      </div>
    </form>
  );
}

export default function App() {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState(["Other"]);
  const [filter, setFilter] = useState({ category: "", search: "" });
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [list, s] = await Promise.all([api.listItems(filter), api.stats()]);
      setItems(list);
      setStats(s);
      setError("");
    } catch (e) {
      setError(`Could not reach the API (${e.message})`);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => {});
    api.health().then((h) => setVersion(h.version)).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const run = async (fn) => {
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e.message);
    }
  };

  const adjustQty = (item, delta) =>
    run(() => api.updateItem(item.id, { quantity: Math.max(0, item.quantity + delta) }));

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <img src="/favicon.svg" alt="" width="36" height="36" />
          <div>
            <h1>PantryPal</h1>
            <p>Know what's in your kitchen before it goes off.</p>
          </div>
        </div>
        {version && <span className="version">v{version.slice(0, 7)}</span>}
      </header>

      {stats && (
        <section className="stats">
          <StatCard label="Items tracked" value={stats.total_items} tone="neutral" />
          <StatCard label="Expiring in 3 days" value={stats.expiring_soon} tone="warn" />
          <StatCard label="Expired" value={stats.expired} tone="bad" />
          <StatCard label="Categories" value={Object.keys(stats.by_category).length} tone="good" />
        </section>
      )}

      <section className="card">
        <h2>Add an item</h2>
        <ItemForm
          key="create"
          categories={categories}
          initial={EMPTY_FORM}
          submitLabel="Add to pantry"
          onSubmit={(data) => run(() => api.createItem(data))}
        />
      </section>

      {error && <div className="error" role="alert">{error}</div>}

      <section className="card">
        <div className="list-header">
          <h2>Your pantry</h2>
          <div className="filters">
            <input
              type="search"
              placeholder="Search…"
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
            />
            <select value={filter.category} onChange={(e) => setFilter({ ...filter, category: e.target.value })}>
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <p className="muted">Loading…</p>
        ) : items.length === 0 ? (
          <p className="muted empty">Nothing here yet — add your first item above.</p>
        ) : (
          <ul className="items">
            {items.map((item) =>
              editing === item.id ? (
                <li key={item.id} className="item editing">
                  <ItemForm
                    categories={categories}
                    initial={{ ...item, expiry_date: item.expiry_date ?? "" }}
                    submitLabel="Save"
                    onCancel={() => setEditing(null)}
                    onSubmit={(data) =>
                      run(async () => {
                        await api.updateItem(item.id, data);
                        setEditing(null);
                      })
                    }
                  />
                </li>
              ) : (
                <li key={item.id} className="item">
                  <div className="item-main">
                    <span className="item-name">{item.name}</span>
                    <span className="chip">{item.category}</span>
                  </div>
                  <div className="qty">
                    <button className="btn btn-icon" aria-label="Decrease" onClick={() => adjustQty(item, -1)}>−</button>
                    <span>
                      {item.quantity} {item.unit}
                    </span>
                    <button className="btn btn-icon" aria-label="Increase" onClick={() => adjustQty(item, 1)}>+</button>
                  </div>
                  <ExpiryBadge date={item.expiry_date} />
                  <div className="item-actions">
                    <button className="btn" onClick={() => setEditing(item.id)}>Edit</button>
                    <button className="btn btn-danger" onClick={() => run(() => api.deleteItem(item.id))}>Delete</button>
                  </div>
                </li>
              ),
            )}
          </ul>
        )}
      </section>

      <footer className="footer">PantryPal · FastAPI + PostgreSQL + React · DevOps capstone</footer>
    </div>
  );
}
