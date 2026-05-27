import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
import threading
import os
import time
from datetime import datetime

SERVER = "http://172.98.23.64:5000"
CARD_API = "https://tgpremium.site/tgyinxiao/verify.php"  # 卡密验证接口

class TelegramFullGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("天师府TG全能营销系统 联系@Tian2547")
        self.root.geometry("1100x800")
        self.root.resizable(True, True)
        
        # 是否已登录
        self.is_logged_in = False
        self.card_info = None
        
        # 数据存储
        self.accounts = []      # 账号列表
        self.proxies = []       # 代理列表
        self.running_tasks = {}
        
        # 先显示卡密登录窗口
        self.show_card_login()
    
    def show_card_login(self):
        """显示卡密登录窗口"""
        login_window = tk.Toplevel(self.root)
        login_window.title("卡密登录 - 天师府TG全能营销系统")
        login_window.geometry("450x350")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        
        # 居中显示
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (login_window.winfo_screenheight() // 2) - (350 // 2)
        login_window.geometry(f"+{x}+{y}")
        
        # 标题
        title_label = tk.Label(login_window, text="天师府TG全能营销系统", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=20)
        
        sub_label = tk.Label(login_window, text="请输入卡密激活", font=("微软雅黑", 10))
        sub_label.pack()
        
        # 卡密输入框
        frame = ttk.Frame(login_window)
        frame.pack(pady=30)
        
        ttk.Label(frame, text="卡密:", font=("微软雅黑", 12)).grid(row=0, column=0, padx=10, pady=10)
        self.card_entry = ttk.Entry(frame, width=30, font=("微软雅黑", 12), show="●")
        self.card_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # 状态标签
        self.login_status = ttk.Label(login_window, text="", foreground="red")
        self.login_status.pack(pady=5)
        
        # 按钮
        btn_frame = ttk.Frame(login_window)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="激活", command=lambda: self.verify_card(login_window), width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="购买卡密", command=self.buy_card, width=12).pack(side="left", padx=10)
        
        # 提示
        tip_label = tk.Label(login_window, text="购买卡密请联系 @Tian2547", font=("微软雅黑", 9), foreground="gray")
        tip_label.pack(side="bottom", pady=10)
        
        # 绑定回车键
        self.card_entry.bind("<Return>", lambda event: self.verify_card(login_window))
    
    def verify_card(self, login_window):
        """验证卡密"""
        card_code = self.card_entry.get().strip()
        if not card_code:
            self.login_status.config(text="请输入卡密", foreground="red")
            return
        
        self.login_status.config(text="验证中...", foreground="blue")
        login_window.update()
        
        # 调用卡密验证接口
        try:
            resp = requests.post(
                CARD_API,
                json={"action": "verify", "card": card_code},
                timeout=15,
                proxies={"http": None, "https": None}
            )
            result = resp.json()
            
            if result.get("success"):
                self.is_logged_in = True
                self.card_info = result
                self.login_status.config(text="激活成功！正在启动...", foreground="green")
                login_window.update()
                
                # 延迟关闭登录窗口，启动主界面
                login_window.after(1000, lambda: self.on_login_success(login_window))
            else:
                error_msg = result.get("error", "卡密无效")
                self.login_status.config(text=error_msg, foreground="red")
                
        except requests.exceptions.ConnectionError:
            self.login_status.config(text="无法连接验证服务器，请检查网络", foreground="red")
        except Exception as e:
            self.login_status.config(text=f"验证失败: {str(e)[:30]}", foreground="red")
    
    def buy_card(self):
        """购买卡密"""
        import webbrowser
        webbrowser.open("https://t.me/Tian2547")
    
    def on_login_success(self, login_window):
        """登录成功后初始化主界面"""
        login_window.destroy()
        self.init_main_interface()
    
    def init_main_interface(self):
        """初始化主界面"""
        # 创建菜单栏
        self.create_menu()
        
        # 创建选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 各功能页面
        self.create_server_page()
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
        
        # 状态栏显示卡密信息
        self.status_bar = ttk.Label(self.root, text=f"已激活 | 有效期: {self.card_info.get('expire_date', '永久')}", relief="sunken")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.log("系统启动完成")
        self.log(f"卡密验证成功，有效期至: {self.card_info.get('expire_date', '永久')}")
    
    def create_menu(self):
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
    
    def show_card_info(self):
        """显示卡密信息"""
        if self.card_info:
            messagebox.showinfo("卡密信息", 
                f"天师府TG全能营销系统\n\n"
                f"卡密状态: 已激活\n"
                f"有效期至: {self.card_info.get('expire_date', '永久')}\n"
                f"功能权限:\n"
                f"  - 采集群成员: {'✓' if self.card_info.get('permissions', {}).get('scrape', True) else '✗'}\n"
                f"  - 批量拉人: {'✓' if self.card_info.get('permissions', {}).get('invite', True) else '✗'}\n"
                f"  - 群发广告: {'✓' if self.card_info.get('permissions', {}).get('send', True) else '✗'}\n"
                f"  - 自动群聊: {'✓' if self.card_info.get('permissions', {}).get('chat', True) else '✗'}\n"
                f"  - 代理IP: {'✓' if self.card_info.get('permissions', {}).get('proxy', True) else '✗'}\n"
                f"  - 多账号管理: {'✓' if self.card_info.get('permissions', {}).get('account', True) else '✗'}\n\n"
                f"联系客服: @Tian2547")
        else:
            messagebox.showinfo("卡密信息", "未找到卡密信息，请重新登录")
    
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def call_api(self, endpoint, data=None):
        server = self.server_entry.get()
        url = f"{server}{endpoint}"
        try:
            if data:
                resp = requests.post(url, json=data, timeout=60, proxies={"http": None, "https": None})
            else:
                resp = requests.get(url, timeout=10, proxies={"http": None, "https": None})
            return resp.json()
        except Exception as e:
            self.log(f"API错误: {e}", "ERROR")
            return None
    
    def test_connection(self):
        self.log("正在测试连接...")
        result = self.call_api("/status")
        if result:
            self.status_label.config(text="已连接", foreground="green")
            self.log("连接成功")
        else:
            self.status_label.config(text="连接失败", foreground="red")
            self.log("连接失败")
    
    def send_code(self):
        self.log("发送验证码...")
        result = self.call_api("/login", {})
        if result and result.get("status") == "code_sent":
            self.log("验证码已发送")
            messagebox.showinfo("提示", "验证码已发送到Telegram")
        else:
            self.log("发送失败")
    
    def verify_login(self):
        code = self.code_entry.get().strip()
        if not code:
            self.log("请输入验证码")
            return
        result = self.call_api("/login", {"code": code})
        if result and result.get("status") == "success":
            self.login_status.config(text=f"已登录: {result['user']}", foreground="green")
            self.log(f"登录成功: {result['user']}")
            messagebox.showinfo("成功", f"登录成功: {result['user']}")
        else:
            self.log("登录失败")
    
    # ==================== 服务器配置页面 ====================
    def create_server_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="服务器配置")
        
        frame = ttk.LabelFrame(page, text="连接设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="服务器地址:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.server_entry = ttk.Entry(frame, width=40)
        self.server_entry.insert(0, SERVER)
        self.server_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(frame, text="测试连接", command=self.test_connection).grid(row=0, column=2, padx=5, pady=5)
        self.status_label = ttk.Label(frame, text="未连接", foreground="red")
        self.status_label.grid(row=0, column=3, padx=10, pady=5)
        
        login_frame = ttk.LabelFrame(page, text="账号登录")
        login_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(login_frame, text="验证码:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.code_entry = ttk.Entry(login_frame, width=20)
        self.code_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(login_frame, text="发送验证码", command=self.send_code).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(login_frame, text="确认登录", command=self.verify_login).grid(row=0, column=3, padx=5, pady=5)
        self.login_status = ttk.Label(login_frame, text="未登录", foreground="red")
        self.login_status.grid(row=0, column=4, padx=10, pady=5)
    
    # ==================== 多账号管理页面 ====================
    def create_account_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="多账号管理")
        
        # 工具栏
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(toolbar, text="导入账号(文件夹)", command=self.import_accounts_folder).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导出账号", command=self.export_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除死号", command=self.delete_dead_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="账号检测", command=self.check_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="资料修改", command=self.edit_profile).pack(side="left", padx=2)
        
        # 账号列表
        frame = ttk.LabelFrame(page, text="账号列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "手机号", "昵称", "当前任务", "上一次操作", "账号状态", "注册时长")
        self.account_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.account_tree.heading(col, text=col)
            self.account_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        self.account_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
    
    def import_accounts_folder(self):
        folder = filedialog.askdirectory(title="选择账号文件夹")
        if folder:
            self.log(f"从文件夹导入账号: {folder}")
            for file in os.listdir(folder):
                if file.endswith(".session"):
                    self.accounts.append({
                        "phone": file.replace(".session", ""),
                        "nickname": "",
                        "status": "正常",
                        "register_time": "未知"
                    })
            self.refresh_account_list()
            self.log(f"导入 {len([f for f in os.listdir(folder) if f.endswith('.session')])} 个账号")
    
    def export_accounts(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=2)
            self.log(f"导出 {len(self.accounts)} 个账号到 {file_path}")
    
    def delete_dead_accounts(self):
        selected = self.account_tree.selection()
        if selected:
            for item in selected:
                idx = int(self.account_tree.item(item)['values'][0]) - 1
                self.accounts.pop(idx)
            self.refresh_account_list()
            self.log("删除选中账号")
    
    def check_accounts(self):
        self.log("开始检测账号状态...")
        messagebox.showinfo("提示", "账号检测功能开发中")
    
    def edit_profile(self):
        selected = self.account_tree.selection()
        if not selected:
            self.log("请先选择账号")
            return
        messagebox.showinfo("提示", "资料修改功能开发中")
    
    def refresh_account_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        for i, acc in enumerate(self.accounts, 1):
            self.account_tree.insert("", "end", values=(
                i, acc.get('phone', ''), acc.get('nickname', ''),
                acc.get('current_task', ''), acc.get('last_action', ''),
                acc.get('status', '正常'), acc.get('register_time', '未知')
            ))
    
    # ==================== 代理IP页面 ====================
    def create_proxy_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="代理IP")
        
        # 工具栏
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        self.proxy_count_label = ttk.Label(toolbar, text=f"IP数: {len(self.proxies)}/10")
        self.proxy_count_label.pack(side="left", padx=10)
        
        ttk.Button(toolbar, text="添加代理IP", command=self.add_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除代理IP", command=self.delete_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="检测代理IP", command=self.check_proxies).pack(side="left", padx=2)
        
        # 代理列表
        frame = ttk.LabelFrame(page, text="代理列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "代理类型", "IP/域名", "端口", "用户名", "密码", "状态")
        self.proxy_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.proxy_tree.heading(col, text=col)
            self.proxy_tree.column(col, width=100)
        self.proxy_tree.pack(fill="both", expand=True, padx=5, pady=5)
    
    def add_proxy(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加代理")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="代理类型:").grid(row=0, column=0, padx=5, pady=5)
        proxy_type = ttk.Combobox(dialog, values=["http", "https", "socks4", "socks5"], width=20)
        proxy_type.set("socks5")
        proxy_type.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="IP/域名:").grid(row=1, column=0, padx=5, pady=5)
        proxy_host = ttk.Entry(dialog, width=30)
        proxy_host.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="端口:").grid(row=2, column=0, padx=5, pady=5)
        proxy_port = ttk.Entry(dialog, width=30)
        proxy_port.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="用户名(可选):").grid(row=3, column=0, padx=5, pady=5)
        proxy_user = ttk.Entry(dialog, width=30)
        proxy_user.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="密码(可选):").grid(row=4, column=0, padx=5, pady=5)
        proxy_pass = ttk.Entry(dialog, width=30, show="*")
        proxy_pass.grid(row=4, column=1, padx=5, pady=5)
        
        def save_proxy():
            if len(self.proxies) >= 10:
                messagebox.showerror("错误", "最多添加10个代理")
                return
            self.proxies.append({
                "type": proxy_type.get(),
                "host": proxy_host.get(),
                "port": proxy_port.get(),
                "user": proxy_user.get(),
                "pass": proxy_pass.get(),
                "status": "未检测"
            })
            self.refresh_proxy_list()
            self.proxy_count_label.config(text=f"IP数: {len(self.proxies)}/10")
            dialog.destroy()
            self.log(f"添加代理: {proxy_host.get()}:{proxy_port.get()}")
        
        ttk.Button(dialog, text="保存", command=save_proxy).grid(row=5, column=0, columnspan=2, pady=20)
    
    def delete_proxy(self):
        selected = self.proxy_tree.selection()
        if selected:
            for item in selected:
                idx = int(self.proxy_tree.item(item)['values'][0]) - 1
                self.proxies.pop(idx)
            self.refresh_proxy_list()
            self.proxy_count_label.config(text=f"IP数: {len(self.proxies)}/10")
            self.log("删除代理")
    
    def check_proxies(self):
        self.log("开始检测代理...")
        messagebox.showinfo("提示", "代理检测功能开发中")
    
    def refresh_proxy_list(self):
        for item in self.proxy_tree.get_children():
            self.proxy_tree.delete(item)
        for i, p in enumerate(self.proxies, 1):
            self.proxy_tree.insert("", "end", values=(
                i, p.get('type', ''), p.get('host', ''),
                p.get('port', ''), p.get('user', ''),
                p.get('pass', '***'), p.get('status', '未检测')
            ))
    
    # ==================== 采集群成员页面 ====================
    def create_scrape_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="采集群成员")
        
        frame = ttk.LabelFrame(page, text="采集设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="群组链接:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.scrape_group = ttk.Entry(frame, width=50)
        self.scrape_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="采集数量:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.scrape_limit = ttk.Entry(frame, width=10)
        self.scrape_limit.insert(0, "200")
        self.scrape_limit.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="开始采集", command=self.start_scrape).pack()
    
    def start_scrape(self):
        group = self.scrape_group.get()
        limit = self.scrape_limit.get()
        if not group:
            self.log("请输入群组链接")
            return
        
        self.log(f"开始采集: {group} (数量: {limit})")
        
        def do_scrape():
            result = self.call_api("/scrape", {"group": group, "limit": int(limit)})
            if result:
                members = result.get("members", [])
                self.log(f"采集到 {len(members)} 个成员")
                with open("members.json", "w", encoding="utf-8") as f:
                    json.dump(members, f, ensure_ascii=False, indent=2)
                self.log("已保存到 members.json")
            else:
                self.log("采集失败")
        
        threading.Thread(target=do_scrape, daemon=True).start()
    
    # ==================== 批量拉人页面 ====================
    def create_invite_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="批量拉人")
        
        frame = ttk.LabelFrame(page, text="拉人设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="目标群组:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.target_group = ttk.Entry(frame, width=50)
        self.target_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="拉人数量:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.invite_limit = ttk.Entry(frame, width=10)
        self.invite_limit.insert(0, "50")
        self.invite_limit.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="拉人间隔(秒):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.invite_delay_entry = ttk.Entry(frame, width=10)
        self.invite_delay_entry.insert(0, "60")
        self.invite_delay_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="选择任务账号:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.task_account = ttk.Combobox(frame, values=["全部账号"] + [a.get('phone', '') for a in self.accounts], width=30)
        self.task_account.set("全部账号")
        self.task_account.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="开始拉人", command=self.start_invite).pack()
    
    def start_invite(self):
        group = self.target_group.get()
        limit = self.invite_limit.get()
        delay = self.invite_delay_entry.get()
        
        if not group:
            self.log("请输入目标群组")
            return
        if not os.path.exists("members.json"):
            self.log("请先采集成员")
            return
        
        with open("members.json", "r") as f:
            members = json.load(f)
        
        self.log(f"开始拉人: 共 {min(int(limit), len(members))} 人")
        
        def do_invite():
            success = 0
            for i, m in enumerate(members[:int(limit)]):
                try:
                    result = self.call_api("/invite", {"group": group, "user_id": m['id']})
                    if result and result.get("success"):
                        success += 1
                        self.log(f"拉人成功: {m.get('first_name', m.get('username', m['id']))}")
                    time.sleep(int(delay))
                except Exception as e:
                    self.log(f"拉人失败: {e}")
            self.log(f"拉人完成: 成功 {success}")
        
        threading.Thread(target=do_invite, daemon=True).start()
    
    # ==================== 群发广告页面 ====================
    def create_send_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="群发广告")
        
        frame = ttk.LabelFrame(page, text="群发设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="选择任务账号:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.send_account = ttk.Combobox(frame, values=["全部账号"] + [a.get('phone', '') for a in self.accounts], width=30)
        self.send_account.set("全部账号")
        self.send_account.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="广告词:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.ad_text = scrolledtext.ScrolledText(frame, width=60, height=5)
        self.ad_text.grid(row=1, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(btn_frame, text="导入广告词文本", command=self.import_ad_text).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="导入用户列表", command=self.import_user_list).pack(side="left", padx=2)
        
        ttk.Label(frame, text="时间间隔(秒):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.send_delay = ttk.Entry(frame, width=10)
        self.send_delay.insert(0, "30")
        self.send_delay.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="线程数:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.thread_count = ttk.Entry(frame, width=10)
        self.thread_count.insert(0, "1")
        self.thread_count.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame2, text="开始群发", command=self.start_send).pack()
    
    def import_ad_text(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.ad_text.delete("1.0", tk.END)
            self.ad_text.insert("1.0", content)
            self.log(f"导入广告词: {file_path}")
    
    def import_user_list(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")])
        if file_path:
            self.log(f"导入用户列表: {file_path}")
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                self.log(f"导入 {len(users)} 个用户")
    
    def start_send(self):
        ad_content = self.ad_text.get("1.0", tk.END).strip()
        if not ad_content:
            self.log("请输入广告词")
            return
        
        if not os.path.exists("members.json"):
            self.log("请先导入用户列表")
            return
        
        with open("members.json", "r") as f:
            members = json.load(f)
        
        delay = int(self.send_delay.get())
        threads = int(self.thread_count.get())
        
        self.log(f"开始群发: {len(members)} 个用户, 线程数: {threads}, 间隔: {delay}秒")
        
        def do_send(start_idx, end_idx):
            for i in range(start_idx, min(end_idx, len(members))):
                try:
                    result = self.call_api("/send", {"user_id": members[i]['id'], "message": ad_content})
                    if result and result.get("success"):
                        self.log(f"发送成功: {members[i].get('first_name', members[i].get('username', members[i]['id']))}")
                    time.sleep(delay)
                except Exception as e:
                    self.log(f"发送失败: {e}")
        
        chunk_size = len(members) // threads if threads > 0 else len(members)
        for t in range(threads):
            start = t * chunk_size
            end = start + chunk_size if t < threads - 1 else len(members)
            threading.Thread(target=do_send, args=(start, end), daemon=True).start()
    
    # ==================== 自动群聊页面 ====================
    def create_group_chat_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动群聊+回复")
        
        frame = ttk.LabelFrame(page, text="群聊设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="目标群组:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.chat_group = ttk.Entry(frame, width=50)
        self.chat_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="发言间隔(秒):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.chat_interval = ttk.Entry(frame, width=10)
        self.chat_interval.insert(0, "60")
        self.chat_interval.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="每日上限:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.chat_daily = ttk.Entry(frame, width=10)
        self.chat_daily.insert(0, "100")
        self.chat_daily.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="启动炒群", command=self.start_group_chat).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="停止炒群", command=self.stop_group_chat).pack(side="left", padx=5)
        
        kw_frame = ttk.LabelFrame(page, text="关键词自动回复")
        kw_frame.pack(fill="x", padx=10, pady=5)
        
        self.keyword_text = scrolledtext.ScrolledText(kw_frame, width=80, height=6)
        self.keyword_text.pack(fill="x", padx=5, pady=5)
        
        btn_frame2 = ttk.Frame(kw_frame)
        btn_frame2.pack(pady=5)
        ttk.Button(btn_frame2, text="保存关键词配置", command=self.save_keywords).pack()
    
    def start_group_chat(self):
        group = self.chat_group.get()
        if not group:
            self.log("请输入目标群组")
            return
        self.log(f"启动炒群: {group}")
        self.running_tasks['chat'] = True
    
    def stop_group_chat(self):
        self.running_tasks['chat'] = False
        self.log("停止炒群")
    
    def save_keywords(self):
        content = self.keyword_text.get("1.0", tk.END)
        with open("keywords.json", "w", encoding="utf-8") as f:
            f.write(content)
        self.log("关键词配置已保存")
    
    # ==================== 自动注册页面 ====================
    def create_auto_register_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动注册账号")
        
        frame = ttk.LabelFrame(page, text="注册设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="接码平台API:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.sms_api = ttk.Entry(frame, width=50)
        self.sms_api.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="API Key:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.sms_key = ttk.Entry(frame, width=50, show="*")
        self.sms_key.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="注册数量:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.register_count = ttk.Entry(frame, width=10)
        self.register_count.insert(0, "10")
        self.register_count.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="开始批量注册", command=self.start_register).pack()
    
    def start_register(self):
        self.log("批量注册功能需要对接具体接码平台API")
        messagebox.showinfo("提示", "批量注册功能开发中")
    
    # ==================== 监听页面 ====================
    def create_monitor_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="监听群组")
        
        frame = ttk.LabelFrame(page, text="监听设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="监听群组列表:").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self.monitor_groups = scrolledtext.ScrolledText(frame, width=60, height=6)
        self.monitor_groups.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="触发动作:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.monitor_action = ttk.Combobox(frame, values=["私信", "拉入群组", "两者都做"], width=20)
        self.monitor_action.set("私信")
        self.monitor_action.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="目标群组(拉人用):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.monitor_target = ttk.Entry(frame, width=40)
        self.monitor_target.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="私信内容:").grid(row=3, column=0, sticky="nw", padx=5, pady=5)
        self.monitor_msg = scrolledtext.ScrolledText(frame, width=60, height=4)
        self.monitor_msg.grid(row=3, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="启动监听", command=self.start_monitor).pack()
    
    def start_monitor(self):
        self.log("监听功能需要服务器端支持实时消息推送")
        messagebox.showinfo("提示", "监听功能开发中")
    
    # ==================== 话术配置页面 ====================
    def create_script_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="话术配置")
        
        frame = ttk.LabelFrame(page, text="话术库")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.script_text = scrolledtext.ScrolledText(frame, width=80, height=15)
        self.script_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="导入TXT", command=self.import_txt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_scripts).pack(side="left", padx=5)
    
    def import_txt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", content)
            self.log(f"导入话术: {file_path}")
    
    def save_scripts(self):
        content = self.script_text.get("1.0", tk.END)
        with open("scripts.txt", "w", encoding="utf-8") as f:
            f.write(content)
        self.log("话术已保存")
    
    # ==================== 日志页面 ====================
    def create_log_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="运行日志")
        
        frame = ttk.LabelFrame(page, text="日志记录")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(frame, width=100, height=20)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="清空日志", command=self.clear_log).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="导出日志", command=self.export_log).pack(side="left", padx=5)
    
    def clear_log(self):
        self.log_text.delete("1.0", tk.END)
        self.log("日志已清空")
    
    def export_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            content = self.log_text.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.log(f"日志已导出: {file_path}")
    
    def export_config(self):
        config = {
            "accounts": self.accounts,
            "proxies": self.proxies,
            "server": self.server_entry.get()
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.log("配置已导出")
    
    def import_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.accounts = config.get("accounts", [])
            self.proxies = config.get("proxies", [])
            self.server_entry.delete(0, tk.END)
            self.server_entry.insert(0, config.get("server", SERVER))
            self.refresh_account_list()
            self.refresh_proxy_list()
            self.log("配置已导入")
    
    def about(self):
        messagebox.showinfo("关于", "天师府TG全能营销系统\n联系@Tian2547\n\n功能：\n- 多账号管理\n- 代理IP管理\n- 采集群成员\n- 批量拉人\n- 群发广告\n- 自动群聊\n- 话术配置\n\n服务器: " + SERVER)

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
