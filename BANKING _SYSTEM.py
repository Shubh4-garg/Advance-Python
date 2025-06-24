import json
import os
from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
from tkinter import ttk

class Account(ABC):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0):
        self._account_number = account_number
        self._account_holder_id = account_holder_id
        self._balance = initial_balance

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def account_holder_id(self) -> str:
        return self._account_holder_id

    @abstractmethod
    def deposit(self, amount: float) -> bool:
        pass

    @abstractmethod
    def withdraw(self, amount: float) -> bool:
        pass

    def display_details(self) -> str:
        return f"Acc No: {self._account_number}, Balance: ${self._balance:.2f}"

    def to_dict(self) -> dict:
        return {
            'account_number': self._account_number,
            'account_holder_id': self._account_holder_id,
            'balance': self._balance
        }

class SavingsAccount(Account):
    def __init__(self, account_number: str, account_holder_id: str,
                 initial_balance: float = 0.0, interest_rate: float = 0.01):
        super().__init__(account_number, account_holder_id, initial_balance)
        self._interest_rate = interest_rate

    @property
    def interest_rate(self) -> float:
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value: float):
        if value >= 0:
            self._interest_rate = value

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self._balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or amount > self._balance:
            return False
        self._balance -= amount
        return True

    def apply_interest(self):
        self._balance += self._balance * self._interest_rate

    def display_details(self) -> str:
        base = super().display_details()
        return f"{base}, Type: Savings, Interest Rate: {self._interest_rate:.2%}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({'type': 'savings', 'interest_rate': self._interest_rate})
        return data

class CheckingAccount(Account):
    def __init__(self, account_number: str, account_holder_id: str,
                 initial_balance: float = 0.0, overdraft_limit: float = 0.0):
        super().__init__(account_number, account_holder_id, initial_balance)
        self._overdraft_limit = overdraft_limit

    @property
    def overdraft_limit(self) -> float:
        return self._overdraft_limit

    @overdraft_limit.setter
    def overdraft_limit(self, value: float):
        if value >= 0:
            self._overdraft_limit = value

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self._balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0:
            return False
        if self._balance - amount >= -self._overdraft_limit:
            self._balance -= amount
            return True
        return False

    def display_details(self) -> str:
        base = super().display_details()
        return f"{base}, Type: Checking, Overdraft Limit: ${self._overdraft_limit:.2f}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({'type': 'checking', 'overdraft_limit': self._overdraft_limit})
        return data

class Customer:
    def __init__(self, customer_id: str, name: str, address: str):
        self._customer_id = customer_id
        self._name = name
        self._address = address
        self._account_numbers = []

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str):
        self._address = value

    @property
    def account_numbers(self) -> list[str]:
        return self._account_numbers.copy()

    def add_account_number(self, account_number: str):
        if account_number not in self._account_numbers:
            self._account_numbers.append(account_number)

    def remove_account_number(self, account_number: str):
        if account_number in self._account_numbers:
            self._account_numbers.remove(account_number)

    def display_details(self) -> str:
        return (f"Customer ID: {self._customer_id}, Name: {self._name}, "
                f"Address: {self._address}, Accounts: {len(self._account_numbers)}")

    def to_dict(self) -> dict:
        return {
            'customer_id': self._customer_id,
            'name': self._name,
            'address': self._address,
            'account_numbers': self._account_numbers
        }

class Bank:
    def __init__(self, customer_file='customers.json', account_file='accounts.json'):
        self._customers = {}
        self._accounts = {}
        self._customer_file = customer_file
        self._account_file = account_file
        self._load_data()

    def _load_data(self):
        try:
            with open(self._customer_file, 'r') as f:
                customers_data = json.load(f)
                for data in customers_data:
                    customer = Customer(data['customer_id'], data['name'], data['address'])
                    customer._account_numbers = data['account_numbers']
                    self._customers[customer.customer_id] = customer
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {self._customer_file}. Starting with no customers.")

        try:
            with open(self._account_file, 'r') as f:
                accounts_data = json.load(f)
                for data in accounts_data:
                    if data['type'] == 'savings':
                        account = SavingsAccount(
                            data['account_number'],
                            data['account_holder_id'],
                            data['balance'],
                            data['interest_rate']
                        )
                    elif data['type'] == 'checking':
                        account = CheckingAccount(
                            data['account_number'],
                            data['account_holder_id'],
                            data['balance'],
                            data['overdraft_limit']
                        )
                    self._accounts[account.account_number] = account
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {self._account_file}. Starting with no accounts.")

    def _save_data(self):
        with open(self._customer_file, 'w') as f:
            json.dump([c.to_dict() for c in self._customers.values()], f, indent=2)
        with open(self._account_file, 'w') as f:
            json.dump([a.to_dict() for a in self._accounts.values()], f, indent=2)

    def add_customer(self, customer: Customer) -> bool:
        if customer.customer_id in self._customers:
            return False
        self._customers[customer.customer_id] = customer
        self._save_data()
        return True

    def remove_customer(self, customer_id: str) -> bool:
        customer = self._customers.get(customer_id)
        if not customer or customer.account_numbers:
            return False
        del self._customers[customer_id]
        self._save_data()
        return True

    def _generate_account_number(self) -> str:
        existing_nums = [int(acc[4:]) for acc in self._accounts.keys() if acc.startswith('ACCT')]
        next_num = max(existing_nums) + 1 if existing_nums else 1
        return f"ACCT{next_num:06d}"

    def create_account(self, customer_id: str, account_type: str,
                      initial_balance: float = 0.0, **kwargs) -> Account | None:
        if customer_id not in self._customers:
            return None
        account_number = self._generate_account_number()
        account = None
        if account_type.lower() == 'savings':
            interest_rate = kwargs.get('interest_rate', 0.01)
            account = SavingsAccount(account_number, customer_id, initial_balance, interest_rate)
        elif account_type.lower() == 'checking':
            overdraft_limit = kwargs.get('overdraft_limit', 0.0)
            account = CheckingAccount(account_number, customer_id, initial_balance, overdraft_limit)
        else:
            return None
        self._accounts[account_number] = account
        self._customers[customer_id].add_account_number(account_number)
        self._save_data()
        return account

    def deposit(self, account_number: str, amount: float) -> bool:
        account = self._accounts.get(account_number)
        if not account:
            return False
        success = account.deposit(amount)
        if success:
            self._save_data()
        return success

    def withdraw(self, account_number: str, amount: float) -> bool:
        account = self._accounts.get(account_number)
        if not account:
            return False
        success = account.withdraw(amount)
        if success:
            self._save_data()
        return success

    def transfer_funds(self, from_acc_num: str, to_acc_num: str, amount: float) -> bool:
        from_acc = self._accounts.get(from_acc_num)
        to_acc = self._accounts.get(to_acc_num)
        if not from_acc or not to_acc:
            return False
        if from_acc.withdraw(amount):
            if to_acc.deposit(amount):
                self._save_data()
                return True
            else:
                from_acc.deposit(amount)
        return False

    def get_customer_accounts(self, customer_id: str) -> list[Account]:
        customer = self._customers.get(customer_id)
        if not customer:
            return []
        return [self._accounts[acc_num] for acc_num in customer.account_numbers
                if acc_num in self._accounts]

    def display_all_customers(self) -> list[str]:
        return [customer.display_details() for customer in self._customers.values()]

    def display_all_accounts(self) -> list[str]:
        return [account.display_details() for account in self._accounts.values()]

    def apply_all_interest(self):
        for account in self._accounts.values():
            if isinstance(account, SavingsAccount):
                account.apply_interest()
        self._save_data()

class BankGUI:
    def __init__(self, master):
        self.master = master
        master.title("Vibrant Banking System")
        master.geometry("750x750")
        master.resizable(True, True)

        self.colors = {
            "primary_bg": "#ADD8E6",
            "secondary_bg": "#F0F8FF",
            "button_bg": "#4682B4",
            "button_active_bg": "#5F9EA0",
            "text_color": "#2F4F4F",
            "header_color": "#00008B",
            "accent_color": "#FFD700",
            "frame_bg": "#B0E0E6",
            "success_color": "#228B22",
            "error_color": "#B22222",
            "white": "#FFFFFF"
        }

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('TButton', font=('Arial', 10, 'bold'),
                             background=self.colors['button_bg'], foreground=self.colors['white'],
                             padding=6, borderwidth=0)
        self.style.map('TButton',
                       background=[('active', self.colors['button_active_bg'])])

        self.style.configure('TLabel', font=('Arial', 10), background=self.colors['secondary_bg'], foreground=self.colors['text_color'])
        self.style.configure('TEntry', padding=4, fieldbackground=self.colors['white'], foreground=self.colors['text_color'])
        self.style.configure('TCombobox', padding=4, fieldbackground=self.colors['white'], foreground=self.colors['text_color'])

        self.style.configure('TNotebook', background=self.colors['primary_bg'], borderwidth=0)
        self.style.configure('TNotebook.Tab', font=('Arial', 11, 'bold'),
                             background=self.colors['button_bg'], foreground=self.colors['white'],
                             padding=[10, 5])
        self.style.map('TNotebook.Tab',
                       background=[('selected', self.colors['accent_color'])],
                       foreground=[('selected', self.colors['header_color'])])

        self.style.configure('TFrame', background=self.colors['frame_bg'])
        self.style.configure('TLabelframe', background=self.colors['secondary_bg'], borderwidth=2, relief="groove")
        self.style.configure('TLabelframe.Label', font=('Arial', 11, 'bold'), foreground=self.colors['header_color'], background=self.colors['secondary_bg'])

        master.config(bg=self.colors['primary_bg'])

        self.bank = Bank()

        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=15, pady=15)

        self.customer_frame = ttk.Frame(self.notebook, padding="15 15 15 15")
        self.notebook.add(self.customer_frame, text="Customer Management")
        self._create_customer_tab(self.customer_frame)

        self.account_frame = ttk.Frame(self.notebook, padding="15 15 15 15")
        self.notebook.add(self.account_frame, text="Account Operations")
        self._create_account_tab(self.account_frame)

        self.view_data_frame = ttk.Frame(self.notebook, padding="15 15 15 15")
        self.notebook.add(self.view_data_frame, text="View Data")
        self._create_view_data_tab(self.view_data_frame)

        ttk.Button(self.master, text="Exit Application", command=self.master.quit, style='TButton').pack(pady=15)

    def _create_customer_tab(self, parent_frame):
        ttk.Label(parent_frame, text="Customer Management", font=("Arial", 16, "bold"),
                   background=self.colors['frame_bg'], foreground=self.colors['header_color']).grid(row=0, column=0, columnspan=2, pady=15)

        add_customer_frame = ttk.LabelFrame(parent_frame, text="Add New Customer", padding="15 15 15 15")
        add_customer_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        ttk.Label(add_customer_frame, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.cid_entry = ttk.Entry(add_customer_frame, width=35)
        self.cid_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(add_customer_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cname_entry = ttk.Entry(add_customer_frame, width=35)
        self.cname_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(add_customer_frame, text="Address:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.caddress_entry = ttk.Entry(add_customer_frame, width=35)
        self.caddress_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(add_customer_frame, text="Add Customer", command=self._add_customer_action).grid(row=3, column=0, columnspan=2, pady=15)

        add_customer_frame.grid_columnconfigure(1, weight=1)
        add_customer_frame.grid_rowconfigure(3, weight=1)

        remove_customer_frame = ttk.LabelFrame(parent_frame, text="Remove Customer", padding="15 15 15 15")
        remove_customer_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        ttk.Label(remove_customer_frame, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.remove_cid_entry = ttk.Entry(remove_customer_frame, width=35)
        self.remove_cid_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(remove_customer_frame, text="Remove Customer", command=self._remove_customer_action).grid(row=1, column=0, columnspan=2, pady=15)
        remove_customer_frame.grid_columnconfigure(1, weight=1)

    def _create_account_tab(self, parent_frame):
        ttk.Label(parent_frame, text="Account Operations", font=("Arial", 16, "bold"),
                   background=self.colors['frame_bg'], foreground=self.colors['header_color']).grid(row=0, column=0, columnspan=3, pady=15)

        create_account_frame = ttk.LabelFrame(parent_frame, text="Create New Account", padding="15 15 15 15")
        create_account_frame.grid(row=1, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

        ttk.Label(create_account_frame, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.acc_cid_entry = ttk.Entry(create_account_frame, width=30)
        self.acc_cid_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(create_account_frame, text="Account Type:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.acc_type_var = tk.StringVar(create_account_frame)
        self.acc_type_combobox = ttk.Combobox(create_account_frame, textvariable=self.acc_type_var,
                                               values=["Savings", "Checking"], state="readonly", width=28)
        self.acc_type_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.acc_type_combobox.bind("<<ComboboxSelected>>", self._on_account_type_select)

        ttk.Label(create_account_frame, text="Initial Balance:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.acc_balance_entry = ttk.Entry(create_account_frame, width=30)
        self.acc_balance_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.interest_rate_label = ttk.Label(create_account_frame, text="Interest Rate:")
        self.interest_rate_entry = ttk.Entry(create_account_frame, width=30)
        self.overdraft_limit_label = ttk.Label(create_account_frame, text="Overdraft Limit:")
        self.overdraft_limit_entry = ttk.Entry(create_account_frame, width=30)

        ttk.Button(create_account_frame, text="Create Account", command=self._create_account_action).grid(row=5, column=0, columnspan=2, pady=15)
        create_account_frame.grid_columnconfigure(1, weight=1)

        op_frame = ttk.LabelFrame(parent_frame, text="Account Transactions", padding="15 15 15 15")
        op_frame.grid(row=2, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

        ttk.Label(op_frame, text="Account No:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.op_acc_num_entry = ttk.Entry(op_frame, width=25)
        self.op_acc_num_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(op_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.op_amount_entry = ttk.Entry(op_frame, width=25)
        self.op_amount_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(op_frame, text="Deposit", command=self._deposit_action).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(op_frame, text="Withdraw", command=self._withdraw_action).grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        ttk.Label(op_frame, text="From Acc:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.from_acc_entry = ttk.Entry(op_frame, width=25)
        self.from_acc_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(op_frame, text="To Acc:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.to_acc_entry = ttk.Entry(op_frame, width=25)
        self.to_acc_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(op_frame, text="Transfer", command=self._transfer_funds_action).grid(row=2, column=2, rowspan=2, padx=5, pady=5, sticky="nsew")

        op_frame.grid_columnconfigure(1, weight=1)
        op_frame.grid_columnconfigure(2, weight=0)

        ttk.Button(parent_frame, text="Apply Interest to All Savings Accounts", command=self._apply_interest_action).grid(row=3, column=0, columnspan=3, pady=15)

    def _create_view_data_tab(self, parent_frame):
        ttk.Label(parent_frame, text="View Bank Data", font=("Arial", 16, "bold"),
                   background=self.colors['frame_bg'], foreground=self.colors['header_color']).grid(row=0, column=0, columnspan=2, pady=15)

        customer_view_frame = ttk.LabelFrame(parent_frame, text="All Customers", padding="15")
        customer_view_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.customer_text = scrolledtext.ScrolledText(customer_view_frame, wrap=tk.WORD, width=40, height=12, font=('Consolas', 9),
                                                       bg=self.colors['white'], fg=self.colors['text_color'])
        self.customer_text.pack(expand=True, fill="both")
        self.customer_text.config(state='disabled')
        ttk.Button(customer_view_frame, text="Refresh Customers", command=self._view_all_customers_action).pack(pady=8)

        account_view_frame = ttk.LabelFrame(parent_frame, text="All Accounts", padding="15")
        account_view_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.account_text = scrolledtext.ScrolledText(account_view_frame, wrap=tk.WORD, width=40, height=12, font=('Consolas', 9),
                                                      bg=self.colors['white'], fg=self.colors['text_color'])
        self.account_text.pack(expand=True, fill="both")
        self.account_text.config(state='disabled')
        ttk.Button(account_view_frame, text="Refresh Accounts", command=self._view_all_accounts_action).pack(pady=8)

        customer_accounts_frame = ttk.LabelFrame(parent_frame, text="Customer's Accounts", padding="15")
        customer_accounts_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ttk.Label(customer_accounts_frame, text="Customer ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.view_customer_acc_id_entry = ttk.Entry(customer_accounts_frame, width=25)
        self.view_customer_acc_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(customer_accounts_frame, text="View Accounts", command=self._view_customer_accounts_action).grid(row=0, column=2, padx=5, pady=5)
        self.customer_specific_acc_text = scrolledtext.ScrolledText(customer_accounts_frame, wrap=tk.WORD, width=60, height=6, font=('Consolas', 9),
                                                                     bg=self.colors['white'], fg=self.colors['text_color'])
        self.customer_specific_acc_text.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.customer_specific_acc_text.config(state='disabled')
        customer_accounts_frame.grid_columnconfigure(1, weight=1)

        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)

    def _on_account_type_select(self, event):
        selected_type = self.acc_type_var.get().lower()

        self.interest_rate_label.grid_forget()
        self.interest_rate_entry.grid_forget()
        self.overdraft_limit_label.grid_forget()
        self.overdraft_limit_entry.grid_forget()

        if selected_type == "savings":
            self.interest_rate_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.interest_rate_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        elif selected_type == "checking":
            self.overdraft_limit_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.overdraft_limit_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    def _add_customer_action(self):
        cid = self.cid_entry.get().strip()
        name = self.cname_entry.get().strip()
        address = self.caddress_entry.get().strip()

        if not all([cid, name, address]):
            messagebox.showerror("Input Error", "All customer fields are required.", icon='warning')
            return

        customer = Customer(cid, name, address)
        if self.bank.add_customer(customer):
            messagebox.showinfo("Success", "Customer added successfully!", icon='info')
            self.cid_entry.delete(0, tk.END)
            self.cname_entry.delete(0, tk.END)
            self.caddress_entry.delete(0, tk.END)
            self._view_all_customers_action()
        else:
            messagebox.showerror("Error", "Customer ID already exists.", icon='error')

    def _remove_customer_action(self):
        cid = self.remove_cid_entry.get().strip()
        if not cid:
            messagebox.showerror("Input Error", "Customer ID is required to remove.", icon='warning')
            return

        if self.bank.remove_customer(cid):
            messagebox.showinfo("Success", f"Customer {cid} removed successfully!", icon='info')
            self.remove_cid_entry.delete(0, tk.END)
            self._view_all_customers_action()
            self._view_all_accounts_action()
        else:
            messagebox.showerror("Error", "Failed to remove customer. Customer might have active accounts or ID not found.", icon='error')

    def _create_account_action(self):
        cid = self.acc_cid_entry.get().strip()
        acc_type = self.acc_type_var.get().lower().strip()
        balance_str = self.acc_balance_entry.get().strip()

        if not all([cid, acc_type, balance_str]):
            messagebox.showerror("Input Error", "Customer ID, Account Type, and Balance are required.", icon='warning')
            return

        try:
            balance = float(balance_str)
            if balance < 0:
                messagebox.showerror("Invalid Input", "Balance cannot be negative.", icon='warning')
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for balance.", icon='warning')
            return

        account = None
        if acc_type == 'savings':
            rate_str = self.interest_rate_entry.get().strip()
            if not rate_str:
                messagebox.showerror("Input Error", "Interest Rate is required for Savings Account.", icon='warning')
                return
            try:
                rate = float(rate_str)
                if rate < 0:
                    messagebox.showerror("Invalid Input", "Interest rate cannot be negative.", icon='warning')
                    return
                account = self.bank.create_account(cid, acc_type, balance, interest_rate=rate)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number for interest rate.", icon='warning')
                return
        elif acc_type == 'checking':
            limit_str = self.overdraft_limit_entry.get().strip()
            if not limit_str:
                messagebox.showerror("Input Error", "Overdraft Limit is required for Checking Account.", icon='warning')
                return
            try:
                limit = float(limit_str)
                if limit < 0:
                    messagebox.showerror("Invalid Input", "Overdraft limit cannot be negative.", icon='warning')
                    return
                account = self.bank.create_account(cid, acc_type, balance, overdraft_limit=limit)
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid number for overdraft limit.", icon='warning')
                return
        else:
            messagebox.showerror("Invalid Input", "Please select a valid account type.", icon='warning')
            return

        if account:
            messagebox.showinfo("Success", f"Account created: {account.account_number}", icon='info')
            self.acc_cid_entry.delete(0, tk.END)
            self.acc_type_var.set('')
            self.acc_balance_entry.delete(0, tk.END)
            self.interest_rate_entry.delete(0, tk.END)
            self.overdraft_limit_entry.delete(0, tk.END)
            self._on_account_type_select(None)
            self._view_all_accounts_action()
            self._view_all_customers_action()
        else:
            messagebox.showerror("Error", "Failed to create account. Customer ID might not exist.", icon='error')

    def _deposit_action(self):
        acc_num = self.op_acc_num_entry.get().strip()
        amount_str = self.op_amount_entry.get().strip()

        if not all([acc_num, amount_str]):
            messagebox.showerror("Input Error", "Account Number and Amount are required.", icon='warning')
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Invalid Input", "Amount must be positive.", icon='warning')
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for amount.", icon='warning')
            return

        if self.bank.deposit(acc_num, amount):
            messagebox.showinfo("Success", "Deposit successful!", icon='info')
            self.op_acc_num_entry.delete(0, tk.END)
            self.op_amount_entry.delete(0, tk.END)
            self._view_all_accounts_action()
            self._refresh_customer_specific_accounts_if_active()
        else:
            messagebox.showerror("Error", "Deposit failed. Account not found or invalid amount.", icon='error')

    def _withdraw_action(self):
        acc_num = self.op_acc_num_entry.get().strip()
        amount_str = self.op_amount_entry.get().strip()

        if not all([acc_num, amount_str]):
            messagebox.showerror("Input Error", "Account Number and Amount are required.", icon='warning')
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Invalid Input", "Amount must be positive.", icon='warning')
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for amount.", icon='warning')
            return

        if self.bank.withdraw(acc_num, amount):
            messagebox.showinfo("Success", "Withdrawal successful!", icon='info')
            self.op_acc_num_entry.delete(0, tk.END)
            self.op_amount_entry.delete(0, tk.END)
            self._view_all_accounts_action()
            self._refresh_customer_specific_accounts_if_active()
        else:
            messagebox.showerror("Error", "Withdrawal failed. Account not found or insufficient funds/overdraft limit exceeded.", icon='error')

    def _transfer_funds_action(self):
        from_acc = self.from_acc_entry.get().strip()
        to_acc = self.to_acc_entry.get().strip()
        amount_str = self.op_amount_entry.get().strip()

        if not all([from_acc, to_acc, amount_str]):
            messagebox.showerror("Input Error", "All transfer fields (From, To, Amount) are required.", icon='warning')
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Invalid Input", "Amount must be positive.", icon='warning')
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for amount.", icon='warning')
            return

        if self.bank.transfer_funds(from_acc, to_acc, amount):
            messagebox.showinfo("Success", "Funds transferred successfully!", icon='info')
            self.from_acc_entry.delete(0, tk.END)
            self.to_acc_entry.delete(0, tk.END)
            self.op_amount_entry.delete(0, tk.END)
            self._view_all_accounts_action()
            self._refresh_customer_specific_accounts_if_active()
        else:
            messagebox.showerror("Error", "Transfer failed. Check account numbers or insufficient funds.", icon='error')

    def _apply_interest_action(self):
        self.bank.apply_all_interest()
        messagebox.showinfo("Success", "Interest applied to all savings accounts.", icon='info')
        self._view_all_accounts_action()
        self._refresh_customer_specific_accounts_if_active()

    def _view_all_customers_action(self):
        customers = self.bank.display_all_customers()
        self.customer_text.config(state='normal')
        self.customer_text.delete(1.0, tk.END)
        if customers:
            self.customer_text.insert(tk.END, "\n\n".join(customers))
        else:
            self.customer_text.insert(tk.END, "No customers registered yet.")
        self.customer_text.config(state='disabled')

    def _view_all_accounts_action(self):
        accounts = self.bank.display_all_accounts()
        self.account_text.config(state='normal')
        self.account_text.delete(1.0, tk.END)
        if accounts:
            self.account_text.insert(tk.END, "\n\n".join(accounts))
        else:
            self.account_text.insert(tk.END, "No accounts created yet.")
        self.account_text.config(state='disabled')

    def _view_customer_accounts_action(self):
        cid = self.view_customer_acc_id_entry.get().strip()
        self.customer_specific_acc_text.config(state='normal')
        self.customer_specific_acc_text.delete(1.0, tk.END)
        if not cid:
            self.customer_specific_acc_text.insert(tk.END, "Please enter a Customer ID.")
            self.customer_specific_acc_text.config(state='disabled')
            return

        accounts = self.bank.get_customer_accounts(cid)
        if accounts:
            details = "\n\n".join([acc.display_details() for acc in accounts])
            self.customer_specific_acc_text.insert(tk.END, f"Accounts for Customer ID {cid}:\n\n{details}")
        else:
            self.customer_specific_acc_text.insert(tk.END, f"No accounts found for Customer ID {cid} or customer does not exist.")
        self.customer_specific_acc_text.config(state='disabled')

    def _refresh_customer_specific_accounts_if_active(self):
        cid_to_refresh = self.view_customer_acc_id_entry.get().strip()
        if cid_to_refresh:
            self._view_customer_accounts_action()

if __name__ == "__main__":
    root = tk.Tk()
    app = BankGUI(root)
    root.mainloop()