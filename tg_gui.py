import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import requests
import json
import threading
import os
import time
import platform
import uuid
import hashlib
from datetime import datetime, timedelta
import shutil
import random
import sqlite3
import asyncio
import re
from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, UserDeactivatedError, SessionPasswordNeededError, 
    PhoneNumberBannedError, UserAlreadyParticipantError, UserPrivacyRestrictedError,
    PeerFloodError, InviteHashExpiredError, InviteHashInvalidError,
    ChannelInvalidError, ChannelPrivateError, UserInvalidError, UsernameInvalidError,
    UserKickedError, UserBannedInChannelError, ChatAdminRequiredError,
    UserNotMutualContactError, ChatWriteForbiddenError, UserChannelsTooMuchError
)
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantsRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsAdmins, ChannelParticipantsBots, ChannelParticipantsRecent, Message, InputPeerChannel, InputPhoto
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.types import UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth, UserStatusOffline, UserStatusOnline, InputFile
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest

SERVER = "http://172.98.23.64:5000"
CARD_API = "https://tgpremium.site/tgyinxiao/verify.php"
CONFIG_FILE = "tg_config.json"

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
        self.proxy_groups = ["默认分组"]
        self.groups = ["默认分组"]
        self.running_tasks = {}
        self.log_widgets = {}
        self.is_paused = False
        self.user_list_file_path = None
        self.user_list_lock = threading.Lock()
        
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("微软雅黑", 11, "bold"), padding=[20, 8])
        
        self.machine_id = self.get_machine_id()
        
        self.load_config()
        
        self.show_card_login()
    
    def get_machine_id(self):
        try:
            mac = uuid.getnode()
            hostname = platform.node()
            return hashlib.md5(f"{mac}{hostname}".encode()).hexdigest()
        except:
            return hashlib.md5(platform.node().encode()).hexdigest()
    
    def save_config(self):
        try:
            config = {
                "accounts": [],
                "proxies": self.proxies,
                "groups": self.groups,
                "proxy_groups": self.proxy_groups
            }
            for acc in self.accounts:
                config["accounts"].append({
                    "phone": acc.get("phone", ""),
                    "nickname": acc.get("nickname", ""),
                    "group": acc.get("group", "默认分组"),
                    "status": acc.get("status", ""),
                    "register_time": acc.get("register_time", ""),
                    "session_path": acc.get("session_path", ""),
                    "json_path": acc.get("json_path", ""),
                    "proxy": acc.get("proxy", "")
                })
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.accounts = config.get("accounts", [])
                self.proxies = config.get("proxies", [])
                self.groups = config.get("groups", ["默认分组"])
                self.proxy_groups = config.get("proxy_groups", ["默认分组"])
                if not self.groups:
                    self.groups = ["默认分组"]
                if not self.proxy_groups:
                    self.proxy_groups = ["默认分组"]
        except Exception as e:
            print(f"加载配置失败: {e}")
    
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
    
    def log(self, page_name, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {msg}\n"
        if page_name in self.log_widgets:
            self.log_widgets[page_name].insert(tk.END, log_entry)
            self.log_widgets[page_name].see(tk.END)
    
    def update_account_task(self, phone, task_name, is_current=True):
        for acc in self.accounts:
            if acc.get('phone') == phone:
                if is_current:
                    acc['current_task'] = task_name
                else:
                    acc['last_action'] = task_name
                break
        self.refresh_account_list()
    
    def remove_user_from_file(self, username):
        if not self.user_list_file_path or not os.path.exists(self.user_list_file_path):
            return False
        
        with self.user_list_lock:
            try:
                with open(self.user_list_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                clean_username = username.lstrip('@')
                new_lines = []
                removed = False
                for line in lines:
                    line_username = line.strip().lstrip('@')
                    if line_username != clean_username:
                        new_lines.append(line)
                    else:
                        removed = True
                
                if removed:
                    with open(self.user_list_file_path, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    return True
                return False
            except Exception as e:
                return False
    
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
            resp = requests.post(CARD_API, json={"action": "verify", "card": card_code, "machine_id": self.machine_id}, timeout=15, proxies={"http": None, "https": None})
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
        
        self.status_bar = ttk.Label(self.root, text=f"已激活 | 有效期: {self.card_info.get('expire_date', '永久')} | 联系@Tian2547", relief="sunken")
        self.status_bar.pack(side="bottom", fill="x")
        
        self.refresh_invite_group_filter()
        
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
    
    def refresh_invite_group_filter(self):
        if hasattr(self, 'invite_group_filter'):
            self.invite_group_filter['values'] = ["全部"] + self.groups
            self.invite_group_filter.set("全部")
        if hasattr(self, 'account_group_filter'):
            self.account_group_filter['values'] = ["全部"] + self.groups
            self.account_group_filter.set("全部")
        if hasattr(self, 'proxy_group_filter'):
            self.proxy_group_filter['values'] = ["全部"] + self.proxy_groups
            self.proxy_group_filter.set("全部")
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_command(label="导入配置", command=self.import_config)
        file_menu.add_separator()
        file_menu.add_command(label="卡密信息", command=self.show_card_info)
        file_menu.add_command(label="退出", command=self.on_exit)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.about)
    
    def on_exit(self):
        self.save_config()
        self.root.quit()
    
    def show_card_info(self):
        if self.card_info:
            info_text = f"天师府TG全能营销系统\n\n卡密状态: 已激活\n有效期至: {self.card_info.get('expire_date', '永久')}\n设备绑定: 已绑定\n\n联系客服: @Tian2547"
            self.show_centered_info("卡密信息", info_text)
    
    def read_account_from_json(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {
                'valid': True,
                'phone': data.get('phone', ''),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'register_time': data.get('register_time', 0),
                'twoFA': data.get('twoFA', ''),
                'proxy': data.get('proxy', ''),
                'app_id': data.get('app_id', 0),
                'app_hash': data.get('app_hash', '')
            }
        except:
            return {'valid': False}
    
    def get_account_api_credentials(self, acc):
        account_info = acc.get('account_info', {})
        if account_info and account_info.get('app_id') and account_info.get('app_hash'):
            return account_info.get('app_id'), account_info.get('app_hash')
        return 34256693, "6cb54edb306a8a938d7759b6b8fb82cf"
    
    def get_account_twofa(self, acc):
        account_info = acc.get('account_info', {})
        return account_info.get('twoFA', '')
    
    def refresh_scrape_accounts(self):
        if hasattr(self, 'scrape_account'):
            account_list = [a.get('phone', '') for a in self.accounts if a.get('status') == '正常']
            self.scrape_account['values'] = account_list
            if account_list:
                self.scrape_account.set(account_list[0])
            else:
                self.scrape_account.set('')
    
    def toggle_listbox_select(self, listbox, var):
        if var.get():
            listbox.selection_set(0, tk.END)
        else:
            listbox.selection_clear(0, tk.END)
    
    # ==================== 多账号管理页面 ====================
    def create_account_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="多账号管理")
        
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="分组管理", command=self.open_group_manager).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导入账号(文件夹)", command=self.import_accounts_folder).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导出账号", command=self.export_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="一键登录并检测", command=self.login_and_check_all).pack(side="left", padx=2)
        ttk.Button(toolbar, text="修改资料", command=self.batch_edit_profile).pack(side="left", padx=2)
        ttk.Button(toolbar, text="刷新列表", command=self.refresh_account_list).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中账号", command=self.delete_selected_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除死号", command=self.delete_dead_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="保存配置", command=self.save_config).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(main_frame, text="账号列表")
        frame.pack(fill="both", expand=True, pady=5)
        
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
        
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["多账号管理"] = scrolledtext.ScrolledText(log_frame, width=100, height=8)
        self.log_widgets["多账号管理"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def batch_edit_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("批量修改资料")
        dialog.geometry("650x700")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 650, 700)
        
        ttk.Label(dialog, text="批量修改资料", font=("微软雅黑", 12, "bold")).pack(pady=10)
        
        account_frame = ttk.LabelFrame(dialog, text="选择账号")
        account_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        filter_row = ttk.Frame(account_frame)
        filter_row.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_row, text="按分组筛选:").pack(side="left", padx=5)
        group_filter = ttk.Combobox(filter_row, values=["全部"] + self.groups, width=20)
        group_filter.set("全部")
        group_filter.pack(side="left", padx=5)
        
        select_all_var = tk.BooleanVar()
        ttk.Checkbutton(filter_row, text="全选", variable=select_all_var,
                       command=lambda: self.toggle_listbox_select(account_listbox, select_all_var)).pack(side="left", padx=20)
        
        listbox_frame = ttk.Frame(account_frame)
        listbox_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        account_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=account_listbox.yview)
        account_listbox.configure(yscrollcommand=scrollbar.set)
        account_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def refresh_account_listbox():
            account_listbox.delete(0, tk.END)
            filter_group = group_filter.get()
            for acc in self.accounts:
                if acc.get('status') == '正常':
                    if filter_group == "全部" or acc.get('group') == filter_group:
                        account_listbox.insert(tk.END, f"{acc.get('phone')} - {acc.get('nickname')} [{acc.get('group')}]")
        
        def on_filter_change(event):
            refresh_account_listbox()
            select_all_var.set(False)
        
        group_filter.bind("<<ComboboxSelected>>", on_filter_change)
        refresh_account_listbox()
        
        photo_frame = ttk.LabelFrame(dialog, text="头像")
        photo_frame.pack(fill="x", padx=10, pady=5)
        photo_row = ttk.Frame(photo_frame)
        photo_row.pack(fill="x", padx=5, pady=5)
        self.photo_folder_path = tk.StringVar()
        ttk.Entry(photo_row, textvariable=self.photo_folder_path, width=50).pack(side="left", padx=5)
        ttk.Button(photo_row, text="选择头像文件夹", command=self.select_photo_folder, width=15).pack(side="left", padx=5)
        ttk.Label(photo_frame, text="支持格式: jpg, jpeg, png, gif, bmp | 按文件名排序后依次分配给选中的账号", font=("微软雅黑", 8), foreground="gray").pack(anchor="w", padx=5, pady=2)
        
        username_frame = ttk.LabelFrame(dialog, text="用户名（不带@）")
        username_frame.pack(fill="x", padx=10, pady=5)
        username_row = ttk.Frame(username_frame)
        username_row.pack(fill="x", padx=5, pady=5)
        self.username_file_path = tk.StringVar()
        ttk.Entry(username_row, textvariable=self.username_file_path, width=50).pack(side="left", padx=5)
        ttk.Button(username_row, text="导入TXT文件", command=self.select_username_file, width=15).pack(side="left", padx=5)
        ttk.Label(username_frame, text="每行一个用户名（不带@），按行依次分配给选中的账号", font=("微软雅黑", 8), foreground="gray").pack(anchor="w", padx=5, pady=2)
        
        firstname_frame = ttk.LabelFrame(dialog, text="昵称")
        firstname_frame.pack(fill="x", padx=10, pady=5)
        firstname_row = ttk.Frame(firstname_frame)
        firstname_row.pack(fill="x", padx=5, pady=5)
        self.firstname_file_path = tk.StringVar()
        ttk.Entry(firstname_row, textvariable=self.firstname_file_path, width=50).pack(side="left", padx=5)
        ttk.Button(firstname_row, text="导入TXT文件", command=self.select_firstname_file, width=15).pack(side="left", padx=5)
        ttk.Label(firstname_frame, text="每行一个昵称，按行依次分配给选中的账号", font=("微软雅黑", 8), foreground="gray").pack(anchor="w", padx=5, pady=2)
        
        bio_frame = ttk.LabelFrame(dialog, text="简介")
        bio_frame.pack(fill="x", padx=10, pady=5)
        bio_row = ttk.Frame(bio_frame)
        bio_row.pack(fill="x", padx=5, pady=5)
        self.bio_file_path = tk.StringVar()
        ttk.Entry(bio_row, textvariable=self.bio_file_path, width=50).pack(side="left", padx=5)
        ttk.Button(bio_row, text="导入TXT文件", command=self.select_bio_file, width=15).pack(side="left", padx=5)
        ttk.Label(bio_frame, text="每行一个简介，按行依次分配给选中的账号", font=("微软雅黑", 8), foreground="gray").pack(anchor="w", padx=5, pady=2)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def do_edit():
            selected_indices = account_listbox.curselection()
            if not selected_indices:
                self.log("多账号管理", "请至少选择一个账号")
                self.show_centered_warning("提示", "请至少选择一个账号")
                return
            
            selected_phones = []
            for idx in selected_indices:
                text = account_listbox.get(idx)
                phone = text.split(" - ")[0]
                selected_phones.append(phone)
            
            photo_folder = self.photo_folder_path.get().strip()
            username_file = self.username_file_path.get().strip()
            firstname_file = self.firstname_file_path.get().strip()
            bio_file = self.bio_file_path.get().strip()
            
            usernames, firstnames, bios, photos = [], [], [], []
            
            if username_file and os.path.exists(username_file):
                with open(username_file, 'r', encoding='utf-8') as f:
                    usernames = [line.strip() for line in f if line.strip()]
                self.log("多账号管理", f"读取用户名文件: {len(usernames)} 个")
            
            if firstname_file and os.path.exists(firstname_file):
                with open(firstname_file, 'r', encoding='utf-8') as f:
                    firstnames = [line.strip() for line in f if line.strip()]
                self.log("多账号管理", f"读取昵称文件: {len(firstnames)} 个")
            
            if bio_file and os.path.exists(bio_file):
                with open(bio_file, 'r', encoding='utf-8') as f:
                    bios = [line.strip() for line in f if line.strip()]
                self.log("多账号管理", f"读取简介文件: {len(bios)} 个")
            
            if photo_folder and os.path.exists(photo_folder):
                valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
                photos = [os.path.join(photo_folder, f) for f in os.listdir(photo_folder) if f.lower().endswith(valid_extensions)]
                photos.sort()
                self.log("多账号管理", f"读取头像文件夹: {len(photos)} 张图片")
            
            dialog.destroy()
            self.log("多账号管理", f"开始批量修改 {len(selected_phones)} 个账号的资料")
            
            def edit_thread():
                for i, phone in enumerate(selected_phones):
                    for acc in self.accounts:
                        if acc.get('phone') == phone and acc.get('status') == '正常':
                            self.update_account_task(phone, "修改资料", True)
                            photo_path = photos[i % len(photos)] if photos else None
                            username = usernames[i % len(usernames)] if usernames else None
                            firstname = firstnames[i % len(firstnames)] if firstnames else None
                            bio = bios[i % len(bios)] if bios else None
                            self.edit_single_account_profile(acc, photo_path, username, firstname, bio)
                            self.update_account_task(phone, "", False)
                            self.update_account_task(phone, "修改资料", False)
                            break
                self.log("多账号管理", "批量修改资料完成")
                self.root.after(0, lambda: self.show_centered_info("完成", f"已完成 {len(selected_phones)} 个账号的资料修改"))
            
            threading.Thread(target=edit_thread, daemon=True).start()
        
        ttk.Button(btn_frame, text="开始修改", command=do_edit, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12).pack(side="left", padx=10)
    
    def select_photo_folder(self):
        folder = filedialog.askdirectory(title="选择头像文件夹")
        if folder:
            self.photo_folder_path.set(folder)
            self.log("多账号管理", f"选择头像文件夹: {folder}")
    
    def select_username_file(self):
        file_path = filedialog.askopenfilename(title="选择用户名文件", filetypes=[("文本文件", "*.txt")])
        if file_path:
            self.username_file_path.set(file_path)
            self.log("多账号管理", f"选择用户名文件: {file_path}")
    
    def select_firstname_file(self):
        file_path = filedialog.askopenfilename(title="选择昵称文件", filetypes=[("文本文件", "*.txt")])
        if file_path:
            self.firstname_file_path.set(file_path)
            self.log("多账号管理", f"选择昵称文件: {file_path}")
    
    def select_bio_file(self):
        file_path = filedialog.askopenfilename(title="选择简介文件", filetypes=[("文本文件", "*.txt")])
        if file_path:
            self.bio_file_path.set(file_path)
            self.log("多账号管理", f"选择简介文件: {file_path}")
    
    def edit_single_account_profile(self, acc, photo_path, username, first_name, bio):
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        
        async def do_edit():
            client = None
            try:
                client = TelegramClient(session_path, api_id, api_hash)
                await client.connect()
                if not await client.is_user_authorized():
                    self.log("多账号管理", f"[{phone}] 账号未登录")
                    return
                
                if username:
                    try:
                        await client(UpdateUsernameRequest(username=username))
                        self.log("多账号管理", f"[{phone}] 用户名修改成功: {username}")
                    except Exception as e:
                        self.log("多账号管理", f"[{phone}] 用户名修改失败: {str(e)}")
                
                if first_name:
                    try:
                        await client(UpdateProfileRequest(first_name=first_name, last_name=""))
                        self.log("多账号管理", f"[{phone}] 昵称修改成功: {first_name}")
                        acc['nickname'] = first_name
                    except Exception as e:
                        self.log("多账号管理", f"[{phone}] 昵称修改失败: {str(e)}")
                
                if bio:
                    try:
                        await client(UpdateProfileRequest(about=bio))
                        self.log("多账号管理", f"[{phone}] 简介修改成功")
                    except Exception as e:
                        self.log("多账号管理", f"[{phone}] 简介修改失败: {str(e)}")
                
                if photo_path and os.path.exists(photo_path):
                    try:
                        photos = await client.get_profile_photos('me')
                        if photos:
                            await client(DeletePhotosRequest(id=[photos[0]]))
                        await client(UploadProfilePhotoRequest(file=await client.upload_file(photo_path)))
                        self.log("多账号管理", f"[{phone}] 头像修改成功")
                    except Exception as e:
                        self.log("多账号管理", f"[{phone}] 头像修改失败: {str(e)}")
                
                await client.disconnect()
                self.root.after(0, self.refresh_account_list)
            except Exception as e:
                self.log("多账号管理", f"[{phone}] 修改资料失败: {str(e)}")
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(do_edit())
        loop.close()
    
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
            self.refresh_invite_group_filter()
            self.save_config()
            self.log("多账号管理", f"移动账号 {self.accounts[idx].get('phone')} 到分组「{target_group}」")
        
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
            self.refresh_invite_group_filter()
            self.save_config()
            self.log("多账号管理", f"创建分组: {name}")
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
                self.refresh_invite_group_filter()
                self.save_config()
                self.log("多账号管理", f"重命名分组: {old_name} -> {new_name}")
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
                self.refresh_invite_group_filter()
                self.save_config()
                self.log("多账号管理", f"删除分组: {group_name}")
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
        folder = filedialog.askdirectory(title="选择账号文件夹")
        if not folder:
            return
        
        self.log("多账号管理", f"开始扫描账号文件夹: {folder}")
        
        session_files = []
        json_files = {}
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".session"):
                    session_files.append(os.path.join(root_dir, file))
                elif file.endswith(".json"):
                    phone = file.replace(".json", "")
                    json_files[phone] = os.path.join(root_dir, file)
        
        if not session_files:
            self.log("多账号管理", "未找到任何.session文件")
            self.show_centered_warning("导入失败", "未找到任何.session文件")
            return
        
        count = 0
        for session_path in session_files:
            filename = os.path.basename(session_path)
            phone = filename.replace(".session", "")
            json_path = json_files.get(phone)
            account_info = None
            
            if json_path:
                account_info = self.read_account_from_json(json_path)
                self.log("多账号管理", f"找到JSON文件: {phone}.json")
            else:
                self.log("多账号管理", f"警告: 未找到 {phone}.json 文件")
            
            exists = False
            for acc in self.accounts:
                if acc.get('phone') == phone:
                    exists = True
                    break
            
            if exists:
                self.log("多账号管理", f"跳过重复账号: {phone}")
                continue
            
            nickname = ""
            register_time = ""
            proxy = ""
            if account_info and account_info.get('valid'):
                first_name = account_info.get('first_name', '')
                last_name = account_info.get('last_name', '')
                nickname = f"{first_name} {last_name}".strip() if first_name or last_name else phone
                reg_ts = account_info.get('register_time', 0)
                if reg_ts:
                    register_time = datetime.fromtimestamp(reg_ts).strftime("%Y-%m-%d")
                proxy = account_info.get('proxy', '')
            
            self.accounts.append({
                "phone": phone,
                "nickname": nickname if nickname else "待获取",
                "group": target_group,
                "status": "待检测",
                "current_task": "",
                "last_action": "",
                "register_time": register_time if register_time else "未知",
                "session_path": session_path,
                "json_path": json_path,
                "account_info": account_info,
                "proxy": proxy
            })
            count += 1
            self.log("多账号管理", f"导入账号: {phone} - 昵称: {nickname if nickname else '无'}")
        
        self.refresh_account_list()
        self.refresh_scrape_accounts()
        self.refresh_invite_group_filter()
        self.save_config()
        self.log("多账号管理", f"导入 {count} 个账号到分组「{target_group}」")
        if count > 0:
            self.show_centered_info("导入完成", f"成功导入 {count} 个账号")
    
    def export_accounts(self):
        selected = self.account_tree.selection()
        if not selected:
            self.log("多账号管理", "请先选择要导出的账号")
            self.show_centered_warning("提示", "请先选择要导出的账号")
            return
        
        export_folder = filedialog.askdirectory(title="选择导出文件夹")
        if not export_folder:
            return
        
        export_count = 0
        for item in selected:
            idx = int(self.account_tree.item(item)['values'][0]) - 1
            acc = self.accounts[idx]
            phone = acc.get('phone', '')
            session_path = acc.get('session_path', '')
            json_path = acc.get('json_path', '')
            
            if session_path and os.path.exists(session_path):
                dest_session = os.path.join(export_folder, f"{phone}.session")
                shutil.copy2(session_path, dest_session)
                export_count += 1
                self.log("多账号管理", f"导出账号: {phone}")
            
            if json_path and os.path.exists(json_path):
                dest_json = os.path.join(export_folder, f"{phone}.json")
                shutil.copy2(json_path, dest_json)
        
        self.log("多账号管理", f"导出完成，共导出 {export_count} 个账号到 {export_folder}")
        self.show_centered_info("导出完成", f"成功导出 {export_count} 个账号")
    
    def login_single_account(self, acc):
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        twofa = self.get_account_twofa(acc)
        
        async def do_login():
            client = None
            try:
                client = TelegramClient(session_path, api_id, api_hash)
                await client.connect()
                
                if await client.is_user_authorized():
                    me = await client.get_me()
                    nickname = me.first_name or me.username or phone
                    acc['nickname'] = nickname
                    if hasattr(me, 'date'):
                        acc['register_time'] = me.date.strftime("%Y-%m-%d")
                    acc['status'] = '正常'
                    self.log("多账号管理", f"[{phone}] 登录成功 | 昵称: {nickname}")
                    await client.disconnect()
                    return True
                else:
                    self.log("多账号管理", f"[{phone}] session未授权")
                    acc['status'] = '未授权'
                    return False
            except FloodWaitError as e:
                self.log("多账号管理", f"[{phone}] 被限制，需等待{e.seconds}秒")
                acc['status'] = f'限制({e.seconds}秒)'
                return False
            except UserDeactivatedError:
                self.log("多账号管理", f"[{phone}] 账号已注销")
                acc['status'] = '销号'
                return False
            except PhoneNumberBannedError:
                self.log("多账号管理", f"[{phone}] 账号已被封禁")
                acc['status'] = '封禁'
                return False
            except SessionPasswordNeededError:
                if twofa:
                    try:
                        await client.sign_in(password=twofa)
                        me = await client.get_me()
                        acc['nickname'] = me.first_name or phone
                        acc['status'] = '正常'
                        self.log("多账号管理", f"[{phone}] 2FA登录成功")
                        return True
                    except:
                        self.log("多账号管理", f"[{phone}] 2FA密码错误")
                        acc['status'] = '2FA错误'
                else:
                    self.log("多账号管理", f"[{phone}] 需要2FA密码")
                    acc['status'] = '需要2FA'
                return False
            except Exception as e:
                self.log("多账号管理", f"[{phone}] 登录失败 - {str(e)[:80]}")
                acc['status'] = '登录失败'
                return False
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(do_login())
        loop.close()
        
        self.root.after(0, self.refresh_account_list)
        self.root.after(0, self.refresh_scrape_accounts)
        self.save_config()
        return result
    
    def login_and_check_all(self):
        if not self.accounts:
            self.log("多账号管理", "没有账号可操作")
            self.show_centered_warning("提示", "请先导入账号")
            return
        
        self.log("多账号管理", f"开始登录并检测 {len(self.accounts)} 个账号...")
        
        def do_login():
            for idx, acc in enumerate(self.accounts, 1):
                phone = acc.get('phone', '')
                self.log("多账号管理", f"[{idx}/{len(self.accounts)}] 正在处理账号: {phone}")
                self.login_single_account(acc)
                time.sleep(2)
            self.log("多账号管理", "登录检测完成")
            self.save_config()
        
        threading.Thread(target=do_login, daemon=True).start()
    
    def refresh_account_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        for i, acc in enumerate(self.accounts, 1):
            self.account_tree.insert("", "end", values=(
                i, acc.get('phone', ''), acc.get('group', '默认分组'),
                acc.get('nickname', ''), acc.get('current_task', ''),
                acc.get('last_action', ''), acc.get('status', '待检测'),
                acc.get('register_time', '未知'), acc.get('proxy', '未设置')
            ))
    
    def delete_selected_accounts(self):
        selected = self.account_tree.selection()
        if selected:
            def do_delete():
                indices = sorted([int(self.account_tree.item(item)['values'][0]) - 1 for item in selected], reverse=True)
                for idx in indices:
                    self.accounts.pop(idx)
                self.refresh_account_list()
                self.refresh_scrape_accounts()
                self.refresh_invite_group_filter()
                self.save_config()
                self.log("多账号管理", f"删除 {len(selected)} 个选中账号")
            self.show_centered_yesno("确认", f"确定删除 {len(selected)} 个账号？", do_delete)
    
    def delete_dead_accounts(self):
        dead_states = ['销号', '封禁']
        dead_indices = [i for i, acc in enumerate(self.accounts) if acc.get('status') in dead_states]
        if dead_indices:
            def do_delete():
                for idx in sorted(dead_indices, reverse=True):
                    self.accounts.pop(idx)
                self.refresh_account_list()
                self.refresh_scrape_accounts()
                self.refresh_invite_group_filter()
                self.save_config()
                self.log("多账号管理", f"删除 {len(dead_indices)} 个已失效账号")
            self.show_centered_yesno("确认", f"确定删除 {len(dead_indices)} 个已失效账号？", do_delete)
        else:
            self.log("多账号管理", "没有发现已失效的账号")
            self.show_centered_info("提示", "没有发现已失效的账号")
    
    # ==================== 代理IP页面 ====================
    def create_proxy_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="代理IP")
        
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)
        
        self.proxy_count_label = ttk.Label(toolbar, text=f"代理数量: {len(self.proxies)}", font=("微软雅黑", 10))
        self.proxy_count_label.pack(side="left", padx=10)
        
        ttk.Button(toolbar, text="新建分组", command=self.add_proxy_group).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导入代理", command=self.import_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中代理", command=self.delete_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="检测所有代理", command=self.check_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="清空所有代理", command=self.clear_all_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="分配代理IP", command=self.assign_proxies_to_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="保存配置", command=self.save_config).pack(side="left", padx=2)
        
        frame = ttk.LabelFrame(main_frame, text="代理列表")
        frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("分组", "序号", "代理类型", "代理地址", "状态")
        self.proxy_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col in columns:
            self.proxy_tree.heading(col, text=col)
        
        self.proxy_tree.column("分组", anchor="center", width=100)
        self.proxy_tree.column("序号", anchor="center", width=50)
        self.proxy_tree.column("代理类型", anchor="center", width=100)
        self.proxy_tree.column("代理地址", anchor="center", width=350)
        self.proxy_tree.column("状态", anchor="center", width=200)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.proxy_tree.yview)
        self.proxy_tree.configure(yscrollcommand=scrollbar.set)
        self.proxy_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["代理IP"] = scrolledtext.ScrolledText(log_frame, width=100, height=8)
        self.log_widgets["代理IP"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def add_proxy_group(self):
        group_name = simpledialog.askstring("新建分组", "请输入分组名称:", parent=self.root)
        if group_name and group_name not in self.proxy_groups:
            self.proxy_groups.append(group_name)
            self.refresh_invite_group_filter()
            self.save_config()
            self.log("代理IP", f"创建代理分组: {group_name}")
        elif group_name in self.proxy_groups:
            self.show_centered_warning("提示", "分组已存在")
    
    def assign_proxies_to_accounts(self):
        if not self.proxies:
            self.log("代理IP", "没有可用的代理")
            self.show_centered_warning("提示", "请先导入代理")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("分配代理IP")
        dialog.geometry("780x650")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 780, 650)
        
        ttk.Label(dialog, text="分配代理IP", font=("微软雅黑", 12, "bold")).pack(pady=10)
        
        main_paned = ttk.Frame(dialog)
        main_paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        left_frame = ttk.LabelFrame(main_paned, text="选择账号")
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        right_frame = ttk.LabelFrame(main_paned, text="选择代理")
        right_frame.pack(side="right", fill="both", expand=True, padx=5)
        
        ttk.Label(left_frame, text="账号分组筛选:").pack(anchor="w", padx=5, pady=5)
        self.account_group_filter = ttk.Combobox(left_frame, values=["全部"] + self.groups, width=20)
        self.account_group_filter.set("全部")
        self.account_group_filter.pack(fill="x", padx=5, pady=5)
        
        account_select_all_frame = ttk.Frame(left_frame)
        account_select_all_frame.pack(fill="x", padx=5, pady=5)
        account_select_all_var = tk.BooleanVar()
        ttk.Checkbutton(account_select_all_frame, text="全选", variable=account_select_all_var,
                       command=lambda: self.toggle_listbox_select(account_listbox, account_select_all_var)).pack(side="left")
        
        account_listbox = tk.Listbox(left_frame, selectmode=tk.MULTIPLE, height=15, exportselection=False)
        account_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=account_listbox.yview)
        account_listbox.configure(yscrollcommand=account_scrollbar.set)
        account_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        account_scrollbar.pack(side="right", fill="y")
        
        ttk.Label(right_frame, text="代理分组筛选:").pack(anchor="w", padx=5, pady=5)
        self.proxy_group_filter = ttk.Combobox(right_frame, values=["全部"] + self.proxy_groups, width=20)
        self.proxy_group_filter.set("全部")
        self.proxy_group_filter.pack(fill="x", padx=5, pady=5)
        
        proxy_select_all_frame = ttk.Frame(right_frame)
        proxy_select_all_frame.pack(fill="x", padx=5, pady=5)
        proxy_select_all_var = tk.BooleanVar()
        ttk.Checkbutton(proxy_select_all_frame, text="全选", variable=proxy_select_all_var,
                       command=lambda: self.toggle_listbox_select(proxy_listbox, proxy_select_all_var)).pack(side="left")
        
        proxy_listbox = tk.Listbox(right_frame, selectmode=tk.MULTIPLE, height=15, exportselection=False)
        proxy_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=proxy_listbox.yview)
        proxy_listbox.configure(yscrollcommand=proxy_scrollbar.set)
        proxy_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        proxy_scrollbar.pack(side="right", fill="y")
        
        def refresh_account_list():
            account_listbox.delete(0, tk.END)
            filter_group = self.account_group_filter.get()
            for acc in self.accounts:
                if acc.get('status') == '正常':
                    if filter_group == "全部" or acc.get('group') == filter_group:
                        account_listbox.insert(tk.END, f"{acc.get('phone')} - {acc.get('nickname')} [{acc.get('group')}]")
        
        def refresh_proxy_list():
            proxy_listbox.delete(0, tk.END)
            filter_group = self.proxy_group_filter.get()
            for p in self.proxies:
                p_group = p.get('group', '默认分组')
                if filter_group == "全部" or p_group == filter_group:
                    display_addr = p.get('address', f"{p.get('host')}:{p.get('port')}")
                    proxy_listbox.insert(tk.END, f"[{p_group}] {p.get('type')}://{display_addr}")
        
        def on_account_filter_change(event):
            refresh_account_list()
            account_select_all_var.set(False)
        
        def on_proxy_filter_change(event):
            refresh_proxy_list()
            proxy_select_all_var.set(False)
        
        self.account_group_filter.bind("<<ComboboxSelected>>", on_account_filter_change)
        self.proxy_group_filter.bind("<<ComboboxSelected>>", on_proxy_filter_change)
        
        refresh_account_list()
        refresh_proxy_list()
        
        mode_frame = ttk.LabelFrame(dialog, text="分配模式")
        mode_frame.pack(fill="x", padx=10, pady=5)
        assign_mode = tk.StringVar(value="round_robin")
        ttk.Radiobutton(mode_frame, text="轮流分配（账号轮流使用选中的代理）", variable=assign_mode, value="round_robin").pack(anchor="w", padx=10, pady=2)
        ttk.Radiobutton(mode_frame, text="一对一分配（按顺序一一对应）", variable=assign_mode, value="one_to_one").pack(anchor="w", padx=10, pady=2)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def do_assign():
            selected_account_indices = account_listbox.curselection()
            selected_proxy_indices = proxy_listbox.curselection()
            
            if not selected_account_indices:
                self.log("代理IP", "请至少选择一个账号")
                self.show_centered_warning("提示", "请至少选择一个账号")
                return
            if not selected_proxy_indices:
                self.log("代理IP", "请至少选择一个代理")
                self.show_centered_warning("提示", "请至少选择一个代理")
                return
            
            selected_accounts = [account_listbox.get(idx).split(" - ")[0] for idx in selected_account_indices]
            selected_proxies = []
            for idx in selected_proxy_indices:
                text = proxy_listbox.get(idx)
                match = re.search(r'\]\s*(\w+)://([^@]+@)?([^:]+):(\d+)', text)
                if match:
                    p_type = match.group(1)
                    host = match.group(3)
                    port = match.group(4)
                    user_pass = match.group(2) if match.group(2) else ""
                    user, password = "", ""
                    if user_pass and ':' in user_pass:
                        user_pass = user_pass.rstrip('@')
                        if ':' in user_pass:
                            user, password = user_pass.split(':', 1)
                    selected_proxies.append({'type': p_type, 'host': host, 'port': port, 'user': user, 'password': password})
            
            dialog.destroy()
            self.log("代理IP", f"开始为 {len(selected_accounts)} 个账号分配代理")
            
            if assign_mode.get() == "round_robin":
                for i, phone in enumerate(selected_accounts):
                    p = selected_proxies[i % len(selected_proxies)]
                    proxy_str = f"{p['type']}://{p['host']}:{p['port']}"
                    if p.get('user') and p.get('password'):
                        proxy_str = f"{p['type']}://{p['user']}:{p['password']}@{p['host']}:{p['port']}"
                    for acc in self.accounts:
                        if acc.get('phone') == phone:
                            acc['proxy'] = proxy_str
                            break
                    self.log("代理IP", f"账号 {phone} 分配代理: {proxy_str}")
            else:
                min_len = min(len(selected_accounts), len(selected_proxies))
                for i in range(min_len):
                    phone = selected_accounts[i]
                    p = selected_proxies[i]
                    proxy_str = f"{p['type']}://{p['host']}:{p['port']}"
                    if p.get('user') and p.get('password'):
                        proxy_str = f"{p['type']}://{p['user']}:{p['password']}@{p['host']}:{p['port']}"
                    for acc in self.accounts:
                        if acc.get('phone') == phone:
                            acc['proxy'] = proxy_str
                            break
                    self.log("代理IP", f"账号 {phone} 分配代理: {proxy_str}")
            
            self.refresh_account_list()
            self.refresh_proxy_list()
            self.save_config()
            self.log("代理IP", f"分配完成，共为 {len(selected_accounts)} 个账号分配代理")
            self.show_centered_info("完成", f"已为 {len(selected_accounts)} 个账号分配代理")
        
        ttk.Button(btn_frame, text="确定分配", command=do_assign, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12).pack(side="left", padx=10)
    
    def import_proxies(self):
        group_dialog = tk.Toplevel(self.root)
        group_dialog.title("选择代理分组")
        group_dialog.geometry("300x150")
        group_dialog.resizable(False, False)
        group_dialog.transient(self.root)
        group_dialog.grab_set()
        self.center_window(group_dialog, 300, 150)
        
        ttk.Label(group_dialog, text="请选择导入代理的目标分组:").pack(pady=15)
        group_var = tk.StringVar()
        group_combo = ttk.Combobox(group_dialog, textvariable=group_var, values=self.proxy_groups, width=25)
        group_combo.pack(pady=5)
        if self.proxy_groups:
            group_combo.set(self.proxy_groups[0])
        
        result_group = [None]
        def confirm_group():
            result_group[0] = group_var.get() or "默认分组"
            group_dialog.destroy()
        ttk.Button(group_dialog, text="确定", command=confirm_group).pack(pady=15)
        self.root.wait_window(group_dialog)
        if result_group[0] is None:
            return
        target_group = result_group[0]
        
        file_path = filedialog.askopenfilename(title="选择代理文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not file_path:
            return
        
        type_dialog = tk.Toplevel(self.root)
        type_dialog.title("选择代理类型")
        type_dialog.geometry("350x200")
        type_dialog.resizable(False, False)
        type_dialog.transient(self.root)
        type_dialog.grab_set()
        self.center_window(type_dialog, 350, 200)
        
        ttk.Label(type_dialog, text="请选择代理类型:", font=("微软雅黑", 12)).pack(pady=25)
        proxy_type = ttk.Combobox(type_dialog, values=["socks5", "socks4", "http", "https"], width=15, font=("微软雅黑", 11))
        proxy_type.set("socks5")
        proxy_type.pack(pady=10)
        
        result_type = [None]
        def confirm_type():
            result_type[0] = proxy_type.get()
            type_dialog.destroy()
        button_frame = ttk.Frame(type_dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="确定", command=confirm_type, width=12).pack(side="left", padx=15)
        ttk.Button(button_frame, text="取消", command=type_dialog.destroy, width=12).pack(side="left", padx=15)
        self.root.wait_window(type_dialog)
        if not result_type[0]:
            return
        p_type = result_type[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.show_centered_error("错误", f"读取文件失败: {str(e)}")
            return
        
        lines = content.strip().split('\n')
        added_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 2:
                host = parts[0]
                port = parts[1]
                user = parts[2] if len(parts) >= 3 else ""
                password = parts[3] if len(parts) >= 4 else ""
                self.proxies.append({
                    "type": p_type, "host": host, "port": port, "user": user, "password": password,
                    "address": f"{host}:{port}", "status": "未检测", "group": target_group
                })
                added_count += 1
                self.log("代理IP", f"导入代理: {p_type}://{host}:{port} 到分组「{target_group}」")
        
        self.refresh_proxy_list()
        self.proxy_count_label.config(text=f"代理数量: {len(self.proxies)}")
        self.save_config()
        if added_count > 0:
            self.log("代理IP", f"导入完成，共导入 {added_count} 个代理")
            self.show_centered_info("导入完成", f"成功导入 {added_count} 个代理")
        else:
            self.log("代理IP", "导入失败：未找到有效的代理格式")
            self.show_centered_warning("导入失败", "未找到有效的代理格式")
    
    def delete_proxy(self):
        selected = self.proxy_tree.selection()
        if selected:
            indices = sorted([int(self.proxy_tree.item(item)['values'][1]) - 1 for item in selected], reverse=True)
            for idx in indices:
                self.proxies.pop(idx)
            self.refresh_proxy_list()
            self.proxy_count_label.config(text=f"代理数量: {len(self.proxies)}")
            self.save_config()
            self.log("代理IP", f"删除 {len(selected)} 个代理")
    
    def clear_all_proxies(self):
        if self.proxies:
            def do_clear():
                self.proxies.clear()
                self.refresh_proxy_list()
                self.proxy_count_label.config(text=f"代理数量: 0")
                self.save_config()
                self.log("代理IP", "清空所有代理")
            self.show_centered_yesno("确认", "确定要清空所有代理吗？", do_clear)
        else:
            self.log("代理IP", "没有代理需要清空")
            self.show_centered_info("提示", "没有代理需要清空")
    
    def check_proxies(self):
        if not self.proxies:
            self.log("代理IP", "没有代理需要检测")
            self.show_centered_warning("提示", "没有代理需要检测")
            return
        self.log("代理IP", f"开始检测 {len(self.proxies)} 个代理...")
        
        def do_check():
            for p in self.proxies:
                proxy_str = f"{p.get('host')}:{p.get('port')}"
                try:
                    proxy_url = f"{p.get('type')}://"
                    if p.get('user') and p.get('password'):
                        proxy_url += f"{p.get('user')}:{p.get('password')}@"
                    proxy_url += f"{p.get('host')}:{p.get('port')}"
                    proxies = {p.get('type'): proxy_url}
                    start_time = time.time()
                    resp = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
                    elapsed = time.time() - start_time
                    if resp.status_code == 200:
                        p['status'] = f"可用 ({elapsed:.1f}s) - IP: {resp.text}"
                        self.log("代理IP", f"{p.get('type')}://{proxy_str}: 可用")
                    else:
                        p['status'] = "不可用"
                        self.log("代理IP", f"{p.get('type')}://{proxy_str}: 不可用")
                except Exception as e:
                    p['status'] = f"不可用"
                    self.log("代理IP", f"{p.get('type')}://{proxy_str}: 不可用")
                self.root.after(0, self.refresh_proxy_list)
            self.log("代理IP", "代理检测完成")
        
        threading.Thread(target=do_check, daemon=True).start()
    
    def refresh_proxy_list(self):
        for item in self.proxy_tree.get_children():
            self.proxy_tree.delete(item)
        for i, p in enumerate(self.proxies, 1):
            display_addr = p.get('address', f"{p.get('host')}:{p.get('port')}")
            p_group = p.get('group', '默认分组')
            self.proxy_tree.insert("", "end", values=(p_group, i, p.get('type', 'socks5'), display_addr, p.get('status', '未检测')))
    
    # ==================== 采集群成员页面 ====================
    def create_scrape_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="采集群成员")
        
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        left_frame = ttk.LabelFrame(main_frame, text="采集设置")
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(left_frame, text="群组链接:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.scrape_group = ttk.Entry(left_frame, width=45)
        self.scrape_group.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        
        ttk.Label(left_frame, text="选择采集账号:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.scrape_account = ttk.Combobox(left_frame, width=40)
        self.scrape_account.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        
        ttk.Button(left_frame, text="刷新账号列表", command=self.refresh_scrape_accounts, width=12).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(left_frame, text="采集模式:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.scrape_mode = ttk.Combobox(left_frame, values=[
            "获取全部成员(公开群)", 
            "获取发言用户(隐藏群)",
            "隐私群采集(仅邀请链接)",
            "多讨论组采集(多个子群)",
            "频道评论采集"
        ], width=30)
        self.scrape_mode.set("获取全部成员(公开群)")
        self.scrape_mode.grid(row=3, column=1, padx=5, pady=5, columnspan=2)
        
        self.sub_groups_label = ttk.Label(left_frame, text="子群链接列表(每行一个):")
        self.sub_groups_text = scrolledtext.ScrolledText(left_frame, width=40, height=4)
        
        def on_mode_change(event):
            mode = self.scrape_mode.get()
            if mode == "多讨论组采集(多个子群)":
                self.sub_groups_label.grid(row=4, column=0, sticky="nw", padx=5, pady=5)
                self.sub_groups_text.grid(row=4, column=1, padx=5, pady=5, columnspan=2)
                self.sub_groups_text.config(state="normal")
            else:
                self.sub_groups_label.grid_remove()
                self.sub_groups_text.grid_remove()
                self.sub_groups_text.config(state="disabled")
        
        self.scrape_mode.bind("<<ComboboxSelected>>", on_mode_change)
        on_mode_change(None)
        
        ttk.Label(left_frame, text="在线天数筛选:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.online_filter = ttk.Combobox(left_frame, values=["不限", "1天内", "3天内", "7天内", "15天内", "30天内"], width=15)
        self.online_filter.set("不限")
        self.online_filter.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        filter_frame = ttk.LabelFrame(left_frame, text="过滤选项")
        filter_frame.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        
        self.filter_admin = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="过滤管理员", variable=self.filter_admin).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.filter_bot = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="过滤机器人", variable=self.filter_bot).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        self.filter_deleted = tk.BooleanVar()
        ttk.Checkbutton(filter_frame, text="过滤已注销", variable=self.filter_deleted).grid(row=0, column=2, sticky="w", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="过滤昵称含广告:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.filter_keywords = ttk.Entry(filter_frame, width=35)
        self.filter_keywords.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        ttk.Label(filter_frame, text="（多个关键词用逗号分隔）", font=("微软雅黑", 8)).grid(row=2, column=1, sticky="w", padx=5)
        
        save_frame = ttk.LabelFrame(left_frame, text="保存设置")
        save_frame.grid(row=7, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        
        ttk.Label(save_frame, text="保存格式:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.save_format = ttk.Combobox(save_frame, values=["TXT", "JSON"], width=10)
        self.save_format.set("TXT")
        self.save_format.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(save_frame, text="保存目录:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.save_path = ttk.Entry(save_frame, width=35)
        self.save_path.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(save_frame, text="浏览", command=self.select_save_path, width=8).grid(row=1, column=2, padx=5)
        ttk.Label(save_frame, text="请选择保存目录，采集完成或停止时自动保存", font=("微软雅黑", 8), foreground="blue").grid(row=2, column=0, columnspan=3, sticky="w", padx=5)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=15)
        
        self.start_btn = ttk.Button(btn_frame, text="开始采集", command=self.start_scrape, width=12)
        self.start_btn.pack(side="left", padx=5)
        self.complete_btn = ttk.Button(btn_frame, text="完成采集", command=self.complete_scrape, width=12)
        self.complete_btn.pack(side="left", padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.pause_scrape, width=12)
        self.stop_btn.pack(side="left", padx=5)
        self.continue_btn = ttk.Button(btn_frame, text="继续", command=self.resume_scrape, width=12)
        self.continue_btn.pack(side="left", padx=5)
        
        right_frame = ttk.LabelFrame(main_frame, text="采集预览与日志")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        preview_frame = ttk.Frame(right_frame)
        preview_frame.pack(fill="both", expand=True)
        
        preview_columns = ("序号", "用户ID", "用户名", "昵称", "在线状态", "是否管理员", "是否机器人")
        self.preview_tree = ttk.Treeview(preview_frame, columns=preview_columns, show="headings", height=15)
        for col in preview_columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, anchor="center", width=100)
        
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        self.preview_tree.configure(yscrollcommand=preview_scrollbar.set)
        self.preview_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        preview_scrollbar.pack(side="right", fill="y")
        
        self.scrape_stats = ttk.Label(preview_frame, text="已采集: 0 人", font=("微软雅黑", 10))
        self.scrape_stats.pack(pady=5)
        
        log_frame = ttk.LabelFrame(right_frame, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["采集群成员"] = scrolledtext.ScrolledText(log_frame, width=100, height=6)
        self.log_widgets["采集群成员"].pack(fill="both", expand=True, padx=5, pady=5)
        
        self.is_scraping = False
        self.scraped_members = []
        self.scrape_task = None
        self.scrape_loop = None
        self.refresh_scrape_accounts()
    
    def select_save_path(self):
        folder = filedialog.askdirectory(title="选择保存目录")
        if folder:
            self.save_path.delete(0, tk.END)
            self.save_path.insert(0, folder)
            self.log("采集群成员", f"已设置保存目录: {folder}")
    
    def save_scraped_members(self, group_username, is_stop=False):
        if not self.scraped_members:
            if is_stop:
                self.log("采集群成员", "没有采集到任何成员，不保存文件")
            return False
        
        save_dir = self.save_path.get().strip()
        if not save_dir:
            self.log("采集群成员", "请先选择保存目录")
            self.show_centered_warning("提示", "请先选择保存目录")
            return False
        
        os.makedirs(save_dir, exist_ok=True)
        
        save_format = self.save_format.get()
        current_date = datetime.now().strftime('%Y%m%d')
        current_time = datetime.now().strftime('%H%M%S')
        action = "stop" if is_stop else "complete"
        base_name = f"members_{group_username}_{current_date}_{current_time}_{action}"
        
        usernames = list(set([m.get('username', '') for m in self.scraped_members if m.get('username')]))
        
        try:
            if save_format == "JSON":
                save_path = os.path.join(save_dir, f"{base_name}.json")
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(usernames, f, ensure_ascii=False, indent=2)
                self.log("采集群成员", f"已保存JSON文件: {save_path}, 共 {len(usernames)} 个用户名")
            else:
                save_path = os.path.join(save_dir, f"{base_name}.txt")
                with open(save_path, 'w', encoding='utf-8') as f:
                    for username in usernames:
                        if username:
                            f.write(f"@{username}\n")
                self.log("采集群成员", f"已保存TXT文件: {save_path}, 共 {len(usernames)} 个用户名")
            return True
        except Exception as e:
            self.log("采集群成员", f"保存文件失败: {str(e)}")
            return False
    
    def stop_scrape(self):
        if self.is_scraping:
            self.is_scraping = False
            self.log("采集群成员", "用户停止采集，正在保存已采集的数据...")
    
    def complete_scrape(self):
        if self.is_scraping:
            self.is_scraping = False
            self.is_paused = False
            self.log("采集群成员", "用户完成采集，正在保存已采集的数据...")
    
    def pause_scrape(self):
        if self.is_scraping and not self.is_paused:
            self.is_paused = True
            self.log("采集群成员", "用户暂停采集")
    
    def resume_scrape(self):
        if self.is_scraping and self.is_paused:
            self.is_paused = False
            self.log("采集群成员", "用户继续采集")
    
    def get_online_status_text(self, user_status):
        if user_status is None:
            return "未知"
        if hasattr(user_status, '__class__'):
            class_name = user_status.__class__.__name__
            if class_name == 'UserStatusRecently':
                return "最近在线"
            elif class_name == 'UserStatusLastWeek':
                return "7天内在线"
            elif class_name == 'UserStatusLastMonth':
                return "30天内在线"
            elif class_name == 'UserStatusOnline':
                return "在线"
            elif class_name == 'UserStatusOffline':
                return "离线"
        if isinstance(user_status, UserStatusRecently):
            return "最近在线"
        elif isinstance(user_status, UserStatusLastWeek):
            return "7天内在线"
        elif isinstance(user_status, UserStatusLastMonth):
            return "30天内在线"
        elif isinstance(user_status, UserStatusOnline):
            return "在线"
        elif isinstance(user_status, UserStatusOffline):
            return "离线"
        return "未知"
    
    def check_online_days(self, user_status, online_days):
        if online_days is None:
            return True
        if user_status is None:
            return False
        class_name = user_status.__class__.__name__
        if class_name == 'UserStatusRecently':
            return online_days >= 1
        elif class_name == 'UserStatusLastWeek':
            return online_days >= 7
        elif class_name == 'UserStatusLastMonth':
            return online_days >= 30
        elif class_name == 'UserStatusOnline':
            return True
        elif class_name == 'UserStatusOffline':
            if hasattr(user_status, 'was_online') and user_status.was_online:
                try:
                    days_ago = (datetime.now().replace(tzinfo=user_status.was_online.tzinfo) - user_status.was_online).days
                    return days_ago <= online_days
                except:
                    pass
            return False
        return False
    
    def batch_update_preview(self, member_infos):
        self.preview_tree.delete(*self.preview_tree.get_children())
        for idx, info in enumerate(self.scraped_members):
            current_num = idx + 1
            display_name = info.get('first_name', '') or info.get('username', '') or str(info.get('id', ''))
            if len(display_name) > 20:
                display_name = display_name[:20] + "..."
            is_bot = info.get('is_bot', False)
            self.preview_tree.insert("", "end", values=(
                current_num, info.get('id', ''), info.get('username', '')[:20] if info.get('username') else "-",
                display_name, info.get('online_status', '未知'),
                "是" if info.get('is_admin', False) else "否", "是" if is_bot else "否"
            ))
        total_count = len(self.scraped_members)
        self.scrape_stats.config(text=f"已采集: {total_count} 人")
        self.preview_tree.yview_moveto(1)
    
    def parse_group_link(self, link):
        topic_id = None
        group_username = None
        if 't.me/' in link:
            clean_link = link.replace('https://', '').replace('http://', '')
            path = clean_link.split('t.me/')[-1].strip('/')
            parts = path.split('/')
            group_username = parts[0]
            if group_username.startswith('+') or group_username == 'joinchat':
                group_username = path
            if len(parts) >= 2 and parts[1].isdigit():
                topic_id = int(parts[1])
        elif 'https://' in link:
            group_username = link.split('/')[-1]
        else:
            group_username = link
        return group_username, topic_id
    
    def start_scrape(self):
        if self.is_scraping:
            self.log("采集群成员", "采集任务正在进行中")
            return
        
        group = self.scrape_group.get().strip()
        account_phone = self.scrape_account.get()
        save_dir = self.save_path.get().strip()
        scrape_mode = self.scrape_mode.get()
        
        if not group and scrape_mode != "多讨论组采集(多个子群)":
            self.log("采集群成员", "请输入群组链接")
            self.show_centered_warning("提示", "请输入群组链接")
            return
        
        if not account_phone:
            self.log("采集群成员", "请选择采集账号")
            self.show_centered_warning("提示", "请先登录账号并刷新账号列表")
            return
        
        if not save_dir:
            self.log("采集群成员", "请先选择保存目录")
            self.show_centered_warning("提示", "请先选择保存目录")
            return
        
        acc = None
        for a in self.accounts:
            if a.get('phone') == account_phone:
                acc = a
                break
        
        if not acc:
            self.log("采集群成员", "未找到账号，请刷新账号列表")
            self.show_centered_warning("提示", "未找到账号，请刷新账号列表")
            return
        if acc.get('status') != '正常':
            self.log("采集群成员", "请先登录账号")
            self.show_centered_warning("提示", "请先登录账号")
            return
        
        os.makedirs(save_dir, exist_ok=True)
        group_username, topic_id = self.parse_group_link(group)
        
        keywords_text = self.filter_keywords.get().strip()
        ad_keywords = [kw.strip().lower() for kw in keywords_text.split(',') if kw.strip()]
        
        online_filter_text = self.online_filter.get()
        online_days = None
        if online_filter_text == "1天内":
            online_days = 1
        elif online_filter_text == "3天内":
            online_days = 3
        elif online_filter_text == "7天内":
            online_days = 7
        elif online_filter_text == "15天内":
            online_days = 15
        elif online_filter_text == "30天内":
            online_days = 30
        
        self.is_scraping = True
        self.is_paused = False
        self.scraped_members = []
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.scrape_stats.config(text="已采集: 0 人")
        
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        
        self.log("采集群成员", f"开始采集群成员: {group_username if group else '多讨论组'}")
        if topic_id:
            self.log("采集群成员", f"Topic ID: {topic_id} (精准采集该讨论串)")
        self.log("采集群成员", f"采集模式: {scrape_mode}")
        self.log("采集群成员", f"过滤设置: 管理员={self.filter_admin.get()}, 机器人={self.filter_bot.get()}, 已注销={self.filter_deleted.get()}, 广告关键词={ad_keywords}, 在线筛选={online_filter_text}")
        self.log("采集群成员", f"保存目录: {save_dir}")
        self.log("采集群成员", "采集规则: 只采集有用户名的成员（username不为空）")
        
        self.update_account_task(account_phone, "采集群成员", True)
        
        async def do_scrape():
            client = None
            admin_ids = set()
            all_results = []
            all_collected_ids = set()
            total_count = 0
            
            try:
                client = TelegramClient(session_path, api_id, api_hash)
                await client.connect()
                if not await client.is_user_authorized():
                    self.log("采集群成员", "账号未登录")
                    return
                
                if self.filter_admin.get():
                    try:
                        if scrape_mode == "多讨论组采集(多个子群)":
                            sub_groups_text = self.sub_groups_text.get("1.0", tk.END).strip()
                            sub_group_links = [link.strip() for link in sub_groups_text.split('\n') if link.strip()]
                            for link in sub_group_links:
                                try:
                                    sub_username, sub_topic = self.parse_group_link(link)
                                    if sub_username:
                                        entity = await client.get_entity(sub_username)
                                        async for user in client.iter_participants(entity, filter=ChannelParticipantsAdmins):
                                            admin_ids.add(user.id)
                                except:
                                    pass
                        else:
                            if group_username.isdigit():
                                entity = await client.get_entity(int(group_username))
                            else:
                                entity = await client.get_entity(group_username)
                            async for user in client.iter_participants(entity, filter=ChannelParticipantsAdmins):
                                admin_ids.add(user.id)
                        self.log("采集群成员", f"获取到 {len(admin_ids)} 个管理员")
                    except Exception as e:
                        self.log("采集群成员", f"获取管理员列表失败: {str(e)}")
                
                if scrape_mode == "获取全部成员(公开群)":
                    self.log("采集群成员", "开始采集成员（获取全部成员）...")
                    if group_username.isdigit():
                        entity = await client.get_entity(int(group_username))
                    else:
                        entity = await client.get_entity(group_username)
                    async for user in client.iter_participants(entity):
                        if not self.is_scraping:
                            break
                        while self.is_paused:
                            await asyncio.sleep(0.5)
                        if not self.is_scraping:
                            break
                        if not user.username:
                            continue
                        if user.id in all_collected_ids:
                            continue
                        all_collected_ids.add(user.id)
                        if self.filter_admin.get() and user.id in admin_ids:
                            continue
                        if self.filter_bot.get() and user.bot:
                            continue
                        if self.filter_deleted.get() and user.deleted:
                            continue
                        if ad_keywords:
                            name_lower = f"{user.first_name or ''} {user.last_name or ''}".lower()
                            if any(kw in name_lower for kw in ad_keywords):
                                continue
                        if online_days is not None:
                            if not self.check_online_days(user.status, online_days):
                                continue
                        online_status = self.get_online_status_text(user.status)
                        member_info = {
                            'id': user.id, 'username': user.username,
                            'first_name': user.first_name or "", 'last_name': user.last_name or "",
                            'phone': user.phone if hasattr(user, 'phone') and user.phone else "",
                            'online_status': online_status,
                            'is_admin': user.id in admin_ids,
                            'is_bot': user.bot if hasattr(user, 'bot') else False,
                            'deleted': user.deleted if hasattr(user, 'deleted') else False
                        }
                        all_results.append(member_info)
                        self.scraped_members = all_results.copy()
                        total_count += 1
                        if total_count % 10 == 0:
                            self.root.after(0, lambda: self.batch_update_preview([]))
                        await asyncio.sleep(0.05)
                
                elif scrape_mode == "获取发言用户(隐藏群)":
                    self.log("采集群成员", "开始采集发言用户（极速模式）...")
                    if group_username.isdigit():
                        entity = await client.get_entity(int(group_username))
                    else:
                        entity = await client.get_entity(group_username)
                    
                    offset_id = 0
                    batch_size = 3000
                    input_peer = InputPeerChannel(entity.id, entity.access_hash)
                    pending_infos = []
                    last_ui_update = time.time()
                    
                    while self.is_scraping:
                        while self.is_paused:
                            await asyncio.sleep(0.5)
                        if not self.is_scraping:
                            break
                        try:
                            if topic_id:
                                messages = await client.get_messages(entity, limit=batch_size, offset_id=offset_id, reply_to=topic_id)
                                messages_list = messages
                            else:
                                request_args = {
                                    "peer": input_peer,
                                    "offset_id": offset_id,
                                    "offset_date": None,
                                    "add_offset": 0,
                                    "limit": batch_size,
                                    "max_id": 0,
                                    "min_id": 0,
                                    "hash": 0
                                }
                                history = await client(GetHistoryRequest(**request_args))
                                messages_list = history.messages
                                users_map = {u.id: u for u in history.users}
                            
                            if not messages_list:
                                break
                            
                            for msg in messages_list:
                                if not self.is_scraping:
                                    break
                                while self.is_paused:
                                    await asyncio.sleep(0.5)
                                if not self.is_scraping:
                                    break
                                if not msg.sender_id:
                                    continue
                                if 'users_map' in locals() and msg.sender_id in users_map:
                                    sender = users_map.get(msg.sender_id)
                                elif hasattr(msg, 'sender') and msg.sender:
                                    sender = msg.sender
                                else:
                                    try:
                                        sender = await client.get_input_entity(msg.sender_id)
                                    except:
                                        continue
                                if not sender:
                                    continue
                                if not hasattr(sender, 'username') or not sender.username:
                                    continue
                                if sender.id in all_collected_ids:
                                    continue
                                if self.filter_admin.get() and sender.id in admin_ids:
                                    continue
                                if self.filter_bot.get() and hasattr(sender, 'bot') and sender.bot:
                                    continue
                                if self.filter_deleted.get() and getattr(sender, 'deleted', False):
                                    continue
                                if ad_keywords:
                                    name_lower = f"{sender.first_name or ''} {sender.last_name or ''}".lower()
                                    if any(kw in name_lower for kw in ad_keywords):
                                        continue
                                all_collected_ids.add(sender.id)
                                member_info = {
                                    'id': sender.id, 'username': sender.username,
                                    'first_name': sender.first_name or "", 'last_name': sender.last_name or "",
                                    'phone': "", 'online_status': "未知",
                                    'is_admin': sender.id in admin_ids,
                                    'is_bot': sender.bot,
                                    'deleted': getattr(sender, 'deleted', False)
                                }
                                all_results.append(member_info)
                                self.scraped_members = all_results.copy()
                                pending_infos.append(member_info)
                                total_count += 1
                            current_time = time.time()
                            if current_time - last_ui_update >= 1.0 and pending_infos:
                                self.root.after(0, lambda: self.batch_update_preview([]))
                                pending_infos.clear()
                                last_ui_update = current_time
                            if messages_list:
                                offset_id = messages_list[-1].id
                            else:
                                break
                        except FloodWaitError as e:
                            self.log("采集群成员", f"等待 {e.seconds} 秒...")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            self.log("采集群成员", f"错误: {str(e)}")
                            break
                    if pending_infos:
                        self.root.after(0, lambda: self.batch_update_preview([]))
                
                elif scrape_mode == "隐私群采集(仅邀请链接)":
                    self.log("采集群成员", "开始隐私群采集（通过聊天记录获取发言用户）...")
                    if group_username.isdigit():
                        entity = await client.get_entity(int(group_username))
                    else:
                        entity = await client.get_entity(group_username)
                    
                    offset_id = 0
                    batch_size = 3000
                    input_peer = InputPeerChannel(entity.id, entity.access_hash)
                    pending_infos = []
                    last_ui_update = time.time()
                    
                    while self.is_scraping:
                        while self.is_paused:
                            await asyncio.sleep(0.5)
                        if not self.is_scraping:
                            break
                        try:
                            if topic_id:
                                messages = await client.get_messages(entity, limit=batch_size, offset_id=offset_id, reply_to=topic_id)
                                messages_list = messages
                            else:
                                request_args = {
                                    "peer": input_peer,
                                    "offset_id": offset_id,
                                    "offset_date": None,
                                    "add_offset": 0,
                                    "limit": batch_size,
                                    "max_id": 0,
                                    "min_id": 0,
                                    "hash": 0
                                }
                                history = await client(GetHistoryRequest(**request_args))
                                messages_list = history.messages
                                users_map = {u.id: u for u in history.users}
                            
                            if not messages_list:
                                break
                            
                            for msg in messages_list:
                                if not self.is_scraping:
                                    break
                                while self.is_paused:
                                    await asyncio.sleep(0.5)
                                if not self.is_scraping:
                                    break
                                if not msg.sender_id:
                                    continue
                                if 'users_map' in locals() and msg.sender_id in users_map:
                                    sender = users_map.get(msg.sender_id)
                                elif hasattr(msg, 'sender') and msg.sender:
                                    sender = msg.sender
                                else:
                                    try:
                                        sender = await client.get_input_entity(msg.sender_id)
                                    except:
                                        continue
                                if not sender:
                                    continue
                                if not hasattr(sender, 'username') or not sender.username:
                                    continue
                                if sender.id in all_collected_ids:
                                    continue
                                if self.filter_admin.get() and sender.id in admin_ids:
                                    continue
                                if self.filter_bot.get() and sender.bot:
                                    continue
                                if self.filter_deleted.get() and getattr(sender, 'deleted', False):
                                    continue
                                if ad_keywords:
                                    name_lower = f"{sender.first_name or ''} {sender.last_name or ''}".lower()
                                    if any(kw in name_lower for kw in ad_keywords):
                                        continue
                                all_collected_ids.add(sender.id)
                                member_info = {
                                    'id': sender.id, 'username': sender.username,
                                    'first_name': sender.first_name or "", 'last_name': sender.last_name or "",
                                    'phone': "", 'online_status': "未知",
                                    'is_admin': sender.id in admin_ids,
                                    'is_bot': sender.bot,
                                    'deleted': getattr(sender, 'deleted', False)
                                }
                                all_results.append(member_info)
                                self.scraped_members = all_results.copy()
                                pending_infos.append(member_info)
                                total_count += 1
                            current_time = time.time()
                            if current_time - last_ui_update >= 1.0 and pending_infos:
                                self.root.after(0, lambda: self.batch_update_preview([]))
                                pending_infos.clear()
                                last_ui_update = current_time
                            if messages_list:
                                offset_id = messages_list[-1].id
                            else:
                                break
                        except FloodWaitError as e:
                            self.log("采集群成员", f"等待 {e.seconds} 秒...")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            self.log("采集群成员", f"错误: {str(e)}")
                            break
                    if pending_infos:
                        self.root.after(0, lambda: self.batch_update_preview([]))
                
                elif scrape_mode == "多讨论组采集(多个子群)":
                    self.log("采集群成员", "开始多讨论组采集...")
                    sub_groups_text = self.sub_groups_text.get("1.0", tk.END).strip()
                    sub_group_links = [link.strip() for link in sub_groups_text.split('\n') if link.strip()]
                    if not sub_group_links:
                        self.log("采集群成员", "请填写子群链接列表")
                        return
                    self.log("采集群成员", f"共 {len(sub_group_links)} 个子群待采集")
                    for idx, link in enumerate(sub_group_links, 1):
                        if not self.is_scraping:
                            break
                        while self.is_paused:
                            await asyncio.sleep(0.5)
                        if not self.is_scraping:
                            break
                        self.log("采集群成员", f"正在采集第 {idx}/{len(sub_group_links)} 个子群: {link}")
                        try:
                            sub_username, sub_topic = self.parse_group_link(link)
                            if not sub_username:
                                self.log("采集群成员", f"无效的子群链接: {link}")
                                continue
                            entity = await client.get_entity(sub_username)
                            offset_id = 0
                            batch_size = 3000
                            input_peer = InputPeerChannel(entity.id, entity.access_hash)
                            sub_pending = []
                            sub_count = 0
                            while self.is_scraping:
                                while self.is_paused:
                                    await asyncio.sleep(0.5)
                                if not self.is_scraping:
                                    break
                                try:
                                    if sub_topic:
                                        messages = await client.get_messages(entity, limit=batch_size, offset_id=offset_id, reply_to=sub_topic)
                                        messages_list = messages
                                    else:
                                        request_args = {
                                            "peer": input_peer,
                                            "offset_id": offset_id,
                                            "offset_date": None,
                                            "add_offset": 0,
                                            "limit": batch_size,
                                            "max_id": 0,
                                            "min_id": 0,
                                            "hash": 0
                                        }
                                        history = await client(GetHistoryRequest(**request_args))
                                        messages_list = history.messages
                                        users_map = {u.id: u for u in history.users}
                                    if not messages_list:
                                        break
                                    for msg in messages_list:
                                        if not self.is_scraping:
                                            break
                                        while self.is_paused:
                                            await asyncio.sleep(0.5)
                                        if not self.is_scraping:
                                            break
                                        if not msg.sender_id:
                                            continue
                                        if 'users_map' in locals() and msg.sender_id in users_map:
                                            sender = users_map.get(msg.sender_id)
                                        elif hasattr(msg, 'sender') and msg.sender:
                                            sender = msg.sender
                                        else:
                                            try:
                                                sender = await client.get_input_entity(msg.sender_id)
                                            except:
                                                continue
                                        if not sender:
                                            continue
                                        if not hasattr(sender, 'username') or not sender.username:
                                            continue
                                        if sender.id in all_collected_ids:
                                            continue
                                        if self.filter_admin.get() and sender.id in admin_ids:
                                            continue
                                        if self.filter_bot.get() and sender.bot:
                                            continue
                                        if self.filter_deleted.get() and getattr(sender, 'deleted', False):
                                            continue
                                        if ad_keywords:
                                            name_lower = f"{sender.first_name or ''} {sender.last_name or ''}".lower()
                                            if any(kw in name_lower for kw in ad_keywords):
                                                continue
                                        all_collected_ids.add(sender.id)
                                        member_info = {
                                            'id': sender.id, 'username': sender.username,
                                            'first_name': sender.first_name or "", 'last_name': sender.last_name or "",
                                            'phone': "", 'online_status': "未知",
                                            'is_admin': sender.id in admin_ids,
                                            'is_bot': sender.bot,
                                            'deleted': getattr(sender, 'deleted', False)
                                        }
                                        all_results.append(member_info)
                                        self.scraped_members = all_results.copy()
                                        sub_pending.append(member_info)
                                        total_count += 1
                                        sub_count += 1
                                    if messages_list:
                                        offset_id = messages_list[-1].id
                                    else:
                                        break
                                except FloodWaitError as e:
                                    self.log("采集群成员", f"等待 {e.seconds} 秒...")
                                    await asyncio.sleep(e.seconds)
                                except Exception as e:
                                    self.log("采集群成员", f"子群采集错误: {str(e)}")
                                    break
                            self.log("采集群成员", f"子群 {link} 采集完成，本群采集 {sub_count} 人，当前累计 {total_count} 人")
                        except Exception as e:
                            self.log("采集群成员", f"获取子群 {link} 失败: {str(e)}")
                    if total_count > 0:
                        self.root.after(0, lambda: self.batch_update_preview([]))
                
                elif scrape_mode == "频道评论采集":
                    self.log("采集群成员", "开始频道评论采集...")
                    if group_username.isdigit():
                        entity = await client.get_entity(int(group_username))
                    else:
                        entity = await client.get_entity(group_username)
                    
                    offset_id = 0
                    batch_size = 3000
                    input_peer = InputPeerChannel(entity.id, entity.access_hash)
                    pending_infos = []
                    last_ui_update = time.time()
                    
                    while self.is_scraping:
                        while self.is_paused:
                            await asyncio.sleep(0.5)
                        if not self.is_scraping:
                            break
                        try:
                            if topic_id:
                                messages = await client.get_messages(entity, limit=batch_size, offset_id=offset_id, reply_to=topic_id)
                                messages_list = messages
                            else:
                                request_args = {
                                    "peer": input_peer,
                                    "offset_id": offset_id,
                                    "offset_date": None,
                                    "add_offset": 0,
                                    "limit": batch_size,
                                    "max_id": 0,
                                    "min_id": 0,
                                    "hash": 0
                                }
                                history = await client(GetHistoryRequest(**request_args))
                                messages_list = history.messages
                                users_map = {u.id: u for u in history.users}
                            
                            if not messages_list:
                                break
                            
                            for msg in messages_list:
                                if not self.is_scraping:
                                    break
                                while self.is_paused:
                                    await asyncio.sleep(0.5)
                                if not self.is_scraping:
                                    break
                                if not msg.sender_id:
                                    continue
                                if 'users_map' in locals() and msg.sender_id in users_map:
                                    sender = users_map.get(msg.sender_id)
                                elif hasattr(msg, 'sender') and msg.sender:
                                    sender = msg.sender
                                else:
                                    try:
                                        sender = await client.get_input_entity(msg.sender_id)
                                    except:
                                        continue
                                if not sender:
                                    continue
                                if not hasattr(sender, 'username') or not sender.username:
                                    continue
                                if sender.id in all_collected_ids:
                                    continue
                                if self.filter_admin.get() and sender.id in admin_ids:
                                    continue
                                if self.filter_bot.get() and sender.bot:
                                    continue
                                if self.filter_deleted.get() and getattr(sender, 'deleted', False):
                                    continue
                                if ad_keywords:
                                    name_lower = f"{sender.first_name or ''} {sender.last_name or ''}".lower()
                                    if any(kw in name_lower for kw in ad_keywords):
                                        continue
                                all_collected_ids.add(sender.id)
                                member_info = {
                                    'id': sender.id, 'username': sender.username,
                                    'first_name': sender.first_name or "", 'last_name': sender.last_name or "",
                                    'phone': "", 'online_status': "未知",
                                    'is_admin': sender.id in admin_ids,
                                    'is_bot': sender.bot,
                                    'deleted': getattr(sender, 'deleted', False)
                                }
                                all_results.append(member_info)
                                self.scraped_members = all_results.copy()
                                pending_infos.append(member_info)
                                total_count += 1
                            
                            current_time = time.time()
                            if current_time - last_ui_update >= 1.0 and pending_infos:
                                self.root.after(0, lambda: self.batch_update_preview([]))
                                pending_infos.clear()
                                last_ui_update = current_time
                            
                            if messages_list:
                                offset_id = messages_list[-1].id
                            else:
                                break
                        except FloodWaitError as e:
                            self.log("采集群成员", f"等待 {e.seconds} 秒...")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            self.log("采集群成员", f"错误: {str(e)}")
                            break
                    if pending_infos:
                        self.root.after(0, lambda: self.batch_update_preview([]))
                
                self.scraped_members = all_results
                self.log("采集群成员", f"采集完成！累计 {total_count} 人")
                
                if self.scraped_members:
                    is_stop = not self.is_scraping
                    self.save_scraped_members(group_username if group else "multi_groups", is_stop)
                    self.root.after(0, lambda: self.show_centered_info("采集完成" if not is_stop else "采集已停止", f"共采集 {len(self.scraped_members)} 个有用户名的成员\n保存目录: {self.save_path.get()}"))
                else:
                    self.log("采集群成员", "没有采集到任何成员")
                await client.disconnect()
            except Exception as e:
                self.log("采集群成员", f"采集失败: {str(e)}")
                if self.scraped_members:
                    self.save_scraped_members(group_username if group else "multi_groups", True)
            finally:
                self.is_scraping = False
                self.is_paused = False
                self.update_account_task(account_phone, "", False)
                self.update_account_task(account_phone, "采集群成员", False)
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass
        
        def run_scrape():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.scrape_loop = loop
            loop.run_until_complete(do_scrape())
            loop.close()
            self.scrape_loop = None
        
        self.scrape_task = threading.Thread(target=run_scrape, daemon=True)
        self.scrape_task.start()
    
    # ==================== 批量拉人页面 ====================
    def create_invite_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="批量拉人")
        
        main_container = ttk.Frame(page)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        settings_container = ttk.Frame(main_container)
        settings_container.pack(fill="both", expand=True, pady=(0, 5))
        
        settings_canvas = tk.Canvas(settings_container, highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(settings_container, orient="vertical", command=settings_canvas.yview)
        settings_frame = ttk.Frame(settings_canvas)
        
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        settings_canvas.pack(side="left", fill="both", expand=True)
        settings_scrollbar.pack(side="right", fill="y")
        
        canvas_window = settings_canvas.create_window((0, 0), window=settings_frame, anchor="nw", width=settings_canvas.winfo_width())
        
        def on_frame_configure(event):
            settings_canvas.configure(scrollregion=settings_canvas.bbox("all"))
        settings_frame.bind("<Configure>", on_frame_configure)
        
        def on_canvas_configure(event):
            settings_canvas.itemconfig(canvas_window, width=event.width)
        settings_canvas.bind("<Configure>", on_canvas_configure)
        
        def on_mousewheel(event):
            settings_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        settings_canvas.bind("<MouseWheel>", on_mousewheel)
        
        mode_frame = ttk.LabelFrame(settings_frame, text="拉人模式")
        mode_frame.pack(fill="x", pady=5, padx=5)
        
        self.invite_mode = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="单群拉人", variable=self.invite_mode, value="single", command=self.on_invite_mode_change).pack(side="left", padx=20, pady=5)
        ttk.Radiobutton(mode_frame, text="多群拉人", variable=self.invite_mode, value="multi", command=self.on_invite_mode_change).pack(side="left", padx=20, pady=5)
        ttk.Radiobutton(mode_frame, text="管理员拉人", variable=self.invite_mode, value="admin", command=self.on_invite_mode_change).pack(side="left", padx=20, pady=5)
        
        self.settings_panel = ttk.LabelFrame(settings_frame, text="拉人设置")
        self.settings_panel.pack(fill="x", pady=5, padx=5)
        
        self.target_container = ttk.Frame(self.settings_panel)
        self.target_container.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.single_frame = ttk.Frame(self.target_container)
        ttk.Label(self.single_frame, text="目标群组:").pack(side="left", padx=5)
        self.single_target_group = ttk.Entry(self.single_frame, width=50)
        self.single_target_group.pack(side="left", padx=5)
        ttk.Label(self.single_frame, text="（支持链接或ID）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=5)
        
        self.multi_frame = ttk.Frame(self.target_container)
        ttk.Label(self.multi_frame, text="目标群组列表（多个用英文逗号分隔）:").pack(side="left", padx=5)
        self.multi_target_groups = ttk.Entry(self.multi_frame, width=50)
        self.multi_target_groups.pack(side="left", padx=5)
        ttk.Label(self.multi_frame, text="单账号拉群数:").pack(side="left", padx=20)
        self.multi_per_account_limit = ttk.Entry(self.multi_frame, width=10)
        self.multi_per_account_limit.insert(0, "0")
        self.multi_per_account_limit.pack(side="left", padx=5)
        ttk.Label(self.multi_frame, text="（0=不限制）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=2)
        
        self.admin_frame = ttk.Frame(self.target_container)
        ttk.Label(self.admin_frame, text="目标群组或频道:").pack(side="left", padx=5)
        self.admin_target_group = ttk.Entry(self.admin_frame, width=50)
        self.admin_target_group.pack(side="left", padx=5)
        ttk.Label(self.admin_frame, text="（支持链接或ID）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=5)
        ttk.Label(self.admin_frame, text="单账号拉群数:").pack(side="left", padx=20)
        self.admin_per_account_limit = ttk.Entry(self.admin_frame, width=10)
        self.admin_per_account_limit.insert(0, "0")
        self.admin_per_account_limit.pack(side="left", padx=5)
        ttk.Label(self.admin_frame, text="（0=不限制）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=2)
        
        self.single_frame.pack(fill="x")
        self.multi_frame.pack_forget()
        self.admin_frame.pack_forget()
        
        current_row = 1
        separator = ttk.Separator(self.settings_panel, orient="horizontal")
        separator.grid(row=current_row, column=0, sticky="ew", pady=10)
        current_row += 1
        
        file_frame = ttk.Frame(self.settings_panel)
        file_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        ttk.Label(file_frame, text="选择用户列表文件:").pack(side="left", padx=5)
        self.user_list_file = ttk.Entry(file_frame, width=40)
        self.user_list_file.pack(side="left", padx=5)
        ttk.Button(file_frame, text="浏览", command=self.select_user_list_file, width=8).pack(side="left", padx=2)
        ttk.Label(file_frame, text="执行后自动删除已处理的用户", font=("微软雅黑", 8), foreground="red").pack(side="left", padx=10)
        current_row += 1
        
        group_frame = ttk.Frame(self.settings_panel)
        group_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        ttk.Label(group_frame, text="账号分组筛选:").pack(side="left", padx=5)
        self.invite_group_filter = ttk.Combobox(group_frame, values=["全部"] + self.groups, width=15)
        self.invite_group_filter.set("全部")
        self.invite_group_filter.pack(side="left", padx=5)
        self.invite_group_filter.bind("<<ComboboxSelected>>", self.refresh_invite_account_listbox)
        current_row += 1
        
        select_frame = ttk.Frame(self.settings_panel)
        select_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        ttk.Label(select_frame, text="选择账号（可多选）:").pack(side="left", padx=5)
        self.account_select_all_var = tk.BooleanVar()
        ttk.Checkbutton(select_frame, text="全选", variable=self.account_select_all_var,
                       command=lambda: self.toggle_listbox_select(self.invite_account_listbox, self.account_select_all_var)).pack(side="left", padx=5)
        current_row += 1
        
        listbox_frame = ttk.Frame(self.settings_panel)
        listbox_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        self.invite_account_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=4, exportselection=False)
        account_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.invite_account_listbox.yview)
        self.invite_account_listbox.configure(yscrollcommand=account_scrollbar.set)
        self.invite_account_listbox.pack(side="left", fill="x", expand=True)
        account_scrollbar.pack(side="right", fill="y")
        current_row += 1
        
        param_frame = ttk.LabelFrame(self.settings_panel, text="拉人参数")
        param_frame.grid(row=current_row, column=0, sticky="ew", pady=10)
        current_row += 1
        
        param_row1 = ttk.Frame(param_frame)
        param_row1.pack(fill="x", padx=5, pady=5)
        ttk.Label(param_row1, text="单账号每次拉人数:").pack(side="left", padx=5)
        self.invite_per_batch = ttk.Entry(param_row1, width=10)
        self.invite_per_batch.insert(0, "1")
        self.invite_per_batch.pack(side="left", padx=5)
        ttk.Label(param_row1, text="单账号最大拉人数:").pack(side="left", padx=20)
        self.invite_per_account_max = ttk.Entry(param_row1, width=10)
        self.invite_per_account_max.insert(0, "3")
        self.invite_per_account_max.pack(side="left", padx=5)
        ttk.Label(param_row1, text="（0=不限制）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=2)
        
        param_row2 = ttk.Frame(param_frame)
        param_row2.pack(fill="x", padx=5, pady=5)
        ttk.Label(param_row2, text="限制拉人数:").pack(side="left", padx=5)
        self.total_limit = ttk.Entry(param_row2, width=10)
        self.total_limit.insert(0, "0")
        self.total_limit.pack(side="left", padx=5)
        ttk.Label(param_row2, text="（0=不限制）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=2)
        ttk.Label(param_row2, text="线程数:").pack(side="left", padx=20)
        self.thread_count = ttk.Entry(param_row2, width=10)
        self.thread_count.insert(0, "2")
        self.thread_count.pack(side="left", padx=5)
        
        param_row3 = ttk.Frame(param_frame)
        param_row3.pack(fill="x", padx=5, pady=5)
        ttk.Label(param_row3, text="线程等待间隔（秒）:").pack(side="left", padx=5)
        self.thread_interval = ttk.Entry(param_row3, width=10)
        self.thread_interval.insert(0, "20")
        self.thread_interval.pack(side="left", padx=5)
        ttk.Label(param_row3, text="账号每次拉人间隔（秒）:").pack(side="left", padx=20)
        self.invite_interval = ttk.Entry(param_row3, width=10)
        self.invite_interval.insert(0, "20")
        self.invite_interval.pack(side="left", padx=5)
        
        param_row4 = ttk.Frame(param_frame)
        param_row4.pack(fill="x", padx=5, pady=5)
        self.auto_switch_account = tk.BooleanVar(value=True)
        ttk.Checkbutton(param_row4, text="异常账号自动换号", variable=self.auto_switch_account).pack(side="left", padx=20)
        
        self.settings_panel.columnconfigure(0, weight=1)
        
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.pack(pady=10)
        self.start_invite_btn = ttk.Button(btn_frame, text="开始拉人", command=self.start_invite_advanced, width=12)
        self.start_invite_btn.pack(side="left", padx=10)
        self.stop_invite_btn = ttk.Button(btn_frame, text="停止拉人", command=self.stop_invite, width=12)
        self.stop_invite_btn.pack(side="left", padx=10)
        
        log_frame = ttk.LabelFrame(main_container, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["批量拉人"] = scrolledtext.ScrolledText(log_frame, width=100, height=6)
        self.log_widgets["批量拉人"].pack(fill="both", expand=True, padx=5, pady=5)
        
        self.is_inviting = False
        self.invite_stop_flag = False
        self.refresh_invite_account_listbox()
    
    def refresh_invite_account_listbox(self, event=None):
        self.invite_account_listbox.delete(0, tk.END)
        filter_group = self.invite_group_filter.get()
        for acc in self.accounts:
            if acc.get('status') == '正常':
                if filter_group == "全部" or acc.get('group') == filter_group:
                    display_text = f"{acc.get('phone')[-6:]} - {acc.get('nickname')[:10]}"
                    self.invite_account_listbox.insert(tk.END, display_text)
        self.account_select_all_var.set(False)
    
    def get_selected_invite_accounts(self):
        selected_indices = self.invite_account_listbox.curselection()
        selected_accounts = []
        for idx in selected_indices:
            text = self.invite_account_listbox.get(idx)
            phone = text.split(" - ")[0]
            for acc in self.accounts:
                if acc.get('phone')[-6:] == phone and acc.get('status') == '正常':
                    selected_accounts.append(acc)
                    break
        return selected_accounts
    
    def select_user_list_file(self):
        file_path = filedialog.askopenfilename(title="选择用户列表文件", filetypes=[("文本文件", "*.txt"), ("JSON文件", "*.json"), ("所有文件", "*.*")])
        if file_path:
            self.user_list_file.delete(0, tk.END)
            self.user_list_file.insert(0, file_path)
            self.user_list_file_path = file_path
            self.log("批量拉人", f"选择文件: {os.path.basename(file_path)}")
    
    def on_invite_mode_change(self):
        mode = self.invite_mode.get()
        self.single_frame.pack_forget()
        self.multi_frame.pack_forget()
        self.admin_frame.pack_forget()
        if mode == "single":
            self.single_frame.pack(fill="x")
        elif mode == "multi":
            self.multi_frame.pack(fill="x")
        else:
            self.admin_frame.pack(fill="x")
    
    def load_user_list(self):
        file_path = self.user_list_file.get().strip()
        if not file_path:
            self.log("批量拉人", "请先选择用户列表文件")
            return None
        if not os.path.exists(file_path):
            self.log("批量拉人", f"文件不存在: {file_path}")
            return None
        self.user_list_file_path = file_path
        users = []
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        users = data
                    else:
                        users = []
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        username = line.strip()
                        if username:
                            if username.startswith('@'):
                                username = username[1:]
                            users.append(username)
            self.log("批量拉人", f"加载用户: {len(users)} 个")
            return users
        except Exception as e:
            self.log("批量拉人", f"加载失败: {str(e)}")
            return None
    
    def start_invite_advanced(self):
        if self.is_inviting:
            self.log("批量拉人", "任务进行中")
            return
        
        users = self.load_user_list()
        if not users:
            self.log("批量拉人", "请先选择用户列表文件")
            self.show_centered_warning("提示", "请先选择用户列表文件")
            return
        
        selected_accounts = self.get_selected_invite_accounts()
        if not selected_accounts:
            self.log("批量拉人", "请至少选择一个账号")
            self.show_centered_warning("提示", "请至少选择一个账号")
            return
        
        try:
            per_batch = int(self.invite_per_batch.get())
            per_account_max = int(self.invite_per_account_max.get())
            total_limit = int(self.total_limit.get())
            thread_cnt = int(self.thread_count.get())
            thread_wait = float(self.thread_interval.get())
            invite_wait = float(self.invite_interval.get())
            auto_switch = self.auto_switch_account.get()
        except ValueError as e:
            self.log("批量拉人", f"参数错误: {str(e)}")
            self.show_centered_warning("提示", "请检查参数格式")
            return
        
        if per_batch <= 0:
            self.log("批量拉人", "每次拉人数必须大于0")
            return
        if thread_cnt <= 0:
            thread_cnt = 1
        
        mode = self.invite_mode.get()
        targets = []
        if mode == "single":
            target = self.single_target_group.get().strip()
            if not target:
                self.log("批量拉人", "请输入目标群组")
                return
            targets = [target]
            per_account_limit = 0
        elif mode == "multi":
            target_text = self.multi_target_groups.get().strip()
            if not target_text:
                self.log("批量拉人", "请输入目标群组列表")
                return
            targets = [t.strip() for t in target_text.split(',') if t.strip()]
            try:
                per_account_limit = int(self.multi_per_account_limit.get())
            except:
                per_account_limit = 0
        else:
            target = self.admin_target_group.get().strip()
            if not target:
                self.log("批量拉人", "请输入目标群组或频道")
                return
            targets = [target]
            try:
                per_account_limit = int(self.admin_per_account_limit.get())
            except:
                per_account_limit = 0
        
        if total_limit > 0 and total_limit < len(users):
            users = users[:total_limit]
        
        self.log("批量拉人", f"========== 开始拉人 ==========")
        self.log("批量拉人", f"目标: {targets[0] if len(targets)==1 else f'{len(targets)}个群'} | 用户: {len(users)} | 账号: {len(selected_accounts)} | 每账号限: {per_account_max if per_account_max>0 else '不限'}人")
        
        self.is_inviting = True
        self.invite_stop_flag = False
        self.total_success = 0
        self.total_fail = 0
        self.total_processed = 0
        
        for acc in selected_accounts:
            self.update_account_task(acc.get('phone'), "批量拉人", True)
        
        def run_invite_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_invite_advanced_multi_accounts(
                selected_accounts, users, targets, per_batch, per_account_max, 
                per_account_limit, thread_cnt, thread_wait, invite_wait, auto_switch
            ))
            loop.close()
            self.is_inviting = False
            for acc in selected_accounts:
                self.update_account_task(acc.get('phone'), "", False)
                self.update_account_task(acc.get('phone'), "批量拉人", False)
            self.log("批量拉人", f"========== 拉人完成 ==========")
            self.log("批量拉人", f"总统计 | 成功:{self.total_success} | 失败:{self.total_fail} | 总处理:{self.total_processed}")
        
        threading.Thread(target=run_invite_task, daemon=True).start()
    
    async def run_invite_advanced_multi_accounts(self, accounts, users, targets, per_batch, per_account_max, per_account_limit, thread_cnt, thread_wait, invite_wait, auto_switch):
        tasks = []
        for acc in accounts:
            task = self.run_single_account_invite(
                acc, targets, users, per_batch, per_account_max, 
                per_account_limit, invite_wait
            )
            tasks.append(task)
            await asyncio.sleep(1)
        await asyncio.gather(*tasks)
    
    async def invite_user(self, client, phone, entity, username):
        clean_username = username.lstrip('@')
        
        try:
            user_entity = await client.get_entity(clean_username)
        except:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 用户不存在"
        
        if hasattr(user_entity, 'deleted') and user_entity.deleted:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 已注销"
        
        if hasattr(user_entity, 'bot') and user_entity.bot:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 机器人"
        
        try:
            await client(InviteToChannelRequest(entity, [user_entity.id]))
            await asyncio.sleep(0.5)
            self.total_success += 1
            self.total_processed += 1
            return True, f"[{phone[-6:]}] 成功 {clean_username[:15]}"
        except UserPrivacyRestrictedError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 隐私设置"
        except UserNotMutualContactError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 非双向联系人"
        except UserAlreadyParticipantError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 跳过 {clean_username[:15]} | 已在群"
        except UserKickedError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 曾被踢出"
        except UserBannedInChannelError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 被封禁"
        except UserChannelsTooMuchError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 群组已满"
        except FloodWaitError as e:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 频率限制 {e.seconds}s"
        except PeerFloodError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 账号风控"
        except ChatAdminRequiredError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 需管理员权限"
        except ChatWriteForbiddenError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 账号被禁言"
        except PhoneNumberBannedError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 账号已封禁"
        except UserDeactivatedError:
            self.total_fail += 1
            self.total_processed += 1
            return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 账号已注销"
        except Exception as e:
            error_msg = str(e).lower()
            self.total_fail += 1
            self.total_processed += 1
            if "banned" in error_msg:
                return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 账号封禁"
            elif "flood" in error_msg:
                return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 频率限制"
            else:
                return False, f"[{phone[-6:]}] 失败 {clean_username[:15]} | 未知错误"
    
    async def run_single_account_invite(self, acc, targets, users, per_batch, per_account_max, per_account_limit, invite_wait):
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.tl.functions.messages import ImportChatInviteRequest
        from telethon.errors import UserAlreadyParticipantError
        
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        
        client = None
        account_invited_count = 0
        
        try:
            client = TelegramClient(session_path, api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                self.log("批量拉人", f"[{phone[-6:]}] 未登录")
                return
            
            target_entities = []
            for target in targets:
                try:
                    entity = None
                    
                    if 't.me/+' in target or 't.me/joinchat' in target:
                        if '/+' in target:
                            invite_hash = target.split('/+')[-1].split('?')[0]
                        else:
                            invite_hash = target.split('/joinchat/')[-1].split('?')[0]
                        try:
                            result = await client(ImportChatInviteRequest(invite_hash))
                            if result.chats:
                                entity = result.chats[0]
                                self.log("批量拉人", f"[{phone[-6:]}] 加入群组成功")
                        except UserAlreadyParticipantError:
                            self.log("批量拉人", f"[{phone[-6:]}] 已是群成员")
                            try:
                                entity = await client.get_entity(target)
                            except:
                                pass
                        except Exception as e:
                            self.log("批量拉人", f"[{phone[-6:]}] 加入失败: {str(e)[:30]}")
                        if not entity:
                            try:
                                entity = await client.get_entity(target)
                            except:
                                pass
                    else:
                        if 't.me/' in target:
                            username = target.split('t.me/')[-1]
                        elif target.isdigit():
                            username = int(target)
                        else:
                            username = target
                        
                        entity = await client.get_entity(username)
                        
                        self.log("批量拉人", f"[{phone[-6:]}] 加入群组: {getattr(entity, 'title', target)[:20]}")
                        try:
                            await client(JoinChannelRequest(entity))
                            self.log("批量拉人", f"[{phone[-6:]}] 加入成功")
                            await asyncio.sleep(1)
                        except UserAlreadyParticipantError:
                            self.log("批量拉人", f"[{phone[-6:]}] 已是成员")
                        except Exception as e:
                            self.log("批量拉人", f"[{phone[-6:]}] 加入失败: {str(e)[:30]}")
                            continue
                    
                    if entity:
                        target_entities.append((target, entity))
                except Exception as e:
                    self.log("批量拉人", f"[{phone[-6:]}] 解析失败: {str(e)[:30]}")
            
            if not target_entities:
                self.log("批量拉人", f"[{phone[-6:]}] 无有效目标")
                return
            
            user_index = 0
            while user_index < len(users) and not self.invite_stop_flag:
                if per_account_max > 0 and account_invited_count >= per_account_max:
                    break
                
                username = users[user_index]
                user_index += 1
                
                for target, entity in target_entities:
                    if self.invite_stop_flag:
                        break
                    if per_account_limit > 0 and account_invited_count >= per_account_limit:
                        break
                    
                    success, log_msg = await self.invite_user(
                        client, phone, entity, username
                    )
                    
                    self.log("批量拉人", log_msg)
                    
                    self.remove_user_from_file(username)
                    
                    if success:
                        account_invited_count += 1
                    
                    await asyncio.sleep(invite_wait)
                    break
                
        except Exception as e:
            self.log("批量拉人", f"[{phone[-6:]}] 异常: {str(e)[:50]}")
        finally:
            if client:
                await client.disconnect()
    
    def stop_invite(self):
        if self.is_inviting:
            self.invite_stop_flag = True
            self.log("批量拉人", "停止拉人")
        else:
            self.log("批量拉人", "无进行中的任务")
    
    # ==================== 群发广告页面 ====================
    def create_send_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="群发广告")
        
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        frame = ttk.LabelFrame(main_frame, text="群发设置")
        frame.pack(fill="x", pady=5)
        
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
        
        ttk.Label(frame, text="时间间隔(秒):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.send_delay = ttk.Entry(frame, width=10)
        self.send_delay.insert(0, "30")
        self.send_delay.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame2, text="开始群发", command=self.start_send).pack()
        
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["群发广告"] = scrolledtext.ScrolledText(log_frame, width=100, height=12)
        self.log_widgets["群发广告"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def import_ad_text(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.ad_text.delete("1.0", tk.END)
            self.ad_text.insert("1.0", content)
            self.log("群发广告", f"导入广告词: {file_path}")
    
    def start_send(self):
        ad_content = self.ad_text.get("1.0", tk.END).strip()
        account_phone = self.send_account.get()
        delay = int(self.send_delay.get())
        if not ad_content:
            self.log("群发广告", "请输入广告词")
            return
        save_dir = self.save_path.get().strip()
        if not save_dir:
            self.log("群发广告", "请先在采集页面选择保存目录")
            self.show_centered_warning("提示", "请先在采集页面选择保存目录")
            return
        if os.path.exists(save_dir):
            json_files = [f for f in os.listdir(save_dir) if f.startswith("members_") and f.endswith(".json")]
        else:
            json_files = []
        if not json_files:
            self.log("群发广告", "请先采集群成员")
            self.show_centered_warning("提示", "请先采集群成员")
            return
        latest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(save_dir, f)))
        with open(os.path.join(save_dir, latest_file), "r", encoding="utf-8") as f:
            usernames = json.load(f)
        self.log("群发广告", f"开始群发: {len(usernames)} 个用户, 间隔: {delay}秒")
        if account_phone != "全部账号":
            self.update_account_task(account_phone, "群发广告", True)
        async def do_send():
            client = None
            try:
                if account_phone == "全部账号":
                    for acc in self.accounts:
                        if acc.get('status') == '正常':
                            phone = acc.get('phone', '')
                            session_path = acc.get('session_path', '')
                            api_id, api_hash = self.get_account_api_credentials(acc)
                            client = TelegramClient(session_path, api_id, api_hash)
                            await client.connect()
                            for username in usernames:
                                try:
                                    user_entity = await client.get_entity(username)
                                    await client.send_message(user_entity.id, ad_content)
                                    self.log("群发广告", f"[{phone}] 发送成功: {username}")
                                    await asyncio.sleep(delay)
                                except FloodWaitError as e:
                                    self.log("群发广告", f"请求频繁，等待{e.seconds}秒")
                                    await asyncio.sleep(e.seconds)
                                except Exception as e:
                                    self.log("群发广告", f"发送失败 {username}: {str(e)[:50]}")
                            await client.disconnect()
                            client = None
                else:
                    acc = None
                    for a in self.accounts:
                        if a.get('phone') == account_phone:
                            acc = a
                            break
                    if not acc:
                        self.log("群发广告", "未找到账号")
                        return
                    if acc.get('status') != '正常':
                        self.log("群发广告", "请先登录账号")
                        return
                    session_path = acc.get('session_path', '')
                    api_id, api_hash = self.get_account_api_credentials(acc)
                    client = TelegramClient(session_path, api_id, api_hash)
                    await client.connect()
                    for username in usernames:
                        try:
                            user_entity = await client.get_entity(username)
                            await client.send_message(user_entity.id, ad_content)
                            self.log("群发广告", f"发送成功: {username}")
                            await asyncio.sleep(delay)
                        except FloodWaitError as e:
                            self.log("群发广告", f"请求频繁，等待{e.seconds}秒")
                            await asyncio.sleep(e.seconds)
                        except Exception as e:
                            self.log("群发广告", f"发送失败 {username}: {str(e)[:50]}")
                self.log("群发广告", "群发完成")
                self.show_centered_info("群发完成", "群发已完成")
                if account_phone != "全部账号":
                    self.update_account_task(account_phone, "", False)
                    self.update_account_task(account_phone, "群发广告", False)
            except Exception as e:
                self.log("群发广告", f"群发失败: {e}")
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass
        def run_send():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(do_send())
            loop.close()
        threading.Thread(target=run_send, daemon=True).start()
    
    # ==================== 自动群聊页面 ====================
    def create_group_chat_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动群聊+回复")
        
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        frame = ttk.LabelFrame(main_frame, text="群聊设置")
        frame.pack(fill="x", pady=5)
        
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
        
        kw_frame = ttk.LabelFrame(main_frame, text="关键词自动回复")
        kw_frame.pack(fill="x", pady=5)
        
        self.keyword_text = scrolledtext.ScrolledText(kw_frame, width=80, height=6)
        self.keyword_text.pack(fill="x", padx=5, pady=5)
        
        btn_frame2 = ttk.Frame(kw_frame)
        btn_frame2.pack(pady=5)
        ttk.Button(btn_frame2, text="保存关键词配置", command=self.save_keywords).pack(side="left", padx=5)
        ttk.Button(btn_frame2, text="加载关键词配置", command=self.load_keywords).pack(side="left", padx=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["自动群聊"] = scrolledtext.ScrolledText(log_frame, width=100, height=8)
        self.log_widgets["自动群聊"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def start_group_chat(self):
        group = self.chat_group.get()
        account_phone = self.chat_account.get()
        interval = int(self.chat_interval.get())
        daily_limit = int(self.chat_daily.get())
        if not group:
            self.log("自动群聊", "请输入目标群组")
            return
        if not account_phone:
            self.log("自动群聊", "请选择账号")
            return
        acc = None
        for a in self.accounts:
            if a.get('phone') == account_phone:
                acc = a
                break
        if not acc:
            self.log("自动群聊", "未找到账号")
            return
        if acc.get('status') != '正常':
            self.log("自动群聊", "请先登录账号")
            self.show_centered_warning("提示", "请先登录账号")
            return
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        self.log("自动群聊", f"启动炒群: {group} 使用账号: {account_phone}")
        self.running_tasks['chat'] = True
        self.update_account_task(account_phone, "自动群聊", True)
        scripts = []
        if os.path.exists("scripts.txt"):
            with open("scripts.txt", "r", encoding="utf-8") as f:
                scripts = [line.strip() for line in f if line.strip()]
        if not scripts:
            scripts = ["Hello!", "Good morning!", "Nice to meet you!"]
        keywords = {}
        if os.path.exists("keywords.json"):
            with open("keywords.json", "r") as f:
                keywords = json.load(f)
        async def do_chat():
            from telethon import events
            client = None
            try:
                client = TelegramClient(session_path, api_id, api_hash)
                await client.connect()
                if not await client.is_user_authorized():
                    self.log("自动群聊", "账号未登录")
                    return
                if 't.me/' in group:
                    group_username = group.split('t.me/')[-1]
                    entity = await client.get_entity(group_username)
                else:
                    entity = await client.get_entity(int(group))
                @client.on(events.NewMessage(chats=entity))
                async def handle_reply(event):
                    if not self.running_tasks.get('chat', False):
                        return
                    text = event.message.text
                    for kw, reply in keywords.items():
                        if kw.lower() in text.lower():
                            await event.reply(reply)
                            self.log("自动群聊", f"自动回复: {reply[:30]}...")
                            break
                async def auto_speak():
                    import random
                    count = 0
                    while self.running_tasks.get('chat', False) and count < daily_limit:
                        script = random.choice(scripts)
                        await client.send_message(entity, script)
                        self.log("自动群聊", f"自动发言: {script[:30]}...")
                        count += 1
                        await asyncio.sleep(interval)
                asyncio.create_task(auto_speak())
                await client.run_until_disconnected()
            except Exception as e:
                self.log("自动群聊", f"炒群出错: {e}")
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass
        def run_chat():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(do_chat())
            loop.close()
            self.update_account_task(account_phone, "", False)
            self.update_account_task(account_phone, "自动群聊", False)
        threading.Thread(target=run_chat, daemon=True).start()
    
    def stop_group_chat(self):
        self.running_tasks['chat'] = False
        self.log("自动群聊", "停止炒群")
    
    def save_keywords(self):
        content = self.keyword_text.get("1.0", tk.END).strip()
        keywords = {}
        for line in content.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                keywords[key.strip()] = value.strip()
        with open("keywords.json", "w", encoding="utf-8") as f:
            json.dump(keywords, f, ensure_ascii=False, indent=2)
        self.log("自动群聊", "关键词配置已保存")
    
    def load_keywords(self):
        if os.path.exists("keywords.json"):
            with open("keywords.json", "r") as f:
                keywords = json.load(f)
            content = "\n".join([f"{k}={v}" for k, v in keywords.items()])
            self.keyword_text.delete("1.0", tk.END)
            self.keyword_text.insert("1.0", content)
            self.log("自动群聊", "关键词配置已加载")
    
    # ==================== 自动注册页面 ====================
    def create_auto_register_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动注册账号")
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        frame = ttk.LabelFrame(main_frame, text="注册设置")
        frame.pack(fill="x", pady=5)
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
        self.save_path_register = ttk.Entry(frame, width=40)
        self.save_path_register.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        ttk.Button(frame, text="浏览", command=self.select_register_path).grid(row=3, column=2, padx=5)
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="开始批量注册", command=self.start_register).pack()
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["自动注册"] = scrolledtext.ScrolledText(log_frame, width=100, height=12)
        self.log_widgets["自动注册"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def select_register_path(self):
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.save_path_register.delete(0, tk.END)
            self.save_path_register.insert(0, folder)
            self.log("自动注册", f"设置保存路径: {folder}")
    
    def start_register(self):
        self.log("自动注册", "批量注册功能需要对接具体接码平台API")
        self.show_centered_info("提示", "请先配置接码平台API")
    
    # ==================== 监听页面 ====================
    def create_monitor_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="监听群组")
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        frame = ttk.LabelFrame(main_frame, text="监听设置")
        frame.pack(fill="x", pady=5)
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
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["监听群组"] = scrolledtext.ScrolledText(log_frame, width=100, height=12)
        self.log_widgets["监听群组"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def start_monitor(self):
        self.log("监听群组", "监听功能开发中")
        self.show_centered_info("提示", "监听功能开发中")
    
    def stop_monitor(self):
        self.log("监听群组", "停止监听")
        self.running_tasks['monitor'] = False
    
    # ==================== 话术配置页面 ====================
    def create_script_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="话术配置")
        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        frame = ttk.LabelFrame(main_frame, text="话术库")
        frame.pack(fill="both", expand=True, pady=5)
        self.script_text = scrolledtext.ScrolledText(frame, width=80, height=15)
        self.script_text.pack(fill="both", expand=True, padx=5, pady=5)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="导入TXT", command=self.import_script).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_scripts).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="加载配置", command=self.load_scripts).pack(side="left", padx=5)
        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["话术配置"] = scrolledtext.ScrolledText(log_frame, width=100, height=8)
        self.log_widgets["话术配置"].pack(fill="both", expand=True, padx=5, pady=5)
    
    def import_script(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", content)
            self.log("话术配置", f"导入话术: {file_path}")
    
    def save_scripts(self):
        content = self.script_text.get("1.0", tk.END).strip()
        with open("scripts.txt", "w", encoding="utf-8") as f:
            f.write(content)
        self.log("话术配置", "话术已保存")
    
    def load_scripts(self):
        if os.path.exists("scripts.txt"):
            with open("scripts.txt", "r", encoding="utf-8") as f:
                content = f.read()
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", content)
            self.log("话术配置", "话术已加载")
    
    def export_config(self):
        self.save_config()
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            shutil.copy(CONFIG_FILE, file_path)
            self.log("多账号管理", "配置已导出")
    
    def import_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            shutil.copy(file_path, CONFIG_FILE)
            self.load_config()
            self.refresh_account_list()
            self.refresh_proxy_list()
            self.refresh_scrape_accounts()
            self.refresh_invite_group_filter()
            self.log("多账号管理", "配置已导入")
    
    def about(self):
        self.show_centered_info("关于", "天师府TG全能营销系统\n联系@Tian2547\n版本: 2.0\n\n功能：\n- 多账号管理\n- 代理IP管理\n- 采集群成员\n- 批量拉人\n- 群发广告\n- 自动群聊\n- 话术配置")

if __name__ == "__main__":
    from telethon import events
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
