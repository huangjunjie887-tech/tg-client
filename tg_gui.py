import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
import threading
import os
import time
import platform
import uuid
import hashlib
from datetime import datetime

SERVER = "http://172.98.23.64:5000"
CARD_API = "https://tgpremium.site/tgyinxiao/verify.php"

class TelegramFullGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("天师府TG全能营销系统 联系@Tian2547")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        self.is_logged_in = False
        self.card_info = None
        self.accounts = []
        self.proxies = []
        self.groups = ["默认分组"]
        self.running_tasks = {}
        
        self.machine_id = self.get_machine_id()
        self.show_card_login()
    
    def get_machine_id(self):
        try:
            mac = uuid.getnode()
            hostname = platform.node()
            return hashlib.md5(f"{mac}{hostname}".encode()).hexdigest()
        except:
            return hashlib.md5(platform.node().encode()).hexdigest()
    
    def show_card_login(self):
        login_window = tk.Toplevel(self.root)
        login_window.title("卡密登录")
        login_window.geometry("450x350")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        
        x = (login_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (login_window.winfo_screenheight() // 2) - (350 // 2)
        login_window.geometry(f"+{x}+{y}")
        
        tk.Label(login_window, text="天师府TG全能营销系统", font=("微软雅黑", 18, "bold")).pack(pady=20)
        tk.Label(login_window, text="请输入卡密激活", font=("微软雅黑", 10)).pack()
        
        frame = ttk.Frame(login_window)
        frame.pack(pady=30)
        
        ttk.Label(frame, text="卡密:", font=("微软雅黑", 12)).grid(row=0, column=0, padx=10, pady=10)
        self.card_entry = ttk.Entry(frame, width=30, font=("微软雅黑", 12), show="●")
        self.card_entry.grid(row=0, column=1, padx=10, pady=10)
        
        self.login_status = ttk.Label(login_window, text="", foreground="red")
        self.login_status.pack(pady=5)
        
        btn_frame = ttk.Frame(login_window)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="激活", command=lambda: self.verify_card(login_window), width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="购买卡密", command=self.buy_card, width=12).pack(side="left", padx=10)
        
        tk.Label(login_window, text="购买卡密请联系 @Tian2547", font=("微软雅黑", 9), fg="gray").pack(side="bottom", pady=10)
        self.card_entry.bind("<Return>", lambda event: self.verify_card(login_window))
    
    def verify_card(self, login_window):
        card_code = self.card_entry.get().strip()
        if not card_code:
            self.login_status.config(text="请输入卡密", foreground="red")
            return
        
        self.login_status.config(text="验证中...", foreground="blue")
        login_window.update()
        
        try:
            resp = requests.post(CARD_API, json={"action": "verify", "card": card_code, "machine_id": self.machine_id}, timeout=15, proxies={"http": None, "https": None})
            result = resp.json()
            if result.get("success"):
                self.is_logged_in = True
                self.card_info = result
                self.login_status.config(text="激活成功！正在启动...", foreground="green")
                login_window.update()
                login_window.after(1000, lambda: self.on_login_success(login_window))
            else:
                self.login_status.config(text=result.get("error", "卡密无效"), foreground="red")
        except Exception as e:
            self.login_status.config(text=f"验证失败", foreground="red")
    
    def buy_card(self):
        import webbrowser
        webbrowser.open("https://t.me/Tian2547")
    
    def on_login_success(self, login_window):
        login_window.destroy()
        self.init_main_interface()
    
    def init_main_interface(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_command(label="导入配置", command=self.import_config)
        file_menu.add_separator()
        file_menu.add_command(label="卡密信息", command=self.show_card_info)
        file_menu.add_command(label="退出", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.about)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_account_page()
        self.create_proxy_page()
        self.create_scrape_page()
        self.create_invite_page()
        self.create_send_page()
        self.create_group_chat_page()
        self.create_auto_register_page()
        self.create_monitor_page()
        self.create_script_page()
        self.create_log_page()
        
        self.status_bar = ttk.Label(self.root, text=f"已激活 | 有效期: {self.card_info.get('expire_date', '永久')}", relief="sunken")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.log("系统启动完成")
    
    def show_card_info(self):
        if self.card_info:
            messagebox.showinfo("卡密信息", f"天师府TG全能营销系统\n\n卡密状态: 已激活\n有效期至: {self.card_info.get('expire_date', '永久')}\n联系客服: @Tian2547")
    
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def call_api(self, endpoint, data=None):
        url = f"{SERVER}{endpoint}"
        try:
            if data:
                resp = requests.post(url, json=data, timeout=60, proxies={"http": None, "https": None})
            else:
                resp = requests.get(url, timeout=10, proxies={"http": None, "https": None})
            return resp.json()
        except Exception as e:
            self.log(f"API错误: {e}", "ERROR")
            return None
    
    # ==================== 多账号管理页面 ====================
    def create_account_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="多账号管理")
        
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(toolbar, text="导入账号(文件夹)", command=self.import_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导出账号", command=self.export_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除死号", command=self.delete_dead_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中", command=self.delete_selected).pack(side="left", padx=2)
        ttk.Button(toolbar, text="分组管理", command=self.group_manager).pack(side="left", padx=2)
        ttk.Button(toolbar, text="账号检测", command=self.check_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="资料修改", command=self.edit_profile).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(page, text="账号列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "手机号", "昵称", "分组", "账号状态")
        self.account_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.account_tree.heading(col, text=col)
            self.account_tree.column(col, anchor="center", width=120)
        self.account_tree.column("序号", width=50)
        self.account_tree.column("账号状态", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        self.account_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
    
    def import_accounts(self):
        if not self.groups:
            self.groups = ["默认分组"]
        group = messagebox.askstring("选择分组", f"当前分组: {', '.join(self.groups)}\n请输入分组名称:")
        if not group:
            group = "默认分组"
        if group not in self.groups:
            self.groups.append(group)
        
        folder = filedialog.askdirectory(title="选择账号文件夹")
        if folder:
            count = 0
            for item in os.listdir(folder):
                if item.endswith(".session"):
                    self.accounts.append({
                        "phone": item.replace(".session", ""),
                        "nickname": "",
                        "group": group,
                        "status": "正常"
                    })
                    count += 1
                elif os.path.isdir(os.path.join(folder, item)):
                    self.accounts.append({
                        "phone": item,
                        "nickname": "",
                        "group": group,
                        "status": "正常"
                    })
                    count += 1
            self.refresh_account_list()
            self.log(f"导入 {count} 个账号到分组 [{group}]")
    
    def export_accounts(self):
        if not self.accounts:
            self.log("没有账号可导出")
            return
        folder = filedialog.askdirectory(title="选择导出文件夹")
        if folder:
            count = 0
            for acc in self.accounts:
                phone = acc.get('phone', '')
                if phone:
                    with open(os.path.join(folder, f"{phone}.session"), 'w') as f:
                        f.write("# Session file\n")
                    count += 1
            self.log(f"导出 {count} 个账号")
    
    def delete_selected(self):
        selected = self.account_tree.selection()
        if not selected:
            self.log("请先选择账号")
            return
        if messagebox.askyesno("确认", f"删除 {len(selected)} 个账号？"):
            indices = [int(self.account_tree.item(item)['values'][0]) - 1 for item in selected]
            indices.sort(reverse=True)
            for idx in indices:
                if idx < len(self.accounts):
                    self.accounts.pop(idx)
            self.refresh_account_list()
            self.log(f"删除 {len(selected)} 个账号")
    
    def delete_dead_accounts(self):
        dead = [i for i, acc in enumerate(self.accounts) if acc.get('status') == '死号']
        if not dead:
            self.log("没有死号账号")
            return
        if messagebox.askyesno("确认", f"删除 {len(dead)} 个死号账号？"):
            for idx in sorted(dead, reverse=True):
                self.accounts.pop(idx)
            self.refresh_account_list()
            self.log(f"删除 {len(dead)} 个死号账号")
    
    def group_manager(self):
        win = tk.Toplevel(self.root)
        win.title("分组管理")
        win.geometry("500x400")
        win.transient(self.root)
        win.grab_set()
        
        left = ttk.LabelFrame(win, text="分组列表")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        group_listbox = tk.Listbox(left, height=15)
        group_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        for g in self.groups:
            group_listbox.insert(tk.END, g)
        
        right = ttk.LabelFrame(win, text="移动账号到分组")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        ttk.Label(right, text="选择账号:").pack(anchor="w", padx=10, pady=5)
        acc_listbox = tk.Listbox(right, height=10)
        acc_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        for acc in self.accounts:
            acc_listbox.insert(tk.END, f"{acc.get('phone', '')} [{acc.get('group', '未分组')}]")
        
        ttk.Label(right, text="移动到分组:").pack(anchor="w", padx=10, pady=5)
        target_combo = ttk.Combobox(right, values=self.groups, width=20)
        target_combo.pack(padx=10, pady=5)
        
        def add_group():
            new = messagebox.askstring("新建分组", "分组名称:")
            if new and new not in self.groups:
                self.groups.append(new)
                group_listbox.insert(tk.END, new)
                target_combo['values'] = self.groups
                self.log(f"新建分组: {new}")
        
        def del_group():
            sel = group_listbox.curselection()
            if sel:
                g = group_listbox.get(sel)
                if g == "默认分组":
                    messagebox.showwarning("提示", "不能删除默认分组")
                    return
                if messagebox.askyesno("确认", f"删除分组 [{g}]？账号将移到默认分组"):
                    self.groups.remove(g)
                    group_listbox.delete(sel)
                    target_combo['values'] = self.groups
                    for acc in self.accounts:
                        if acc.get('group') == g:
                            acc['group'] = "默认分组"
                    self.refresh_account_list()
                    self.log(f"删除分组: {g}")
        
        def move():
            sel = acc_listbox.curselection()
            target = target_combo.get()
            if not sel or not target:
                return
            for idx in sel:
                if idx < len(self.accounts):
                    self.accounts[idx]['group'] = target
            self.refresh_account_list()
            acc_listbox.delete(0, tk.END)
            for acc in self.accounts:
                acc_listbox.insert(tk.END, f"{acc.get('phone', '')} [{acc.get('group', '未分组')}]")
            self.log(f"移动 {len(sel)} 个账号到 [{target}]")
        
        btn_frame = ttk.Frame(win)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        ttk.Button(btn_frame, text="新建分组", command=add_group).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="删除分组", command=del_group).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="移动", command=move).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side="right", padx=5)
    
    def check_accounts(self):
        self.log("账号检测功能开发中")
        messagebox.showinfo("提示", "账号检测功能开发中")
    
    def edit_profile(self):
        sel = self.account_tree.selection()
        if not sel:
            self.log("请先选择账号")
            return
        messagebox.showinfo("提示", "资料修改功能开发中")
    
    def refresh_account_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        for i, acc in enumerate(self.accounts, 1):
            self.account_tree.insert("", "end", values=(i, acc.get('phone', ''), acc.get('nickname', ''), acc.get('group', '未分组'), acc.get('status', '正常')))
    
    # ==================== 代理IP页面 ====================
    def create_proxy_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="代理IP")
        
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        self.proxy_count_label = ttk.Label(toolbar, text=f"IP数: {len(self.proxies)}/10")
        self.proxy_count_label.pack(side="left", padx=10)
        ttk.Button(toolbar, text="添加代理", command=self.add_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除代理", command=self.del_proxy).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(page, text="代理列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "类型", "IP", "端口", "状态")
        self.proxy_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.proxy_tree.heading(col, text=col)
            self.proxy_tree.column(col, anchor="center", width=100)
        self.proxy_tree.pack(fill="both", expand=True, padx=5, pady=5)
    
    def add_proxy(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加代理")
        dialog.geometry("350x250")
        
        ttk.Label(dialog, text="类型:").grid(row=0, column=0, padx=10, pady=10)
        ptype = ttk.Combobox(dialog, values=["socks5", "http", "https"], width=20)
        ptype.set("socks5")
        ptype.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="IP:").grid(row=1, column=0, padx=10, pady=10)
        ip = ttk.Entry(dialog, width=30)
        ip.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="端口:").grid(row=2, column=0, padx=10, pady=10)
        port = ttk.Entry(dialog, width=30)
        port.grid(row=2, column=1, padx=10, pady=10)
        
        def save():
            if ip.get() and port.get():
                self.proxies.append({"type": ptype.get(), "ip": ip.get(), "port": port.get(), "status": "未检测"})
                self.refresh_proxy_list()
                self.proxy_count_label.config(text=f"IP数: {len(self.proxies)}/10")
                dialog.destroy()
                self.log(f"添加代理: {ip.get()}:{port.get()}")
        ttk.Button(dialog, text="保存", command=save).pack(pady=20)
    
    def del_proxy(self):
        sel = self.proxy_tree.selection()
        if sel:
            idx = int(self.proxy_tree.item(sel[0])['values'][0]) - 1
            if idx < len(self.proxies):
                self.proxies.pop(idx)
            self.refresh_proxy_list()
            self.proxy_count_label.config(text=f"IP数: {len(self.proxies)}/10")
            self.log("删除代理")
    
    def refresh_proxy_list(self):
        for item in self.proxy_tree.get_children():
            self.proxy_tree.delete(item)
        for i, p in enumerate(self.proxies, 1):
            self.proxy_tree.insert("", "end", values=(i, p.get('type'), p.get('ip'), p.get('port'), p.get('status')))
    
    # ==================== 采集群成员页面 ====================
    def create_scrape_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="采集群成员")
        
        frame = ttk.LabelFrame(page, text="采集设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="群组链接:").grid(row=0, column=0, padx=5, pady=5)
        self.scrape_group = ttk.Entry(frame, width=50)
        self.scrape_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="采集数量:").grid(row=1, column=0, padx=5, pady=5)
        self.scrape_limit = ttk.Entry(frame, width=10)
        self.scrape_limit.insert(0, "200")
        self.scrape_limit.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Button(frame, text="开始采集", command=self.start_scrape).pack(pady=10)
    
    def start_scrape(self):
        group = self.scrape_group.get()
        limit = self.scrape_limit.get()
        if not group:
            self.log("请输入群组链接")
            return
        self.log(f"开始采集: {group}")
        def do():
            res = self.call_api("/scrape", {"group": group, "limit": int(limit)})
            if res:
                with open("members.json", "w", encoding="utf-8") as f:
                    json.dump(res.get("members", []), f, ensure_ascii=False, indent=2)
                self.log(f"采集到 {len(res.get('members', []))} 个成员")
        threading.Thread(target=do, daemon=True).start()
    
    # ==================== 批量拉人页面 ====================
    def create_invite_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="批量拉人")
        
        frame = ttk.LabelFrame(page, text="拉人设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="目标群组:").grid(row=0, column=0, padx=5, pady=5)
        self.target_group = ttk.Entry(frame, width=50)
        self.target_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="拉人数量:").grid(row=1, column=0, padx=5, pady=5)
        self.invite_limit = ttk.Entry(frame, width=10)
        self.invite_limit.insert(0, "50")
        self.invite_limit.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="间隔(秒):").grid(row=2, column=0, padx=5, pady=5)
        self.invite_delay = ttk.Entry(frame, width=10)
        self.invite_delay.insert(0, "60")
        self.invite_delay.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Button(frame, text="开始拉人", command=self.start_invite).pack(pady=10)
    
    def start_invite(self):
        group = self.target_group.get()
        limit = self.invite_limit.get()
        if not group:
            self.log("请输入目标群组")
            return
        if not os.path.exists("members.json"):
            self.log("请先采集成员")
            return
        with open("members.json", "r") as f:
            members = json.load(f)
        self.log(f"开始拉人: {min(int(limit), len(members))} 人")
        def do():
            for i, m in enumerate(members[:int(limit)]):
                self.call_api("/invite", {"group": group, "user_id": m['id']})
                time.sleep(int(self.invite_delay.get()))
        threading.Thread(target=do, daemon=True).start()
    
    # ==================== 群发广告页面 ====================
    def create_send_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="群发广告")
        
        frame = ttk.LabelFrame(page, text="群发设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="广告词:").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self.ad_text = scrolledtext.ScrolledText(frame, width=60, height=5)
        self.ad_text.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="间隔(秒):").grid(row=1, column=0, padx=5, pady=5)
        self.send_delay = ttk.Entry(frame, width=10)
        self.send_delay.insert(0, "30")
        self.send_delay.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Button(frame, text="导入文本", command=self.import_ad).pack(pady=5)
        ttk.Button(frame, text="开始群发", command=self.start_send).pack(pady=5)
    
    def import_ad(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.ad_text.delete("1.0", tk.END)
                self.ad_text.insert("1.0", f.read())
            self.log(f"导入广告词: {path}")
    
    def start_send(self):
        msg = self.ad_text.get("1.0", tk.END).strip()
        if not msg:
            self.log("请输入广告词")
            return
        if not os.path.exists("members.json"):
            self.log("请先采集成员")
            return
        with open("members.json", "r") as f:
            members = json.load(f)
        self.log(f"开始群发: {len(members)} 人")
        def do():
            for m in members:
                self.call_api("/send", {"user_id": m['id'], "message": msg})
                time.sleep(int(self.send_delay.get()))
        threading.Thread(target=do, daemon=True).start()
    
    # ==================== 自动群聊页面 ====================
    def create_group_chat_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动群聊")
        
        frame = ttk.LabelFrame(page, text="群聊设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="目标群组:").grid(row=0, column=0, padx=5, pady=5)
        self.chat_group = ttk.Entry(frame, width=50)
        self.chat_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="间隔(秒):").grid(row=1, column=0, padx=5, pady=5)
        self.chat_interval = ttk.Entry(frame, width=10)
        self.chat_interval.insert(0, "60")
        self.chat_interval.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Button(frame, text="启动", command=self.start_chat).pack(pady=5)
        ttk.Button(frame, text="停止", command=self.stop_chat).pack(pady=5)
        
        kw_frame = ttk.LabelFrame(page, text="关键词回复")
        kw_frame.pack(fill="x", padx=10, pady=5)
        self.keyword_text = scrolledtext.ScrolledText(kw_frame, width=80, height=6)
        self.keyword_text.pack(fill="x", padx=5, pady=5)
        ttk.Button(kw_frame, text="保存关键词", command=self.save_keywords).pack(pady=5)
    
    def start_chat(self):
        group = self.chat_group.get()
        if group:
            self.log(f"启动炒群: {group}")
            self.running_tasks['chat'] = True
    
    def stop_chat(self):
        self.running_tasks['chat'] = False
        self.log("停止炒群")
    
    def save_keywords(self):
        with open("keywords.json", "w", encoding="utf-8") as f:
            f.write(self.keyword_text.get("1.0", tk.END))
        self.log("关键词已保存")
    
    # ==================== 自动注册页面 ====================
    def create_auto_register_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动注册")
        
        frame = ttk.LabelFrame(page, text="注册设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="接码API:").grid(row=0, column=0, padx=5, pady=5)
        self.sms_api = ttk.Entry(frame, width=50)
        self.sms_api.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="API Key:").grid(row=1, column=0, padx=5, pady=5)
        self.sms_key = ttk.Entry(frame, width=50, show="*")
        self.sms_key.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="注册数量:").grid(row=2, column=0, padx=5, pady=5)
        self.reg_count = ttk.Entry(frame, width=10)
        self.reg_count.insert(0, "10")
        self.reg_count.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Button(frame, text="开始注册", command=self.start_register).pack(pady=10)
    
    def start_register(self):
        self.log("批量注册功能开发中")
        messagebox.showinfo("提示", "批量注册功能开发中")
    
    # ==================== 监听页面 ====================
    def create_monitor_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="监听群组")
        
        frame = ttk.LabelFrame(page, text="监听设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="监听群组:").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self.monitor_groups = scrolledtext.ScrolledText(frame, width=60, height=6)
        self.monitor_groups.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="触发动作:").grid(row=1, column=0, padx=5, pady=5)
        self.monitor_action = ttk.Combobox(frame, values=["私信", "拉人", "两者"], width=20)
        self.monitor_action.set("私信")
        self.monitor_action.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Button(frame, text="启动监听", command=self.start_monitor).pack(pady=10)
    
    def start_monitor(self):
        self.log("监听功能开发中")
        messagebox.showinfo("提示", "监听功能开发中")
    
    # ==================== 话术配置页面 ====================
    def create_script_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="话术配置")
        
        frame = ttk.LabelFrame(page, text="话术库")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.script_text = scrolledtext.ScrolledText(frame, width=80, height=15)
        self.script_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        ttk.Button(frame, text="导入TXT", command=self.import_script).pack(pady=5)
        ttk.Button(frame, text="保存", command=self.save_script).pack(pady=5)
    
    def import_script(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.script_text.delete("1.0", tk.END)
                self.script_text.insert("1.0", f.read())
            self.log(f"导入话术: {path}")
    
    def save_script(self):
        with open("scripts.txt", "w", encoding="utf-8") as f:
            f.write(self.script_text.get("1.0", tk.END))
        self.log("话术已保存")
    
    # ==================== 日志页面 ====================
    def create_log_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="运行日志")
        
        frame = ttk.LabelFrame(page, text="日志")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(frame, width=100, height=20)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_log).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="导出", command=self.export_log).pack(side="left", padx=5)
    
    def clear_log(self):
        self.log_text.delete("1.0", tk.END)
    
    def export_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get("1.0", tk.END))
            self.log(f"日志已导出")
    
    def export_config(self):
        cfg = {"accounts": self.accounts, "proxies": self.proxies, "groups": self.groups}
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self.log("配置已导出")
    
    def import_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.accounts = cfg.get("accounts", [])
            self.proxies = cfg.get("proxies", [])
            self.groups = cfg.get("groups", ["默认分组"])
            self.refresh_account_list()
            self.refresh_proxy_list()
            self.log("配置已导入")
    
    def about(self):
        messagebox.showinfo("关于", "天师府TG全能营销系统\n联系@Tian2547")

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
