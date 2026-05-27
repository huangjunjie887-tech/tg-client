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
import shutil

# 内置服务器地址，不需要用户配置
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
        self.groups = []        # 分组列表
        self.running_tasks = {}
        
        # 获取机器码
        self.machine_id = self.get_machine_id()
        
        # 先显示卡密登录窗口
        self.show_card_login()
    
    def get_machine_id(self):
        """获取设备唯一标识"""
        try:
            mac = uuid.getnode()
            hostname = platform.node()
            machine_id = hashlib.md5(f"{mac}{hostname}".encode()).hexdigest()
            return machine_id
        except:
            return hashlib.md5(platform.node().encode()).hexdigest()
    
    def show_card_login(self):
        """显示卡密登录窗口"""
        login_window = tk.Toplevel(self.root)
        login_window.title("卡密登录 - 天师府TG全能营销系统")
        login_window.geometry("450x350")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        
        login_window.update_idletasks()
        x = (login_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (login_window.winfo_screenheight() // 2) - (350 // 2)
        login_window.geometry(f"+{x}+{y}")
        
        title_label = tk.Label(login_window, text="天师府TG全能营销系统", font=("微软雅黑", 18, "bold"))
        title_label.pack(pady=20)
        
        sub_label = tk.Label(login_window, text="请输入卡密激活", font=("微软雅黑", 10))
        sub_label.pack()
        
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
        
        tip_label = tk.Label(login_window, text="购买卡密请联系 @Tian2547", font=("微软雅黑", 9), foreground="gray")
        tip_label.pack(side="bottom", pady=10)
        
        self.card_entry.bind("<Return>", lambda event: self.verify_card(login_window))
    
    def verify_card(self, login_window):
        """验证卡密"""
        card_code = self.card_entry.get().strip()
        if not card_code:
            self.login_status.config(text="请输入卡密", foreground="red")
            return
        
        self.login_status.config(text="验证中...", foreground="blue")
        login_window.update()
        
        try:
            resp = requests.post(
                CARD_API,
                json={"action": "verify", "card": card_code, "machine_id": self.machine_id},
                timeout=15,
                proxies={"http": None, "https": None}
            )
            result = resp.json()
            
            if result.get("success"):
                self.is_logged_in = True
                self.card_info = result
                self.login_status.config(text="激活成功！正在启动...", foreground="green")
                login_window.update()
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
        login_window.destroy()
        self.init_main_interface()
    
    def init_main_interface(self):
        """初始化主界面"""
        self.create_menu()
        
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
        
        self.status_bar = ttk.Label(self.root, text=f"已激活 | 有效期: {self.card_info.get('expire_date', '永久')} | 服务器: {SERVER}", relief="sunken")
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
        if self.card_info:
            messagebox.showinfo("卡密信息", 
                f"天师府TG全能营销系统\n\n"
                f"卡密状态: 已激活\n"
                f"有效期至: {self.card_info.get('expire_date', '永久')}\n"
                f"设备绑定: 已绑定\n"
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
        
        # 分组管理工具栏
        group_toolbar = ttk.LabelFrame(page, text="分组管理")
        group_toolbar.pack(fill="x", padx=10, pady=5)
        
        group_frame = ttk.Frame(group_toolbar)
        group_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(group_frame, text="当前分组:").pack(side="left", padx=5)
        self.group_combobox = ttk.Combobox(group_frame, values=self.groups, width=20)
        self.group_combobox.pack(side="left", padx=5)
        if self.groups:
            self.group_combobox.set(self.groups[0])
        
        ttk.Button(group_frame, text="新建分组", command=self.create_group).pack(side="left", padx=5)
        ttk.Button(group_frame, text="删除分组", command=self.delete_group).pack(side="left", padx=5)
        ttk.Button(group_frame, text="移动账号到分组", command=self.move_to_group).pack(side="left", padx=5)
        
        # 账号操作工具栏
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(toolbar, text="导入账号(文件夹)", command=self.import_accounts_folder).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导出账号", command=self.export_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中账号", command=self.delete_selected_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除死号", command=self.delete_dead_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="账号检测", command=self.check_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="资料修改", command=self.edit_profile).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(page, text="账号列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "手机号", "分组", "昵称", "当前任务", "上一次操作", "账号状态", "注册时长")
        self.account_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.account_tree.heading(col, text=col)
        
        self.account_tree.column("序号", anchor="center", width=60)
        self.account_tree.column("手机号", anchor="center", width=120)
        self.account_tree.column("分组", anchor="center", width=100)
        self.account_tree.column("昵称", anchor="center", width=120)
        self.account_tree.column("当前任务", anchor="center", width=120)
        self.account_tree.column("上一次操作", anchor="center", width=150)
        self.account_tree.column("账号状态", anchor="center", width=100)
        self.account_tree.column("注册时长", anchor="center", width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        self.account_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
    
    def create_group(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("新建分组")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="分组名称:").pack(pady=20)
        group_name = ttk.Entry(dialog, width=30)
        group_name.pack(pady=5)
        
        def save_group():
            name = group_name.get().strip()
            if name:
                if name not in self.groups:
                    self.groups.append(name)
                    self.group_combobox['values'] = self.groups
                    self.group_combobox.set(name)
                    self.log(f"创建分组: {name}")
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "分组已存在")
        
        ttk.Button(dialog, text="确定", command=save_group).pack(pady=20)
    
    def delete_group(self):
        current_group = self.group_combobox.get()
        if not current_group:
            messagebox.showwarning("提示", "请选择要删除的分组")
            return
        if current_group == "默认分组":
            messagebox.showwarning("提示", "默认分组不能删除")
            return
        
        if messagebox.askyesno("确认", f"确定要删除分组「{current_group}」吗？\n该分组下的账号将移动到「默认分组」"):
            # 将分组下的账号移动到默认分组
            for acc in self.accounts:
                if acc.get('group', '默认分组') == current_group:
                    acc['group'] = '默认分组'
            self.groups.remove(current_group)
            if not self.groups:
                self.groups = ["默认分组"]
            self.group_combobox['values'] = self.groups
            self.group_combobox.set(self.groups[0] if self.groups else "")
            self.refresh_account_list()
            self.log(f"删除分组: {current_group}")
    
    def move_to_group(self):
        selected = self.account_tree.selection()
        if not selected:
            self.log("请先选择要移动的账号")
            return
        
        target_group = self.group_combobox.get()
        if not target_group:
            messagebox.showwarning("提示", "请选择目标分组")
            return
        
        for item in selected:
            idx = int(self.account_tree.item(item)['values'][0]) - 1
            self.accounts[idx]['group'] = target_group
        
        self.refresh_account_list()
        self.log(f"移动 {len(selected)} 个账号到分组: {target_group}")
    
    def import_accounts_folder(self):
        """导入账号文件夹"""
        # 先选择分组
        target_group = self.group_combobox.get()
        if not target_group:
            # 如果没有分组，提示创建
            if messagebox.askyesno("提示", "请先创建分组，是否现在创建？"):
                self.create_group()
                return
            target_group = "默认分组"
            if "默认分组" not in self.groups:
                self.groups.append("默认分组")
                self.group_combobox['values'] = self.groups
                self.group_combobox.set("默认分组")
        
        folder = filedialog.askdirectory(title="选择账号文件夹")
        if folder:
            self.log(f"从文件夹导入账号: {folder}")
            count = 0
            for item in os.listdir(folder):
                item_path = os.path.join(folder, item)
                # 支持 .session 文件
                if item.endswith(".session"):
                    phone = item.replace(".session", "")
                    self.accounts.append({
                        "phone": phone,
                        "nickname": "",
                        "group": target_group,
                        "status": "正常",
                        "register_time": "未知",
                        "session_path": item_path
                    })
                    count += 1
                # 支持文件夹（tdata或其他账号文件夹）
                elif os.path.isdir(item_path):
                    self.accounts.append({
                        "phone": item,
                        "nickname": "账号",
                        "group": target_group,
                        "status": "正常",
                        "register_time": "未知",
                        "session_path": item_path
                    })
                    count += 1
            self.refresh_account_list()
            self.log(f"导入 {count} 个账号到分组「{target_group}」")
    
    def export_accounts(self):
        """导出账号 - 导出为.session文件格式，与导入格式一致"""
        selected = self.account_tree.selection()
        if not selected:
            self.log("请先选择要导出的账号")
            return
        
        export_folder = filedialog.askdirectory(title="选择导出文件夹")
        if export_folder:
            export_count = 0
            for item in selected:
                idx = int(self.account_tree.item(item)['values'][0]) - 1
                acc = self.accounts[idx]
                session_path = acc.get('session_path', '')
                
                if session_path and os.path.exists(session_path):
                    # 如果是.session文件，直接复制
                    filename = os.path.basename(session_path)
                    dest = os.path.join(export_folder, filename)
                    shutil.copy2(session_path, dest)
                    export_count += 1
                elif acc.get('phone'):
                    # 如果没有session_path，创建一个空的.session文件占位
                    session_file = os.path.join(export_folder, f"{acc['phone']}.session")
                    with open(session_file, 'w') as f:
                        f.write("# 请将真实的.session文件替换此文件")
                    export_count += 1
            
            self.log(f"导出 {export_count} 个账号到 {export_folder}")
    
    def delete_selected_accounts(self):
        """删除选中的账号"""
        selected = self.account_tree.selection()
        if selected:
            if messagebox.askyesno("确认", f"确定要删除选中的 {len(selected)} 个账号吗？"):
                # 从后往前删除，避免索引错误
                indices = sorted([int(self.account_tree.item(item)['values'][0]) - 1 for item in selected], reverse=True)
                for idx in indices:
                    self.accounts.pop(idx)
                self.refresh_account_list()
                self.log(f"删除 {len(selected)} 个选中账号")
    
    def delete_dead_accounts(self):
        """一键删除所有账号状态为"销号"的账号"""
        dead_indices = []
        for i, acc in enumerate(self.accounts):
            if acc.get('status') == '销号':
                dead_indices.append(i)
        
        if dead_indices:
            # 从后往前删除
            for idx in sorted(dead_indices, reverse=True):
                self.accounts.pop(idx)
            self.refresh_account_list()
            self.log(f"一键删除 {len(dead_indices)} 个已销号账号")
        else:
            self.log("没有发现已销号的账号")
    
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
                i, 
                acc.get('phone', ''), 
                acc.get('group', '默认分组'),
                acc.get('nickname', ''),
                acc.get('current_task', ''),
                acc.get('last_action', ''),
                acc.get('status', '正常'), 
                acc.get('register_time', '未知')
            ))
    
    # ==================== 代理IP页面 ====================
    def create_proxy_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="代理IP")
        
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        self.proxy_count_label = ttk.Label(toolbar, text=f"IP数: {len(self.proxies)}/10")
        self.proxy_count_label.pack(side="left", padx=10)
        
        ttk.Button(toolbar, text="添加代理IP", command=self.add_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除代理IP", command=self.delete_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="检测代理IP", command=self.check_proxies).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(page, text="代理列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "代理类型", "IP/域名", "端口", "用户名", "密码", "状态")
        self.proxy_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.proxy_tree.heading(col, text=col)
        
        self.proxy_tree.column("序号", anchor="center", width=50)
        self.proxy_tree.column("代理类型", anchor="center", width=80)
        self.proxy_tree.column("IP/域名", anchor="center", width=120)
        self.proxy_tree.column("端口", anchor="center", width=80)
        self.proxy_tree.column("用户名", anchor="center", width=100)
        self.proxy_tree.column("密码", anchor="center", width=80)
        self.proxy_tree.column("状态", anchor="center", width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.proxy_tree.yview)
        self.proxy_tree.configure(yscrollcommand=scrollbar.set)
        self.proxy_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
    
    def add_proxy(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加代理")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
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
            "groups": self.groups
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
            self.groups = config.get("groups", [])
            if not self.groups:
                self.groups = ["默认分组"]
            self.group_combobox['values'] = self.groups
            self.group_combobox.set(self.groups[0] if self.groups else "")
            self.refresh_account_list()
            self.refresh_proxy_list()
            self.log("配置已导入")
    
    def about(self):
        messagebox.showinfo("关于", "天师府TG全能营销系统\n联系@Tian2547\n\n功能：\n- 多账号管理\n- 代理IP管理\n- 采集群成员\n- 批量拉人\n- 群发广告\n- 自动群聊\n- 话术配置")

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
