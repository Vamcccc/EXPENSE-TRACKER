import os, tkinter as tk, hashlib, json, datetime, platform, subprocess
from tkinter import messagebox, ttk, filedialog
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False; plt = None

DEFAULT_CATEGORIES = {"Rent": [], "Food": [], "Bills": [], "Transportation": [], "Clothes": []}

def load_data():
    try:
        if os.path.exists("users.json"):
            with open("users.json") as f: data = json.load(f)
            for user in data.get("users", {}).values():
                for cat in DEFAULT_CATEGORIES: user["expenses"].setdefault(cat, [])
                user.setdefault("balance", 0.0)
            return data
    except Exception as e: print(f"Error loading data: {e}")
    return {"users": {}}

def save_data(data):
    try:
        with open("users.json", "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print(f"Error saving data: {e}")

def add_expense(expenses, category, amount, desc=""):
    expenses[category].append({"amount": amount, "description": desc, "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

def create_pie_chart(expenses, balance, user_id):
    if not MATPLOTLIB_AVAILABLE: return None
    labels, amounts = [], []
    for cat, entries in expenses.items():
        total = sum(e["amount"] for e in entries)
        if total > 0: labels.append(f"{cat}: ₹{total:.2f}"); amounts.append(total)
    if balance > 0: labels.append(f"Balance: ₹{balance:.2f}"); amounts.append(balance)
    if not amounts: return None
    try:
        plt.figure(figsize=(7,7))
        wedges, _, _ = plt.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title(f"Expense & Balance for {user_id} (Total: ₹{sum(amounts):.2f})")
        plt.axis('equal')
        plt.legend(wedges, labels, loc="center left", bbox_to_anchor=(1,0.5))
        fname = f"{user_id}_pie.png"
        plt.savefig(fname, bbox_inches='tight'); plt.close()
        return fname
    except Exception as e:
        print(f"Pie chart error: {e}")
        return None

def open_image(path):
    try:
        if platform.system() == "Windows": os.startfile(path)
        elif platform.system() == "Darwin": subprocess.run(["open", path])
        else: subprocess.run(["xdg-open", path])
    except Exception as e:
        print(f"Open image error: {e}")

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root; root.title("Expense Tracker"); root.geometry("800x700")
        self.data = load_data()
        self.user_id = None; self.expenses = None; self.balance = 0.0; self.dark_mode = False
        self.monthly_budget = 0.0; self.show_login_page()

    def clear(self): [w.destroy() for w in self.root.winfo_children()]

    def hash_pass(self, pwd): return hashlib.sha256(pwd.encode()).hexdigest()

    def show_login_page(self):
        self.clear()
        f = tk.Frame(self.root, padx=20, pady=20); f.pack(expand=True)
        tk.Label(f, text="Login", font=("Arial", 24)).grid(row=0,column=0,columnspan=2,pady=15)
        tk.Label(f, text="User ID:").grid(row=1,column=0,sticky="e")
        self.login_user = tk.Entry(f); self.login_user.grid(row=1,column=1,pady=5)
        tk.Label(f, text="Password:").grid(row=2,column=0,sticky="e")
        self.login_pass = tk.Entry(f, show="*"); self.login_pass.grid(row=2,column=1,pady=5)
        tk.Button(f,text="Login",command=self.login).grid(row=3,column=0,columnspan=2,pady=10)
        tk.Button(f,text="Register",command=self.show_register_page).grid(row=4,column=0,columnspan=2)

    def show_register_page(self):
        self.clear()
        f = tk.Frame(self.root, padx=20, pady=20); f.pack(expand=True)
        tk.Label(f, text="Register", font=("Arial", 24)).grid(row=0,column=0,columnspan=2,pady=15)
        tk.Label(f,text="User ID:").grid(row=1,column=0,sticky="e")
        self.reg_user = tk.Entry(f); self.reg_user.grid(row=1,column=1,pady=5)
        tk.Label(f,text="Name:").grid(row=2,column=0,sticky="e")
        self.reg_name = tk.Entry(f); self.reg_name.grid(row=2,column=1,pady=5)
        tk.Label(f,text="Password:").grid(row=3,column=0,sticky="e")
        self.reg_pass = tk.Entry(f,show="*"); self.reg_pass.grid(row=3,column=1,pady=5)
        tk.Label(f,text="Initial Balance (₹):").grid(row=4,column=0,sticky="e")
        self.reg_balance = tk.Entry(f); self.reg_balance.grid(row=4,column=1,pady=5)
        tk.Button(f,text="Register",command=self.register).grid(row=5,column=0,columnspan=2,pady=10)
        tk.Button(f,text="Back",command=self.show_login_page).grid(row=6,column=0,columnspan=2)

    def login(self):
        uid, pwd = self.login_user.get().strip(), self.login_pass.get().strip()
        if not uid or not pwd: messagebox.showwarning("Input Error", "Fill all fields"); return
        user = self.data["users"].get(uid)
        if not user or user["password"] != self.hash_pass(pwd):
            messagebox.showerror("Login Failed", "Invalid credentials")
            return
        self.user_id = uid; self.expenses = user["expenses"]; self.balance = user.get("balance", 0.0)
        self.monthly_budget = user.get("monthly_budget", self.balance)
        self.show_main_page()

    def register(self):
        uid, name, pwd, bal = self.reg_user.get().strip(), self.reg_name.get().strip(), self.reg_pass.get().strip(), self.reg_balance.get().strip()
        if not uid or not name or not pwd or not bal: messagebox.showwarning("Input Error", "Fill all fields"); return
        try: bal = float(bal); assert bal >= 0
        except: messagebox.showwarning("Input Error", "Balance must be non-negative number"); return
        if uid in self.data["users"]: messagebox.showwarning("User Exists", "User ID already exists"); return
        self.data["users"][uid] = {"name": name, "password": self.hash_pass(pwd), "balance": bal,
                                   "monthly_budget": bal, "expenses": {cat: [] for cat in DEFAULT_CATEGORIES}}
        save_data(self.data)
        messagebox.showinfo("Success", "Registered! Please login.")
        self.show_login_page()

    def show_main_page(self):
        self.clear()
        user = self.data["users"][self.user_id]
        top_frame = tk.Frame(self.root); top_frame.pack(pady=10, fill='x')
        tk.Label(top_frame, text=f"Welcome, {user['name']}!", font=("Arial", 22)).pack(side='left')
        self.balance_label = tk.Label(top_frame, text=f"Balance: ₹{self.balance:.2f}", fg='green', font=("Arial", 18))
        self.balance_label.pack(side='left', padx=20)
        self.dark_btn = tk.Button(top_frame, text="Toggle Dark Mode", command=self.toggle_dark_mode)
        self.dark_btn.pack(side='right')

        budget_frame = tk.Frame(self.root); budget_frame.pack(pady=5)
        tk.Label(budget_frame, text="Set Monthly Budget (₹):").pack(side='left')
        self.budget_entry = tk.Entry(budget_frame, width=10); self.budget_entry.pack(side='left', padx=5)
        self.budget_entry.insert(0, f"{self.monthly_budget:.2f}")
        tk.Button(budget_frame, text="Set", command=self.set_budget).pack(side='left')

        self.budget_progress = ttk.Progressbar(self.root, length=300, maximum=self.monthly_budget)
        self.budget_progress.pack(pady=5)
        self.update_budget_progress()

        add_frame = tk.LabelFrame(self.root, text="Add Expense"); add_frame.pack(pady=10, fill='x', padx=10)
        tk.Label(add_frame, text="Category:").grid(row=0,column=0,padx=5,pady=5)
        self.category_var = tk.StringVar(value=next(iter(DEFAULT_CATEGORIES)))
        ttk.Combobox(add_frame, textvariable=self.category_var, values=list(DEFAULT_CATEGORIES.keys()), state='readonly').grid(row=0,column=1,padx=5,pady=5)
        tk.Label(add_frame, text="Amount (₹):").grid(row=1,column=0,padx=5,pady=5)
        self.amount_entry = tk.Entry(add_frame); self.amount_entry.grid(row=1,column=1,padx=5,pady=5)
        tk.Label(add_frame, text="Description:").grid(row=2,column=0,padx=5,pady=5)
        self.desc_entry = tk.Entry(add_frame); self.desc_entry.grid(row=2,column=1,padx=5,pady=5)
        tk.Button(add_frame, text="Add Expense", command=self.add_expense_action).grid(row=3,column=0,columnspan=2,pady=10)

        self.tree = ttk.Treeview(self.root, columns=("Category", "Amount", "Description", "Date"), show="headings", height=12)
        for col in ("Category", "Amount", "Description", "Date"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.pack(pady=10, padx=10, fill='both', expand=True)

        btn_frame = tk.Frame(self.root); btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Delete Selected Expense", command=self.delete_selected).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Export to CSV", command=self.export_csv).pack(side='left', padx=10)
        tk.Button(btn_frame, text="View Pie Chart", command=self.show_pie_chart).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Logout", command=self.logout).pack(side='left', padx=10)

        self.load_expenses()
        self.apply_theme()

    def update_budget_progress(self):
        spent = sum(sum(e["amount"] for e in entries) for entries in self.expenses.values())
        self.budget_progress["maximum"] = self.monthly_budget if self.monthly_budget > 0 else 1
        self.budget_progress["value"] = spent
        self.budget_progress.config(style="red.Horizontal.TProgressbar" if spent > self.monthly_budget else "green.Horizontal.TProgressbar")

    def set_budget(self):
        try:
            val = float(self.budget_entry.get())
            if val < 0: raise ValueError
            self.monthly_budget = val
            self.data["users"][self.user_id]["monthly_budget"] = val
            save_data(self.data)
            self.update_budget_progress()
        except:
            messagebox.showwarning("Input Error", "Invalid budget amount")

    def add_expense_action(self):
        try:
            amt = float(self.amount_entry.get())
            if amt <= 0: raise ValueError
        except:
            messagebox.showwarning("Input Error", "Amount must be positive number")
            return
        cat, desc = self.category_var.get(), self.desc_entry.get().strip()
        add_expense(self.expenses, cat, amt, desc)
        self.balance -= amt
        self.data["users"][self.user_id]["balance"] = self.balance
        save_data(self.data)
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.load_expenses()
        self.balance_label.config(text=f"Balance: ₹{self.balance:.2f}")
        self.update_budget_progress()

    def load_expenses(self):
        self.tree.delete(*self.tree.get_children())
        for cat, entries in self.expenses.items():
            for e in entries:
                self.tree.insert("", "end", values=(cat, f"₹{e['amount']:.2f}", e.get("description", ""), e["date"]))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Delete Expense", "Select an expense first")
            return
        item = self.tree.item(sel[0])
        cat, amt_str, desc, date = item["values"]
        amt = float(amt_str.replace("₹", ""))
        entries = self.expenses.get(cat, [])
        for i, e in enumerate(entries):
            if abs(e["amount"] - amt) < 0.001 and e.get("description","") == desc and e["date"] == date:
                del entries[i]
                self.balance += amt
                self.data["users"][self.user_id]["balance"] = self.balance
                save_data(self.data)
                self.load_expenses()
                self.balance_label.config(text=f"Balance: ₹{self.balance:.2f}")
                self.update_budget_progress()
                return
        messagebox.showerror("Delete Error", "Expense not found")

    def export_csv(self):
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if not fname: return
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write("Category,Amount,Description,Date\n")
                for cat, entries in self.expenses.items():
                    for e in entries:
                        desc = e.get("description","").replace(",", ";")
                        f.write(f"{cat},{e['amount']},{desc},{e['date']}\n")
            messagebox.showinfo("Export CSV", f"Data exported to {fname}")
        except Exception as e:
            messagebox.showerror("Export CSV", f"Failed to export: {e}")

    def show_pie_chart(self):
        fname = create_pie_chart(self.expenses, self.balance, self.user_id)
        if fname: open_image(fname)
        else: messagebox.showinfo("Pie Chart", "No data or matplotlib not available")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        bg, fg = ("#222", "#eee") if self.dark_mode else ("#fff", "#000")
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg)
        style.configure("Treeview.Heading", background=bg, foreground=fg)
        style.configure("red.Horizontal.TProgressbar", troughcolor=bg, background='red')
        style.configure("green.Horizontal.TProgressbar", troughcolor=bg, background='green')
        self.root.configure(bg=bg)
        for w in self.root.winfo_children():
            try:
                w.configure(bg=bg, fg=fg)
            except: pass
        self.tree.tag_configure("evenrow", background=bg)
        self.tree.tag_configure("oddrow", background=bg)
        self.balance_label.config(fg="lime" if self.balance >= 0 else "red")

    def logout(self):
        self.user_id = None; self.expenses = None; self.balance = 0.0
        self.show_login_page()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()
