import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv, os
from datetime import datetime

# ===================== Config =====================
APP_TITLE = "Expense Tracker — Multi User"
DATA_DIR = "user_data"
DATE_FMT = "%Y-%m-%d"
HIGH_EXPENSE_THRESHOLD = 100.0  # row highlight threshold

os.makedirs(DATA_DIR, exist_ok=True)

# ===================== Small Utilities =====================
def safe_name(name: str) -> str:
    return "".join(ch for ch in name if ch.isalnum() or ch in ("_", "-")).strip() or "user"

def csv_path(person: str) -> str:
    return os.path.join(DATA_DIR, f"expenses_{safe_name(person)}.csv")

def ensure_csv(path: str):
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(["Date", "Category", "Amount", "Description"])

def read_rows(path: str):
    rows = []
    if os.path.exists(path):
        with open(path, "r", newline="") as f:
            rd = csv.reader(f)
            next(rd, None)
            for r in rd: rows.append(r)
    return rows

def write_rows(path: str, rows):
    with open(path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["Date", "Category", "Amount", "Description"])
        wr.writerows(rows)

def valid_date(s: str) -> bool:
    try:
        datetime.strptime(s, DATE_FMT)
        return True
    except Exception:
        return False

def try_float(s: str):
    try:
        return float(s)
    except Exception:
        return None

# ===================== ToolTip =====================
class ToolTip:
    def __init__(self, widget, text: str, delay=500):
        self.widget, self.text, self.delay = widget, text, delay
        self._id = None
        self._tip = None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<ButtonPress>", self._leave, add="+")

    def _enter(self, _): self._schedule()
    def _leave(self, _): self._unschedule(); self._hide()
    def _schedule(self):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show)
    def _unschedule(self):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
    def _show(self):
        if self._tip: return
        x, y, *_ = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 18
        y += self.widget.winfo_rooty() + 20
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self._tip, text=self.text, background="#ffffe0",
                       relief="solid", borderwidth=1, font=("Segoe UI", 9))
        lbl.pack(ipadx=6, ipady=4)
    def _hide(self):
        if self._tip:
            self._tip.destroy()
            self._tip = None

# ===================== Hover helper =====================
def make_hover(btn: tk.Button, normal: str, hover: str):
    def _in(_): btn.configure(bg=hover)
    def _out(_): btn.configure(bg=normal)
    btn.bind("<Enter>", _in, add="+")
    btn.bind("<Leave>", _out, add="+")
    return btn

# ===================== Main App (single Tk with frame swap) =====================
class ExpenseTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1040x720")
        self.minsize(920, 640)

        # ttk look
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TLabelframe.Label", font=("Segoe UI Semibold", 10))

        self.person = None
        self.file = None
        self.budget = None

        # container for swapping screens
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.login_frame = None
        self.tracker_frame = None

        self.show_login()

    # ---------- Screens ----------
    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def show_login(self):
        self.clear_container()
        self.login_frame = ttk.Frame(self.container, padding=16)
        # pack with fill and expand so it fills the root window and redraws properly
        self.login_frame.pack(fill="both", expand=True)

        title = ttk.Label(self.login_frame, text="Who’s using the tracker?",
                          font=("Segoe UI Semibold", 14))
        title.pack(pady=(0, 10))

        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(self.login_frame, textvariable=self.name_var, width=28)
        name_entry.pack(pady=(0, 8))
        name_entry.focus_set()

        # create button, apply hover, then pack (avoid chaining .pack on helper return)
        btn = tk.Button(self.login_frame, text="Continue →", fg="white",
                        bg="#2563eb", activebackground="#1d4ed8",
                        relief="flat", command=self._continue_from_login)
        make_hover(btn, "#2563eb", "#1d4ed8")
        btn.pack(ipadx=10, ipady=6)

        ToolTip(btn, "Create or open a profile for this name")

        ttk.Label(self.login_frame, text="Tip: Type a new name to create a new profile.",
                  foreground="#666").pack(pady=(8, 0))

        # bind return to move forward
        self.bind("<Return>", lambda _e: self._continue_from_login())

        # force a quick UI update so window renders correctly immediately
        self.update_idletasks()
        self.update()

    def _continue_from_login(self):
        name = (self.name_var.get() or "").strip()
        if not name:
            messagebox.showwarning("Name required", "Please enter a name.")
            return
        self.person = name
        self.file = csv_path(name)
        ensure_csv(self.file)
        self.unbind("<Return>")
        self.show_tracker()

    def show_tracker(self):
        self.clear_container()
        self.tracker_frame = TrackerFrame(self.container, self.person, self.file,
                                          on_back=self.show_login)
        self.tracker_frame.pack(fill="both", expand=True)

# ===================== Tracker Frame =====================
class TrackerFrame(ttk.Frame):
    def __init__(self, parent, person, file, on_back):
        super().__init__(parent, padding=8)
        self.person = person
        self.file = file
        self.on_back = on_back

        # state
        self.sort_state = {"Date": True, "Category": True, "Amount": True, "Description": True}  # True asc
        self.budget = None

        # Top bar
        top = ttk.Frame(self); top.pack(fill="x", pady=(4, 6))
        ttk.Label(top, text=f"👤 {self.person}", font=("Segoe UI Semibold", 12)).pack(side="left")

        back_btn = tk.Button(top, text="← Switch Person", fg="white", bg="#6b7280",
                             activebackground="#4b5563", relief="flat", command=self._go_back)
        make_hover(back_btn, "#6b7280", "#4b5563").pack(side="right", ipadx=10, ipady=4, padx=(6, 0))
        ToolTip(back_btn, "Go back to the name screen")

        # Budget controls
        bud_wrap = ttk.Frame(top); bud_wrap.pack(side="right")
        ttk.Label(bud_wrap, text="Monthly Budget:").pack(side="left", padx=(0, 6))
        self.bud_var = tk.StringVar()
        bud_entry = ttk.Entry(bud_wrap, textvariable=self.bud_var, width=10); bud_entry.pack(side="left")
        set_btn = tk.Button(bud_wrap, text="Set", fg="white", bg="#059669", relief="flat", command=self.set_budget)
        make_hover(set_btn, "#059669", "#047857").pack(side="left", padx=(6, 0))
        ToolTip(set_btn, "Set / update monthly budget")

        self.bud_status = tk.StringVar(value="No budget set")
        ttk.Label(top, textvariable=self.bud_status, foreground="#555").pack(side="right", padx=(10, 0))

        # Tabs
        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=6, pady=6)
        tab_manage = ttk.Frame(nb, padding=10); nb.add(tab_manage, text="Add / Edit")
        tab_view = ttk.Frame(nb, padding=10); nb.add(tab_view, text="Browse")
        tab_reports = ttk.Frame(nb, padding=10); nb.add(tab_reports, text="Reports")

        # ==== Add/Edit Tab ====
        self.date_var = tk.StringVar(value=datetime.now().strftime(DATE_FMT))
        self.cat_var = tk.StringVar()
        self.amt_var = tk.StringVar()
        self.desc_var = tk.StringVar()

        form = ttk.Frame(tab_manage); form.pack(fill="x")
        ttk.Label(form, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.date_var, width=16).grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Category").grid(row=0, column=2, sticky="w", padx=(20, 8))
        ttk.Entry(form, textvariable=self.cat_var, width=18).grid(row=0, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Amount").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.amt_var, width=16).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Description").grid(row=1, column=2, sticky="w", padx=(20, 8))
        ttk.Entry(form, textvariable=self.desc_var, width=40).grid(row=1, column=3, sticky="we", pady=4)

        btns = ttk.Frame(tab_manage); btns.pack(fill="x", pady=(8, 0))
        add_btn = tk.Button(btns, text="＋ Add (Ctrl+N)", fg="white", bg="#2563eb",
                            activebackground="#1d4ed8", relief="flat", command=self.on_add)
        make_hover(add_btn, "#2563eb", "#1d4ed8").pack(side="left", ipadx=12, ipady=6, padx=(0, 6))
        ToolTip(add_btn, "Add a new expense")

        upd_btn = tk.Button(btns, text="✎ Update", fg="white", bg="#f59e0b",
                            activebackground="#d97706", relief="flat", command=self.on_update_from_selection)
        make_hover(upd_btn, "#f59e0b", "#d97706").pack(side="left", ipadx=12, ipady=6, padx=6)
        ToolTip(upd_btn, "Load selected row into fields, remove it, then click Add")

        del_btn = tk.Button(btns, text="🗑 Delete (Del)", fg="white", bg="#ef4444",
                            activebackground="#dc2626", relief="flat", command=self.on_delete)
        make_hover(del_btn, "#ef4444", "#dc2626").pack(side="left", ipadx=12, ipady=6, padx=6)
        ToolTip(del_btn, "Delete selected expense")

        exp_btn = tk.Button(btns, text="⇩ Export CSV (Ctrl+E)", fg="white", bg="#7c3aed",
                            activebackground="#6d28d9", relief="flat", command=self.on_export)
        make_hover(exp_btn, "#7c3aed", "#6d28d9").pack(side="left", ipadx=12, ipady=6, padx=6)
        ToolTip(exp_btn, "Export current user's data")

        # ==== Browse Tab ====
        filters = ttk.Labelframe(tab_view, text="Quick Filters", padding=10); filters.pack(fill="x")
        self.f_cat = tk.StringVar(); self.f_date = tk.StringVar(); self.f_search = tk.StringVar()

        ttk.Label(filters, text="Category").grid(row=0, column=0, sticky="w")
        ttk.Entry(filters, textvariable=self.f_cat, width=16).grid(row=0, column=1, padx=6, pady=2)

        ttk.Label(filters, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w")
        ttk.Entry(filters, textvariable=self.f_date, width=16).grid(row=0, column=3, padx=6, pady=2)

        ttk.Label(filters, text="Search Description").grid(row=0, column=4, sticky="w")
        ent_search = ttk.Entry(filters, textvariable=self.f_search, width=28)
        ent_search.grid(row=0, column=5, padx=6, pady=2)

        apply_btn = tk.Button(filters, text="Apply", fg="white", bg="#0ea5e9",
                              activebackground="#0284c7", relief="flat", command=self.reload_tree)
        make_hover(apply_btn, "#0ea5e9", "#0284c7").grid(row=0, column=6, padx=(6, 0), ipadx=12)

        ent_search.bind("<KeyRelease>", lambda _e: self.reload_tree())  # live search

        tree_wrap = ttk.Frame(tab_view); tree_wrap.pack(fill="both", expand=True, pady=(10, 0))
        self.columns = ("Date", "Category", "Amount", "Description")
        self.tree = ttk.Treeview(tree_wrap, columns=self.columns, show="headings", selectmode="browse")
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_col(c))
            self.tree.column(col, width=150 if col != "Description" else 360, stretch=True)
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set); vsb.pack(side="right", fill="y")

        self.tree.tag_configure("odd", background="#fafafa")
        self.tree.tag_configure("even", background="#ffffff")
        self.tree.tag_configure("high", background="#fde2e2")

        # ==== Reports Tab ====
        rp = ttk.Frame(tab_reports); rp.pack(fill="x")
        sum_btn = tk.Button(rp, text="📅 Monthly Summary", fg="white", bg="#16a34a",
                            activebackground="#15803d", relief="flat", command=self.on_monthly_summary)
        make_hover(sum_btn, "#16a34a", "#15803d").pack(side="left", ipadx=12, ipady=6, padx=(0, 8))
        ToolTip(sum_btn, "Show total spend per YYYY-MM")

        high_btn = tk.Button(rp, text="🏷 Highest Category", fg="white", bg="#f59e0b",
                             activebackground="#d97706", relief="flat", command=self.on_highest_category)
        make_hover(high_btn, "#f59e0b", "#d97706").pack(side="left", ipadx=12, ipady=6, padx=8)
        ToolTip(high_btn, "Find the category with maximum spend")

        total_btn = tk.Button(rp, text="Σ Total Expenses", fg="white", bg="#2563eb",
                              activebackground="#1d4ed8", relief="flat", command=self.on_total)
        make_hover(total_btn, "#2563eb", "#1d4ed8").pack(side="left", ipadx=12, ipady=6, padx=8)
        ToolTip(total_btn, "Show total of all expenses")

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var, padding=(10, 6)).pack(side="bottom", fill="x")

        # Load initial data and shortcuts
        self.reload_tree()
        self.bind_all("<Control-n>", lambda _e: self.on_add())
        self.bind_all("<Delete>", lambda _e: self.on_delete())
        self.bind_all("<Control-e>", lambda _e: self.on_export())
        self.bind_all("<Control-f>", lambda _e: ent_search.focus_set())

    # ---------- Helpers / Data ----------
    def rows(self):
        return read_rows(self.file)

    def save_rows(self, rows):
        write_rows(self.file, rows)

    def status(self, msg): self.status_var.set(msg)

    # ---------- Actions ----------
    def on_add(self):
        d = self.date_var.get().strip()
        c = self.cat_var.get().strip()
        a = self.amt_var.get().strip()
        desc = self.desc_var.get().strip()

        if not d or not c or not a:
            messagebox.showwarning("Missing data", "Date, Category and Amount are required.")
            return
        if not valid_date(d):
            messagebox.showwarning("Invalid date", f"Please use {DATE_FMT}.")
            return
        f = try_float(a)
        if f is None:
            messagebox.showwarning("Invalid amount", "Amount must be numeric.")
            return

        with open(self.file, "a", newline="") as fcsv:
            csv.writer(fcsv).writerow([d, c, f, desc])

        self.date_var.set(datetime.now().strftime(DATE_FMT))
        self.cat_var.set(""); self.amt_var.set(""); self.desc_var.set("")
        self.reload_tree()
        self.check_budget()
        self.status("Added expense.")

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a row to delete.")
            return
        if not messagebox.askyesno("Confirm delete", "Delete the selected expense?"):
            return
        vals = self.tree.item(sel[0], "values")
        rows = self.rows()
        rows2 = [r for r in rows if tuple(map(str, r)) != tuple(map(str, vals))]
        self.save_rows(rows2)
        self.reload_tree()
        self.status("Deleted expense.")

    def on_update_from_selection(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a row to update.")
            return
        vals = self.tree.item(sel[0], "values")
        # load to fields
        self.date_var.set(vals[0]); self.cat_var.set(vals[1])
        self.amt_var.set(vals[2]); self.desc_var.set(vals[3])
        # remove original
        rows = self.rows()
        rows2 = [r for r in rows if tuple(map(str, r)) != tuple(map(str, vals))]
        self.save_rows(rows2)
        self.reload_tree()
        self.status("Loaded row into fields. Edit and click Add to save changes.")

    def on_export(self):
        dest = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")],
                                            title="Export CSV")
        if not dest: return
        with open(self.file, "r") as src, open(dest, "w") as out:
            out.write(src.read())
        self.status(f"Exported to {dest}")

    def on_total(self):
        total = sum(float(r[2]) for r in self.rows() or [])
        messagebox.showinfo("Total Expenses", f"Total: {total:.2f}")

    def on_monthly_summary(self):
        summary = {}
        for d, _c, a, _desc in self.rows():
            ym = d[:7]
            summary[ym] = summary.get(ym, 0.0) + float(a)
        if not summary:
            messagebox.showinfo("Monthly Summary", "No data.")
            return
        lines = "\n".join(f"{k}: {v:.2f}" for k, v in sorted(summary.items()))
        messagebox.showinfo("Monthly Summary", lines)

    def on_highest_category(self):
        cat = {}
        for _d, c, a, _desc in self.rows():
            cat[c] = cat.get(c, 0.0) + float(a)
        if not cat:
            messagebox.showinfo("Highest Category", "No data.")
            return
        k = max(cat, key=cat.get)
        messagebox.showinfo("Highest Category", f"{k}: {cat[k]:.2f}")

    def set_budget(self):
        raw = self.bud_var.get().strip()
        f = try_float(raw)
        if f is None:
            messagebox.showwarning("Invalid budget", "Enter a valid number.")
            return
        self.budget = f
        self.update_budget_status()
        self.status(f"Budget set to {f:.2f}")

    def check_budget(self):
        if self.budget is None: return
        total = sum(float(r[2]) for r in self.rows())
        if total > self.budget:
            messagebox.showwarning("Budget Alert",
                                   f"Budget exceeded!\nTotal: {total:.2f} > {self.budget:.2f}")
        self.update_budget_status()

    def update_budget_status(self):
        if self.budget is None:
            self.bud_status.set("No budget set"); return
        total = sum(float(r[2]) for r in self.rows())
        remaining = self.budget - total
        self.bud_status.set(f"Spent: {total:.2f} | Remaining: {remaining:.2f}")

    # ---------- Table ----------
    def reload_tree(self):
        for iid in self.tree.get_children(): self.tree.delete(iid)
        rows = self.rows()

        # Apply filters
        fcat = self.f_cat.get().strip().lower()
        fdate = self.f_date.get().strip()
        fsearch = self.f_search.get().strip().lower()

        def keep(r):
            d, c, _a, desc = r
            if fcat and c.lower() != fcat: return False
            if fdate and d != fdate: return False
            if fsearch and fsearch not in (desc or "").lower(): return False
            return True

        rows = [r for r in rows if keep(r)]

        for i, r in enumerate(rows):
            tags = ["even" if i % 2 == 0 else "odd"]
            try:
                if float(r[2]) > HIGH_EXPENSE_THRESHOLD:
                    tags.append("high")
            except Exception:
                pass
            self.tree.insert("", "end", values=r, tags=tuple(tags))
        self.status(f"Loaded {len(rows)} item(s).")

    def sort_by_col(self, col):
        items = [(self.tree.set(i, col), i) for i in self.tree.get_children("")]
        asc = self.sort_state.get(col, True)

        if col == "Amount":
            def conv(x):
                try: return float(x)
                except: return float("inf")
        elif col == "Date":
            def conv(x):
                try: return datetime.strptime(x, DATE_FMT)
                except: return datetime.max
        else:
            def conv(x): return x.lower()

        items.sort(key=lambda t: conv(t[0]), reverse=not asc)
        for idx, (_v, iid) in enumerate(items):
            self.tree.move(iid, "", idx)
        self.sort_state[col] = not asc
        self.status(f"Sorted by {col} ({'asc' if asc else 'desc'}).")

    def _go_back(self):
        if messagebox.askyesno("Switch person", "Return to name screen?"):
            self.master.master.focus_set()
            self.on_back()

# ===================== Entry =====================
if __name__ == "__main__":
    app = ExpenseTrackerApp()
    app.mainloop()
