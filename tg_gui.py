import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
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
import sqlite3
import asyncio
from struct import pack, unpack

# 内置服务器地址
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
    
    def center_window(self, window, width, height):
        window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    def show_centered_info(self, title, message):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        self.center_window(dialog, 400, 200)
        tk.Label(dialog, text=message, font=("微软雅黑", 10), wraplength=350).pack(pady=40)
        ttk.Button(dialog, text="确定", command=dialog.destroy, width=12).pack(pady=10)
    
    def show_centered_warning(self, title, message):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        self.center_window(dialog, 400, 200)
        tk.Label(dialog, text=message, font=("微软雅黑", 10), wraplength=350, fg="orange").pack(pady=40)
        ttk.Button(dialog, text="确定", command=dialog.destroy, width=12).pack(pady=10)
    
    def show_centered_error(self, title, message):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        self.center_window(dialog, 400, 200)
        tk.Label(dialog, text=message, font=("微软雅黑", 10), wraplength=350, fg="red").pack(pady=40)
        ttk.Button(dialog, text="确定", command=dialog.destroy, width=12).pack(pady=10)
    
    def show_centered_yesno(self, title, message, callback_yes=None, callback_no=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        self.center_window(dialog, 400, 200)
        tk.Label(dialog, text=message, font=("微软雅黑", 10), wraplength=350).pack(pady=30)
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def on_yes():
            dialog.destroy()
            if callback_yes:
                callback_yes()
        
        def on_no():
            dialog.destroy()
            if callback_no:
                callback_no()
        
        ttk.Button(btn_frame, text="是", command=on_yes, width=10).pack(side="left", padx=20)
        ttk.Button(btn_frame, text="否", command=on_no, width=10).pack(side="left", padx=20)
        return dialog
    
    def log(self, msg, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def show_card_login(self):
        login_window = tk.Toplevel(self.root)
        login_window.title("卡密登录 - 天师府TG全能营销系统")
        login_window.geometry("450x350")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        self.center_window(login_window, 450, 350)
        
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
        except Exception as e:
            self.login_status.config(text=f"验证失败: {str(e)[:30]}", foreground="red")
    
    def buy_card(self):
        import webbrowser
        webbrowser.open("https://t.me/Tian2547")
    
    def on_login_success(self, login_window):
        login_window.destroy()
        self.init_main_interface()
    
    def init_main_interface(self):
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
        
        self.status_bar = ttk.Label(self.root, text=f"已激活 | 有效期: {self.card_info.get('expire_date', '永久')} | 联系@Tian2547", relief="sunken")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.log("系统启动完成")
    
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
            info_text = f"天师府TG全能营销系统\n\n卡密状态: 已激活\n有效期至: {self.card_info.get('expire_date', '永久')}\n设备绑定: 已绑定\n\n联系客服: @Tian2547"
            self.show_centered_info("卡密信息", info_text)
    
    def read_session_data(self, session_path):
        """从SQLite session文件中读取auth_key和账号信息"""
        try:
            conn = sqlite3.connect(session_path)
            cursor = conn.cursor()
            
            # 读取sessions表
            cursor.execute("SELECT dc_id, server_address, port, auth_key FROM sessions")
            session_row = cursor.fetchone()
            
            # 读取entities表获取账号信息
            cursor.execute("SELECT id, phone, name FROM entities")
            entity_row = cursor.fetchone()
            
            conn.close()
            
            if session_row:
                dc_id, server_address, port, auth_key = session_row
                phone = entity_row[1] if entity_row else None
                name = entity_row[2] if entity_row else None
                user_id = entity_row[0] if entity_row else None
                
                return {
                    'valid': True,
                    'dc_id': dc_id,
                    'server': server_address,
                    'port': port,
                    'auth_key': auth_key,
                    'phone': phone,
                    'name': name,
                    'user_id': user_id
                }
            return {'valid': False}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    # ==================== 多账号管理页面 ====================
    def create_account_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="多账号管理")
        
        toolbar = ttk.Frame(page)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(toolbar, text="分组管理", command=self.open_group_manager).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导入账号(文件夹)", command=self.import_accounts_folder).pack(side="left", padx=2)
        ttk.Button(toolbar, text="一键登录所有账号", command=self.login_all_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="账号检测", command=self.check_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="资料修改", command=self.edit_profile).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中账号", command=self.delete_selected_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除死号", command=self.delete_dead_accounts).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(page, text="账号列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "手机号", "分组", "昵称", "当前任务", "上一次操作", "账号状态", "注册时长", "代理IP")
        self.account_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.account_tree.heading(col, text=col)
        
        self.account_tree.column("序号", anchor="center", width=50)
        self.account_tree.column("手机号", anchor="center", width=120)
        self.account_tree.column("分组", anchor="center", width=100)
        self.account_tree.column("昵称", anchor="center", width=120)
        self.account_tree.column("当前任务", anchor="center", width=100)
        self.account_tree.column("上一次操作", anchor="center", width=130)
        self.account_tree.column("账号状态", anchor="center", width=100)
        self.account_tree.column("注册时长", anchor="center", width=100)
        self.account_tree.column("代理IP", anchor="center", width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        self.account_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
    
    def open_group_manager(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("分组管理")
        dialog.geometry("550x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 550, 500)
        
        group_frame = ttk.LabelFrame(dialog, text="分组列表")
        group_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        group_listbox = tk.Listbox(group_frame, height=8)
        group_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        for g in self.groups:
            group_listbox.insert(tk.END, g)
        
        btn_frame = ttk.Frame(group_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Label(btn_frame, text="分组名称:").pack(side="left", padx=5)
        group_name_entry = ttk.Entry(btn_frame, width=15)
        group_name_entry.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="新建", command=lambda: self.add_group(group_name_entry, group_listbox)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="重命名", command=lambda: self.rename_group(group_name_entry, group_listbox)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="删除", command=lambda: self.delete_group_from_manager(group_listbox)).pack(side="left", padx=2)
        
        move_frame = ttk.LabelFrame(dialog, text="移动账号到分组")
        move_frame.pack(fill="x", padx=10, pady=10)
        
        account_frame = ttk.Frame(move_frame)
        account_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(account_frame, text="选择账号:").pack(side="left", padx=5)
        account_var = tk.StringVar()
        account_combo = ttk.Combobox(account_frame, textvariable=account_var, width=35)
        account_combo.pack(side="left", padx=5, fill="x", expand=True)
        
        def refresh_account_combo():
            accounts_list = [f"{i+1}. {acc.get('phone', '未知')}" for i, acc in enumerate(self.accounts)]
            account_combo['values'] = accounts_list
            if accounts_list:
                account_combo.set(accounts_list[0])
        refresh_account_combo()
        
        target_frame = ttk.Frame(move_frame)
        target_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(target_frame, text="目标分组:").pack(side="left", padx=5)
        target_group_var = tk.StringVar()
        target_group_combo = ttk.Combobox(target_frame, textvariable=target_group_var, values=self.groups, width=20)
        target_group_combo.pack(side="left", padx=5)
        if self.groups:
            target_group_combo.set(self.groups[0])
        
        button_line = ttk.Frame(move_frame)
        button_line.pack(pady=10)
        
        def move_account_to_group():
            if not self.accounts:
                self.show_centered_warning("提示", "没有账号可移动")
                return
            selected_account = account_var.get()
            target_group = target_group_var.get()
            if not selected_account or not target_group:
                self.show_centered_warning("提示", "请选择账号和目标分组")
                return
            idx = int(selected_account.split('.')[0]) - 1
            self.accounts[idx]['group'] = target_group
            self.refresh_account_list()
            refresh_account_combo()
            self.log(f"移动账号到分组「{target_group}」")
        
        def refresh_all():
            refresh_account_combo()
            target_group_combo['values'] = self.groups
            if self.groups:
                target_group_combo.set(self.groups[0])
            group_listbox.delete(0, tk.END)
            for g in self.groups:
                group_listbox.insert(tk.END, g)
        
        ttk.Button(button_line, text="移动账号", command=move_account_to_group, width=12).pack(side="left", padx=5)
        ttk.Button(button_line, text="刷新列表", command=refresh_all, width=12).pack(side="left", padx=5)
    
    def add_group(self, name_entry, listbox):
        name = name_entry.get().strip()
        if name and name not in self.groups:
            self.groups.append(name)
            listbox.insert(tk.END, name)
            name_entry.delete(0, tk.END)
            self.log(f"创建分组: {name}")
        elif name in self.groups:
            self.show_centered_error("错误", "分组已存在")
    
    def rename_group(self, name_entry, listbox):
        selected = listbox.curselection()
        if selected:
            old_name = listbox.get(selected[0])
            if old_name == "默认分组":
                self.show_centered_warning("提示", "默认分组不能重命名")
                return
            new_name = name_entry.get().strip()
            if new_name and new_name not in self.groups:
                for acc in self.accounts:
                    if acc.get('group') == old_name:
                        acc['group'] = new_name
                idx = self.groups.index(old_name)
                self.groups[idx] = new_name
                listbox.delete(selected[0])
                listbox.insert(selected[0], new_name)
                self.refresh_account_list()
                self.log(f"重命名分组: {old_name} -> {new_name}")
                name_entry.delete(0, tk.END)
    
    def delete_group_from_manager(self, listbox):
        selected = listbox.curselection()
        if selected:
            group_name = listbox.get(selected[0])
            if group_name == "默认分组":
                self.show_centered_warning("提示", "默认分组不能删除")
                return
            def do_delete():
                for acc in self.accounts:
                    if acc.get('group') == group_name:
                        acc['group'] = '默认分组'
                self.groups.remove(group_name)
                listbox.delete(selected[0])
                self.refresh_account_list()
                self.log(f"删除分组: {group_name}")
            self.show_centered_yesno("确认", f"确定删除分组「{group_name}」？账号将移至默认分组", do_delete)
    
    def import_accounts_folder(self):
        if not self.groups:
            self.groups = ["默认分组"]
        
        group_dialog = tk.Toplevel(self.root)
        group_dialog.title("选择分组")
        group_dialog.geometry("300x150")
        group_dialog.resizable(False, False)
        group_dialog.transient(self.root)
        group_dialog.grab_set()
        self.center_window(group_dialog, 300, 150)
        
        ttk.Label(group_dialog, text="请选择导入账号的目标分组:").pack(pady=15)
        group_var = tk.StringVar()
        group_combo = ttk.Combobox(group_dialog, textvariable=group_var, values=self.groups, width=25)
        group_combo.pack(pady=5)
        if self.groups:
            group_combo.set(self.groups[0])
        
        def confirm_import():
            target_group = group_var.get() or "默认分组"
            group_dialog.destroy()
            self.do_import_accounts(target_group)
        ttk.Button(group_dialog, text="确定", command=confirm_import).pack(pady=15)
    
    def do_import_accounts(self, target_group):
        folder = filedialog.askdirectory(title="选择账号文件夹（包含.session文件的目录）")
        if not folder:
            return
        
        self.log(f"开始扫描账号文件夹: {folder}")
        
        session_files = []
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".session"):
                    session_files.append(os.path.join(root_dir, file))
                    self.log(f"发现session文件: {file}")
        
        if not session_files:
            self.log("未找到任何.session文件")
            self.show_centered_warning("导入失败", "未找到任何.session文件")
            return
        
        count = 0
        for session_path in session_files:
            filename = os.path.basename(session_path)
            phone = filename.replace(".session", "")
            
            # 读取session数据
            session_data = self.read_session_data(session_path)
            
            exists = False
            for acc in self.accounts:
                if acc.get('phone') == phone:
                    exists = True
                    break
            
            if exists:
                self.log(f"跳过重复账号: {phone}")
                continue
            
            self.accounts.append({
                "phone": phone,
                "nickname": session_data.get('name', '待获取') if session_data.get('valid') else '待获取',
                "group": target_group,
                "status": "正常" if session_data.get('valid') else "无效",
                "register_time": "未知",
                "session_path": session_path,
                "session_data": session_data,
                "proxy": ""
            })
            count += 1
            self.log(f"导入账号: {phone} - 昵称: {session_data.get('name', '无') if session_data.get('valid') else '无效'}")
        
        self.refresh_account_list()
        self.log(f"导入 {count} 个账号到分组「{target_group}」")
        if count > 0:
            self.show_centered_info("导入完成", f"成功导入 {count} 个账号\n\n注：账号状态已从session文件中读取")
    
    def login_all_accounts(self):
        """一键登录所有账号 - 验证session有效性"""
        accounts_to_login = []
        for i, acc in enumerate(self.accounts):
            status = acc.get('status', '')
            if status != '正常':
                accounts_to_login.append((i, acc))
            else:
                self.log(f"账号 {acc.get('phone')} 已有效，无需重新登录")
        
        if not accounts_to_login:
            self.log("所有账号都已有效")
            self.show_centered_info("提示", "所有账号都已有效")
            return
        
        self.log(f"开始验证 {len(accounts_to_login)} 个账号...")
        
        for idx, (i, acc) in enumerate(accounts_to_login, 1):
            phone = acc.get('phone', '')
            session_path = acc.get('session_path', '')
            
            self.log(f"[{idx}/{len(accounts_to_login)}] 正在验证账号: {phone}")
            
            if not session_path or not os.path.exists(session_path):
                self.log(f"❌ {phone}: session文件不存在")
                acc['status'] = '文件不存在'
                self.refresh_account_list()
                continue
            
            session_data = self.read_session_data(session_path)
            
            if session_data.get('valid'):
                acc['status'] = '正常'
                acc['nickname'] = session_data.get('name', phone)
                acc['session_data'] = session_data
                self.log(f"✅ {phone}: session有效 | 昵称: {acc['nickname']}")
            else:
                self.log(f"❌ {phone}: session无效")
                acc['status'] = '无效'
            
            self.refresh_account_list()
            time.sleep(0.5)
        
        self.log("账号验证完成")
        self.show_centered_info("验证完成", "账号验证已完成，请查看列表状态")
    
    def check_accounts(self):
        """检测账号状态"""
        selected = self.account_tree.selection()
        if not selected:
            self.show_centered_warning("提示", "请先选择要检测的账号")
            return
        
        self.log(f"开始检测 {len(selected)} 个账号...")
        
        for item in selected:
            idx = int(self.account_tree.item(item)['values'][0]) - 1
            acc = self.accounts[idx]
            phone = acc.get('phone', '')
            session_path = acc.get('session_path', '')
            
            if not session_path or not os.path.exists(session_path):
                acc['status'] = '文件不存在'
                self.log(f"❌ {phone}: session文件不存在")
                self.refresh_account_list()
                continue
            
            session_data = self.read_session_data(session_path)
            
            if session_data.get('valid'):
                acc['status'] = '正常'
                acc['nickname'] = session_data.get('name', phone)
                acc['session_data'] = session_data
                self.log(f"✅ {phone}: 有效 | 昵称: {acc['nickname']}")
            else:
                acc['status'] = '无效'
                self.log(f"❌ {phone}: session无效")
            
            self.refresh_account_list()
            time.sleep(0.5)
        
        self.log("账号检测完成")
    
    def edit_profile(self):
        selected = self.account_tree.selection()
        if not selected:
            self.show_centered_warning("提示", "请先选择要修改资料的账号")
            return
        
        idx = int(self.account_tree.item(selected[0])['values'][0]) - 1
        acc = self.accounts[idx]
        phone = acc.get('phone', '')
        
        self.show_centered_info("提示", f"账号 {phone}\n\n资料修改功能需要通过Telegram API\n当前session文件有效，如需修改昵称请使用Telegram客户端")
    
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
                acc.get('status', '待检测'), 
                acc.get('register_time', '未知'),
                acc.get('proxy', '未设置')
            ))
    
    def delete_selected_accounts(self):
        selected = self.account_tree.selection()
        if selected:
            def do_delete():
                indices = sorted([int(self.account_tree.item(item)['values'][0]) - 1 for item in selected], reverse=True)
                for idx in indices:
                    self.accounts.pop(idx)
                self.refresh_account_list()
                self.log(f"删除 {len(selected)} 个选中账号")
            self.show_centered_yesno("确认", f"确定删除 {len(selected)} 个账号？", do_delete)
    
    def delete_dead_accounts(self):
        dead_indices = [i for i, acc in enumerate(self.accounts) if acc.get('status') == '销号']
        if dead_indices:
            def do_delete():
                for idx in sorted(dead_indices, reverse=True):
                    self.accounts.pop(idx)
                self.refresh_account_list()
                self.log(f"删除 {len(dead_indices)} 个已销号账号")
            self.show_centered_yesno("确认", f"确定删除 {len(dead_indices)} 个已销号账号？", do_delete)
        else:
            self.show_centered_info("提示", "没有发现已销号的账号")
    
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
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 400, 300)
        
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
                self.show_centered_error("错误", "最多添加10个代理")
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
        if not self.proxies:
            self.log("没有代理需要检测")
            return
        
        self.log("开始检测代理...")
        
        def do_check():
            for i, p in enumerate(self.proxies):
                proxy_str = f"{p.get('host')}:{p.get('port')}"
                try:
                    proxy_url = f"{p.get('type')}://"
                    if p.get('user') and p.get('pass'):
                        proxy_url += f"{p.get('user')}:{p.get('pass')}@"
                    proxy_url += f"{p.get('host')}:{p.get('port')}"
                    
                    proxies = {p.get('type'): proxy_url}
                    
                    resp = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
                    if resp.status_code == 200:
                        p['status'] = f"可用 (IP: {resp.text})"
                        self.log(f"✅ {proxy_str}: 可用")
                    else:
                        p['status'] = "不可用"
                        self.log(f"❌ {proxy_str}: 不可用")
                except Exception as e:
                    p['status'] = f"不可用: {str(e)[:20]}"
                    self.log(f"❌ {proxy_str}: 不可用 - {str(e)[:30]}")
                
                self.root.after(0, self.refresh_proxy_list)
            
            self.log("代理检测完成")
        
        threading.Thread(target=do_check, daemon=True).start()
    
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
        
        ttk.Label(frame, text="选择采集账号:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.scrape_account = ttk.Combobox(frame, values=[a.get('phone', '') for a in self.accounts], width=30)
        self.scrape_account.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="开始采集", command=self.start_scrape).pack()
    
    def start_scrape(self):
        group = self.scrape_group.get()
        limit = self.scrape_limit.get()
        account_phone = self.scrape_account.get()
        
        if not group:
            self.log("请输入群组链接")
            return
        if not account_phone:
            self.log("请选择采集账号")
            return
        
        acc = None
        for a in self.accounts:
            if a.get('phone') == account_phone:
                acc = a
                break
        
        if not acc:
            self.log("未找到账号")
            return
        
        if acc.get('status') != '正常':
            self.log("账号session无效，请先导入有效的session文件")
            return
        
        session_path = acc.get('session_path', '')
        if not session_path or not os.path.exists(session_path):
            self.log("session文件不存在")
            return
        
        self.log(f"开始采集: {group} (数量: {limit}) 使用账号: {account_phone}")
        self.log("注意：采集功能需要通过Telegram API实现，当前版本已读取session中的账号信息")
        self.log(f"账号 {account_phone} 昵称: {acc.get('nickname', '未知')} session有效")
        self.show_centered_info("提示", f"账号 {account_phone} 已验证有效\n\n采集功能需要完整实现Telegram MTProto协议\n当前版本已成功读取session中的auth_key\n可配合Telethon或Pyrogram使用")
    
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
        self.task_account = ttk.Combobox(frame, values=[a.get('phone', '') for a in self.accounts], width=30)
        self.task_account.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="开始拉人", command=self.start_invite).pack()
    
    def start_invite(self):
        account_phone = self.task_account.get()
        
        if not account_phone:
            self.log("请选择任务账号")
            return
        
        acc = None
        for a in self.accounts:
            if a.get('phone') == account_phone:
                acc = a
                break
        
        if not acc:
            self.log("未找到账号")
            return
        
        if acc.get('status') != '正常':
            self.log("账号session无效，请先导入有效的session文件")
            return
        
        self.log(f"开始拉人，使用账号: {account_phone}")
        self.log(f"账号 {account_phone} 昵称: {acc.get('nickname', '未知')} session有效")
        self.show_centered_info("提示", f"账号 {account_phone} 已验证有效\n\n拉人功能需要完整实现Telegram MTProto协议\n当前版本已成功读取session中的auth_key")
    
    # ==================== 群发广告页面 ====================
    def create_send_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="群发广告")
        
        frame = ttk.LabelFrame(page, text="群发设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="选择任务账号:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.send_account = ttk.Combobox(frame, values=[a.get('phone', '') for a in self.accounts], width=30)
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
                with open("members.json", "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
                self.log(f"导入 {len(users)} 个用户到 members.json")
    
    def start_send(self):
        account_phone = self.send_account.get()
        
        if not account_phone:
            self.log("请选择任务账号")
            return
        
        acc = None
        for a in self.accounts:
            if a.get('phone') == account_phone:
                acc = a
                break
        
        if not acc:
            self.log("未找到账号")
            return
        
        if acc.get('status') != '正常':
            self.log("账号session无效，请先导入有效的session文件")
            return
        
        self.log(f"开始群发，使用账号: {account_phone}")
        self.log(f"账号 {account_phone} 昵称: {acc.get('nickname', '未知')} session有效")
        self.show_centered_info("提示", f"账号 {account_phone} 已验证有效\n\n群发功能需要完整实现Telegram MTProto协议\n当前版本已成功读取session中的auth_key")
    
    # ==================== 自动群聊页面 ====================
    def create_group_chat_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动群聊+回复")
        
        frame = ttk.LabelFrame(page, text="群聊设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="目标群组:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.chat_group = ttk.Entry(frame, width=50)
        self.chat_group.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="选择账号:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.chat_account = ttk.Combobox(frame, values=[a.get('phone', '') for a in self.accounts], width=30)
        self.chat_account.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="发言间隔(秒):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.chat_interval = ttk.Entry(frame, width=10)
        self.chat_interval.insert(0, "60")
        self.chat_interval.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="每日上限:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.chat_daily = ttk.Entry(frame, width=10)
        self.chat_daily.insert(0, "100")
        self.chat_daily.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="启动炒群", command=self.start_group_chat).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="停止炒群", command=self.stop_group_chat).pack(side="left", padx=5)
        
        kw_frame = ttk.LabelFrame(page, text="关键词自动回复")
        kw_frame.pack(fill="x", padx=10, pady=5)
        
        self.keyword_text = scrolledtext.ScrolledText(kw_frame, width=80, height=6)
        self.keyword_text.pack(fill="x", padx=5, pady=5)
        
        btn_frame2 = ttk.Frame(kw_frame)
        btn_frame2.pack(pady=5)
        ttk.Button(btn_frame2, text="保存关键词配置", command=self.save_keywords).pack(side="left", padx=5)
        ttk.Button(btn_frame2, text="加载关键词配置", command=self.load_keywords).pack(side="left", padx=5)
    
    def start_group_chat(self):
        account_phone = self.chat_account.get()
        
        if not account_phone:
            self.log("请选择账号")
            return
        
        acc = None
        for a in self.accounts:
            if a.get('phone') == account_phone:
                acc = a
                break
        
        if not acc:
            self.log("未找到账号")
            return
        
        if acc.get('status') != '正常':
            self.log("账号session无效，请先导入有效的session文件")
            return
        
        self.log(f"启动炒群，使用账号: {account_phone}")
        self.log(f"账号 {account_phone} 昵称: {acc.get('nickname', '未知')} session有效")
        self.show_centered_info("提示", f"账号 {account_phone} 已验证有效\n\n自动群聊功能需要完整实现Telegram MTProto协议")
    
    def stop_group_chat(self):
        self.running_tasks['chat'] = False
        self.log("停止炒群")
    
    def save_keywords(self):
        content = self.keyword_text.get("1.0", tk.END).strip()
        keywords = {}
        for line in content.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                keywords[key.strip()] = value.strip()
        with open("keywords.json", "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
        self.log("关键词配置已保存")
    
    def load_keywords(self):
        if os.path.exists("keywords.json"):
            with open("keywords.json", "r") as f:
                keywords = json.load(f)
            content = "\n".join([f"{k}={v}" for k, v in keywords.items()])
            self.keyword_text.delete("1.0", tk.END)
            self.keyword_text.insert("1.0", content)
            self.log("关键词配置已加载")
    
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
        
        ttk.Label(frame, text="保存路径:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.save_path = ttk.Entry(frame, width=40)
        self.save_path.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(frame, text="浏览", command=self.select_save_path).grid(row=3, column=2, padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="开始批量注册", command=self.start_register).pack()
    
    def select_save_path(self):
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.save_path.delete(0, tk.END)
            self.save_path.insert(0, folder)
    
    def start_register(self):
        self.log("批量注册功能需要对接具体接码平台API")
        self.show_centered_info("提示", "请先配置接码平台API")
    
    # ==================== 监听页面 ====================
    def create_monitor_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="监听群组")
        
        frame = ttk.LabelFrame(page, text="监听设置")
        frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame, text="选择监听账号:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.monitor_account = ttk.Combobox(frame, values=[a.get('phone', '') for a in self.accounts], width=30)
        self.monitor_account.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="监听群组列表(每行一个):").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.monitor_groups = scrolledtext.ScrolledText(frame, width=50, height=6)
        self.monitor_groups.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="触发动作:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.monitor_action = ttk.Combobox(frame, values=["私信", "拉入群组", "两者都做"], width=20)
        self.monitor_action.set("私信")
        self.monitor_action.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame, text="目标群组(拉人用):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.monitor_target = ttk.Entry(frame, width=40)
        self.monitor_target.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="私信内容:").grid(row=4, column=0, sticky="nw", padx=5, pady=5)
        self.monitor_msg = scrolledtext.ScrolledText(frame, width=50, height=4)
        self.monitor_msg.grid(row=4, column=1, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="启动监听", command=self.start_monitor).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="停止监听", command=self.stop_monitor).pack(side="left", padx=5)
    
    def start_monitor(self):
        self.log("监听功能开发中")
        self.show_centered_info("提示", "监听功能开发中")
    
    def stop_monitor(self):
        self.log("停止监听")
        self.running_tasks['monitor'] = False
    
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
        
        ttk.Button(btn_frame, text="导入TXT", command=self.import_script).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_scripts).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self.load_scripts).pack(side="left", padx=5)
    
    def import_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", content)
            self.log(f"导入话术: {file_path}")
    
    def save_scripts(self):
        content = self.script_text.get("1.0", tk.END).strip()
        with open("scripts.txt", "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"话术已保存")
    
    def load_scripts(self):
        if os.path.exists("scripts.txt"):
            with open("scripts.txt", "r", encoding="utf-8") as f:
                content = f.read()
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", content)
            self.log("话术已加载")
    
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
            "accounts": [{"phone": a.get('phone'), "group": a.get('group'), "session_path": a.get('session_path')} for a in self.accounts],
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
            self.groups = config.get("groups", ["默认分组"])
            if not self.groups:
                self.groups = ["默认分组"]
            self.refresh_account_list()
            self.refresh_proxy_list()
            self.log("配置已导入")
    
    def about(self):
        self.show_centered_info("关于", "天师府TG全能营销系统\n联系@Tian2547\n版本: 2.0\n\n功能：\n- 多账号管理\n- 代理IP管理\n- 采集群成员\n- 批量拉人\n- 群发广告\n- 自动群聊\n- 话术配置\n\n说明：已支持读取原生MTProto session文件\n可获取账号昵称、验证session有效性")

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
