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
from telethon import TelegramClient, events
from telethon.errors import (
    FloodWaitError, UserDeactivatedError, SessionPasswordNeededError,
    PhoneNumberBannedError, UserAlreadyParticipantError, UserPrivacyRestrictedError,
    PeerFloodError, InviteHashExpiredError, InviteHashInvalidError,
    ChannelInvalidError, ChannelPrivateError, UsernameInvalidError,
    UserKickedError, UserBannedInChannelError, ChatAdminRequiredError,
    UserNotMutualContactError, ChatWriteForbiddenError, UserChannelsTooMuchError,
    AuthKeyUnregisteredError, SessionRevokedError, RPCError
)
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantsRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsAdmins, ChannelParticipantsBots, ChannelParticipantsRecent, Message, InputPeerChannel, InputPhoto
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest, GetPasswordRequest, UpdatePasswordSettingsRequest
from telethon.tl.types import UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth, UserStatusOffline, UserStatusOnline, InputFile, PasswordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.messages import GetInlineBotResultsRequest, SendInlineBotResultRequest
from telethon.tl.functions.auth import SendCodeRequest, SignInRequest, LogOutRequest
from telethon.tl.functions.account import GetAuthorizationsRequest, ResetAuthorizationRequest
from telethon.sessions import StringSession, MemorySession
from telethon.crypto import AuthKey

SERVER = "http://172.98.23.64:5000"
CARD_API = "https://tgpremium.site/tgyinxiao/verify.php"
CONFIG_FILE = "tg_config.json"

class TelegramFullGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("良子TG全能营销系统 联系@Liangzi1952")
        self.root.geometry("1200x950")
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

        self.chat_message_cache = {}

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
            self.root.update_idletasks()

    def update_account_task(self, phone, task_name, is_current=True):
        for acc in self.accounts:
            if acc.get('phone') == phone:
                if is_current:
                    acc['current_task'] = task_name
                else:
                    acc['last_action'] = task_name
                break
        self.refresh_account_list_filter()

    def update_account_status_by_phone(self, phone, error_type, error_detail=""):
        for acc in self.accounts:
            if acc.get('phone') == phone:
                old_status = acc.get('status', '正常')
                if error_type == '封禁':
                    acc['status'] = '封禁'
                elif error_type == '销号':
                    acc['status'] = '销号'
                elif error_type == '限制加群':
                    acc['status'] = '限制加群'
                elif error_type == '发言限制':
                    acc['status'] = '发言限制'
                elif error_type == '频率限制' and old_status not in ['封禁', '销号']:
                    acc['status'] = '频率限制'
                elif error_type == '风控限制' and old_status not in ['封禁', '销号', '频率限制']:
                    acc['status'] = '风控限制'
                elif error_type == '双向限制' and old_status not in ['封禁', '销号', '频率限制', '风控限制']:
                    acc['status'] = '双向限制'
                break
        self.refresh_account_list_filter()
        self.update_status_filter_options()

    def update_status_filter_options(self):
        statuses = set(["全部"])
        for acc in self.accounts:
            status = acc.get('status', '待检测')
            statuses.add(status)
        all_statuses = ["全部", "正常", "未授权", "待检测", "销号", "封禁", "限制加群", "发言限制", "频率限制", "风控限制", "双向限制", "需要2FA重新登录", "被踢下线", "session已过期", "2FA已修改", "账号冻结", "登录限制", "未授权(超时)", "未注册", "手机号无效", "需要Premium"]
        for s in all_statuses:
            statuses.add(s)
        self.account_list_status_filter['values'] = list(statuses)
        current = self.account_list_status_filter.get()
        if current not in statuses and current != "全部":
            self.account_list_status_filter.set("全部")

    def remove_user_from_file(self, username, file_path=None):
        target_file = file_path or self.private_user_list_file.get()
        if not target_file or not os.path.exists(target_file):
            return False

        with self.user_list_lock:
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                clean_username = username.lstrip('@')
                lines = content.split('\n')
                new_lines = []
                removed = False
                for line in lines:
                    line_username = line.strip().lstrip('@')
                    if line_username != clean_username:
                        new_lines.append(line)
                    else:
                        removed = True

                if removed:
                    with open(target_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    return True
                return False
            except Exception as e:
                return False

    def parse_unauthorized_error(self, phone, e, operation="检测"):
        error_msg = str(e)
        error_lower = error_msg.lower()

        if isinstance(e, UserDeactivatedError) or "deactivated" in error_lower:
            return "销号", f"[{phone}] ❌ 账号已注销(销号)"
        if isinstance(e, PhoneNumberBannedError) or "banned" in error_lower:
            return "封禁", f"[{phone}] ❌ 账号已被封禁"
        if isinstance(e, SessionPasswordNeededError) or "password" in error_lower:
            return "需要2FA重新登录", f"[{phone}] ⚠️ 需要2FA密码重新登录"
        if isinstance(e, SessionRevokedError) or "session_revoked" in error_lower:
            return "被踢下线", f"[{phone}] 🔴 账号在其他设备登录，被踢下线"
        if isinstance(e, AuthKeyUnregisteredError) or "auth_key_unregistered" in error_lower:
            return "session已过期", f"[{phone}] 🟡 session已过期，请重新登录"
        if "password_hash_invalid" in error_lower:
            return "2FA已修改", f"[{phone}] 🟠 2FA密码已被修改，需要重新登录"
        if "frozen" in error_lower:
            return "账号冻结", f"[{phone}] 🔵 账号被冻结，需要激活"
        if "phone_number_unregistered" in error_lower or "unregistered" in error_lower:
            return "未注册", f"[{phone}] ❌ 手机号未注册"
        if "phone_number_invalid" in error_lower:
            return "手机号无效", f"[{phone}] ❌ 手机号无效"
        if "api_id" in error_lower or "api_hash" in error_lower:
            return "API错误", f"[{phone}] ⚠️ API ID或API Hash无效"
        if "timeout" in error_lower or "timed out" in error_lower:
            return "未授权(超时)", f"[{phone}] ⚠️ 连接超时"
        if "connection" in error_lower or "network" in error_lower:
            return "未授权", f"[{phone}] ⚠️ 网络连接失败: {error_msg[:50]}"
        return "未授权", f"[{phone}] ⚠️ {operation}异常: {error_msg[:80]}"

    def show_card_login(self):
        login_window = tk.Toplevel(self.root)
        login_window.title("卡密登录 - 良子TG全能营销系统")
        login_window.geometry("450x350")
        login_window.resizable(False, False)
        login_window.transient(self.root)
        login_window.grab_set()
        self.center_window(login_window, 450, 350)

        title_label = tk.Label(login_window, text="良子TG全能营销系统", font=("微软雅黑", 18, "bold"))
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

        tip_label = tk.Label(login_window, text="购买卡密请联系 @Liangzi1952", font=("微软雅黑", 9), foreground="gray")
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
        webbrowser.open("https://t.me/Liangzi1952")

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
        self.create_direct_login_page()

        self.status_bar = ttk.Label(self.root, text=f"已激活 | 有效期: {self.card_info.get('expire_date', '永久')} | 联系@Liangzi1952", relief="sunken")
        self.status_bar.pack(side="bottom", fill="x")

        self.refresh_invite_group_filter()
        self.refresh_account_list_filter()
        self.refresh_proxy_list()
        self.refresh_scrape_accounts()

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
        if hasattr(self, 'account_list_group_filter'):
            self.account_list_group_filter['values'] = ["全部"] + self.groups
            self.account_list_group_filter.set("全部")
        if hasattr(self, 'account_list_status_filter'):
            statuses = set(["全部"])
            for acc in self.accounts:
                status = acc.get('status', '待检测')
                statuses.add(status)
            self.account_list_status_filter['values'] = list(statuses)
            self.account_list_status_filter.set("全部")

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
            info_text = f"良子TG全能营销系统\n\n卡密状态: 已激活\n有效期至: {self.card_info.get('expire_date', '永久')}\n设备绑定: 已绑定\n\n联系客服: @Liangzi1952"
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

    def get_filtered_accounts(self):
        filter_group = self.account_list_group_filter.get()
        filter_status = self.account_list_status_filter.get()

        filtered = []
        for acc in self.accounts:
            if filter_group != "全部" and acc.get('group', '默认分组') != filter_group:
                continue
            if filter_status != "全部" and acc.get('status', '待检测') != filter_status:
                continue
            filtered.append(acc)
        return filtered

    def refresh_account_list_filter(self, event=None):
        filter_group = self.account_list_group_filter.get()
        filter_status = self.account_list_status_filter.get()

        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        i = 1
        for acc in self.accounts:
            if filter_group != "全部" and acc.get('group', '默认分组') != filter_group:
                continue
            if filter_status != "全部" and acc.get('status', '待检测') != filter_status:
                continue

            self.account_tree.insert("", "end", values=(
                i, acc.get('phone', ''), acc.get('group', '默认分组'),
                acc.get('nickname', ''), acc.get('current_task', ''),
                acc.get('last_action', ''), acc.get('status', '待检测'),
                acc.get('register_time', '未知'), acc.get('proxy', '未设置')
            ))
            i += 1

        self.update_status_filter_options()

    def show_account_selector(self, title, group_filter_default="全部", status_filter_default="正常", multi_select=True):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("700x550")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 750, 550)

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill="x", pady=5)

        ttk.Label(filter_frame, text="分组筛选:").pack(side="left", padx=5)
        group_var = tk.StringVar(value=group_filter_default)
        group_combo = ttk.Combobox(filter_frame, textvariable=group_var, values=["全部"] + self.groups, width=15)
        group_combo.pack(side="left", padx=5)

        ttk.Label(filter_frame, text="状态筛选:").pack(side="left", padx=20)
        status_var = tk.StringVar(value=status_filter_default)
        status_combo = ttk.Combobox(filter_frame, textvariable=status_var, values=["全部", "正常", "未授权", "待检测", "销号", "封禁", "限制加群", "发言限制", "频率限制", "风控限制", "双向限制", "需要2FA重新登录", "被踢下线", "session已过期", "2FA已修改", "账号冻结", "登录限制", "未授权(超时)", "未注册", "手机号无效", "需要Premium"], width=15)
        status_combo.pack(side="left", padx=5)

        select_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="全选", variable=select_all_var).pack(side="left", padx=20)

        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.pack(fill="both", expand=True, pady=5)

        columns = ("选择", "序号", "手机号", "昵称", "分组", "状态")
        tree = ttk.Treeview(listbox_frame, columns=columns, show="headings", height=18)

        tree.heading("选择", text="☑")
        tree.heading("序号", text="序号")
        tree.heading("手机号", text="手机号")
        tree.heading("昵称", text="昵称")
        tree.heading("分组", text="分组")
        tree.heading("状态", text="状态")

        tree.column("选择", anchor="center", width=40)
        tree.column("序号", anchor="center", width=50)
        tree.column("手机号", anchor="center", width=120)
        tree.column("昵称", anchor="center", width=150)
        tree.column("分组", anchor="center", width=100)
        tree.column("状态", anchor="center", width=80)

        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        check_vars = {}

        def refresh_account_list():
            for item in tree.get_children():
                tree.delete(item)
            check_vars.clear()

            filter_group = group_var.get()
            filter_status = status_var.get()

            selected_indices = []
            for i, acc in enumerate(self.accounts):
                if filter_group != "全部" and acc.get('group', '默认分组') != filter_group:
                    continue
                if filter_status != "全部" and acc.get('status', '待检测') != filter_status:
                    continue
                selected_indices.append(i)

            for idx, i in enumerate(selected_indices, 1):
                acc = self.accounts[i]
                phone = acc.get('phone', '')
                nickname = acc.get('nickname', '')[:25]
                group = acc.get('group', '默认分组')
                status = acc.get('status', '待检测')

                var = tk.BooleanVar(value=False)
                check_vars[phone] = var

                status_display = status
                tree.insert("", "end", iid=phone, values=("", idx, phone, nickname, group, status_display))

                if status == "正常":
                    tree.tag_configure('normal', background='#e8f5e9')
                    tree.item(phone, tags=('normal',))
                elif status in ["销号", "封禁"]:
                    tree.tag_configure('dead', background='#ffebee')
                    tree.item(phone, tags=('dead',))
                elif status in ["未授权", "需要2FA", "需要2FA重新登录", "被踢下线", "session已过期", "2FA已修改", "账号冻结", "登录限制", "未授权(超时)", "未注册", "手机号无效", "需要Premium"]:
                    tree.tag_configure('unauth', background='#fff3e0')
                    tree.item(phone, tags=('unauth',))
                elif status in ["限制加群", "发言限制", "频率限制", "风控限制", "双向限制"]:
                    tree.tag_configure('limited', background='#fff9c4')
                    tree.item(phone, tags=('limited',))

        def on_tree_click(event):
            region = tree.identify_region(event.x, event.y)
            if region == "cell":
                column = tree.identify_column(event.x)
                if column == "#1":
                    item = tree.identify_row(event.y)
                    if item:
                        current = check_vars.get(item, tk.BooleanVar(value=False))
                        current.set(not current.get())
                        tree.set(item, "#1", "☑" if current.get() else "")

        def on_select_all():
            select_all = select_all_var.get()
            for phone, var in check_vars.items():
                var.set(select_all)
                tree.set(phone, "#1", "☑" if select_all else "")

        def on_group_status_change(event=None):
            refresh_account_list()
            select_all_var.set(False)

        group_combo.bind("<<ComboboxSelected>>", on_group_status_change)
        status_combo.bind("<<ComboboxSelected>>", on_group_status_change)
        select_all_var.trace('w', lambda *args: on_select_all())
        tree.bind("<ButtonRelease-1>", on_tree_click)

        refresh_account_list()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)

        selected_accounts = []

        def on_confirm():
            nonlocal selected_accounts
            for acc in self.accounts:
                phone = acc.get('phone', '')
                if phone in check_vars and check_vars[phone].get():
                    selected_accounts.append(acc)
            dialog.destroy()

        def on_cancel():
            nonlocal selected_accounts
            selected_accounts = []
            dialog.destroy()

        ttk.Button(btn_frame, text="确定", command=on_confirm, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="取消", command=on_cancel, width=12).pack(side="left", padx=10)
        ttk.Label(btn_frame, text=f"共 {len([v for v in check_vars.values() if v.get()])} 个账号", foreground="blue").pack(side="left", padx=20)

        self.root.wait_window(dialog)

        return selected_accounts

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
        ttk.Button(toolbar, text="一键登录", command=self.login_filtered_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="深度检测", command=self.deep_check_filtered_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="修改资料", command=self.batch_edit_profile).pack(side="left", padx=2)
        ttk.Button(toolbar, text="踢出设备", command=self.kick_devices_filtered).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中账号", command=self.delete_selected_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除死号", command=self.delete_dead_accounts_filtered).pack(side="left", padx=2)
        ttk.Button(toolbar, text="刷新列表", command=self.refresh_account_list_filter).pack(side="left", padx=2)

        filter_bar = ttk.Frame(main_frame)
        filter_bar.pack(fill="x", pady=5)

        ttk.Label(filter_bar, text="分组筛选:").pack(side="left", padx=5)
        self.account_list_group_filter = ttk.Combobox(filter_bar, values=["全部"] + self.groups, width=15)
        self.account_list_group_filter.set("全部")
        self.account_list_group_filter.pack(side="left", padx=5)
        self.account_list_group_filter.bind("<<ComboboxSelected>>", self.refresh_account_list_filter)

        ttk.Label(filter_bar, text="状态筛选:").pack(side="left", padx=20)
        self.account_list_status_filter = ttk.Combobox(filter_bar, values=["全部"], width=15)
        self.account_list_status_filter.set("全部")
        self.account_list_status_filter.pack(side="left", padx=5)
        self.account_list_status_filter.bind("<<ComboboxSelected>>", self.refresh_account_list_filter)

        statuses = set(["全部"])
        for acc in self.accounts:
            status = acc.get('status', '待检测')
            statuses.add(status)
        self.account_list_status_filter['values'] = list(statuses)

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
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["多账号管理"] = scrolledtext.ScrolledText(log_frame, width=100, height=4)
        self.log_widgets["多账号管理"].pack(fill="both", expand=True, padx=5, pady=5)

    def login_filtered_accounts(self):
        filtered_accounts = self.get_filtered_accounts()
        if not filtered_accounts:
            self.log("多账号管理", "当前筛选条件下没有账号可操作")
            self.show_centered_warning("提示", "当前筛选条件下没有账号可操作")
            return

        self.log("多账号管理", f"开始登录 {len(filtered_accounts)} 个账号（当前筛选结果）...")

        def do_login():
            for idx, acc in enumerate(filtered_accounts, 1):
                phone = acc.get('phone', '')
                self.log("多账号管理", f"[{idx}/{len(filtered_accounts)}] 正在登录: {phone}")
                self.login_single_account(acc)
                time.sleep(2)
            self.log("多账号管理", "登录完成")
            self.save_config()

        threading.Thread(target=do_login, daemon=True).start()

    def parse_proxy_string(self, proxy_str):
        """解析代理字符串，支持多种格式"""
        if not proxy_str:
            return None
        try:
            proxy_type = 'socks5'
            original = proxy_str
            
            if proxy_str.startswith('http://'):
                proxy_type = 'http'
                proxy_str = proxy_str[7:]
            elif proxy_str.startswith('https://'):
                proxy_type = 'https'
                proxy_str = proxy_str[8:]
            elif proxy_str.startswith('socks5://'):
                proxy_type = 'socks5'
                proxy_str = proxy_str[9:]
            elif proxy_str.startswith('socks4://'):
                proxy_type = 'socks4'
                proxy_str = proxy_str[9:]

            pattern = r'^([^:]+):([^@]+)@([^:]+):(\d+)$'
            match = re.match(pattern, proxy_str)
            if match:
                username = match.group(1)
                password = match.group(2)
                host = match.group(3)
                port = int(match.group(4))
                return (proxy_type, host, port, username, password)

            pattern2 = r'^([^:]+):(\d+)##([^#]+)##([^#]+)$'
            match = re.match(pattern2, proxy_str)
            if match:
                host = match.group(1)
                port = int(match.group(2))
                username = match.group(4)
                password = match.group(3)
                return (proxy_type, host, port, username, password)

            pattern3 = r'^([^:]+):(\d+)$'
            match = re.match(pattern3, proxy_str)
            if match:
                host = match.group(1)
                port = int(match.group(2))
                return (proxy_type, host, port)

            return None
        except Exception as e:
            return None

    def login_single_account(self, acc):
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        twofa = self.get_account_twofa(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

        async def do_login():
            client = None
            try:
                from telethon.sessions import StringSession, MemorySession

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                            self.log("多账号管理", f"[{phone}] 使用StringSession加载")
                    except (UnicodeDecodeError, UnicodeError):
                        session = session_path
                        self.log("多账号管理", f"[{phone}] 使用二进制Session加载")
                    except Exception:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()

                if await client.is_user_authorized():
                    me = await client.get_me()
                    if getattr(me, 'deleted', False):
                        acc['status'] = '销号'
                        self.log("多账号管理", f"[{phone}] ❌ 账号已注销(销号)")
                        await client.disconnect()
                        self.update_status_filter_options()
                        return False

                    nickname = me.first_name or me.username or phone
                    acc['nickname'] = nickname
                    if hasattr(me, 'date'):
                        acc['register_time'] = me.date.strftime("%Y-%m-%d")
                    acc['status'] = '正常'
                    self.log("多账号管理", f"[{phone}] ✅ 登录成功 | 昵称: {nickname} | 代理: {proxy_str if proxy_str else '无'}")
                    await client.disconnect()
                    self.update_status_filter_options()
                    return True
                else:
                    try:
                        await asyncio.wait_for(client.get_me(), timeout=5)
                        me = await client.get_me()
                        if getattr(me, 'deleted', False):
                            acc['status'] = '销号'
                            self.log("多账号管理", f"[{phone}] ❌ 账号已注销(销号)")
                        else:
                            acc['status'] = '未授权'
                            self.log("多账号管理", f"[{phone}] ⚠️ session未授权(登录态失效)")
                    except asyncio.TimeoutError:
                        acc['status'] = '未授权(超时)'
                        self.log("多账号管理", f"[{phone}] ⚠️ 连接超时")
                    except SessionPasswordNeededError:
                        acc['status'] = '需要2FA重新登录'
                        self.log("多账号管理", f"[{phone}] ⚠️ 需要2FA密码重新登录")
                    except UserDeactivatedError:
                        acc['status'] = '销号'
                        self.log("多账号管理", f"[{phone}] ❌ 账号已注销")
                    except PhoneNumberBannedError:
                        acc['status'] = '封禁'
                        self.log("多账号管理", f"[{phone}] ❌ 账号已被封禁")
                    except Exception as e:
                        status, log_msg = self.parse_unauthorized_error(phone, e, "登录")
                        acc['status'] = status
                        self.log("多账号管理", log_msg)
                    self.update_status_filter_options()
                    return False

            except FloodWaitError as e:
                acc['status'] = f'登录限制({e.seconds}秒)'
                self.log("多账号管理", f"[{phone}] ⚠️ 登录过于频繁，等待{e.seconds}秒")
                self.update_status_filter_options()
                return False
            except Exception as e:
                error_msg = str(e)
                error_lower = error_msg.lower()
                if "database" in error_lower:
                    self.log("多账号管理", f"[{phone}] ⚠️ session文件格式问题，尝试重新加载...")
                    try:
                        if session_path and os.path.exists(session_path):
                            with open(session_path, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                            if content:
                                from telethon.sessions import StringSession
                                session = StringSession(content)
                                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                                await client.connect()
                                if await client.is_user_authorized():
                                    me = await client.get_me()
                                    acc['status'] = '正常'
                                    acc['nickname'] = me.first_name or phone
                                    self.log("多账号管理", f"[{phone}] ✅ 重新加载成功 | 昵称: {me.first_name}")
                                    await client.disconnect()
                                    self.update_status_filter_options()
                                    return True
                    except:
                        pass
                    acc['status'] = 'session格式错误'
                    self.log("多账号管理", f"[{phone}] ❌ session文件格式错误")
                elif "deactivated" in error_lower:
                    acc['status'] = '销号'
                    self.log("多账号管理", f"[{phone}] ❌ 账号已注销")
                elif "banned" in error_lower:
                    acc['status'] = '封禁'
                    self.log("多账号管理", f"[{phone}] ❌ 账号已被封禁")
                else:
                    acc['status'] = '登录失败'
                    self.log("多账号管理", f"[{phone}] ❌ 登录失败: {error_msg[:80]}")
                self.update_status_filter_options()
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

        self.root.after(0, self.refresh_account_list_filter)
        self.root.after(0, self.refresh_scrape_accounts)
        self.save_config()
        return result

    def deep_check_filtered_accounts(self):
        filtered_accounts = self.get_filtered_accounts()
        if not filtered_accounts:
            self.log("多账号管理", "当前筛选条件下没有账号可操作")
            self.show_centered_warning("提示", "当前筛选条件下没有账号可操作")
            return

        self.log("多账号管理", f"开始深度检测 {len(filtered_accounts)} 个账号（当前筛选结果）...")
        self.log("多账号管理", "检测项目: 登录状态 | SpamBot官方限制检测 (多语言支持)")

        def do_deep_check():
            for idx, acc in enumerate(filtered_accounts, 1):
                phone = acc.get('phone', '')
                self.log("多账号管理", f"[{idx}/{len(filtered_accounts)}] 正在检测: {phone}")
                self.deep_check_single_account(acc)
                time.sleep(2)
            self.log("多账号管理", "深度检测完成")
            self.save_config()

        threading.Thread(target=do_deep_check, daemon=True).start()

    def deep_check_single_account(self, acc):
        """
        深度检测单个账号 - 多维度综合检测
        
        检测流程：
        第1层：登录状态检测 (get_me)
        第2层：SpamBot官方限制检测 (/start) - 支持多语言
        
        业务能力检测由实际任务执行时实时更新状态
        """
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        twofa = self.get_account_twofa(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

        async def do_check():
            client = None
            try:
                from telethon.sessions import StringSession, MemorySession
                from telethon.tl.functions.messages import GetHistoryRequest
                import re
                from datetime import datetime

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                    except (UnicodeDecodeError, UnicodeError):
                        session = session_path
                    except Exception:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()

                # ==================== 第1层：登录检测 ====================
                if not await client.is_user_authorized():
                    try:
                        await asyncio.wait_for(client.get_me(), timeout=5)
                        me = await client.get_me()
                        if getattr(me, 'deleted', False):
                            acc['status'] = '销号'
                            self.log("多账号管理", f"[{phone}] 检测结果: 销号(账号已注销)")
                        else:
                            acc['status'] = '未授权'
                            self.log("多账号管理", f"[{phone}] 检测结果: 未授权(登录态失效)")
                    except asyncio.TimeoutError:
                        acc['status'] = '未授权(超时)'
                        self.log("多账号管理", f"[{phone}] 检测结果: 未授权(连接超时)")
                    except SessionPasswordNeededError:
                        acc['status'] = '需要2FA重新登录'
                        self.log("多账号管理", f"[{phone}] 检测结果: 需要2FA重新登录")
                    except UserDeactivatedError:
                        acc['status'] = '销号'
                        self.log("多账号管理", f"[{phone}] 检测结果: 销号")
                    except PhoneNumberBannedError:
                        acc['status'] = '封禁'
                        self.log("多账号管理", f"[{phone}] 检测结果: 封禁")
                    except Exception as e:
                        status, log_msg = self.parse_unauthorized_error(phone, e, "深度检测")
                        acc['status'] = status
                        log_msg = log_msg.replace("异常", "结果")
                        self.log("多账号管理", log_msg)
                    self.update_status_filter_options()
                    return

                me = await client.get_me()
                if getattr(me, 'deleted', False):
                    acc['status'] = '销号'
                    self.log("多账号管理", f"[{phone}] 检测结果: 销号(账号已注销)")
                    await client.disconnect()
                    self.update_status_filter_options()
                    return

                nickname = me.first_name or me.username or phone
                acc['nickname'] = nickname

                if hasattr(me, 'date'):
                    reg_time = me.date.strftime("%Y-%m-%d")
                    acc['register_time'] = reg_time
                    days_old = (datetime.now() - me.date.replace(tzinfo=None)).days
                    self.log("多账号管理", f"[{phone}] 注册时间: {reg_time} (已注册{days_old}天)")

                # ==================== 第2层：SpamBot检测 (多语言支持) ====================
                spam_status = "UNKNOWN"
                spam_detail = ""
                restricted_until = None

                try:
                    spambot = await client.get_entity('@SpamBot')
                    if spambot:
                        # 发送 /start 命令
                        await client.send_message(spambot, '/start')
                        await asyncio.sleep(2.5)

                        # 获取最近的回复消息
                        history = await client(GetHistoryRequest(
                            peer=spambot,
                            limit=5,
                            offset_date=None,
                            offset_id=0,
                            max_id=0,
                            min_id=0,
                            add_offset=0,
                            hash=0
                        ))

                        if history and history.messages:
                            for msg in history.messages:
                                if msg.out:
                                    continue
                                if msg.message:
                                    msg_text = msg.message
                                    msg_lower = msg_text.lower()
                                    
                                    # ========== 检测限制关键词 (多语言) ==========
                                    
                                    # 英文限制关键词
                                    english_restricted = [
                                        'limited until',
                                        'restricted',
                                        'temporarily limited',
                                        'your account is limited',
                                        'spam'
                                    ]
                                    
                                    # 印尼语限制关键词
                                    indonesian_restricted = [
                                        'dibatasi',
                                        'terbatas',
                                        'akun anda telah dibatasi',
                                        'telah dibatasi',
                                        'anda tidak akan dapat mengirim',
                                        'tidak dapat mengirim pesan'
                                    ]
                                    
                                    # 中文限制关键词
                                    chinese_restricted = [
                                        '限制',
                                        '受限',
                                        '被限制',
                                        '账号被限制'
                                    ]
                                    
                                    # 俄语限制关键词
                                    russian_restricted = [
                                        'ограничен',
                                        'заблокирован',
                                        'ограничения'
                                    ]
                                    
                                    # 所有限制关键词
                                    all_restricted = (english_restricted + indonesian_restricted + 
                                                      chinese_restricted + russian_restricted)
                                    
                                    # 检查是否包含限制关键词
                                    is_restricted = False
                                    for keyword in all_restricted:
                                        if keyword in msg_lower:
                                            is_restricted = True
                                            break
                                    
                                    if is_restricted:
                                        spam_status = "RESTRICTED"
                                        spam_detail = "账号被Spam限制"
                                        
                                        # 解析限制日期 (多种日期格式)
                                        # 格式1: "limited until 2026-08-20"
                                        date_match = re.search(r'limited until (\d{4}-\d{2}-\d{2})', msg_text, re.IGNORECASE)
                                        if date_match:
                                            restricted_until = date_match.group(1)
                                        else:
                                            # 格式2: "until 20/08/2026"
                                            date_match = re.search(r'until (\d{2}/\d{2}/\d{4})', msg_text, re.IGNORECASE)
                                            if date_match:
                                                try:
                                                    d = datetime.strptime(date_match.group(1), '%d/%m/%Y')
                                                    restricted_until = d.strftime('%Y-%m-%d')
                                                except:
                                                    pass
                                            else:
                                                # 格式3: "until 20-08-2026"
                                                date_match = re.search(r'until (\d{2}-\d{2}-\d{4})', msg_text, re.IGNORECASE)
                                                if date_match:
                                                    try:
                                                        d = datetime.strptime(date_match.group(1), '%d-%m-%Y')
                                                        restricted_until = d.strftime('%Y-%m-%d')
                                                    except:
                                                        pass
                                        break
                                    
                                    # ========== 检测正常状态 (多语言) ==========
                                    
                                    # 英文正常关键词
                                    english_normal = [
                                        'good news',
                                        'no limits',
                                        'no restrictions',
                                        'account is in good standing'
                                    ]
                                    
                                    # 印尼语正常关键词
                                    indonesian_normal = [
                                        'tidak ada batasan',
                                        'baik-baik saja',
                                        'tidak dibatasi'
                                    ]
                                    
                                    # 中文正常关键词
                                    chinese_normal = [
                                        '无限制',
                                        '正常',
                                        '没有被限制'
                                    ]
                                    
                                    all_normal = english_normal + indonesian_normal + chinese_normal
                                    
                                    is_normal = False
                                    for keyword in all_normal:
                                        if keyword in msg_lower:
                                            is_normal = True
                                            break
                                    
                                    if is_normal:
                                        spam_status = "NORMAL"
                                        spam_detail = "账号无Spam限制"
                                        break

                    # 如果状态仍然是 UNKNOWN，尝试更全面的检测
                    if spam_status == "UNKNOWN" and history and history.messages:
                        for msg in history.messages:
                            if msg.out:
                                continue
                            if msg.message:
                                msg_lower = msg.message.lower()
                                # 如果消息包含 "tidak dapat mengirim" (不能发送) 等明确限制词
                                if any(kw in msg_lower for kw in ['tidak dapat mengirim', 'tidak akan dapat mengirim']):
                                    spam_status = "RESTRICTED"
                                    spam_detail = "账号被限制发送消息"
                                    break

                except Exception as e:
                    spam_detail = f"SpamBot检测失败: {str(e)[:30]}"

                # ==================== 综合判定 ====================
                if acc.get('status') in ['销号', '封禁']:
                    pass
                elif spam_status == "RESTRICTED":
                    acc['status'] = 'Spam限制'
                    if restricted_until:
                        self.log("多账号管理", f"[{phone}] ⚠️ SpamBot检测: {spam_detail} 限制至: {restricted_until}")
                    else:
                        self.log("多账号管理", f"[{phone}] ⚠️ SpamBot检测: {spam_detail}")
                else:
                    acc['status'] = '正常'
                    self.log("多账号管理", f"[{phone}] ✅ 检测通过 | Spam: {spam_detail}")
                
                self.update_status_filter_options()
                await client.disconnect()

            except UserDeactivatedError:
                acc['status'] = '销号'
                self.log("多账号管理", f"[{phone}] 检测结果: 销号")
                self.update_status_filter_options()
            except PhoneNumberBannedError:
                acc['status'] = '封禁'
                self.log("多账号管理", f"[{phone}] 检测结果: 封禁")
                self.update_status_filter_options()
            except SessionPasswordNeededError:
                acc['status'] = '需要2FA'
                self.log("多账号管理", f"[{phone}] 检测结果: 需要2FA")
                self.update_status_filter_options()
            except Exception as e:
                error_msg = str(e).lower()
                if "database" in error_msg:
                    acc['status'] = 'session格式错误'
                    self.log("多账号管理", f"[{phone}] 检测结果: session文件格式错误")
                elif "deactivated" in error_msg:
                    acc['status'] = '销号'
                    self.log("多账号管理", f"[{phone}] 检测结果: 销号")
                elif "banned" in error_msg:
                    acc['status'] = '封禁'
                    self.log("多账号管理", f"[{phone}] 检测结果: 封禁")
                elif "password" in error_msg:
                    acc['status'] = '需要2FA'
                    self.log("多账号管理", f"[{phone}] 检测结果: 需要2FA")
                elif "flood" in error_msg or "too many" in error_msg:
                    acc['status'] = '频率限制'
                    self.log("多账号管理", f"[{phone}] 检测结果: 频率限制")
                else:
                    acc['status'] = '检测失败'
                    self.log("多账号管理", f"[{phone}] 检测结果: 检测失败 - {str(e)[:50]}")
                self.update_status_filter_options()
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(do_check())
        loop.close()

        self.root.after(0, self.refresh_account_list_filter)
        self.root.after(0, self.refresh_scrape_accounts)
        self.update_status_filter_options()

    def kick_devices_filtered(self):
        filtered_accounts = self.get_filtered_accounts()
        if not filtered_accounts:
            self.log("多账号管理", "当前筛选条件下没有账号可操作")
            self.show_centered_warning("提示", "当前筛选条件下没有账号可操作")
            return

        def do_kick():
            self.log("多账号管理", f"开始踢出 {len(filtered_accounts)} 个账号的其他设备...")

            def kick_thread():
                for idx, acc in enumerate(filtered_accounts, 1):
                    phone = acc.get('phone', '')
                    self.log("多账号管理", f"[{idx}/{len(filtered_accounts)}] 正在踢出设备: {phone}")
                    self.kick_single_account_devices(acc)
                    time.sleep(2)
                self.log("多账号管理", "踢出设备完成")
                self.show_centered_info("完成", f"已完成 {len(filtered_accounts)} 个账号的设备踢出")

            threading.Thread(target=kick_thread, daemon=True).start()

        self.show_centered_yesno("确认", f"确定将当前筛选的 {len(filtered_accounts)} 个账号踢出所有其他设备吗？\n（当前设备将保留登录状态）", do_kick)

    def kick_single_account_devices(self, acc):
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

        async def do_kick():
            client = None
            try:
                from telethon.sessions import StringSession

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                    except:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()

                if not await client.is_user_authorized():
                    self.log("多账号管理", f"[{phone}] 账号未登录，无需踢出")
                    return

                auths = await client(GetAuthorizationsRequest())

                kicked_count = 0
                for auth in auths.authorizations:
                    if auth.current:
                        device_name = auth.device_model or "当前设备"
                        self.log("多账号管理", f"[{phone}] 保留当前设备: {device_name}")
                        continue
                    try:
                        await client(ResetAuthorizationRequest(hash=auth.hash))
                        kicked_count += 1
                        device_name = auth.device_model or "未知设备"
                        self.log("多账号管理", f"[{phone}] 已踢出设备: {device_name}")
                    except Exception as e:
                        self.log("多账号管理", f"[{phone}] 踢出设备失败: {str(e)[:50]}")

                self.log("多账号管理", f"[{phone}] 踢出完成，共踢出 {kicked_count} 个设备，当前设备已保留")

                if acc.get('status') != '正常':
                    try:
                        me = await client.get_me()
                        if me:
                            acc['status'] = '正常'
                            self.log("多账号管理", f"[{phone}] 账号状态已刷新: 正常")
                    except:
                        pass

                self.update_status_filter_options()
                self.refresh_account_list_filter()

            except Exception as e:
                self.log("多账号管理", f"[{phone}] 踢出设备异常: {str(e)[:50]}")
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except:
                        pass

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(do_kick())
        loop.close()

    def batch_edit_profile(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("批量修改资料")
        dialog.geometry("700x800")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 700, 800)

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

        twofa_frame = ttk.LabelFrame(dialog, text="两步验证密码(2FA)")
        twofa_frame.pack(fill="x", padx=10, pady=5)

        twofa_row = ttk.Frame(twofa_frame)
        twofa_row.pack(fill="x", padx=5, pady=5)

        ttk.Label(twofa_row, text="原密码:").pack(side="left", padx=5)
        self.twofa_old_password = ttk.Entry(twofa_row, width=20, show="●")
        self.twofa_old_password.pack(side="left", padx=5)

        ttk.Label(twofa_row, text="新密码:").pack(side="left", padx=20)
        self.twofa_new_password = ttk.Entry(twofa_row, width=20, show="●")
        self.twofa_new_password.pack(side="left", padx=5)

        ttk.Label(twofa_row, text="确认新密码:").pack(side="left", padx=20)
        self.twofa_confirm_password = ttk.Entry(twofa_row, width=20, show="●")
        self.twofa_confirm_password.pack(side="left", padx=5)

        ttk.Label(twofa_frame, text="如果不修改2FA密码，请留空", font=("微软雅黑", 8), foreground="gray").pack(anchor="w", padx=5, pady=2)

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

            old_twofa = self.twofa_old_password.get().strip()
            new_twofa = self.twofa_new_password.get().strip()
            confirm_twofa = self.twofa_confirm_password.get().strip()

            if new_twofa and new_twofa != confirm_twofa:
                self.log("多账号管理", "新密码和确认密码不一致")
                self.show_centered_warning("提示", "新密码和确认密码不一致")
                return

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
                            self.edit_single_account_profile(acc, photo_path, username, firstname, bio, old_twofa, new_twofa)
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

    def edit_single_account_profile(self, acc, photo_path, username, first_name, bio, old_twofa=None, new_twofa=None):
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

        async def do_edit():
            client = None
            try:
                from telethon.sessions import StringSession

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                    except:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()
                if not await client.is_user_authorized():
                    self.log("多账号管理", f"[{phone}] 账号未登录")
                    return

                if old_twofa and new_twofa and old_twofa.strip() and new_twofa.strip():
                    try:
                        pwd = await client(GetPasswordRequest())
                        if pwd.has_password:
                            await client.edit_2fa(new_password=new_twofa, current_password=old_twofa)
                            self.log("多账号管理", f"[{phone}] 2FA密码修改成功")
                        else:
                            await client.edit_2fa(new_password=new_twofa)
                            self.log("多账号管理", f"[{phone}] 2FA密码设置成功")

                        json_path = acc.get('json_path', '')
                        if json_path and os.path.exists(json_path):
                            with open(json_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            json_data['twoFA'] = new_twofa
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
                            if acc.get('account_info'):
                                acc['account_info']['twoFA'] = new_twofa
                    except Exception as e:
                        self.log("多账号管理", f"[{phone}] 2FA密码修改失败: {str(e)}")

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
                self.root.after(0, self.refresh_account_list_filter)
                self.update_status_filter_options()
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
            self.refresh_account_list_filter()
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
                self.refresh_account_list_filter()
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
                self.refresh_account_list_filter()
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

        self.refresh_account_list_filter()
        self.refresh_scrape_accounts()
        self.refresh_invite_group_filter()
        self.save_config()
        statuses = set(["全部"])
        for acc in self.accounts:
            status = acc.get('status', '待检测')
            statuses.add(status)
        self.account_list_status_filter['values'] = list(statuses)
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

        filtered_accounts = self.get_filtered_accounts()

        export_count = 0
        exported_phones = set()
        for item in selected:
            idx = int(self.account_tree.item(item)['values'][0]) - 1
            if idx < len(filtered_accounts):
                acc = filtered_accounts[idx]
                phone = acc.get('phone', '')
                if phone in exported_phones:
                    continue
                exported_phones.add(phone)

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

    def refresh_account_list(self):
        self.refresh_account_list_filter()

    def delete_selected_accounts(self):
        selected = self.account_tree.selection()
        if selected:
            filtered_accounts = self.get_filtered_accounts()

            phones_to_delete = []
            for item in selected:
                idx = int(self.account_tree.item(item)['values'][0]) - 1
                if idx < len(filtered_accounts):
                    phones_to_delete.append(filtered_accounts[idx].get('phone'))

            if not phones_to_delete:
                return

            def do_delete():
                for phone in phones_to_delete:
                    for i, acc in enumerate(self.accounts):
                        if acc.get('phone') == phone:
                            self.accounts.pop(i)
                            break
                self.refresh_account_list_filter()
                self.refresh_scrape_accounts()
                self.refresh_invite_group_filter()
                self.save_config()
                statuses = set(["全部"])
                for acc in self.accounts:
                    status = acc.get('status', '待检测')
                    statuses.add(status)
                self.account_list_status_filter['values'] = list(statuses)
                self.log("多账号管理", f"删除 {len(selected)} 个选中账号")

            self.show_centered_yesno("确认", f"确定删除 {len(selected)} 个账号？", do_delete)

    def delete_dead_accounts_filtered(self):
        filtered_accounts = self.get_filtered_accounts()
        if not filtered_accounts:
            self.log("多账号管理", "当前筛选条件下没有账号可操作")
            self.show_centered_warning("提示", "当前筛选条件下没有账号可操作")
            return

        dead_states = ['销号', '封禁']
        dead_accounts = []
        for acc in filtered_accounts:
            if acc.get('status') in dead_states:
                dead_accounts.append(acc)

        if dead_accounts:
            def do_delete():
                for acc in dead_accounts:
                    for i, a in enumerate(self.accounts):
                        if a.get('phone') == acc.get('phone'):
                            self.accounts.pop(i)
                            break
                self.refresh_account_list_filter()
                self.refresh_scrape_accounts()
                self.refresh_invite_group_filter()
                self.save_config()
                statuses = set(["全部"])
                for acc in self.accounts:
                    status = acc.get('status', '待检测')
                    statuses.add(status)
                self.account_list_status_filter['values'] = list(statuses)
                self.log("多账号管理", f"删除 {len(dead_accounts)} 个已失效账号（当前筛选结果）")
            self.show_centered_yesno("确认", f"确定删除当前筛选结果中的 {len(dead_accounts)} 个已失效账号？", do_delete)
        else:
            self.log("多账号管理", "当前筛选结果中没有发现已失效的账号")
            self.show_centered_info("提示", "当前筛选结果中没有发现已失效的账号")

    def create_proxy_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="代理IP")

        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)

        self.proxy_count_label = ttk.Label(toolbar, text=f"代理数量: {len(self.proxies)}", font=("微软雅黑", 10))
        self.proxy_count_label.pack(side="left", padx=10)

        ttk.Button(toolbar, text="分组管理", command=self.open_proxy_group_manager).pack(side="left", padx=2)
        ttk.Button(toolbar, text="导入代理", command=self.import_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="删除选中代理", command=self.delete_proxy).pack(side="left", padx=2)
        ttk.Button(toolbar, text="检测选中代理", command=self.check_selected_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="检测筛选代理", command=self.check_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="清空所有代理", command=self.clear_all_proxies).pack(side="left", padx=2)
        ttk.Button(toolbar, text="分配代理IP", command=self.assign_proxies_to_accounts).pack(side="left", padx=2)
        ttk.Button(toolbar, text="重置筛选", command=self.reset_proxy_filters).pack(side="left", padx=2)

        filter_bar = ttk.Frame(main_frame)
        filter_bar.pack(fill="x", pady=5)

        ttk.Label(filter_bar, text="分组筛选:").pack(side="left", padx=5)
        self.proxy_list_group_filter = ttk.Combobox(filter_bar, values=["全部"] + self.proxy_groups, width=15)
        self.proxy_list_group_filter.set("全部")
        self.proxy_list_group_filter.pack(side="left", padx=5)
        self.proxy_list_group_filter.bind("<<ComboboxSelected>>", self.refresh_proxy_list)

        ttk.Label(filter_bar, text="状态筛选:").pack(side="left", padx=20)
        self.proxy_list_status_filter = ttk.Combobox(filter_bar, values=["全部", "未检测", "可用", "不可用", "检测失败", "代理连接失败", "连接被拒绝", "连接超时", "不可用(代理错误)", "不可用(超时)", "不可用(连接错误)"], width=15)
        self.proxy_list_status_filter.set("全部")
        self.proxy_list_status_filter.pack(side="left", padx=5)
        self.proxy_list_status_filter.bind("<<ComboboxSelected>>", self.refresh_proxy_list)

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
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["代理IP"] = scrolledtext.ScrolledText(log_frame, width=100, height=4)
        self.log_widgets["代理IP"].pack(fill="both", expand=True, padx=5, pady=5)

    def reset_proxy_filters(self):
        if hasattr(self, 'proxy_list_group_filter'):
            self.proxy_list_group_filter.set("全部")
        if hasattr(self, 'proxy_list_status_filter'):
            self.proxy_list_status_filter.set("全部")
        self.refresh_proxy_list()
        self.log("代理IP", "已重置筛选条件")

    def open_proxy_group_manager(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("代理分组管理")
        dialog.geometry("550x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 550, 500)

        group_frame = ttk.LabelFrame(dialog, text="分组列表")
        group_frame.pack(fill="both", expand=True, padx=10, pady=10)

        group_listbox = tk.Listbox(group_frame, height=8)
        group_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        for g in self.proxy_groups:
            group_listbox.insert(tk.END, g)

        btn_frame = ttk.Frame(group_frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Label(btn_frame, text="分组名称:").pack(side="left", padx=5)
        group_name_entry = ttk.Entry(btn_frame, width=15)
        group_name_entry.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="新建", command=lambda: self.add_proxy_group_from_manager(group_name_entry, group_listbox)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="重命名", command=lambda: self.rename_proxy_group(group_name_entry, group_listbox)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="删除", command=lambda: self.delete_proxy_group_from_manager(group_listbox)).pack(side="left", padx=2)

        move_frame = ttk.LabelFrame(dialog, text="移动代理到分组")
        move_frame.pack(fill="x", padx=10, pady=10)

        proxy_frame = ttk.Frame(move_frame)
        proxy_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(proxy_frame, text="选择代理:").pack(side="left", padx=5)
        proxy_var = tk.StringVar()
        proxy_combo = ttk.Combobox(proxy_frame, textvariable=proxy_var, width=50)
        proxy_combo.pack(side="left", padx=5, fill="x", expand=True)

        def refresh_proxy_combo():
            proxy_list = [f"{i+1}. {p.get('host')}:{p.get('port')} [{p.get('group', '默认分组')}]" for i, p in enumerate(self.proxies)]
            proxy_combo['values'] = proxy_list
            if proxy_list:
                proxy_combo.set(proxy_list[0])
        refresh_proxy_combo()

        target_frame = ttk.Frame(move_frame)
        target_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(target_frame, text="目标分组:").pack(side="left", padx=5)
        target_group_var = tk.StringVar()
        target_group_combo = ttk.Combobox(target_frame, textvariable=target_group_var, values=self.proxy_groups, width=20)
        target_group_combo.pack(side="left", padx=5)
        if self.proxy_groups:
            target_group_combo.set(self.proxy_groups[0])

        button_line = ttk.Frame(move_frame)
        button_line.pack(pady=10)

        def move_proxy_to_group():
            if not self.proxies:
                self.show_centered_warning("提示", "没有代理可移动")
                return
            selected_proxy = proxy_var.get()
            target_group = target_group_var.get()
            if not selected_proxy or not target_group:
                self.show_centered_warning("提示", "请选择代理和目标分组")
                return
            idx = int(selected_proxy.split('.')[0]) - 1
            self.proxies[idx]['group'] = target_group
            self.refresh_proxy_list()
            refresh_proxy_combo()
            self.save_config()
            self.log("代理IP", f"移动代理 {self.proxies[idx].get('host')}:{self.proxies[idx].get('port')} 到分组「{target_group}」")

        def refresh_all_proxy_groups():
            refresh_proxy_combo()
            target_group_combo['values'] = self.proxy_groups
            if self.proxy_groups:
                target_group_combo.set(self.proxy_groups[0])
            group_listbox.delete(0, tk.END)
            for g in self.proxy_groups:
                group_listbox.insert(tk.END, g)

        ttk.Button(button_line, text="移动代理", command=move_proxy_to_group, width=12).pack(side="left", padx=5)
        ttk.Button(button_line, text="刷新列表", command=refresh_all_proxy_groups, width=12).pack(side="left", padx=5)

    def add_proxy_group_from_manager(self, name_entry, listbox):
        name = name_entry.get().strip()
        if name and name not in self.proxy_groups:
            self.proxy_groups.append(name)
            listbox.insert(tk.END, name)
            name_entry.delete(0, tk.END)
            self.refresh_proxy_list()
            if hasattr(self, 'proxy_list_group_filter'):
                self.proxy_list_group_filter['values'] = ["全部"] + self.proxy_groups
            self.save_config()
            self.log("代理IP", f"创建代理分组: {name}")
        elif name in self.proxy_groups:
            self.show_centered_error("错误", "分组已存在")

    def rename_proxy_group(self, name_entry, listbox):
        selected = listbox.curselection()
        if selected:
            old_name = listbox.get(selected[0])
            if old_name == "默认分组":
                self.show_centered_warning("提示", "默认分组不能重命名")
                return
            new_name = name_entry.get().strip()
            if new_name and new_name not in self.proxy_groups:
                for p in self.proxies:
                    if p.get('group') == old_name:
                        p['group'] = new_name
                idx = self.proxy_groups.index(old_name)
                self.proxy_groups[idx] = new_name
                listbox.delete(selected[0])
                listbox.insert(selected[0], new_name)
                self.refresh_proxy_list()
                if hasattr(self, 'proxy_list_group_filter'):
                    self.proxy_list_group_filter['values'] = ["全部"] + self.proxy_groups
                self.save_config()
                self.log("代理IP", f"重命名代理分组: {old_name} -> {new_name}")
                name_entry.delete(0, tk.END)

    def delete_proxy_group_from_manager(self, listbox):
        selected = listbox.curselection()
        if selected:
            group_name = listbox.get(selected[0])
            if group_name == "默认分组":
                self.show_centered_warning("提示", "默认分组不能删除")
                return
            def do_delete():
                for p in self.proxies:
                    if p.get('group') == group_name:
                        p['group'] = '默认分组'
                self.proxy_groups.remove(group_name)
                listbox.delete(selected[0])
                self.refresh_proxy_list()
                if hasattr(self, 'proxy_list_group_filter'):
                    self.proxy_list_group_filter['values'] = ["全部"] + self.proxy_groups
                self.save_config()
                self.log("代理IP", f"删除代理分组: {group_name}")
            self.show_centered_yesno("确认", f"确定删除代理分组「{group_name}」？代理将移至默认分组", do_delete)

    def add_proxy_group(self):
        group_name = simpledialog.askstring("新建分组", "请输入分组名称:", parent=self.root)
        if group_name and group_name not in self.proxy_groups:
            self.proxy_groups.append(group_name)
            if hasattr(self, 'proxy_list_group_filter'):
                self.proxy_list_group_filter['values'] = ["全部"] + self.proxy_groups
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
                if filter_group == "全部" or acc.get('group') == filter_group:
                    status = acc.get('status', '未知')
                    account_listbox.insert(tk.END, f"{acc.get('phone')} - {acc.get('nickname')} [{acc.get('group')}] 状态:{status}")

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
                    proxy_str = f"{p['type']}://"
                    if p.get('user') and p.get('password'):
                        proxy_str += f"{p['user']}:{p['password']}@"
                    proxy_str += f"{p['host']}:{p['port']}"
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
                    proxy_str = f"{p['type']}://"
                    if p.get('user') and p.get('password'):
                        proxy_str += f"{p['user']}:{p['password']}@"
                    proxy_str += f"{p['host']}:{p['port']}"
                    for acc in self.accounts:
                        if acc.get('phone') == phone:
                            acc['proxy'] = proxy_str
                            break
                    self.log("代理IP", f"账号 {phone} 分配代理: {proxy_str}")

            self.refresh_account_list_filter()
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

            proxy_line = line
            original_type = p_type
            
            if proxy_line.startswith('http://'):
                original_type = 'http'
                proxy_line = proxy_line[7:]
            elif proxy_line.startswith('https://'):
                original_type = 'https'
                proxy_line = proxy_line[8:]
            elif proxy_line.startswith('socks5://'):
                original_type = 'socks5'
                proxy_line = proxy_line[9:]
            elif proxy_line.startswith('socks4://'):
                original_type = 'socks4'
                proxy_line = proxy_line[9:]

            match = re.match(r'^([^:]+):([^@]+)@([^:]+):(\d+)$', proxy_line)
            if match:
                user = match.group(1)
                password = match.group(2)
                host = match.group(3)
                port = match.group(4)
                self.proxies.append({
                    "type": original_type,
                    "host": host,
                    "port": port,
                    "user": user,
                    "password": password,
                    "address": f"{host}:{port}",
                    "status": "未检测",
                    "group": target_group
                })
                added_count += 1
                self.log("代理IP", f"导入代理: {original_type}://{host}:{port} (认证用户: {user}) 到分组「{target_group}」")
                continue

            parts = line.split(':')
            if len(parts) >= 2:
                host = parts[0]
                port = parts[1]
                if port.isdigit():
                    self.proxies.append({
                        "type": original_type,
                        "host": host,
                        "port": port,
                        "user": "",
                        "password": "",
                        "address": f"{host}:{port}",
                        "status": "未检测",
                        "group": target_group
                    })
                    added_count += 1
                    self.log("代理IP", f"导入代理: {original_type}://{host}:{port} (无认证) 到分组「{target_group}」")

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

    def check_selected_proxies(self):
        selected = self.proxy_tree.selection()
        if not selected:
            self.log("代理IP", "请先选择要检测的代理")
            self.show_centered_warning("提示", "请先选择要检测的代理")
            return

        indices = []
        for item in selected:
            try:
                idx = int(self.proxy_tree.item(item)['values'][1]) - 1
                if idx < len(self.proxies):
                    indices.append(idx)
            except:
                pass
        
        if not indices:
            self.log("代理IP", "未找到有效的代理")
            return
        
        self.log("代理IP", f"开始检测选中的 {len(indices)} 个代理...")

        def do_check_selected():
            for idx in indices:
                if idx >= len(self.proxies):
                    continue
                p = self.proxies[idx]
                self._check_single_proxy(p)
                self.root.after(0, self.refresh_proxy_list)
            self.log("代理IP", "选中代理检测完成")

        threading.Thread(target=do_check_selected, daemon=True).start()

    def check_proxies(self):
        filter_group = self.proxy_list_group_filter.get() if hasattr(self, 'proxy_list_group_filter') else "全部"
        filter_status = self.proxy_list_status_filter.get() if hasattr(self, 'proxy_list_status_filter') else "全部"
        
        filtered_proxies = []
        for p in self.proxies:
            p_group = p.get('group', '默认分组')
            if filter_group != "全部" and p_group != filter_group:
                continue
            if filter_status != "全部" and p.get('status', '未检测') != filter_status:
                continue
            filtered_proxies.append(p)
        
        if not filtered_proxies:
            self.log("代理IP", "当前筛选条件下没有代理需要检测")
            self.show_centered_warning("提示", "当前筛选条件下没有代理需要检测")
            return
        
        self.log("代理IP", f"开始检测 {len(filtered_proxies)} 个代理（当前筛选结果）...")

        def do_check():
            for p in filtered_proxies:
                self._check_single_proxy(p)
                self.root.after(0, self.refresh_proxy_list)
            self.log("代理IP", "代理检测完成")

        threading.Thread(target=do_check, daemon=True).start()

    def _check_single_proxy(self, p):
        proxy_str = f"{p.get('host')}:{p.get('port')}"
        proxy_type = p.get('type', 'http')
        
        try:
            if proxy_type in ['http', 'https']:
                proxy_url = f"{proxy_type}://"
                if p.get('user') and p.get('password'):
                    proxy_url += f"{p.get('user')}:{p.get('password')}@"
                proxy_url += f"{p.get('host')}:{p.get('port')}"
                
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                
                start_time = time.time()
                resp = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
                elapsed = time.time() - start_time
                if resp.status_code == 200:
                    p['status'] = f"可用 ({elapsed:.1f}s) - IP: {resp.text}"
                    self.log("代理IP", f"{proxy_type}://{proxy_str}: 可用")
                else:
                    p['status'] = "不可用"
                    self.log("代理IP", f"{proxy_type}://{proxy_str}: 不可用 (状态码: {resp.status_code})")
            else:
                try:
                    import socks
                    import socket
                    
                    sock = socks.socksocket()
                    sock.set_proxy(socks.SOCKS5 if proxy_type == 'socks5' else socks.SOCKS4, 
                                  p.get('host'), int(p.get('port')), 
                                  username=p.get('user'), password=p.get('password'))
                    sock.settimeout(10)
                    sock.connect(('api.ipify.org', 80))
                    sock.send(b'GET / HTTP/1.1\r\nHost: api.ipify.org\r\n\r\n')
                    data = sock.recv(1024)
                    sock.close()
                    if data:
                        p['status'] = f"可用"
                        self.log("代理IP", f"{proxy_type}://{proxy_str}: 可用")
                    else:
                        p['status'] = "不可用"
                        self.log("代理IP", f"{proxy_type}://{proxy_str}: 不可用")
                except ImportError:
                    p['status'] = "需要安装socks库"
                    self.log("代理IP", f"{proxy_type}://{proxy_str}: 需要安装socks库 (pip install PySocks)")
                except Exception as e:
                    p['status'] = "不可用"
                    self.log("代理IP", f"{proxy_type}://{proxy_str}: 不可用 - {str(e)[:30]}")
                
        except requests.exceptions.ProxyError as e:
            p['status'] = "不可用(代理错误)"
            self.log("代理IP", f"{proxy_type}://{proxy_str}: 代理连接失败")
        except requests.exceptions.ConnectTimeout:
            p['status'] = "不可用(超时)"
            self.log("代理IP", f"{proxy_type}://{proxy_str}: 连接超时")
        except requests.exceptions.ConnectionError:
            p['status'] = "不可用(连接错误)"
            self.log("代理IP", f"{proxy_type}://{proxy_str}: 连接被拒绝")
        except Exception as e:
            p['status'] = f"不可用"
            self.log("代理IP", f"{proxy_type}://{proxy_str}: 检测失败 - {str(e)[:30]}")

    def refresh_proxy_list(self, event=None):
        for item in self.proxy_tree.get_children():
            self.proxy_tree.delete(item)
        
        filter_group = self.proxy_list_group_filter.get() if hasattr(self, 'proxy_list_group_filter') else "全部"
        filter_status = self.proxy_list_status_filter.get() if hasattr(self, 'proxy_list_status_filter') else "全部"
        
        i = 1
        for p in self.proxies:
            p_group = p.get('group', '默认分组')
            if filter_group != "全部" and p_group != filter_group:
                continue
            if filter_status != "全部" and p.get('status', '未检测') != filter_status:
                continue
            
            display_addr = p.get('address', f"{p.get('host')}:{p.get('port')}")
            self.proxy_tree.insert("", "end", values=(p_group, i, p.get('type', 'socks5'), display_addr, p.get('status', '未检测')))
            i += 1
        
        self.proxy_count_label.config(text=f"代理数量: {len(self.proxies)}")

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

        right_frame = ttk.LabelFrame(main_frame, text="采集预览")
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

        log_frame = ttk.LabelFrame(right_frame, text="运行日志")
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_widgets["采集群成员"] = scrolledtext.ScrolledText(log_frame, width=100, height=3)
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
        
        import re
        clean_group_name = re.sub(r'[<>:"/\\|?*]', '_', group_username)
        clean_group_name = clean_group_name.replace(' ', '_')
        if len(clean_group_name) > 50:
            clean_group_name = clean_group_name[:50]
        
        base_name = f"members_{clean_group_name}_{current_date}_{current_time}_{action}"

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

    def parse_group_link(self, link):
        topic_id = None
        group_username = None
        is_invite_link = False
        invite_hash = None
        
        if 't.me/' in link:
            clean_link = link.replace('https://', '').replace('http://', '')
            path = clean_link.split('t.me/')[-1].strip('/')
            
            if path.startswith('joinchat'):
                is_invite_link = True
                parts = path.split('/')
                if len(parts) >= 2:
                    invite_hash = parts[1]
                else:
                    invite_hash = path
                group_username = invite_hash
            elif path.startswith('+'):
                is_invite_link = True
                invite_hash = path[1:]
                group_username = invite_hash
            else:
                parts = path.split('/')
                group_username = parts[0]
                if group_username.startswith('+'):
                    is_invite_link = True
                    invite_hash = group_username[1:]
                    group_username = invite_hash
                if len(parts) >= 2 and parts[1].isdigit():
                    topic_id = int(parts[1])
        elif 'https://' in link:
            path = link.split('/')[-1]
            if path.startswith('+') or path.startswith('joinchat'):
                is_invite_link = True
                invite_hash = path[1:] if path.startswith('+') else path.split('/')[-1] if '/' in path else path
                group_username = invite_hash
            else:
                group_username = path
        else:
            group_username = link
            if group_username.startswith('+'):
                is_invite_link = True
                invite_hash = group_username[1:]
                group_username = invite_hash
        
        return group_username, topic_id, is_invite_link, invite_hash

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
            self.show_centered_warning("提示", "请选择采集账号")
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
        group_username, topic_id, is_invite_link, invite_hash = self.parse_group_link(group)

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

        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

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
                from telethon.sessions import StringSession

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                    except:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()
                if not await client.is_user_authorized():
                    self.log("采集群成员", "账号未登录")
                    return

                try:
                    entity = None
                    
                    if is_invite_link and invite_hash:
                        self.log("采集群成员", f"使用邀请链接查找群组，哈希: {invite_hash}")
                        
                        try:
                            result = await client(ImportChatInviteRequest(invite_hash))
                            if result.chats:
                                entity = result.chats[0]
                                self.log("采集群成员", f"✅ 成功加入隐私群: {getattr(entity, 'title', '未知')}")
                        except UserAlreadyParticipantError:
                            self.log("采集群成员", "已经是群组成员，正在遍历对话框查找...")
                            async for dialog in client.iter_dialogs():
                                if dialog.is_group or dialog.is_channel:
                                    try:
                                        full_entity = dialog.entity
                                        dialog_id = str(dialog.id)
                                        str_dialog_id = dialog_id.replace('-100', '')
                                        if invite_hash in str_dialog_id or str_dialog_id.endswith(invite_hash):
                                            entity = full_entity
                                            self.log("采集群成员", f"✅ 通过ID匹配找到群组: {dialog.name} (ID: {dialog.id})")
                                            break
                                        if hasattr(full_entity, 'title') and full_entity.title and invite_hash in full_entity.title:
                                            entity = full_entity
                                            self.log("采集群成员", f"✅ 通过标题匹配找到群组: {dialog.name}")
                                            break
                                    except:
                                        continue
                        except Exception as e:
                            error_msg = str(e)
                            if "You tried to use a method that" in error_msg or "deactivated" in error_msg.lower():
                                self.log("采集群成员", f"账号已注销")
                                return
                            self.log("采集群成员", f"加入群组失败: {error_msg[:50]}")
                            return
                        
                        if not entity:
                            self.log("采集群成员", "❌ 无法获取群组实体")
                            return
                    else:
                        if group_username:
                            if group_username.lstrip('-').isdigit():
                                try:
                                    entity = await client.get_entity(int(group_username))
                                    self.log("采集群成员", f"✅ 通过ID获取群组: {group_username}")
                                except Exception as e1:
                                    self.log("采集群成员", f"直接获取失败: {str(e1)[:30]}")
                                    try:
                                        clean_id = group_username.replace('-100', '')
                                        if clean_id.isdigit():
                                            entity = await client.get_entity(int(clean_id))
                                            self.log("采集群成员", f"✅ 通过清理后的ID获取群组: {clean_id}")
                                    except Exception as e2:
                                        self.log("采集群成员", f"清理ID获取失败: {str(e2)[:30]}")
                                        self.log("采集群成员", "尝试通过遍历对话框查找群组...")
                                        async for dialog in client.iter_dialogs():
                                            if dialog.is_group or dialog.is_channel:
                                                dialog_id = str(dialog.id)
                                                clean_group_id = group_username.replace('-100', '')
                                                if group_username in dialog_id or dialog_id.endswith(clean_group_id):
                                                    entity = dialog.entity
                                                    self.log("采集群成员", f"✅ 通过对话框找到群组: {dialog.name} (ID: {dialog.id})")
                                                    break
                            else:
                                try:
                                    entity = await client.get_entity(group_username)
                                    self.log("采集群成员", f"✅ 通过用户名获取群组: {group_username}")
                                except:
                                    pass
                            
                            if not entity and group_username and len(group_username) > 2:
                                self.log("采集群成员", f"尝试通过群组名称查找: {group_username}")
                                async for dialog in client.iter_dialogs():
                                    if dialog.is_group or dialog.is_channel:
                                        if dialog.name and group_username in dialog.name:
                                            entity = dialog.entity
                                            self.log("采集群成员", f"✅ 通过名称找到群组: {dialog.name} (ID: {dialog.id})")
                                            break
                            
                            if not entity:
                                self.log("采集群成员", f"❌ 无法获取群组实体")
                                return
                                
                except Exception as e:
                    self.log("采集群成员", f"获取群组失败: {str(e)}")
                    return

                if self.filter_admin.get():
                    try:
                        if scrape_mode == "多讨论组采集(多个子群)":
                            sub_groups_text = self.sub_groups_text.get("1.0", tk.END).strip()
                            sub_group_links = [link.strip() for link in sub_groups_text.split('\n') if link.strip()]
                            for link in sub_group_links:
                                try:
                                    sub_username, sub_topic, sub_is_invite, sub_hash = self.parse_group_link(link)
                                    if sub_username:
                                        sub_entity = await client.get_entity(sub_username)
                                        async for user in client.iter_participants(sub_entity, filter=ChannelParticipantsAdmins):
                                            admin_ids.add(user.id)
                                except:
                                    pass
                        else:
                            async for user in client.iter_participants(entity, filter=ChannelParticipantsAdmins):
                                admin_ids.add(user.id)
                        self.log("采集群成员", f"获取到 {len(admin_ids)} 个管理员")
                    except Exception as e:
                        self.log("采集群成员", f"获取管理员列表失败: {str(e)}")

                if scrape_mode == "获取全部成员(公开群)":
                    self.log("采集群成员", "开始采集成员（获取全部成员）...")
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
                            sub_username, sub_topic, sub_is_invite, sub_hash = self.parse_group_link(link)
                            if not sub_username:
                                self.log("采集群成员", f"无效的子群链接: {link}")
                                continue
                            sub_entity = await client.get_entity(sub_username)
                            offset_id = 0
                            batch_size = 3000
                            input_peer = InputPeerChannel(sub_entity.id, sub_entity.access_hash)
                            sub_pending = []
                            sub_count = 0
                            while self.is_scraping:
                                while self.is_paused:
                                    await asyncio.sleep(0.5)
                                if not self.is_scraping:
                                    break
                                try:
                                    if sub_topic:
                                        messages = await client.get_messages(sub_entity, limit=batch_size, offset_id=offset_id, reply_to=sub_topic)
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
                    if group_username:
                        clean_group_name = re.sub(r'[<>:"/\\|?*]', '_', group_username)
                        clean_group_name = clean_group_name.replace(' ', '_')
                        if len(clean_group_name) > 50:
                            clean_group_name = clean_group_name[:50]
                        self.save_scraped_members(clean_group_name, is_stop)
                    else:
                        self.save_scraped_members("unknown", is_stop)
                    self.root.after(0, lambda: self.show_centered_info("采集完成" if not is_stop else "采集已停止", f"共采集 {len(self.scraped_members)} 个有用户名的成员\n保存目录: {self.save_path.get()}"))
                else:
                    self.log("采集群成员", "没有采集到任何成员")
                await client.disconnect()
            except Exception as e:
                self.log("采集群成员", f"采集失败: {str(e)}")
                if self.scraped_members:
                    if group_username:
                        clean_group_name = re.sub(r'[<>:"/\\|?*]', '_', group_username)
                        clean_group_name = clean_group_name.replace(' ', '_')
                        if len(clean_group_name) > 50:
                            clean_group_name = clean_group_name[:50]
                        self.save_scraped_members(clean_group_name, True)
                    else:
                        self.save_scraped_members("unknown", True)
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

    def create_invite_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="批量拉人")

        main_container = ttk.Frame(page)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill="both", expand=True, pady=(0, 5))

        settings_canvas = tk.Canvas(top_frame, highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=settings_canvas.yview)
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

        account_select_frame = ttk.Frame(self.settings_panel)
        account_select_frame.grid(row=current_row, column=0, sticky="ew", pady=5)
        ttk.Button(account_select_frame, text="选择账号", command=self.select_invite_accounts, width=12).pack(side="left", padx=5)
        self.selected_invite_accounts_label = ttk.Label(account_select_frame, text="已选: 0 个账号", foreground="blue")
        self.selected_invite_accounts_label.pack(side="left", padx=10)
        current_row += 1

        self.selected_invite_accounts = []

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
        btn_frame.pack(fill="x", pady=10)
        self.start_invite_btn = ttk.Button(btn_frame, text="开始拉人", command=self.start_invite_advanced, width=12)
        self.start_invite_btn.pack(side="left", padx=10)
        self.stop_invite_btn = ttk.Button(btn_frame, text="停止拉人", command=self.stop_invite, width=12)
        self.stop_invite_btn.pack(side="left", padx=10)

        log_frame = ttk.LabelFrame(main_container, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["批量拉人"] = scrolledtext.ScrolledText(log_frame, width=100, height=24)
        self.log_widgets["批量拉人"].pack(fill="both", expand=True, padx=5, pady=5)

        self.is_inviting = False
        self.invite_stop_flag = False

    def select_invite_accounts(self):
        selected = self.show_account_selector("选择拉人账号", group_filter_default="全部", status_filter_default="正常")
        self.selected_invite_accounts = selected
        self.selected_invite_accounts_label.config(text=f"已选: {len(selected)} 个账号")
        self.log("批量拉人", f"已选择 {len(selected)} 个账号")

    def select_private_accounts(self):
        selected = self.show_account_selector("选择私发账号", group_filter_default="全部", status_filter_default="正常")
        self.selected_private_accounts = selected
        self.selected_private_accounts_label.config(text=f"已选: {len(selected)} 个账号")
        self.log("群发广告", f"已选择 {len(selected)} 个私发账号")

    def select_group_accounts(self):
        selected = self.show_account_selector("选择群发账号", group_filter_default="全部", status_filter_default="正常")
        self.selected_group_accounts = selected
        self.selected_group_accounts_label.config(text=f"已选: {len(selected)} 个账号")
        self.log("群发广告", f"已选择 {len(selected)} 个群发账号")

    def select_chat_accounts(self):
        selected = self.show_account_selector("选择自动群聊账号", group_filter_default="全部", status_filter_default="正常")
        self.selected_chat_accounts = selected
        self.selected_chat_accounts_label.config(text=f"已选: {len(selected)} 个账号")
        self.log("自动群聊", f"已选择 {len(selected)} 个账号")

    def refresh_invite_account_listbox(self, event=None):
        pass

    def get_selected_invite_accounts(self):
        return self.selected_invite_accounts

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
        self.processed_usernames = set()

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
        account_users = [[] for _ in range(len(accounts))]
        user_index = 0
        while user_index < len(users):
            for i in range(len(accounts)):
                if user_index >= len(users):
                    break
                account_users[i].append(users[user_index])
                user_index += 1

        tasks = []
        for i, acc in enumerate(accounts):
            user_slice = account_users[i]
            if user_slice:
                task = self.run_single_account_invite(
                    acc, targets, user_slice, per_batch, per_account_max,
                    per_account_limit, invite_wait
                )
                tasks.append(task)
                await asyncio.sleep(1)
        await asyncio.gather(*tasks)

    async def invite_user(self, client, phone, entity, username):
        clean_username = username.lstrip('@')

        if clean_username in self.processed_usernames:
            return False, f"[{phone[-6:]}] 跳过 | {clean_username[:15]} | 已处理"

        try:
            user_entity = await client.get_entity(clean_username)
        except UsernameInvalidError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '用户无效')
            return False, f"[{phone[-6:]}] ❌用户问题 | {clean_username[:15]} | 用户不存在(用户名无效)"
        except ValueError as e:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户问题 | {clean_username[:15]} | 用户不存在或ID无效"
        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg:
                self.total_fail += 1
                self.total_processed += 1
                self.processed_usernames.add(clean_username)
                return False, f"[{phone[-6:]}] ❌用户问题 | {clean_username[:15]} | 用户不存在"
            raise e

        if hasattr(user_entity, 'deleted') and user_entity.deleted:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户问题 | {clean_username[:15]} | 账号已注销"

        if hasattr(user_entity, 'bot') and user_entity.bot:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户问题 | {clean_username[:15]} | 机器人账号"

        try:
            await client(InviteToChannelRequest(entity, [user_entity.id]))
            self.total_success += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return True, f"[{phone[-6:]}] ✅成功 | {clean_username[:15]}"

        except UserPrivacyRestrictedError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户隐私 | {clean_username[:15]} | 用户设置了隐私保护(无法被邀请)"
        except UserNotMutualContactError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '双向限制')
            return False, f"[{phone[-6:]}] ❌用户隐私 | {clean_username[:15]} | 非双向联系人(需要对方先加你)"
        except UserAlreadyParticipantError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ⚠️跳过 | {clean_username[:15]} | 用户已在群中"
        except UserKickedError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户限制 | {clean_username[:15]} | 用户曾被踢出该群"
        except UserBannedInChannelError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户隐私 | {clean_username[:15]} | 用户拒绝被邀请(隐私设置/屏蔽群组)"
        except UserChannelsTooMuchError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ❌用户限制 | {clean_username[:15]} | 用户加入的群组已达上限"
        except FloodWaitError as e:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '频率限制')
            return False, f"[{phone[-6:]}] ⚠️账号限制 | {clean_username[:15]} | 账号操作频繁(需等待{e.seconds}秒)"
        except PeerFloodError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '风控限制')
            return False, f"[{phone[-6:]}] ⚠️账号风控 | {clean_username[:15]} | 账号被TG风控限制(建议更换代理/休息)"
        except ChatAdminRequiredError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ⚠️群组限制 | {clean_username[:15]} | 账号在群组无管理员权限"
        except ChatWriteForbiddenError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '发言限制')
            return False, f"[{phone[-6:]}] ⚠️账号限制 | {clean_username[:15]} | 账号被群组禁言"
        except PhoneNumberBannedError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '封禁')
            return False, f"[{phone[-6:]}] ⚠️账号封禁 | {clean_username[:15]} | 账号已被TG封禁"
        except UserDeactivatedError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            self.update_account_status_by_phone(phone, '销号')
            return False, f"[{phone[-6:]}] ❌用户问题 | {clean_username[:15]} | 用户账号已注销"
        except InviteHashExpiredError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ⚠️群组问题 | {clean_username[:15]} | 邀请链接已过期"
        except InviteHashInvalidError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ⚠️群组问题 | {clean_username[:15]} | 邀请链接无效"
        except ChannelInvalidError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ⚠️群组问题 | {clean_username[:15]} | 群组/频道无效或不存在"
        except ChannelPrivateError:
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)
            return False, f"[{phone[-6:]}] ⚠️群组问题 | {clean_username[:15]} | 群组为私有(无法加入)"
        except Exception as e:
            error_msg = str(e).lower()
            self.total_fail += 1
            self.total_processed += 1
            self.processed_usernames.add(clean_username)

            if "banned" in error_msg:
                self.update_account_status_by_phone(phone, '封禁')
                return False, f"[{phone[-6:]}] ⚠️账号封禁 | {clean_username[:15]} | 账号被封禁"
            elif "flood" in error_msg:
                self.update_account_status_by_phone(phone, '频率限制')
                return False, f"[{phone[-6:]}] ⚠️账号限制 | {clean_username[:15]} | 账号操作频繁"
            elif "timeout" in error_msg or "timed out" in error_msg:
                return False, f"[{phone[-6:]}] ⚠️网络问题 | {clean_username[:15]} | 连接超时(检查代理/网络)"
            elif "proxy" in error_msg:
                return False, f"[{phone[-6:]}] ⚠️网络问题 | {clean_username[:15]} | 代理连接失败"
            elif "connection" in error_msg:
                return False, f"[{phone[-6:]}] ⚠️网络问题 | {clean_username[:15]} | 网络连接异常"
            else:
                return False, f"[{phone[-6:]}] ❓未知错误 | {clean_username[:15]} | {error_msg[:30]}"

    async def run_single_account_invite(self, acc, targets, users, per_batch, per_account_max, per_account_limit, invite_wait):
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.tl.functions.messages import ImportChatInviteRequest
        from telethon.errors import UserAlreadyParticipantError

        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

        client = None
        account_invited_count = 0

        try:
            from telethon.sessions import StringSession

            session = None
            if session_path and os.path.exists(session_path):
                try:
                    with open(session_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    if content and len(content) > 10:
                        session = StringSession(content)
                except:
                    session = session_path
            else:
                session = MemorySession()

            client = TelegramClient(session, api_id, api_hash, proxy=proxy)
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
                            error_msg = str(e)
                            self.log("批量拉人", f"[{phone[-6:]}] 加入失败: {error_msg[:50]}")
                            if "You tried to use a method that" in error_msg or "USER_DEACTIVATED" in error_msg or "deactivated" in error_msg.lower():
                                self.update_account_status_by_phone(phone, '销号')
                                self.log("批量拉人", f"[{phone[-6:]}] ⚠️账号已注销(销号)")
                            elif "banned" in error_msg.lower() or "restricted" in error_msg.lower():
                                self.update_account_status_by_phone(phone, '限制加群')
                            continue
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
                            error_msg = str(e)
                            self.log("批量拉人", f"[{phone[-6:]}] 加入失败: {error_msg[:50]}")
                            if "You tried to use a method that" in error_msg or "USER_DEACTIVATED" in error_msg:
                                self.update_account_status_by_phone(phone, '销号')
                            elif "banned" in error_msg.lower():
                                self.update_account_status_by_phone(phone, '限制加群')
                            continue

                    if entity:
                        target_entities.append((target, entity))
                except Exception as e:
                    error_msg = str(e)
                    self.log("批量拉人", f"[{phone[-6:]}] 解析失败: {error_msg[:50]}")
                    if "You tried to use a method that" in error_msg:
                        self.update_account_status_by_phone(phone, '销号')

            if not target_entities:
                self.log("批量拉人", f"[{phone[-6:]}] 无有效目标")
                return

            for username in users:
                if self.invite_stop_flag:
                    break
                if per_account_max > 0 and account_invited_count >= per_account_max:
                    break

                for target, entity in target_entities:
                    if self.invite_stop_flag:
                        break
                    if per_account_limit > 0 and account_invited_count >= per_account_limit:
                        break

                    success, log_msg = await self.invite_user(
                        client, phone, entity, username
                    )

                    self.log("批量拉人", log_msg)

                    if success:
                        account_invited_count += 1
                        self.remove_user_from_file(username)
                    else:
                        account_level_errors = [
                            "账号封禁", "账号风控", "账号限制", 
                            "频率限制", "销号", "账号已注销",
                            "发言限制", "限制加群"
                        ]
                        if any(err in log_msg for err in account_level_errors):
                            self.log("批量拉人", f"[{phone[-6:]}] ⚠️ 账号异常，跳过该账号")
                            return
                        else:
                            self.remove_user_from_file(username)
                            continue

                    await asyncio.sleep(invite_wait)
                    break

        except Exception as e:
            error_msg = str(e)
            self.log("批量拉人", f"[{phone[-6:]}] 异常: {error_msg[:50]}")
            if "You tried to use a method that" in error_msg:
                self.update_account_status_by_phone(phone, '销号')
        finally:
            if client:
                await client.disconnect()

    def stop_invite(self):
        if self.is_inviting:
            self.invite_stop_flag = True
            self.log("批量拉人", "停止拉人")
        else:
            self.log("批量拉人", "无进行中的任务")

    def create_send_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="群发广告")

        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        send_notebook = ttk.Notebook(main_frame)
        send_notebook.pack(fill="both", expand=True)

        private_frame = ttk.Frame(send_notebook)
        send_notebook.add(private_frame, text="私发(私聊)")

        private_main = ttk.Frame(private_frame)
        private_main.pack(fill="both", expand=True, padx=10, pady=5)

        private_top = ttk.Frame(private_main)
        private_top.pack(fill="x", pady=(0, 5))

        account_frame = ttk.LabelFrame(private_top, text="选择任务账号")
        account_frame.pack(fill="x", pady=5)

        filter_row = ttk.Frame(account_frame)
        filter_row.pack(fill="x", padx=5, pady=5)

        ttk.Button(filter_row, text="选择账号", command=self.select_private_accounts, width=12).pack(side="left", padx=5)
        self.selected_private_accounts_label = ttk.Label(filter_row, text="已选: 0 个账号", foreground="blue")
        self.selected_private_accounts_label.pack(side="left", padx=10)

        self.selected_private_accounts = []

        user_list_frame = ttk.LabelFrame(private_top, text="用户列表导入")
        user_list_frame.pack(fill="x", pady=5)

        user_list_row = ttk.Frame(user_list_frame)
        user_list_row.pack(fill="x", padx=5, pady=5)

        self.private_user_list_file = tk.StringVar()
        ttk.Entry(user_list_row, textvariable=self.private_user_list_file, width=60).pack(side="left", padx=5)
        ttk.Button(user_list_row, text="导入TXT文件", command=self.import_private_user_txt, width=12).pack(side="left", padx=2)
        ttk.Button(user_list_row, text="导入JSON文件", command=self.import_private_user_json, width=12).pack(side="left", padx=2)
        ttk.Label(user_list_row, text="（每行一个用户名，支持@开头）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=10)

        self.private_user_count_label = ttk.Label(user_list_frame, text="已加载: 0 个用户", foreground="blue")
        self.private_user_count_label.pack(anchor="w", padx=5, pady=2)
        self.private_users = []

        ad_frame = ttk.LabelFrame(private_top, text="广告内容")
        ad_frame.pack(fill="x", pady=5)

        self.private_ad_text = scrolledtext.ScrolledText(ad_frame, width=80, height=6)
        self.private_ad_text.pack(fill="x", padx=5, pady=5)

        ad_btn_frame = ttk.Frame(ad_frame)
        ad_btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(ad_btn_frame, text="导入文本广告", command=self.import_private_ad_text).pack(side="left", padx=5)
        ttk.Button(ad_btn_frame, text="导入图片广告", command=self.import_private_image).pack(side="left", padx=5)
        if hasattr(self, 'private_image_path'):
            ttk.Label(ad_btn_frame, textvariable=self.private_image_path).pack(side="left", padx=5)

        param_frame = ttk.LabelFrame(private_top, text="发送参数")
        param_frame.pack(fill="x", pady=5)

        param_row = ttk.Frame(param_frame)
        param_row.pack(fill="x", padx=5, pady=5)

        ttk.Label(param_row, text="时间间隔(秒):").pack(side="left", padx=5)
        self.private_interval = ttk.Entry(param_row, width=10)
        self.private_interval.insert(0, "30")
        self.private_interval.pack(side="left", padx=5)

        ttk.Label(param_row, text="单号私发数量:").pack(side="left", padx=20)
        self.private_per_account_limit = ttk.Entry(param_row, width=10)
        self.private_per_account_limit.insert(0, "50")
        self.private_per_account_limit.pack(side="left", padx=5)

        ttk.Label(param_row, text="线程数:").pack(side="left", padx=20)
        self.private_thread_count = ttk.Entry(param_row, width=10)
        self.private_thread_count.insert(0, "3")
        self.private_thread_count.pack(side="left", padx=5)

        self.private_auto_skip = tk.BooleanVar(value=True)
        ttk.Checkbutton(param_row, text="账号异常自动跳过", variable=self.private_auto_skip).pack(side="left", padx=20)

        btn_frame = ttk.Frame(private_top)
        btn_frame.pack(pady=10)
        self.private_start_btn = ttk.Button(btn_frame, text="开始", command=self.start_private_send, width=10)
        self.private_start_btn.pack(side="left", padx=5)
        self.private_stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_private_send, width=10)
        self.private_stop_btn.pack(side="left", padx=5)
        self.private_pause_btn = ttk.Button(btn_frame, text="暂停", command=self.pause_private_send, width=10)
        self.private_pause_btn.pack(side="left", padx=5)
        self.private_resume_btn = ttk.Button(btn_frame, text="继续", command=self.resume_private_send, width=10)
        self.private_resume_btn.pack(side="left", padx=5)

        private_log_frame = ttk.LabelFrame(private_main, text="运行日志")
        private_log_frame.pack(fill="both", expand=True, pady=5)
        self.private_log = scrolledtext.ScrolledText(private_log_frame, width=100, height=8)
        self.private_log.pack(fill="both", expand=True, padx=5, pady=5)

        group_frame_tab = ttk.Frame(send_notebook)
        send_notebook.add(group_frame_tab, text="群发(群聊)")

        group_main = ttk.Frame(group_frame_tab)
        group_main.pack(fill="both", expand=True, padx=10, pady=5)

        group_top = ttk.Frame(group_main)
        group_top.pack(fill="x", pady=(0, 5))

        target_frame = ttk.LabelFrame(group_top, text="目标群组")
        target_frame.pack(fill="x", pady=5)

        target_row = ttk.Frame(target_frame)
        target_row.pack(fill="x", padx=5, pady=10)

        self.group_target_file = tk.StringVar()
        ttk.Entry(target_row, textvariable=self.group_target_file, width=60).pack(side="left", padx=5)
        ttk.Button(target_row, text="导入群链接文件", command=self.import_group_targets, width=15).pack(side="left", padx=5)
        ttk.Label(target_row, text="（每行一个群链接或ID）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=10)

        self.group_target_count_label = ttk.Label(target_frame, text="已加载: 0 个群组", foreground="blue")
        self.group_target_count_label.pack(anchor="w", padx=5, pady=2)
        self.group_targets = []

        group_account_frame = ttk.LabelFrame(group_top, text="选择任务账号")
        group_account_frame.pack(fill="x", pady=5)

        group_filter_row = ttk.Frame(group_account_frame)
        group_filter_row.pack(fill="x", padx=5, pady=5)

        ttk.Button(group_filter_row, text="选择账号", command=self.select_group_accounts, width=12).pack(side="left", padx=5)
        self.selected_group_accounts_label = ttk.Label(group_filter_row, text="已选: 0 个账号", foreground="blue")
        self.selected_group_accounts_label.pack(side="left", padx=10)

        self.selected_group_accounts = []

        group_ad_frame = ttk.LabelFrame(group_top, text="广告内容")
        group_ad_frame.pack(fill="x", pady=5)

        self.group_ad_text = scrolledtext.ScrolledText(group_ad_frame, width=80, height=6)
        self.group_ad_text.pack(fill="x", padx=5, pady=5)

        group_ad_btn_frame = ttk.Frame(group_ad_frame)
        group_ad_btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(group_ad_btn_frame, text="导入文本广告", command=self.import_group_ad_text).pack(side="left", padx=5)
        ttk.Button(group_ad_btn_frame, text="导入图片广告", command=self.import_group_image).pack(side="left", padx=5)

        group_param_frame = ttk.LabelFrame(group_top, text="发送参数")
        group_param_frame.pack(fill="x", pady=5)

        group_param_row = ttk.Frame(group_param_frame)
        group_param_row.pack(fill="x", padx=5, pady=5)

        ttk.Label(group_param_row, text="单号同时群发几个群:").pack(side="left", padx=5)
        self.group_concurrent = ttk.Entry(group_param_row, width=10)
        self.group_concurrent.insert(0, "3")
        self.group_concurrent.pack(side="left", padx=5)

        ttk.Label(group_param_row, text="单号群发数量:").pack(side="left", padx=20)
        self.group_per_account_limit = ttk.Entry(group_param_row, width=10)
        self.group_per_account_limit.insert(0, "50")
        self.group_per_account_limit.pack(side="left", padx=5)

        ttk.Label(group_param_row, text="时间间隔(秒):").pack(side="left", padx=20)
        self.group_interval = ttk.Entry(group_param_row, width=10)
        self.group_interval.insert(0, "30")
        self.group_interval.pack(side="left", padx=5)

        ttk.Label(group_param_row, text="线程数:").pack(side="left", padx=20)
        self.group_thread_count = ttk.Entry(group_param_row, width=10)
        self.group_thread_count.insert(0, "3")
        self.group_thread_count.pack(side="left", padx=5)

        group_param_row2 = ttk.Frame(group_param_frame)
        group_param_row2.pack(fill="x", padx=5, pady=5)

        self.group_auto_skip = tk.BooleanVar(value=True)
        ttk.Checkbutton(group_param_row2, text="账号异常自动跳过", variable=self.group_auto_skip).pack(side="left", padx=5)

        group_btn_frame = ttk.Frame(group_top)
        group_btn_frame.pack(pady=10)
        self.group_start_btn = ttk.Button(group_btn_frame, text="开始", command=self.start_group_send, width=10)
        self.group_start_btn.pack(side="left", padx=5)
        self.group_stop_btn = ttk.Button(group_btn_frame, text="停止", command=self.stop_group_send, width=10)
        self.group_stop_btn.pack(side="left", padx=5)
        self.group_pause_btn = ttk.Button(group_btn_frame, text="暂停", command=self.pause_group_send, width=10)
        self.group_pause_btn.pack(side="left", padx=5)
        self.group_resume_btn = ttk.Button(group_btn_frame, text="继续", command=self.resume_group_send, width=10)
        self.group_resume_btn.pack(side="left", padx=5)

        group_log_frame = ttk.LabelFrame(group_main, text="运行日志")
        group_log_frame.pack(fill="both", expand=True, pady=5)
        self.group_log = scrolledtext.ScrolledText(group_log_frame, width=100, height=8)
        self.group_log.pack(fill="both", expand=True, padx=5, pady=5)

        self.private_image_path = tk.StringVar()
        self.group_image_path = tk.StringVar()
        self.private_send_running = False
        self.private_send_paused = False
        self.private_stop_flag = False
        self.group_send_running = False
        self.group_send_paused = False
        self.group_stop_flag = False

    def refresh_private_account_list(self, event=None):
        pass

    def refresh_group_account_list(self, event=None):
        pass

    def import_private_user_txt(self):
        file_path = filedialog.askopenfilename(title="选择用户列表文件", filetypes=[("文本文件", "*.txt")])
        if file_path:
            self.private_user_list_file.set(file_path)
            users = []
            try:
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                content = None
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if content is None:
                    self.private_log_insert(f"导入失败: 无法识别文件编码")
                    return

                for line in content.split('\n'):
                    username = line.strip()
                    if username:
                        if username.startswith('@'):
                            username = username[1:]
                        users.append(username)
                self.private_users = users
                self.private_user_count_label.config(text=f"已加载: {len(users)} 个用户")
                self.private_log_insert(f"导入用户列表: {file_path}, 共 {len(users)} 个用户")
            except Exception as e:
                self.private_log_insert(f"导入失败: {str(e)}")

    def import_private_user_json(self):
        file_path = filedialog.askopenfilename(title="选择用户列表文件", filetypes=[("JSON文件", "*.json")])
        if file_path:
            self.private_user_list_file.set(file_path)
            users = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            username = item.strip() if isinstance(item, str) else str(item)
                            if username:
                                if username.startswith('@'):
                                    username = username[1:]
                                users.append(username)
                    elif isinstance(data, dict) and 'users' in data:
                        for item in data['users']:
                            username = item.strip() if isinstance(item, str) else str(item)
                            if username:
                                if username.startswith('@'):
                                    username = username[1:]
                                users.append(username)
                self.private_users = users
                self.private_user_count_label.config(text=f"已加载: {len(users)} 个用户")
                self.private_log_insert(f"导入用户列表: {file_path}, 共 {len(users)} 个用户")
            except Exception as e:
                self.private_log_insert(f"导入失败: {str(e)}")

    def import_private_ad_text(self):
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt")])
        if file_path:
            try:
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                content = None
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if content is None:
                    self.private_log_insert(f"导入失败: 无法识别文件编码")
                    return
                self.private_ad_text.delete("1.0", tk.END)
                self.private_ad_text.insert("1.0", content)
                self.private_log_insert(f"导入文本广告: {file_path}")
            except Exception as e:
                self.private_log_insert(f"导入失败: {str(e)}")

    def import_private_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp")])
        if file_path:
            self.private_image_path.set(file_path)
            self.private_log_insert(f"选择图片广告: {file_path}")

    def import_group_ad_text(self):
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt")])
        if file_path:
            try:
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                content = None
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if content is None:
                    self.group_log_insert(f"导入失败: 无法识别文件编码")
                    return
                self.group_ad_text.delete("1.0", tk.END)
                self.group_ad_text.insert("1.0", content)
                self.group_log_insert(f"导入文本广告: {file_path}")
            except Exception as e:
                self.group_log_insert(f"导入失败: {str(e)}")

    def import_group_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp")])
        if file_path:
            self.group_image_path.set(file_path)
            self.group_log_insert(f"选择图片广告: {file_path}")

    def import_group_targets(self):
        file_path = filedialog.askopenfilename(title="选择群组链接文件", filetypes=[("文本文件", "*.txt")])
        if file_path:
            self.group_target_file.set(file_path)
            targets = []
            try:
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                content = None
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if content is None:
                    self.group_log_insert(f"导入失败: 无法识别文件编码")
                    return

                for line in content.split('\n'):
                    target = line.strip()
                    if target:
                        targets.append(target)
                self.group_targets = targets
                self.group_target_count_label.config(text=f"已加载: {len(targets)} 个群组")
                self.group_log_insert(f"导入群组链接: {file_path}, 共 {len(targets)} 个群组")
            except Exception as e:
                self.group_log_insert(f"导入失败: {str(e)}")

    def private_log_insert(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.private_log.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.private_log.see(tk.END)

    def group_log_insert(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.group_log.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.group_log.see(tk.END)

    def get_selected_private_accounts(self):
        return self.selected_private_accounts

    def get_selected_group_accounts(self):
        return self.selected_group_accounts

    def start_private_send(self):
        if self.private_send_running:
            self.private_log_insert("任务进行中")
            return

        selected_accounts = self.get_selected_private_accounts()
        if not selected_accounts:
            self.private_log_insert("请至少选择一个账号")
            self.show_centered_warning("提示", "请至少选择一个账号")
            return

        if not self.private_users:
            self.private_log_insert("请先导入用户列表")
            self.show_centered_warning("提示", "请先导入用户列表")
            return

        ad_text = self.private_ad_text.get("1.0", tk.END).strip()
        image_path = self.private_image_path.get().strip()
        if not ad_text and not image_path:
            self.private_log_insert("请输入广告内容或选择图片")
            self.show_centered_warning("提示", "请输入广告内容或选择图片")
            return

        try:
            interval = int(self.private_interval.get())
            per_account_limit = int(self.private_per_account_limit.get())
            thread_cnt = int(self.private_thread_count.get())
            auto_skip = self.private_auto_skip.get()
        except ValueError:
            self.private_log_insert("参数错误")
            return

        self.private_send_running = True
        self.private_send_paused = False
        self.private_stop_flag = False

        self.private_user_file_path = self.private_user_list_file.get()

        self.private_log_insert(f"========== 开始私发 ==========")
        self.private_log_insert(f"目标用户: {len(self.private_users)} | 账号: {len(selected_accounts)} | 每号限: {per_account_limit}人 | 线程数: {thread_cnt} | 间隔: {interval}秒")

        def run_private_send():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.do_private_send(selected_accounts, self.private_users, ad_text, image_path, interval, per_account_limit, thread_cnt, auto_skip))
            loop.close()
            self.private_send_running = False
            self.private_log_insert("========== 私发完成 ==========")

        threading.Thread(target=run_private_send, daemon=True).start()

    async def do_private_send(self, accounts, users, ad_text, image_path, interval, per_account_limit, thread_cnt, auto_skip):
        """
        私发功能 - 每个账号按顺序发送不同的用户
        账号A发用户1，账号B发用户2，账号C发用户3...
        发送成功或用户问题 → 删除该用户
        账号问题 → 淘汰该账号
        """
        if not accounts or not users:
            self.private_log_insert("账号或用户列表为空")
            return

        if per_account_limit <= 0:
            self.private_log_insert("每账号发送数量必须大于0")
            return

        active_accounts = [acc for acc in accounts if acc.get('status') == '正常']
        if not active_accounts:
            self.private_log_insert("没有可用的正常账号")
            return

        user_list = users.copy()
        eliminated_accounts = set()
        account_sent_count = {acc.get('phone'): 0 for acc in active_accounts}
        
        send_stats = {'success': 0, 'fail': 0}
        round_num = 1
        total_eliminated = 0
        
        self.private_log_insert(f"========== 开始私发 ==========")
        self.private_log_insert(f"初始账号: {len(active_accounts)}个, 用户: {len(user_list)}个, 每号限: {per_account_limit}人")

        while True:
            if self.private_stop_flag:
                self.private_log_insert("收到停止信号，停止发送")
                break
                
            while self.private_send_paused:
                await asyncio.sleep(1)
                if self.private_stop_flag:
                    break

            if not user_list:
                self.private_log_insert("用户列表已为空，停止发送")
                break

            available_accounts = [acc for acc in active_accounts 
                                  if acc.get('phone') not in eliminated_accounts 
                                  and account_sent_count.get(acc.get('phone'), 0) < per_account_limit]
            
            if not available_accounts:
                if len(eliminated_accounts) == len(active_accounts):
                    self.private_log_insert(f"所有账号已被淘汰，停止发送")
                else:
                    self.private_log_insert(f"所有账号已达到发送上限({per_account_limit}人)，停止发送")
                break

            self.private_log_insert(f"")
            self.private_log_insert(f"========== 第 {round_num} 轮 ==========")
            self.private_log_insert(f"参与账号: {len(available_accounts)}个, 剩余用户: {len(user_list)}个")

            total_batches = (len(available_accounts) + thread_cnt - 1) // thread_cnt
            
            for batch_idx in range(total_batches):
                if self.private_stop_flag:
                    break
                while self.private_send_paused:
                    await asyncio.sleep(1)
                    if self.private_stop_flag:
                        break

                if not user_list:
                    break

                start = batch_idx * thread_cnt
                end = min(start + thread_cnt, len(available_accounts))
                batch_accounts = available_accounts[start:end]
                
                batch_num = batch_idx + 1
                self.private_log_insert(f"第 {batch_num}/{total_batches} 批 (账号: {len(batch_accounts)}个)")

                for acc in batch_accounts:
                    if self.private_stop_flag:
                        break
                    if not user_list:
                        break
                        
                    phone = acc.get('phone', '')
                    if phone in eliminated_accounts:
                        continue
                    if account_sent_count.get(phone, 0) >= per_account_limit:
                        continue
                    
                    current_user = user_list[0]
                    
                    result, error_type = await self.send_single_message_v2_with_type(
                        acc, current_user, ad_text, image_path,
                        send_stats, auto_skip
                    )
                    
                    if result:
                        account_sent_count[phone] = account_sent_count.get(phone, 0) + 1
                        send_stats['success'] += 1
                        self.private_log_insert(f"  [{phone}] ✅ 成功 | {current_user}")
                        
                        if user_list and user_list[0] == current_user:
                            user_list.pop(0)
                            if self.private_user_file_path and os.path.exists(self.private_user_file_path):
                                self.remove_user_from_file(current_user, self.private_user_file_path)
                    else:
                        account_level_errors = ["封禁", "销号", "风控限制", "频率限制", "未授权", "发言限制", "双向限制", "限制加群", "需要2FA重新登录", "网络超时", "代理错误", "权限不足"]
                        if error_type in account_level_errors:
                            eliminated_accounts.add(phone)
                            total_eliminated += 1
                            self.private_log_insert(f"  [{phone}] ❌ 淘汰({error_type})")
                            status_map = {
                                "封禁": "封禁", "销号": "销号", "风控限制": "风控限制",
                                "频率限制": "频率限制", "未授权": "未授权", "发言限制": "发言限制",
                                "双向限制": "双向限制", "限制加群": "限制加群",
                                "需要2FA重新登录": "需要2FA重新登录",
                                "网络超时": "频率限制", "代理错误": "频率限制", "权限不足": "风控限制"
                            }
                            if error_type in status_map:
                                self.update_account_status_by_phone(phone, status_map[error_type])
                        else:
                            self.private_log_insert(f"  [{phone}] ⚠️ 用户问题({error_type}) | {current_user}")
                            if user_list and user_list[0] == current_user:
                                user_list.pop(0)
                                if self.private_user_file_path and os.path.exists(self.private_user_file_path):
                                    self.remove_user_from_file(current_user, self.private_user_file_path)

                    await asyncio.sleep(1)

                # 每批结束后等待间隔
                if batch_idx < total_batches - 1 and not self.private_stop_flag:
                    if user_list and available_accounts:
                        self.private_log_insert(f"等待 {interval} 秒...")
                        await asyncio.sleep(interval)

            available_accounts = [acc for acc in active_accounts 
                                  if acc.get('phone') not in eliminated_accounts 
                                  and account_sent_count.get(acc.get('phone'), 0) < per_account_limit]
            
            if not available_accounts:
                if len(eliminated_accounts) == len(active_accounts):
                    self.private_log_insert(f"所有账号已被淘汰，停止发送")
                else:
                    self.private_log_insert(f"所有账号已达到发送上限({per_account_limit}人)，停止发送")
                break

            if not user_list:
                self.private_log_insert("用户列表已为空，停止发送")
                break

            round_num += 1

        self.private_log_insert(f"")
        self.private_log_insert(f"========== 全部发送完成 ==========")
        self.private_log_insert(f"✅ 成功发送: {send_stats['success']} 条")
        self.private_log_insert(f"❌ 账号淘汰: {total_eliminated} 个")
        self.private_log_insert(f"📊 剩余账号: {len([acc for acc in active_accounts if acc.get('phone') not in eliminated_accounts])} 个")
        self.private_log_insert(f"📊 剩余用户: {len(user_list)} 个")
        
        self.private_users = user_list
        self.private_user_count_label.config(text=f"已加载: {len(self.private_users)} 个用户")
        self.refresh_account_list_filter()

    async def send_single_message_v2_with_type(self, acc, username, ad_text, image_path, send_stats, auto_skip):
        """单个账号发送单条消息，返回 (是否成功, 错误类型) - 修复版"""
        phone = acc.get('phone', '')
        session_path = acc.get('session_path', '')
        api_id, api_hash = self.get_account_api_credentials(acc)
        proxy_str = acc.get('proxy', '')
        proxy = self.parse_proxy_string(proxy_str)

        client = None
        try:
            from telethon.sessions import StringSession

            session = None
            if session_path and os.path.exists(session_path):
                try:
                    with open(session_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                    if content and len(content) > 10:
                        session = StringSession(content)
                except:
                    session = session_path
            else:
                session = MemorySession()

            client = TelegramClient(session, api_id, api_hash, proxy=proxy)
            await client.connect()

            if not await client.is_user_authorized():
                self.private_log_insert(f"[{phone}] 账号未登录")
                self.update_account_status_by_phone(phone, '未授权')
                return False, "未授权"

            clean_username = username.lstrip('@')
            self.private_log_insert(f"[{phone}] 发送给: {clean_username}")

            # ========== 修复：增强用户获取逻辑 ==========
            user_entity = None
            try:
                user_entity = await client.get_entity(clean_username)
            except FloodWaitError as e:
                self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                self.update_account_status_by_phone(phone, '频率限制')
                send_stats['fail'] += 1
                await asyncio.sleep(min(e.seconds, 60))
                return False, "频率限制"
            except UserDeactivatedError:
                self.private_log_insert(f"[{phone}] ❌ 账号已注销 | {clean_username}")
                self.update_account_status_by_phone(phone, '销号')
                send_stats['fail'] += 1
                return False, "销号"
            except PhoneNumberBannedError:
                self.private_log_insert(f"[{phone}] ❌ 账号被封禁 | {clean_username}")
                self.update_account_status_by_phone(phone, '封禁')
                send_stats['fail'] += 1
                return False, "封禁"
            except ValueError:
                pass
            except TimeoutError:
                self.private_log_insert(f"[{phone}] ⚠️ 连接超时 | {clean_username}")
                send_stats['fail'] += 1
                return False, "网络超时"
            except RPCError as e:
                error_msg = str(e).lower()
                if "flood" in error_msg or "429" in error_msg:
                    self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                    self.update_account_status_by_phone(phone, '频率限制')
                    send_stats['fail'] += 1
                    return False, "频率限制"
                elif "banned" in error_msg:
                    self.private_log_insert(f"[{phone}] ❌ 账号被封禁 | {clean_username}")
                    self.update_account_status_by_phone(phone, '封禁')
                    send_stats['fail'] += 1
                    return False, "封禁"
                elif "deactivated" in error_msg:
                    self.private_log_insert(f"[{phone}] ❌ 账号已注销 | {clean_username}")
                    self.update_account_status_by_phone(phone, '销号')
                    send_stats['fail'] += 1
                    return False, "销号"
                elif "403" in error_msg:
                    self.private_log_insert(f"[{phone}] ⚠️ 权限不足 | {clean_username}")
                    send_stats['fail'] += 1
                    return False, "权限不足"
                else:
                    pass
            except Exception as e:
                error_msg = str(e).lower()
                if "timeout" in error_msg:
                    self.private_log_insert(f"[{phone}] ⚠️ 连接超时 | {clean_username}")
                    send_stats['fail'] += 1
                    return False, "网络超时"
                elif "proxy" in error_msg or "connection" in error_msg:
                    self.private_log_insert(f"[{phone}] ⚠️ 代理连接失败 | {clean_username}")
                    send_stats['fail'] += 1
                    return False, "代理错误"
                else:
                    pass

            # 如果第一次获取失败，尝试带@
            if user_entity is None:
                try:
                    user_entity = await client.get_entity(f"@{clean_username}")
                except FloodWaitError as e:
                    self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                    self.update_account_status_by_phone(phone, '频率限制')
                    send_stats['fail'] += 1
                    await asyncio.sleep(min(e.seconds, 60))
                    return False, "频率限制"
                except Exception:
                    pass

            # 如果还是失败，尝试 ResolveUsername
            if user_entity is None:
                try:
                    from telethon.tl.functions.contacts import ResolveUsernameRequest
                    result = await client(ResolveUsernameRequest(clean_username))
                    if result.users:
                        user_entity = result.users[0]
                except FloodWaitError as e:
                    self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                    self.update_account_status_by_phone(phone, '频率限制')
                    send_stats['fail'] += 1
                    await asyncio.sleep(min(e.seconds, 60))
                    return False, "频率限制"
                except Exception:
                    pass

            # 最终判断
            if user_entity is None:
                self.private_log_insert(f"[{phone}] ❌ 用户不存在: {clean_username}")
                send_stats['fail'] += 1
                return False, "用户无效"

            # 确保 user_entity 有 id
            try:
                user_id = user_entity.id
            except AttributeError:
                self.private_log_insert(f"[{phone}] ❌ 无法获取用户ID: {clean_username}")
                send_stats['fail'] += 1
                return False, "用户无效"

            # ========== 发送消息 ==========
            if ad_text.strip().startswith('@PostBot'):
                parts = ad_text.strip().split(' ')
                if len(parts) >= 2:
                    command = parts[1]
                    try:
                        postbot_entity = await client.get_entity('PostBot')
                        result = await client(GetInlineBotResultsRequest(
                            bot=postbot_entity,
                            peer=user_entity.id,
                            query=command,
                            offset=''
                        ))
                        if result.results:
                            await client(SendInlineBotResultRequest(
                                peer=user_entity.id,
                                query_id=result.query_id,
                                id=result.results[0].id
                            ))
                            self.private_log_insert(f"[{phone}] ✅ PostBot成功 | {clean_username}")
                            if self.private_user_file_path and os.path.exists(self.private_user_file_path):
                                self.remove_user_from_file(username, self.private_user_file_path)
                            return True, None
                        else:
                            self.private_log_insert(f"[{phone}] ❌ PostBot无结果 | {clean_username}")
                            send_stats['fail'] += 1
                            return False, "PostBot无结果"
                    except FloodWaitError as e:
                        self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                        self.update_account_status_by_phone(phone, '频率限制')
                        send_stats['fail'] += 1
                        await asyncio.sleep(min(e.seconds, 300))
                        return False, "频率限制"
                    except Exception as e:
                        error_msg = str(e)
                        if "PAYMENT_REQUIRED" in error_msg or "PREMIUM" in error_msg:
                            self.private_log_insert(f"[{phone}] ⚠️ 需要Premium | {clean_username}")
                            send_stats['fail'] += 1
                            return False, "需要Premium"
                        elif "FLOOD" in error_msg or "Too many requests" in error_msg:
                            self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                            self.update_account_status_by_phone(phone, '频率限制')
                            send_stats['fail'] += 1
                            return False, "频率限制"
                        elif "banned" in error_msg.lower():
                            self.update_account_status_by_phone(phone, '封禁')
                            send_stats['fail'] += 1
                            return False, "封禁"
                        elif "deactivated" in error_msg.lower():
                            self.update_account_status_by_phone(phone, '销号')
                            send_stats['fail'] += 1
                            return False, "销号"
                        else:
                            self.private_log_insert(f"[{phone}] ❌ PostBot失败: {error_msg[:50]} | {clean_username}")
                            send_stats['fail'] += 1
                            return False, "PostBot失败"
                else:
                    self.private_log_insert(f"[{phone}] ❌ PostBot命令格式错误")
                    send_stats['fail'] += 1
                    return False, "命令错误"
            elif image_path and os.path.exists(image_path):
                file = await client.upload_file(image_path)
                if ad_text:
                    await client.send_file(user_entity.id, file, caption=ad_text)
                else:
                    await client.send_file(user_entity.id, file)
                self.private_log_insert(f"[{phone}] ✅ 图片发送成功 | {clean_username}")
                if self.private_user_file_path and os.path.exists(self.private_user_file_path):
                    self.remove_user_from_file(username, self.private_user_file_path)
                return True, None
            else:
                await client.send_message(user_entity.id, ad_text)
                self.private_log_insert(f"[{phone}] ✅ 文本发送成功 | {clean_username}")
                if self.private_user_file_path and os.path.exists(self.private_user_file_path):
                    self.remove_user_from_file(username, self.private_user_file_path)
                return True, None

        except FloodWaitError as e:
            self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
            self.update_account_status_by_phone(phone, '频率限制')
            send_stats['fail'] += 1
            await asyncio.sleep(min(e.seconds, 300))
            return False, "频率限制"

        except UserNotMutualContactError:
            self.private_log_insert(f"[{phone}] ❌ 双向限制 | {clean_username}")
            self.update_account_status_by_phone(phone, '双向限制')
            send_stats['fail'] += 1
            return False, "双向限制"

        except PeerFloodError:
            self.private_log_insert(f"[{phone}] ⚠️ 风控限制 | {clean_username}")
            self.update_account_status_by_phone(phone, '风控限制')
            send_stats['fail'] += 1
            return False, "风控限制"

        except UserPrivacyRestrictedError:
            self.private_log_insert(f"[{phone}] ❌ 隐私保护 | {clean_username}")
            send_stats['fail'] += 1
            return False, "用户隐私"

        except UserDeactivatedError:
            self.private_log_insert(f"[{phone}] ❌ 对方已注销 | {clean_username}")
            send_stats['fail'] += 1
            return False, "用户已注销"

        except ChatWriteForbiddenError:
            self.private_log_insert(f"[{phone}] ⚠️ 被禁言 | {clean_username}")
            self.update_account_status_by_phone(phone, '发言限制')
            send_stats['fail'] += 1
            return False, "发言限制"

        except PhoneNumberBannedError:
            self.private_log_insert(f"[{phone}] ❌ 被封禁 | {clean_username}")
            self.update_account_status_by_phone(phone, '封禁')
            send_stats['fail'] += 1
            return False, "封禁"

        except Exception as e:
            error_msg = str(e).lower()
            if "banned" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 账号被封禁 | {clean_username}")
                self.update_account_status_by_phone(phone, '封禁')
                send_stats['fail'] += 1
                return False, "封禁"
            elif "deactivated" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 账号已注销 | {clean_username}")
                self.update_account_status_by_phone(phone, '销号')
                send_stats['fail'] += 1
                return False, "销号"
            elif "too many requests" in error_msg or "flood" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 频率限制 | {clean_username}")
                self.update_account_status_by_phone(phone, '频率限制')
                send_stats['fail'] += 1
                return False, "频率限制"
            elif "password" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 需要重新登录 | {clean_username}")
                self.update_account_status_by_phone(phone, '需要2FA重新登录')
                send_stats['fail'] += 1
                return False, "需要2FA重新登录"
            elif "unauthorized" in error_msg or "auth" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 授权失败 | {clean_username}")
                self.update_account_status_by_phone(phone, '未授权')
                send_stats['fail'] += 1
                return False, "未授权"
            elif "payment_required" in error_msg or "premium" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 需要Premium | {clean_username}")
                send_stats['fail'] += 1
                return False, "需要Premium"
            elif "invalid" in error_msg:
                self.private_log_insert(f"[{phone}] ❌ 用户名无效 | {clean_username}")
                send_stats['fail'] += 1
                return False, "用户无效"
            elif "timeout" in error_msg:
                self.private_log_insert(f"[{phone}] ⚠️ 连接超时 | {clean_username}")
                send_stats['fail'] += 1
                return False, "网络超时"
            else:
                self.private_log_insert(f"[{phone}] ❌ 发送失败: {str(e)[:50]} | {clean_username}")
                send_stats['fail'] += 1
                return False, "未知错误"

        finally:
            if client:
                try:
                    await client.disconnect()
                except:
                    pass

    def stop_private_send(self):
        self.private_stop_flag = True
        self.private_log_insert("停止私发")

    def pause_private_send(self):
        if self.private_send_running and not self.private_send_paused:
            self.private_send_paused = True
            self.private_log_insert("暂停私发")

    def resume_private_send(self):
        if self.private_send_running and self.private_send_paused:
            self.private_send_paused = False
            self.private_log_insert("继续私发")

    def start_group_send(self):
        if self.group_send_running:
            self.group_log_insert("任务进行中")
            return

        selected_accounts = self.get_selected_group_accounts()
        if not selected_accounts:
            self.group_log_insert("请至少选择一个账号")
            self.show_centered_warning("提示", "请至少选择一个账号")
            return

        if not self.group_targets:
            self.group_log_insert("请先导入群组链接文件")
            self.show_centered_warning("提示", "请先导入群组链接文件")
            return

        ad_text = self.group_ad_text.get("1.0", tk.END).strip()
        image_path = self.group_image_path.get().strip()
        if not ad_text and not image_path:
            self.group_log_insert("请输入广告内容或选择图片")
            self.show_centered_warning("提示", "请输入广告内容或选择图片")
            return

        try:
            concurrent = int(self.group_concurrent.get())
            per_account_limit = int(self.group_per_account_limit.get())
            interval = int(self.group_interval.get())
            thread_cnt = int(self.group_thread_count.get())
            auto_skip = self.group_auto_skip.get()
        except ValueError:
            self.group_log_insert("参数错误")
            return

        self.group_send_running = True
        self.group_send_paused = False
        self.group_stop_flag = False

        self.group_log_insert(f"========== 开始群发 ==========")
        self.group_log_insert(f"目标群组: {len(self.group_targets)}个 | 账号: {len(selected_accounts)}个 | 每号限: {per_account_limit}条")

        def run_group_send():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.do_group_send(selected_accounts, self.group_targets, ad_text, image_path, concurrent, per_account_limit, interval, thread_cnt, auto_skip))
            loop.close()
            self.group_send_running = False
            self.group_log_insert("========== 群发完成 ==========")

        threading.Thread(target=run_group_send, daemon=True).start()

    async def do_group_send(self, accounts, targets, ad_text, image_path, concurrent, per_account_limit, interval, thread_cnt, auto_skip):
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.tl.functions.messages import ImportChatInviteRequest
        from telethon.errors import UserAlreadyParticipantError

        def smart_assign_groups(accounts_list, groups_list):
            total_accounts = len(accounts_list)
            total_groups = len(groups_list)

            if total_accounts == 0 or total_groups == 0:
                return {}

            assignment = {}
            account_index = 0

            if total_accounts <= total_groups:
                accounts_per_group = 1
                for group in groups_list:
                    if account_index < total_accounts:
                        assignment[group] = [accounts_list[account_index]]
                        account_index += 1
                    else:
                        assignment[group] = []
            else:
                accounts_per_group = total_accounts // total_groups
                remainder = total_accounts % total_groups

                for i, group in enumerate(groups_list):
                    count = accounts_per_group + (1 if i < remainder else 0)
                    assigned = []
                    for _ in range(count):
                        if account_index < total_accounts:
                            assigned.append(accounts_list[account_index])
                            account_index += 1
                        else:
                            account_index = 0
                            assigned.append(accounts_list[account_index])
                            account_index += 1
                    assignment[group] = assigned

            return assignment

        valid_accounts = [acc for acc in accounts if acc.get('status') == '正常']

        assignment = smart_assign_groups(valid_accounts, targets)

        account_assignment = {}
        for group, assigned_accounts in assignment.items():
            for acc in assigned_accounts:
                phone = acc.get('phone', '')
                if phone not in account_assignment:
                    account_assignment[phone] = []
                account_assignment[phone].append(group)

        self.group_log_insert("========== 智能分配结果 ==========")
        for group, assigned_accounts in assignment.items():
            account_phones = [a.get('phone', '')[-6:] for a in assigned_accounts if a.get('phone')]
            self.group_log_insert(f"群: {group[:30]}... → 账号: {', '.join(account_phones) if account_phones else '无'}")

        async def send_for_account(acc):
            phone = acc.get('phone', '')
            session_path = acc.get('session_path', '')
            api_id, api_hash = self.get_account_api_credentials(acc)
            proxy_str = acc.get('proxy', '')
            proxy = self.parse_proxy_string(proxy_str)

            assigned_groups = account_assignment.get(phone, [])
            if not assigned_groups:
                self.group_log_insert(f"[{phone[-6:]}] 未分配到任何群组")
                return

            client = None
            sent_count = 0
            joined_groups = []

            try:
                from telethon.sessions import StringSession

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                    except:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()
                if not await client.is_user_authorized():
                    self.group_log_insert(f"[{phone[-6:]}] 未登录")
                    return

                for target in assigned_groups:
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
                                    self.group_log_insert(f"[{phone[-6:]}] 加入群组成功")
                            except UserAlreadyParticipantError:
                                self.group_log_insert(f"[{phone[-6:]}] 已是群成员")
                                try:
                                    entity = await client.get_entity(target)
                                except:
                                    pass
                            except Exception as e:
                                error_msg = str(e)
                                self.group_log_insert(f"[{phone[-6:]}] 加入失败: {error_msg[:50]}")
                                continue
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
                            try:
                                await client(JoinChannelRequest(entity))
                                self.group_log_insert(f"[{phone[-6:]}] 加入群组成功")
                            except UserAlreadyParticipantError:
                                self.group_log_insert(f"[{phone[-6:]}] 已是群成员")
                            except Exception as e:
                                error_msg = str(e)
                                self.group_log_insert(f"[{phone[-6:]}] 加入失败: {error_msg[:50]}")
                                continue

                        if entity:
                            joined_groups.append(entity)
                    except Exception as e:
                        self.group_log_insert(f"[{phone[-6:]}] 解析群组失败: {str(e)[:30]}")

                if not joined_groups:
                    self.group_log_insert(f"[{phone[-6:]}] 无有效目标群组")
                    return

                group_index = 0
                while sent_count < per_account_limit or per_account_limit == 0:
                    if self.group_stop_flag:
                        break
                    while self.group_send_paused:
                        await asyncio.sleep(1)

                    target_groups = []
                    for i in range(concurrent):
                        if group_index >= len(joined_groups):
                            group_index = 0
                        target_groups.append(joined_groups[group_index])
                        group_index += 1

                    for entity in target_groups:
                        if self.group_stop_flag:
                            break
                        try:
                            if ad_text.strip().startswith('@PostBot'):
                                parts = ad_text.strip().split(' ')
                                if len(parts) >= 2:
                                    command = parts[1]
                                    try:
                                        postbot_entity = await client.get_entity('PostBot')
                                        result = await client(GetInlineBotResultsRequest(
                                            bot=postbot_entity,
                                            peer=entity,
                                            query=command,
                                            offset=''
                                        ))
                                        if result.results:
                                            await client(SendInlineBotResultRequest(
                                                peer=entity,
                                                query_id=result.query_id,
                                                id=result.results[0].id
                                            ))
                                            self.group_log_insert(f"[{phone[-6:]}] 群发PostBot广告成功")
                                        else:
                                            self.group_log_insert(f"[{phone[-6:]}] PostBot无结果")
                                    except Exception as e:
                                        self.group_log_insert(f"[{phone[-6:]}] PostBot发送失败: {str(e)[:50]}")
                                else:
                                    self.group_log_insert(f"[{phone[-6:]}] PostBot命令格式错误")
                            elif image_path and os.path.exists(image_path):
                                file = await client.upload_file(image_path)
                                if ad_text:
                                    await client.send_file(entity, file, caption=ad_text)
                                else:
                                    await client.send_file(entity, file)
                                self.group_log_insert(f"[{phone[-6:]}] 群发图片成功")
                            else:
                                await client.send_message(entity, ad_text)
                                self.group_log_insert(f"[{phone[-6:]}] 群发文本成功")

                            sent_count += 1
                            group_title = getattr(entity, 'title', str(entity))[:20]
                            self.group_log_insert(f"[{phone[-6:]}] 群发成功 | {group_title} ({sent_count}/{per_account_limit if per_account_limit>0 else '不限'})")
                            await asyncio.sleep(interval)
                        except FloodWaitError as e:
                            self.group_log_insert(f"[{phone[-6:]}] 频率限制，等待{e.seconds}秒")
                            self.update_account_status_by_phone(phone, '频率限制')
                            await asyncio.sleep(e.seconds)
                        except ChatWriteForbiddenError:
                            self.group_log_insert(f"[{phone[-6:]}] 群发失败: 账号被群组禁言")
                            self.update_account_status_by_phone(phone, '发言限制')
                            if auto_skip:
                                continue
                            await asyncio.sleep(interval)
                        except Exception as e:
                            error_msg = str(e).lower()
                            if "banned" in error_msg:
                                self.group_log_insert(f"[{phone[-6:]}] 群发失败: 账号被禁言")
                                self.update_account_status_by_phone(phone, '发言限制')
                            else:
                                self.group_log_insert(f"[{phone[-6:]}] 群发失败: {str(e)[:50]}")
                            if auto_skip:
                                continue
                            await asyncio.sleep(interval)

                    if per_account_limit > 0 and sent_count >= per_account_limit:
                        break

                    await asyncio.sleep(1)

            except Exception as e:
                self.group_log_insert(f"[{phone[-6:]}] 异常: {str(e)[:50]}")
            finally:
                if client:
                    await client.disconnect()

        tasks = []
        for acc in valid_accounts[:thread_cnt]:
            tasks.append(send_for_account(acc))
        await asyncio.gather(*tasks)

    def stop_group_send(self):
        self.group_stop_flag = True
        self.group_log_insert("停止群发")

    def pause_group_send(self):
        if self.group_send_running and not self.group_send_paused:
            self.group_send_paused = True
            self.group_log_insert("暂停群发")

    def resume_group_send(self):
        if self.group_send_running and self.group_send_paused:
            self.group_send_paused = False
            self.group_log_insert("继续群发")

    def create_group_chat_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="自动群聊+回复")

        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="both", expand=True, pady=(0, 5))

        chat_canvas = tk.Canvas(top_frame, highlightthickness=0)
        chat_scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=chat_canvas.yview)
        chat_inner = ttk.Frame(chat_canvas)

        chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
        chat_canvas.pack(side="left", fill="both", expand=True)
        chat_scrollbar.pack(side="right", fill="y")

        chat_window = chat_canvas.create_window((0, 0), window=chat_inner, anchor="nw", width=chat_canvas.winfo_width())

        def on_chat_configure(event):
            chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
        chat_inner.bind("<Configure>", on_chat_configure)

        def on_chat_canvas_configure(event):
            chat_canvas.itemconfig(chat_window, width=event.width)
        chat_canvas.bind("<Configure>", on_chat_canvas_configure)

        def on_chat_mousewheel(event):
            chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        chat_canvas.bind("<MouseWheel>", on_chat_mousewheel)

        mode_frame = ttk.LabelFrame(chat_inner, text="群聊模式")
        mode_frame.pack(fill="x", padx=10, pady=5)

        mode_row = ttk.Frame(mode_frame)
        mode_row.pack(fill="x", padx=5, pady=5)

        self.chat_mode = tk.StringVar(value="all")
        ttk.Radiobutton(mode_row, text="全账号全群", variable=self.chat_mode, value="all").pack(side="left", padx=20)
        ttk.Radiobutton(mode_row, text="分组对应群", variable=self.chat_mode, value="group").pack(side="left", padx=20)

        group_frame = ttk.LabelFrame(chat_inner, text="目标群组列表")
        group_frame.pack(fill="x", padx=10, pady=5)

        group_row = ttk.Frame(group_frame)
        group_row.pack(fill="x", padx=5, pady=5)

        self.chat_group_file = tk.StringVar()
        ttk.Entry(group_row, textvariable=self.chat_group_file, width=60).pack(side="left", padx=5)
        ttk.Button(group_row, text="导入群链接文件", command=self.import_chat_groups, width=15).pack(side="left", padx=5)
        ttk.Label(group_row, text="（每行一个群链接或ID，分组对应群模式下格式：分组名 - 链接）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=10)

        self.chat_group_count_label = ttk.Label(group_frame, text="已加载: 0 个群组", foreground="blue")
        self.chat_group_count_label.pack(anchor="w", padx=5, pady=2)

        account_frame = ttk.LabelFrame(chat_inner, text="选择任务账号")
        account_frame.pack(fill="x", padx=10, pady=5)

        filter_row = ttk.Frame(account_frame)
        filter_row.pack(fill="x", padx=5, pady=5)

        ttk.Button(filter_row, text="选择账号", command=self.select_chat_accounts, width=12).pack(side="left", padx=5)
        self.selected_chat_accounts_label = ttk.Label(filter_row, text="已选: 0 个账号", foreground="blue")
        self.selected_chat_accounts_label.pack(side="left", padx=10)

        self.selected_chat_accounts = []

        script_frame = ttk.LabelFrame(chat_inner, text="话术设置")
        script_frame.pack(fill="x", padx=10, pady=5)

        script_row = ttk.Frame(script_frame)
        script_row.pack(fill="x", padx=5, pady=5)

        self.chat_script_file = tk.StringVar()
        ttk.Entry(script_row, textvariable=self.chat_script_file, width=60).pack(side="left", padx=5)
        ttk.Button(script_row, text="导入话术文件", command=self.import_chat_scripts, width=15).pack(side="left", padx=5)
        ttk.Label(script_row, text="（支持TXT/Excel，格式：序号、话术或序号、@序号 回复内容）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=10)

        self.chat_script_count_label = ttk.Label(script_frame, text="已加载: 0 条话术", foreground="blue")
        self.chat_script_count_label.pack(anchor="w", padx=5, pady=2)

        param_frame = ttk.LabelFrame(chat_inner, text="发言参数")
        param_frame.pack(fill="x", padx=10, pady=5)

        param_row = ttk.Frame(param_frame)
        param_row.pack(fill="x", padx=5, pady=5)

        ttk.Label(param_row, text="最小间隔(秒):").pack(side="left", padx=5)
        self.chat_min_interval = ttk.Entry(param_row, width=10)
        self.chat_min_interval.insert(0, "30")
        self.chat_min_interval.pack(side="left", padx=5)

        ttk.Label(param_row, text="最大间隔(秒):").pack(side="left", padx=20)
        self.chat_max_interval = ttk.Entry(param_row, width=10)
        self.chat_max_interval.insert(0, "60")
        self.chat_max_interval.pack(side="left", padx=5)

        ttk.Label(param_row, text="从第几行话术开始:").pack(side="left", padx=20)
        self.chat_start_line = ttk.Entry(param_row, width=10)
        self.chat_start_line.insert(0, "1")
        self.chat_start_line.pack(side="left", padx=5)
        ttk.Label(param_row, text="（0=从第一行开始）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=5)

        self.chat_loop_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(param_row, text="无限循环", variable=self.chat_loop_enabled).pack(side="left", padx=20)

        btn_frame = ttk.Frame(chat_inner)
        btn_frame.pack(pady=15)
        self.chat_start_btn = ttk.Button(btn_frame, text="启动炒群", command=self.start_auto_chat, width=12)
        self.chat_start_btn.pack(side="left", padx=5)
        self.chat_stop_btn = ttk.Button(btn_frame, text="结束炒群", command=self.stop_auto_chat, width=12)
        self.chat_stop_btn.pack(side="left", padx=5)
        self.chat_pause_btn = ttk.Button(btn_frame, text="暂停", command=self.pause_auto_chat, width=12)
        self.chat_pause_btn.pack(side="left", padx=5)
        self.chat_resume_btn = ttk.Button(btn_frame, text="继续", command=self.resume_auto_chat, width=12)
        self.chat_resume_btn.pack(side="left", padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="x", pady=5)
        self.log_widgets["自动群聊"] = scrolledtext.ScrolledText(log_frame, width=100, height=24)
        self.log_widgets["自动群聊"].pack(fill="both", expand=True, padx=5, pady=5)

        self.chat_groups = []
        self.chat_scripts = []
        self.chat_script_items = []
        self.chat_running = False
        self.chat_paused = False
        self.chat_stop_flag = False
        self.chat_tasks = []
        self.chat_current_script_index = {}

    def import_chat_groups(self):
        file_path = filedialog.askopenfilename(title="选择群组链接文件", filetypes=[("文本文件", "*.txt")])
        if file_path:
            self.chat_group_file.set(file_path)
            groups = []
            try:
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                content = None
                for enc in encodings:
                    try:
                        with open(file_path, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except:
                        continue
                if content is None:
                    self.log("自动群聊", "导入失败: 无法识别文件编码")
                    return

                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue

                    group_name = None
                    group_link = line

                    if ' - ' in line:
                        parts = line.split(' - ', 1)
                        group_name = parts[0].strip()
                        group_link = parts[1].strip()

                    groups.append({
                        'name': group_name,
                        'link': group_link
                    })

                self.chat_groups = groups
                self.chat_group_count_label.config(text=f"已加载: {len(groups)} 个群组")
                self.log("自动群聊", f"导入群组链接: {file_path}, 共 {len(groups)} 个群组")
                group_names = [g['name'] for g in groups if g['name']]
                if group_names:
                    self.log("自动群聊", f"检测到分组绑定: {', '.join(set(group_names))}")
            except Exception as e:
                self.log("自动群聊", f"导入失败: {str(e)}")

    def import_chat_scripts(self):
        file_path = filedialog.askopenfilename(title="选择话术文件", filetypes=[("文本文件", "*.txt"), ("Excel文件", "*.xlsx *.xls")])
        if file_path:
            self.chat_script_file.set(file_path)
            scripts = []
            try:
                if file_path.endswith('.txt'):
                    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
                    content = None
                    for enc in encodings:
                        try:
                            with open(file_path, 'r', encoding=enc) as f:
                                content = f.read()
                            break
                        except:
                            continue
                    if content is None:
                        self.log("自动群聊", "导入失败: 无法识别文件编码")
                        return

                    for line in content.split('\n'):
                        line = line.strip()
                        if line:
                            scripts.append(line)
                elif file_path.endswith(('.xlsx', '.xls')):
                    try:
                        import openpyxl
                        wb = openpyxl.load_workbook(file_path)
                        sheet = wb.active
                        for row in sheet.iter_rows(values_only=True):
                            if row[0]:
                                scripts.append(str(row[0]))
                    except ImportError:
                        self.log("自动群聊", "请先安装openpyxl库: pip install openpyxl")
                        return

                self.chat_scripts = scripts
                self.chat_script_count_label.config(text=f"已加载: {len(scripts)} 条话术")
                self.log("自动群聊", f"导入话术文件: {file_path}, 共 {len(scripts)} 条")
                self.parse_scripts()

            except Exception as e:
                self.log("自动群聊", f"导入失败: {str(e)}")

    def parse_scripts(self):
        self.chat_script_items = []

        for line in self.chat_scripts:
            match = re.match(r'^(\d+)[、，]\s*(.*?)\s*$', line)
            if not match:
                self.log("自动群聊", f"格式错误: {line}")
                continue

            sender_idx = int(match.group(1))
            content = match.group(2).strip()

            reply_to_idx = 0
            at_match = re.search(r'@(\d+)', content)
            if at_match:
                reply_to_idx = int(at_match.group(1))
                content = re.sub(r'@\d+\s*', '', content).strip()

            item = {
                'sender_idx': sender_idx,
                'message': content,
                'reply_to_idx': reply_to_idx,
                'original': line
            }
            self.chat_script_items.append(item)

        self.log("自动群聊", f"话术解析完成，共 {len(self.chat_script_items)} 条有效话术")

    def refresh_chat_account_list(self, event=None):
        pass

    def get_selected_chat_accounts(self):
        return self.selected_chat_accounts

    def get_accounts_by_group(self, group_name):
        return [acc for acc in self.accounts if acc.get('group') == group_name and acc.get('status') == '正常']

    def parse_group_link_entity(self, link):
        if 't.me/' in link:
            username = link.split('t.me/')[-1]
            return username
        return link

    async def get_last_message_from_user(self, client, group_entity, user_id):
        try:
            async for msg in client.iter_messages(group_entity, from_user=user_id, limit=1):
                return msg
        except:
            pass
        return None

    def start_auto_chat(self):
        if self.chat_running:
            self.log("自动群聊", "任务进行中")
            return

        selected_accounts = self.get_selected_chat_accounts()
        if not selected_accounts:
            self.log("自动群聊", "请至少选择一个账号")
            self.show_centered_warning("提示", "请至少选择一个账号")
            return

        if not self.chat_groups:
            self.log("自动群聊", "请先导入目标群组")
            self.show_centered_warning("提示", "请先导入目标群组")
            return

        if not self.chat_script_items:
            self.log("自动群聊", "请先导入话术文件")
            self.show_centered_warning("提示", "请先导入话术文件")
            return

        try:
            min_interval = int(self.chat_min_interval.get())
            max_interval = int(self.chat_max_interval.get())
            loop_enabled = self.chat_loop_enabled.get()
            start_line = int(self.chat_start_line.get()) - 1
            if start_line < 0:
                start_line = 0
        except ValueError:
            self.log("自动群聊", "参数错误")
            return

        if min_interval <= 0 or max_interval < min_interval:
            self.log("自动群聊", "间隔参数无效")
            return

        self.chat_running = True
        self.chat_paused = False
        self.chat_stop_flag = False
        self.chat_current_script_index = {}

        self.chat_message_cache = {}

        self.log("自动群聊", f"========== 启动自动群聊 ==========")
        self.log("自动群聊", f"账号: {len(selected_accounts)}个 | 群组: {len(self.chat_groups)}个 | 话术: {len(self.chat_script_items)}条")
        self.log("自动群聊", f"间隔: {min_interval}~{max_interval}秒 | 无限循环: {'是' if loop_enabled else '否'}")
        self.log("自动群聊", f"模式: {'全账号全群' if self.chat_mode.get() == 'all' else '分组对应群'}")
        self.log("自动群聊", f"从第 {start_line + 1} 行话术开始")

        for acc in selected_accounts:
            self.update_account_task(acc.get('phone'), "自动群聊", True)

        def run_auto_chat():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.do_auto_chat(
                selected_accounts, self.chat_groups, self.chat_script_items,
                min_interval, max_interval, loop_enabled, start_line
            ))
            loop.close()
            self.chat_running = False
            for acc in selected_accounts:
                self.update_account_task(acc.get('phone'), "", False)
                self.update_account_task(acc.get('phone'), "自动群聊", False)
            self.log("自动群聊", "========== 自动群聊已停止 ==========")

        threading.Thread(target=run_auto_chat, daemon=True).start()

    async def do_auto_chat(self, accounts, groups, script_items, min_interval, max_interval, loop_enabled, start_line):
        account_groups = {}

        if self.chat_mode.get() == "group":
            for acc in accounts:
                acc_group = acc.get('group', '默认分组')
                target_links = []
                for g in groups:
                    if g.get('name') and g.get('name') == acc_group:
                        target_links.append(g.get('link'))
                    elif not g.get('name'):
                        target_links.append(g.get('link'))
                if target_links:
                    account_groups[acc.get('phone')] = target_links
        else:
            for acc in accounts:
                account_groups[acc.get('phone')] = [g.get('link') for g in groups]

        if not account_groups:
            self.log("自动群聊", "没有账号分配到有效群组")
            return

        self.log("自动群聊", "正在初始化账号并加入群组...")

        async def init_account(acc):
            phone = acc.get('phone', '')
            if phone not in account_groups:
                return None

            session_path = acc.get('session_path', '')
            api_id, api_hash = self.get_account_api_credentials(acc)
            proxy_str = acc.get('proxy', '')
            proxy = self.parse_proxy_string(proxy_str)
            target_groups = account_groups.get(phone, [])

            if not target_groups:
                return None

            try:
                from telethon.sessions import StringSession

                session = None
                if session_path and os.path.exists(session_path):
                    try:
                        with open(session_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        if content and len(content) > 10:
                            session = StringSession(content)
                    except:
                        session = session_path
                else:
                    session = MemorySession()

                client = TelegramClient(session, api_id, api_hash, proxy=proxy)
                await client.connect()
                if not await client.is_user_authorized():
                    return None

                async def join_single_group(group_link):
                    try:
                        entity = None
                        if 't.me/+' in group_link or 't.me/joinchat' in group_link:
                            if '/+' in group_link:
                                invite_hash = group_link.split('/+')[-1].split('?')[0]
                            else:
                                invite_hash = group_link.split('/joinchat/')[-1].split('?')[0]
                            try:
                                result = await client(ImportChatInviteRequest(invite_hash))
                                if result.chats:
                                    entity = result.chats[0]
                            except UserAlreadyParticipantError:
                                try:
                                    if 't.me/' in group_link:
                                        username = group_link.split('t.me/')[-1].split('?')[0]
                                        entity = await client.get_entity(username)
                                    else:
                                        entity = await client.get_entity(group_link)
                                except:
                                    pass
                            except Exception as e:
                                error_msg = str(e)
                                if "You tried to use a method that" in error_msg:
                                    self.update_account_status_by_phone(phone, '销号')
                                pass
                        else:
                            if 't.me/' in group_link:
                                username = group_link.split('t.me/')[-1].split('?')[0]
                            else:
                                username = group_link
                            try:
                                entity = await client.get_entity(username)
                                try:
                                    await client(JoinChannelRequest(entity))
                                except UserAlreadyParticipantError:
                                    pass
                                except Exception as e:
                                    error_msg = str(e)
                                    if "You tried to use a method that" in error_msg:
                                        self.update_account_status_by_phone(phone, '销号')
                                    pass
                            except Exception:
                                pass
                        return entity
                    except Exception:
                        return None

                join_tasks = [join_single_group(gl) for gl in target_groups]
                entities = await asyncio.gather(*join_tasks)
                group_entities = [e for e in entities if e is not None]

                if not group_entities:
                    await client.disconnect()
                    return None

                for entity in group_entities:
                    @client.on(events.NewMessage(chats=entity))
                    async def message_handler(event):
                        if event.message.out:
                            return
                        if not event.sender_id:
                            return
                        try:
                            sender = await event.client.get_entity(event.sender_id)
                            sender_phone = getattr(sender, 'phone', None)
                            if sender_phone:
                                group_id = event.chat_id
                                if group_id not in self.chat_message_cache:
                                    self.chat_message_cache[group_id] = {}
                                self.chat_message_cache[group_id][sender_phone] = {
                                    'msg_id': event.message.id,
                                    'content': event.message.text or '',
                                    'timestamp': time.time()
                                }
                        except:
                            pass

                return {
                    'client': client,
                    'groups': group_entities,
                    'phone': phone
                }
            except Exception as e:
                self.log("自动群聊", f"[{phone[-6:]}] 初始化失败: {str(e)[:50]}")
                return None

        init_tasks = [init_account(acc) for acc in accounts]
        results = await asyncio.gather(*init_tasks)
        account_clients = {}
        for r in results:
            if r:
                account_clients[r['phone']] = r

        if not account_clients:
            self.log("自动群聊", "没有账号成功初始化")
            return

        self.log("自动群聊", f"初始化完成，成功 {len(account_clients)} 个账号")

        script_queue = []
        for script_item in script_items:
            sender_idx = script_item['sender_idx']
            target_acc = None
            for i, a in enumerate(accounts):
                if i + 1 == sender_idx:
                    target_acc = a
                    break

            if target_acc and target_acc.get('phone') in account_clients:
                script_queue.append({
                    'phone': target_acc.get('phone'),
                    'script': script_item
                })

        if not script_queue:
            self.log("自动群聊", "没有可执行的话术队列")
            return

        if start_line > 0 and start_line < len(script_queue):
            script_queue = script_queue[start_line:]
            self.log("自动群聊", f"从第 {start_line + 1} 行话术开始，剩余 {len(script_queue)} 条")

        self.log("自动群聊", f"话术队列共 {len(script_queue)} 条，将按顺序依次发言")

        script_pointer = 0
        last_phone = None

        while self.chat_running and not self.chat_stop_flag:
            if self.chat_paused:
                await asyncio.sleep(1)
                continue

            if script_pointer >= len(script_queue):
                if loop_enabled:
                    script_pointer = 0
                else:
                    break

            item = script_queue[script_pointer]
            script_pointer += 1

            phone = item['phone']
            script_item = item['script']
            info = account_clients.get(phone)

            if not info:
                continue

            client = info['client']
            group_entities = info['groups']

            for entity in group_entities:
                if self.chat_stop_flag:
                    break

                try:
                    if script_item['reply_to_idx'] > 0:
                        target_account = None
                        for i, a in enumerate(accounts):
                            if i + 1 == script_item['reply_to_idx']:
                                target_account = a
                                break

                        if target_account:
                            target_phone = target_account.get('phone')
                            found_msg = None
                            group_id = entity.id

                            if group_id in self.chat_message_cache:
                                cache = self.chat_message_cache[group_id]
                                if target_phone in cache:
                                    cached = cache[target_phone]
                                    try:
                                        target_user = await client.get_entity(target_phone)
                                        target_user_id = target_user.id
                                        async for msg in client.iter_messages(entity, from_user=target_user_id, limit=1):
                                            found_msg = msg
                                            cache[target_phone] = {
                                                'msg_id': msg.id,
                                                'content': msg.text or '',
                                                'timestamp': time.time()
                                            }
                                            break
                                    except:
                                        try:
                                            found_msg = await client.get_messages(entity, ids=cached['msg_id'])
                                            if not found_msg:
                                                found_msg = None
                                        except:
                                            found_msg = None

                            if not found_msg:
                                try:
                                    target_user = await client.get_entity(target_phone)
                                    target_user_id = target_user.id
                                    async for msg in client.iter_messages(entity, from_user=target_user_id, limit=10):
                                        found_msg = msg
                                        if group_id not in self.chat_message_cache:
                                            self.chat_message_cache[group_id] = {}
                                        self.chat_message_cache[group_id][target_phone] = {
                                            'msg_id': msg.id,
                                            'content': msg.text or '',
                                            'timestamp': time.time()
                                        }
                                        break
                                except:
                                    pass

                            if found_msg:
                                await client.send_message(entity, script_item['message'], reply_to=found_msg.id)
                                self.log("自动群聊", f"[{phone[-6:]}] 回复账号{script_item['reply_to_idx']}: {script_item['message'][:40]}")
                            else:
                                await client.send_message(entity, script_item['message'])
                                self.log("自动群聊", f"[{phone[-6:]}] 发言(未找到@目标): {script_item['message'][:40]}")
                        else:
                            await client.send_message(entity, script_item['message'])
                            self.log("自动群聊", f"[{phone[-6:]}] 发言: {script_item['message'][:40]}")
                    else:
                        sent_msg = await client.send_message(entity, script_item['message'])
                        self.log("自动群聊", f"[{phone[-6:]}] 发言: {script_item['message'][:40]}")

                        if sent_msg:
                            group_id = entity.id
                            if group_id not in self.chat_message_cache:
                                self.chat_message_cache[group_id] = {}
                            self.chat_message_cache[group_id][phone] = {
                                'msg_id': sent_msg.id,
                                'content': script_item['message'],
                                'timestamp': time.time()
                            }

                except FloodWaitError as e:
                    self.log("自动群聊", f"[{phone[-6:]}] 频率限制，等待{e.seconds}秒")
                    self.update_account_status_by_phone(phone, '频率限制')
                    await asyncio.sleep(e.seconds)
                except ChatWriteForbiddenError:
                    self.log("自动群聊", f"[{phone[-6:]}] 发言失败: 账号被群组禁言")
                    self.update_account_status_by_phone(phone, '发言限制')
                except Exception as e:
                    self.log("自动群聊", f"[{phone[-6:]}] 发送失败: {str(e)[:50]}")
                    if "banned" in str(e).lower():
                        self.update_account_status_by_phone(phone, '发言限制')

                await asyncio.sleep(2)

            if script_pointer < len(script_queue) and script_queue[script_pointer]['phone'] == phone:
                self.log("自动群聊", f"同一账号连续发言，跳过间隔等待")
                continue

            interval = random.randint(min_interval, max_interval)
            await asyncio.sleep(interval)

        for phone, info in account_clients.items():
            try:
                await info['client'].disconnect()
            except:
                pass

    def stop_auto_chat(self):
        self.chat_stop_flag = True
        self.chat_running = False
        self.log("自动群聊", "结束炒群")

    def pause_auto_chat(self):
        if self.chat_running and not self.chat_paused:
            self.chat_paused = True
            self.log("自动群聊", "暂停炒群")

    def resume_auto_chat(self):
        if self.chat_running and self.chat_paused:
            self.chat_paused = False
            self.log("自动群聊", "继续炒群")

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

    def create_direct_login_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="直登转协议")

        main_frame = ttk.Frame(page)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        info_frame = ttk.LabelFrame(main_frame, text="账号信息")
        info_frame.pack(fill="x", padx=10, pady=5)

        phone_row = ttk.Frame(info_frame)
        phone_row.grid(row=0, column=0, columnspan=3, sticky="ew", padx=5, pady=10)

        ttk.Label(phone_row, text="手机号:", font=("微软雅黑", 10)).pack(side="left", padx=5)

        self.direct_country_code = ttk.Combobox(phone_row, values=["+86", "+1", "+44", "+91", "+81", "+82", "+84", "+63", "+60", "+62", "+66", "+852", "+853", "+886", "+7", "+49", "+33", "+39", "+34", "+61", "+55", "+52", "+82", "+971", "+966", "+65", "+64", "+31", "+46", "+41", "+47", "+45", "+358", "+46", "+47", "+41", "+43", "+32", "+36", "+420", "+421", "+48", "+351", "+353", "+30", "+90", "+972", "+98", "+92", "+880", "+94", "+977", "+856", "+855", "+95", "+371", "+372", "+370", "+373", "+355", "+356", "+389", "+381", "+382", "+383", "+387", "+385", "+386", "+374", "+994", "+995", "+996", "+992", "+993", "+998", "+380", "+375", "+359", "+40", "+27", "+234", "+254", "+233", "+256", "+250", "+251", "+237", "+225", "+226", "+228", "+229", "+227", "+235", "+236", "+242", "+241", "+243", "+244", "+245", "+248", "+249", "+252", "+253", "+257", "+258", "+260", "+261", "+262", "+263", "+264", "+265", "+266", "+267", "+268", "+269", "+290", "+291", "+297", "+298", "+299", "+350", "+351", "+352", "+353", "+354", "+355", "+356", "+357", "+358", "+359", "+370", "+371", "+372", "+373", "+374", "+375", "+376", "+377", "+378", "+379", "+380", "+381", "+382", "+383", "+385", "+386", "+387", "+389"], width=8)
        self.direct_country_code.set("+86")
        self.direct_country_code.pack(side="left", padx=2)

        self.direct_phone = ttk.Entry(phone_row, width=25, font=("微软雅黑", 11))
        self.direct_phone.pack(side="left", padx=2)

        ttk.Button(phone_row, text="📋 粘贴", command=self.paste_phone, width=8).pack(side="left", padx=2)
        ttk.Button(phone_row, text="📂 批量导入", command=self.batch_import_phones, width=10).pack(side="left", padx=2)

        path_row = ttk.Frame(info_frame)
        path_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(path_row, text="保存路径:").pack(side="left", padx=5)
        self.direct_save_path = ttk.Entry(path_row, width=45)
        self.direct_save_path.pack(side="left", padx=5)
        ttk.Button(path_row, text="浏览", command=self.select_direct_save_path, width=8).pack(side="left", padx=5)

        batch_frame = ttk.LabelFrame(info_frame, text="批量导入列表")
        batch_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        self.batch_phones_text = scrolledtext.ScrolledText(batch_frame, width=60, height=4, state="disabled")
        self.batch_phones_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.batch_phones_text.config(state="normal")
        self.batch_phones_text.insert("1.0", "每行一个手机号（带国家代码）")
        self.batch_phones_text.config(state="disabled")

        self.batch_phones = []
        self.batch_index = 0

        code_frame = ttk.LabelFrame(main_frame, text="登录验证")
        code_frame.pack(fill="x", padx=10, pady=5)

        code_row1 = ttk.Frame(code_frame)
        code_row1.pack(fill="x", padx=5, pady=5)

        ttk.Label(code_row1, text="验证码:").pack(side="left", padx=5)
        self.direct_code = ttk.Entry(code_row1, width=20, font=("微软雅黑", 11), show="●")
        self.direct_code.pack(side="left", padx=5)

        self.direct_send_code_btn = ttk.Button(code_row1, text="发送验证码", command=self.direct_send_code, width=12)
        self.direct_send_code_btn.pack(side="left", padx=5)

        self.direct_code_timer_label = ttk.Label(code_row1, text="", foreground="red")
        self.direct_code_timer_label.pack(side="left", padx=5)

        code_row2 = ttk.Frame(code_frame)
        code_row2.pack(fill="x", padx=5, pady=5)

        ttk.Label(code_row2, text="2FA密码:").pack(side="left", padx=5)
        self.direct_twofa = ttk.Entry(code_row2, width=20, font=("微软雅黑", 11), show="●")
        self.direct_twofa.pack(side="left", padx=5)
        ttk.Label(code_row2, text="（如开启了两步验证）", font=("微软雅黑", 8), foreground="gray").pack(side="left", padx=5)

        status_row = ttk.Frame(code_frame)
        status_row.pack(fill="x", padx=5, pady=5)
        self.direct_status = ttk.Label(status_row, text="就绪", foreground="blue")
        self.direct_status.pack(side="left", padx=5)

        self.direct_progress = ttk.Progressbar(code_frame, length=300, mode='determinate')
        self.direct_progress.pack(fill="x", padx=5, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)

        self.direct_login_btn = ttk.Button(btn_frame, text="🚀 登录并保存", command=self.direct_login, width=15)
        self.direct_login_btn.pack(side="left", padx=10)
        self.direct_login_btn.config(state="disabled")

        ttk.Button(btn_frame, text="⏹ 取消", command=self.direct_cancel, width=12).pack(side="left", padx=10)

        ttk.Button(btn_frame, text="📋 复制Session", command=self.direct_copy_session, width=14).pack(side="left", padx=10)

        batch_op_frame = ttk.LabelFrame(main_frame, text="批量操作")
        batch_op_frame.pack(fill="x", padx=10, pady=5)

        batch_op_row = ttk.Frame(batch_op_frame)
        batch_op_row.pack(fill="x", padx=5, pady=5)

        ttk.Label(batch_op_row, text="进度:").pack(side="left", padx=5)
        self.batch_progress_label = ttk.Label(batch_op_row, text="0/0", foreground="blue")
        self.batch_progress_label.pack(side="left", padx=5)

        ttk.Label(batch_op_row, text="成功:").pack(side="left", padx=20)
        self.batch_success_label = ttk.Label(batch_op_row, text="0", foreground="green")
        self.batch_success_label.pack(side="left", padx=5)

        ttk.Label(batch_op_row, text="失败:").pack(side="left", padx=20)
        self.batch_fail_label = ttk.Label(batch_op_row, text="0", foreground="red")
        self.batch_fail_label.pack(side="left", padx=5)

        self.batch_start_btn = ttk.Button(batch_op_row, text="▶ 批量登录", command=self.batch_direct_login, width=12)
        self.batch_start_btn.pack(side="left", padx=10)

        self.batch_stop_btn = ttk.Button(batch_op_row, text="⏹ 停止", command=self.batch_stop_login, width=8)
        self.batch_stop_btn.pack(side="left", padx=5)
        self.batch_stop_btn.config(state="disabled")

        param_row = ttk.Frame(batch_op_frame)
        param_row.pack(fill="x", padx=5, pady=5)

        ttk.Label(param_row, text="并发数:").pack(side="left", padx=5)
        self.batch_concurrent = ttk.Entry(param_row, width=8)
        self.batch_concurrent.insert(0, "2")
        self.batch_concurrent.pack(side="left", padx=5)

        ttk.Label(param_row, text="重试次数:").pack(side="left", padx=20)
        self.batch_retry = ttk.Entry(param_row, width=8)
        self.batch_retry.insert(0, "3")
        self.batch_retry.pack(side="left", padx=5)

        ttk.Label(param_row, text="重试间隔(秒):").pack(side="left", padx=20)
        self.batch_retry_interval = ttk.Entry(param_row, width=8)
        self.batch_retry_interval.insert(0, "10")
        self.batch_retry_interval.pack(side="left", padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="运行日志")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_widgets["直登转协议"] = scrolledtext.ScrolledText(log_frame, width=100, height=12)
        self.log_widgets["直登转协议"].pack(fill="both", expand=True, padx=5, pady=5)

        self.direct_client = None
        self.direct_phone_code_hash = None
        self.direct_current_phone = None
        self.direct_code_timer = None
        self.direct_code_countdown = 0
        self.direct_is_logging = False
        self.batch_is_running = False
        self.batch_stop_flag = False
        self.direct_session_path = None
        self.direct_loop = None

    def paste_phone(self):
        try:
            phone = self.root.clipboard_get().strip()
            if phone:
                self.direct_phone.delete(0, tk.END)
                self.direct_phone.insert(0, phone)
                self.log("直登转协议", f"粘贴手机号: {phone}")
        except:
            self.log("直登转协议", "粘贴失败")

    def batch_import_phones(self):
        file_path = filedialog.askopenfilename(title="选择手机号文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not file_path:
            return

        try:
            phones = []
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except:
                    continue

            if content is None:
                self.log("直登转协议", "无法识别文件编码")
                return

            for line in content.split('\n'):
                phone = line.strip()
                if phone and not phone.startswith('#'):
                    if not phone.startswith('+'):
                        phone = self.direct_country_code.get() + phone
                    phones.append(phone)

            if phones:
                self.batch_phones = phones
                self.batch_index = 0
                self.batch_phones_text.config(state="normal")
                self.batch_phones_text.delete("1.0", tk.END)
                self.batch_phones_text.insert("1.0", "\n".join(phones))
                self.batch_phones_text.config(state="disabled")
                self.log("直登转协议", f"导入 {len(phones)} 个手机号")
                self.show_centered_info("导入成功", f"成功导入 {len(phones)} 个手机号")
            else:
                self.log("直登转协议", "未找到有效手机号")
        except Exception as e:
            self.log("直登转协议", f"导入失败: {str(e)}")

    def select_direct_save_path(self):
        folder = filedialog.askdirectory(title="选择保存路径")
        if folder:
            self.direct_save_path.delete(0, tk.END)
            self.direct_save_path.insert(0, folder)
            self.log("直登转协议", f"设置保存路径: {folder}")

    def direct_send_code(self):
        if self.direct_is_logging:
            self.log("直登转协议", "登录进行中，请稍候")
            return

        phone = self.direct_phone.get().strip()
        if not phone:
            if self.batch_phones:
                phone = self.batch_phones[0] if self.batch_phones else ""
            if not phone:
                self.log("直登转协议", "请输入手机号")
                self.show_centered_warning("提示", "请输入手机号")
                return

        if not phone.startswith('+'):
            phone = self.direct_country_code.get() + phone

        self.direct_current_phone = phone
        self.direct_phone.delete(0, tk.END)
        self.direct_phone.insert(0, phone)

        self.direct_send_code_btn.config(state="disabled", text="发送中...")
        self.direct_status.config(text="发送验证码中...", foreground="orange")

        def do_send_code():
            async def send():
                try:
                    api_id = 34256693
                    api_hash = "6cb54edb306a8a938d7759b6b8fb82cf"

                    self.direct_client = TelegramClient(None, api_id, api_hash)
                    await self.direct_client.connect()

                    if not await self.direct_client.is_user_authorized():
                        result = await self.direct_client.send_code_request(phone)
                        self.direct_phone_code_hash = result.phone_code_hash
                        self.direct_status.config(text="验证码已发送", foreground="green")
                        self.log("直登转协议", f"验证码已发送至 {phone}")

                        self.start_code_timer()
                        self.root.after(0, lambda: self.direct_login_btn.config(state="normal"))
                    else:
                        self.direct_status.config(text="账号已授权", foreground="blue")
                        self.log("直登转协议", f"账号 {phone} 已授权，可直接登录")
                        self.root.after(0, lambda: self.direct_login_btn.config(state="normal"))

                except FloodWaitError as e:
                    self.direct_status.config(text=f"请等待{e.seconds}秒", foreground="red")
                    self.log("直登转协议", f"请求过于频繁，请等待{e.seconds}秒")
                except Exception as e:
                    error_msg = str(e)
                    self.direct_status.config(text=f"发送失败: {error_msg[:30]}", foreground="red")
                    self.log("直登转协议", f"发送验证码失败: {error_msg}")
                finally:
                    self.root.after(0, lambda: self.direct_send_code_btn.config(state="normal", text="发送验证码"))
                    if not self.direct_client:
                        self.direct_status.config(text="就绪", foreground="blue")

            self.direct_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.direct_loop)
            try:
                self.direct_loop.run_until_complete(send())
            finally:
                pass

        threading.Thread(target=do_send_code, daemon=True).start()

    def parse_proxy_string(self, proxy_str):
        return None

    def start_code_timer(self):
        self.direct_code_countdown = 60

        def update_timer():
            if self.direct_code_countdown <= 0:
                self.direct_code_timer_label.config(text="")
                return
            self.direct_code_timer_label.config(text=f"{self.direct_code_countdown}s")
            self.direct_code_countdown -= 1
            self.direct_code_timer = self.root.after(1000, update_timer)

        if self.direct_code_timer:
            self.root.after_cancel(self.direct_code_timer)
        update_timer()

    def direct_login(self):
        if self.direct_is_logging:
            return

        phone = self.direct_phone.get().strip()
        if not phone:
            if self.batch_phones:
                phone = self.batch_phones[0] if self.batch_phones else ""
            if not phone:
                self.log("直登转协议", "请输入手机号")
                return

        if not phone.startswith('+'):
            phone = self.direct_country_code.get() + phone

        code = self.direct_code.get().strip()
        twofa = self.direct_twofa.get().strip()
        save_path = self.direct_save_path.get().strip()

        if not save_path:
            self.log("直登转协议", "请选择保存路径")
            self.show_centered_warning("提示", "请选择保存路径")
            return

        if not self.direct_client or not self.direct_client.is_connected():
            self.log("直登转协议", "请先点击发送验证码")
            self.show_centered_warning("提示", "请先点击发送验证码")
            return

        self.direct_is_logging = True
        self.direct_login_btn.config(state="disabled", text="登录中...")
        self.direct_status.config(text="登录中...", foreground="orange")
        self.direct_progress['value'] = 30

        client = self.direct_client
        phone_code_hash = self.direct_phone_code_hash

        login_success = False

        async def login():
            nonlocal login_success
            try:
                self.direct_progress['value'] = 50

                try:
                    if code:
                        self.log("直登转协议", f"正在验证验证码...")
                        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
                        self.log("直登转协议", "验证码验证成功")
                    else:
                        me = await client.get_me()
                        self.log("直登转协议", f"账号 {phone} 已登录，昵称: {me.first_name or me.username}")
                        await self.save_direct_account(phone, save_path, client)
                        self.direct_progress['value'] = 100
                        login_success = True
                        return

                    self.direct_progress['value'] = 70

                    try:
                        me = await client.get_me()
                        self.log("直登转协议", f"登录成功！昵称: {me.first_name or me.username}")
                        await self.save_direct_account(phone, save_path, client)
                        self.direct_progress['value'] = 100
                        login_success = True
                    except SessionPasswordNeededError:
                        self.log("直登转协议", "检测到需要2FA验证(get_me阶段)")
                        if twofa:
                            self.log("直登转协议", "正在验证2FA密码...")
                            try:
                                await client.sign_in(password=twofa)
                                me = await client.get_me()
                                self.log("直登转协议", f"2FA验证成功！昵称: {me.first_name or me.username}")
                                await self.save_direct_account(phone, save_path, client)
                                self.direct_progress['value'] = 100
                                login_success = True
                            except Exception as e2:
                                error_msg = str(e2)
                                self.log("直登转协议", f"2FA验证失败: {error_msg}")
                                if "password" in error_msg.lower() or "invalid" in error_msg.lower():
                                    self.log("直登转协议", "2FA密码错误，请重新输入")
                                    self.direct_status.config(text="2FA密码错误", foreground="red")
                                    self.direct_progress['value'] = 0
                                    self.direct_twofa.delete(0, tk.END)
                                    self.direct_twofa.focus()
                                else:
                                    self.direct_status.config(text=f"2FA验证失败: {error_msg[:30]}", foreground="red")
                        else:
                            self.log("直登转协议", "需要2FA密码但未输入")
                            self.direct_status.config(text="需要2FA密码", foreground="red")
                            self.direct_progress['value'] = 0
                            self.direct_twofa.focus()
                            return

                except SessionPasswordNeededError:
                    self.log("直登转协议", "检测到需要2FA验证(sign_in阶段)")
                    if twofa:
                        self.log("直登转协议", "正在验证2FA密码...")
                        try:
                            await client.sign_in(password=twofa)
                            self.direct_progress['value'] = 85
                            me = await client.get_me()
                            self.log("直登转协议", f"2FA验证成功！昵称: {me.first_name or me.username}")
                            await self.save_direct_account(phone, save_path, client)
                            self.direct_progress['value'] = 100
                            login_success = True
                        except Exception as e2:
                            error_msg = str(e2)
                            self.log("直登转协议", f"2FA验证失败: {error_msg}")
                            if "password" in error_msg.lower() or "invalid" in error_msg.lower():
                                self.log("直登转协议", "2FA密码错误，请重新输入")
                                self.direct_status.config(text="2FA密码错误", foreground="red")
                                self.direct_progress['value'] = 0
                                self.direct_twofa.delete(0, tk.END)
                                self.direct_twofa.focus()
                            else:
                                self.direct_status.config(text=f"2FA验证失败: {error_msg[:30]}", foreground="red")
                    else:
                        self.log("直登转协议", "需要2FA密码但未输入")
                        self.direct_status.config(text="需要2FA密码", foreground="red")
                        self.direct_progress['value'] = 0
                        self.direct_twofa.focus()
                        return

                except Exception as e1:
                    error_msg = str(e1)
                    if "phone_code" in error_msg.lower() or "code" in error_msg.lower() or "invalid" in error_msg.lower():
                        if "phone_code" in error_msg.lower() or "code" in error_msg.lower():
                            self.log("直登转协议", f"验证码错误: {error_msg}")
                            self.direct_status.config(text="验证码错误", foreground="red")
                            self.direct_progress['value'] = 0
                            self.direct_code.delete(0, tk.END)
                            self.direct_code.focus()
                        else:
                            raise e1
                    else:
                        raise e1

            except PhoneNumberBannedError:
                self.log("直登转协议", "手机号已被封禁")
                self.direct_status.config(text="手机号被封禁", foreground="red")
                self.direct_progress['value'] = 0
            except UserDeactivatedError:
                self.log("直登转协议", "账号已注销")
                self.direct_status.config(text="账号已注销", foreground="red")
                self.direct_progress['value'] = 0
            except FloodWaitError as e:
                self.log("直登转协议", f"请求频繁，请等待{e.seconds}秒")
                self.direct_status.config(text=f"等待{e.seconds}秒", foreground="red")
                self.direct_progress['value'] = 0
            except Exception as e:
                error_msg = str(e)
                self.log("直登转协议", f"登录失败: {error_msg}")
                self.direct_status.config(text=f"登录失败: {error_msg[:30]}", foreground="red")
                self.direct_progress['value'] = 0
            finally:
                self.direct_is_logging = False
                self.root.after(0, lambda: self.direct_login_btn.config(state="normal", text="🚀 登录并保存"))

                if login_success or "需要2FA" not in self.direct_status.cget("text"):
                    self.direct_progress['value'] = 0
                    if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
                        try:
                            if not self.direct_loop.is_running():
                                self.direct_loop.close()
                                self.direct_loop = None
                        except:
                            self.direct_loop = None

        if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
            try:
                self.direct_loop.run_until_complete(login())
            except RuntimeError as e:
                error_msg = str(e)
                self.log("直登转协议", f"事件循环错误，重新创建: {error_msg}")
                self.direct_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.direct_loop)
                try:
                    self.direct_loop.run_until_complete(login())
                finally:
                    if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
                        try:
                            if not self.direct_loop.is_running():
                                self.direct_loop.close()
                                self.direct_loop = None
                        except:
                            self.direct_loop = None
            except Exception as e:
                self.log("直登转协议", f"执行异常: {str(e)}")
                if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
                    try:
                        if not self.direct_loop.is_running():
                            self.direct_loop.close()
                            self.direct_loop = None
                    except:
                        self.direct_loop = None
        else:
            self.direct_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.direct_loop)
            try:
                self.direct_loop.run_until_complete(login())
            finally:
                if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
                    try:
                        if not self.direct_loop.is_running():
                            self.direct_loop.close()
                            self.direct_loop = None
                    except:
                        self.direct_loop = None

    async def save_direct_account(self, phone, save_path, client=None):
        try:
            if client is None:
                client = self.direct_client

            me = await client.get_me()
            self.log("直登转协议", f"当前用户: {me.first_name} (ID: {me.id})")

            api_id = 34256693
            api_hash = "6cb54edb306a8a938d7759b6b8fb82cf"

            session_file = os.path.join(save_path, f"{phone}.session")
            json_file = os.path.join(save_path, f"{phone}.json")

            from telethon.sessions import StringSession
            from telethon.crypto import AuthKey

            auth_key_bytes = None
            dc_id = None
            server_address = None
            port = None

            if client.session:
                if hasattr(client.session, 'dc_id'):
                    dc_id = client.session.dc_id
                if hasattr(client.session, 'server_address'):
                    server_address = client.session.server_address
                if hasattr(client.session, 'port'):
                    port = client.session.port

                if hasattr(client.session, 'auth_key'):
                    auth_key = client.session.auth_key
                    if auth_key:
                        if isinstance(auth_key, AuthKey):
                            auth_key_bytes = auth_key.key
                        elif isinstance(auth_key, bytes):
                            auth_key_bytes = auth_key

            if not auth_key_bytes:
                raise Exception("无法获取auth_key，请检查登录状态")

            self.log("直登转协议", f"auth_key长度: {len(auth_key_bytes)} 字节")

            string_session = StringSession()
            if dc_id is not None:
                string_session._dc_id = dc_id
            if server_address:
                string_session._server_address = server_address
            if port is not None:
                string_session._port = port

            auth_key_obj = AuthKey(auth_key_bytes)
            string_session._auth_key = auth_key_obj

            session_str = string_session.save()

            if session_str:
                with open(session_file, 'w', encoding='utf-8') as f:
                    f.write(session_str)
                self.log("直登转协议", f"✅ Session保存成功: {session_file}")
                self.log("直登转协议", f"Session字符串长度: {len(session_str)}")
            else:
                raise Exception("StringSession导出失败")

            twofa = self.direct_twofa.get().strip()
            account_info = {
                "phone": phone,
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "username": me.username or "",
                "register_time": me.date.timestamp() if hasattr(me, 'date') else 0,
                "twoFA": twofa,
                "app_id": api_id,
                "app_hash": api_hash
            }

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(account_info, f, ensure_ascii=False, indent=2)

            self.log("直登转协议", f"✅ JSON保存成功: {json_file}")
            self.direct_status.config(text="保存成功", foreground="green")
            self.direct_session_path = session_file

            try:
                self.log("直登转协议", "验证保存的session...")
                from telethon.sessions import StringSession
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_str = f.read()
                test_session = StringSession(session_str)
                test_client = TelegramClient(test_session, api_id, api_hash)
                await test_client.connect()
                if await test_client.is_user_authorized():
                    test_me = await test_client.get_me()
                    self.log("直登转协议", f"✅ Session验证成功: {test_me.first_name}")
                else:
                    self.log("直登转协议", "⚠️ Session验证失败: 未授权")
                await test_client.disconnect()
            except Exception as e:
                self.log("直登转协议", f"⚠️ Session验证异常: {str(e)}")

            self.add_account_from_session(phone, session_file, json_file, account_info)

            self.show_centered_info("成功", f"账号 {phone} 已成功转为协议号并保存\n\nSession: {session_file}\nJSON: {json_file}")

        except Exception as e:
            error_msg = str(e)
            self.log("直登转协议", f"保存失败: {error_msg}")
            raise e

    def add_account_from_session(self, phone, session_path, json_path, account_info):
        for acc in self.accounts:
            if acc.get('phone') == phone:
                self.log("直登转协议", f"账号 {phone} 已存在于列表中，更新信息")
                acc['session_path'] = session_path
                acc['json_path'] = json_path
                acc['account_info'] = account_info
                acc['nickname'] = account_info.get('first_name', '') or phone
                acc['status'] = '正常'
                self.refresh_account_list_filter()
                self.save_config()
                return

        nickname = account_info.get('first_name', '') or phone
        if account_info.get('last_name'):
            nickname = f"{nickname} {account_info.get('last_name')}"

        self.accounts.append({
            "phone": phone,
            "nickname": nickname.strip() or phone,
            "group": "默认分组",
            "status": "正常",
            "current_task": "",
            "last_action": "直登转协议",
            "register_time": datetime.now().strftime("%Y-%m-%d"),
            "session_path": session_path,
            "json_path": json_path,
            "account_info": account_info,
            "proxy": ""
        })

        self.refresh_account_list_filter()
        self.refresh_scrape_accounts()
        self.refresh_invite_group_filter()
        self.save_config()
        self.log("直登转协议", f"账号 {phone} 已添加到列表")

    def direct_cancel(self):
        if self.direct_client and self.direct_client.is_connected():
            async def do_disconnect():
                await self.direct_client.disconnect()
            try:
                if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
                    self.direct_loop.run_until_complete(do_disconnect())
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(do_disconnect())
                    loop.close()
            except:
                pass

        self.direct_client = None
        self.direct_phone_code_hash = None
        self.direct_status.config(text="已取消", foreground="gray")
        self.direct_login_btn.config(state="disabled")
        self.direct_send_code_btn.config(state="normal", text="发送验证码")
        self.direct_is_logging = False
        self.direct_progress['value'] = 0

        if hasattr(self, 'direct_loop') and self.direct_loop and not self.direct_loop.is_closed():
            try:
                self.direct_loop.close()
            except:
                pass
            self.direct_loop = None

        if self.direct_code_timer:
            self.root.after_cancel(self.direct_code_timer)
            self.direct_code_timer_label.config(text="")

        self.log("直登转协议", "操作已取消")

    def direct_copy_session(self):
        if self.direct_session_path and os.path.exists(self.direct_session_path):
            self.root.clipboard_clear()
            self.root.clipboard_append(self.direct_session_path)
            self.log("直登转协议", f"已复制Session路径: {self.direct_session_path}")
            self.show_centered_info("已复制", f"Session路径已复制到剪贴板:\n{self.direct_session_path}")
        else:
            self.log("直登转协议", "没有可复制的Session")
            self.show_centered_warning("提示", "请先登录并保存账号")

    def batch_direct_login(self):
        if not self.batch_phones:
            self.log("直登转协议", "请先导入手机号列表")
            self.show_centered_warning("提示", "请先导入手机号列表")
            return

        save_path = self.direct_save_path.get().strip()
        if not save_path:
            self.log("直登转协议", "请选择保存路径")
            self.show_centered_warning("提示", "请选择保存路径")
            return

        try:
            concurrent = int(self.batch_concurrent.get())
            retry_count = int(self.batch_retry.get())
            retry_interval = int(self.batch_retry_interval.get())
        except ValueError:
            self.log("直登转协议", "参数错误")
            return

        if concurrent <= 0:
            concurrent = 1

        self.batch_is_running = True
        self.batch_stop_flag = False
        self.batch_start_btn.config(state="disabled")
        self.batch_stop_btn.config(state="normal")

        self.batch_success_count = 0
        self.batch_fail_count = 0
        self.batch_total = len(self.batch_phones)
        self.batch_index = 0

        self.batch_progress_label.config(text=f"0/{self.batch_total}")
        self.batch_success_label.config(text="0")
        self.batch_fail_label.config(text="0")

        self.log("直登转协议", f"========== 开始批量登录 ==========")
        self.log("直登转协议", f"总手机号: {self.batch_total} | 并发数: {concurrent} | 重试: {retry_count}次")

        def do_batch_login():
            import concurrent.futures

            def process_phone(phone_data):
                phone, retry = phone_data
                if self.batch_stop_flag:
                    return None

                for attempt in range(retry + 1):
                    if self.batch_stop_flag:
                        return None

                    self.log("直登转协议", f"处理: {phone} (尝试 {attempt + 1}/{retry + 1})")

                    result = self.direct_login_single(phone, save_path)
                    if result == "success":
                        return "success"
                    elif result == "skip":
                        return "skip"
                    elif attempt < retry:
                        self.log("直登转协议", f"等待 {retry_interval} 秒后重试...")
                        time.sleep(retry_interval)

                return "fail"

            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
                futures = []
                for phone in self.batch_phones:
                    if self.batch_stop_flag:
                        break
                    futures.append(executor.submit(process_phone, (phone, retry_count)))

                for future in concurrent.futures.as_completed(futures):
                    if self.batch_stop_flag:
                        break
                    result = future.result()
                    if result == "success":
                        self.batch_success_count += 1
                    elif result == "fail":
                        self.batch_fail_count += 1

                    self.batch_index += 1
                    self.root.after(0, self.update_batch_progress)

            self.batch_is_running = False
            self.root.after(0, self.batch_complete)

        threading.Thread(target=do_batch_login, daemon=True).start()

    def direct_login_single(self, phone, save_path):
        try:
            api_id = 34256693
            api_hash = "6cb54edb306a8a938d7759b6b8fb82cf"

            async def do_login():
                client = None
                try:
                    client = TelegramClient(None, api_id, api_hash)
                    await client.connect()

                    if await client.is_user_authorized():
                        self.log("直登转协议", f"[{phone}] 账号已授权")
                        await client.disconnect()
                        return "skip"

                    result = await client.send_code_request(phone)
                    phone_code_hash = result.phone_code_hash

                    self.log("直登转协议", f"[{phone}] 验证码已发送，请手动输入或使用自动接码")

                    code = simpledialog.askstring("输入验证码", f"请输入 {phone} 的验证码:", parent=self.root)

                    if not code:
                        self.log("直登转协议", f"[{phone}] 用户取消或未输入验证码")
                        await client.disconnect()
                        return "fail"

                    await client.sign_in(phone, code, phone_code_hash=phone_code_hash)

                    try:
                        me = await client.get_me()
                    except SessionPasswordNeededError:
                        twofa = simpledialog.askstring("2FA密码", f"请输入 {phone} 的2FA密码:", parent=self.root, show="*")
                        if twofa:
                            await client.sign_in(password=twofa)
                        else:
                            self.log("直登转协议", f"[{phone}] 未输入2FA密码")
                            await client.disconnect()
                            return "fail"

                    me = await client.get_me()

                    session_file = os.path.join(save_path, f"{phone}.session")
                    await client.disconnect()

                    client2 = TelegramClient(session_file, api_id, api_hash)
                    await client2.connect()

                    if code:
                        await client2.sign_in(phone, code, phone_code_hash=phone_code_hash)
                    else:
                        await client2.sign_in(phone)

                    if twofa:
                        try:
                            await client2.sign_in(password=twofa)
                        except:
                            pass

                    me = await client2.get_me()

                    json_file = os.path.join(save_path, f"{phone}.json")
                    account_info = {
                        "phone": phone,
                        "first_name": me.first_name or "",
                        "last_name": me.last_name or "",
                        "username": me.username or "",
                        "register_time": me.date.timestamp() if hasattr(me, 'date') else 0,
                        "twoFA": twofa if twofa else "",
                        "app_id": api_id,
                        "app_hash": api_hash
                    }

                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(account_info, f, ensure_ascii=False, indent=2)

                    await client2.disconnect()

                    self.root.after(0, lambda: self.add_account_from_session(phone, session_file, json_file, account_info))

                    self.log("直登转协议", f"[{phone}] ✅ 登录成功并保存")
                    return "success"

                except FloodWaitError as e:
                    self.log("直登转协议", f"[{phone}] 频率限制，等待{e.seconds}秒")
                    await asyncio.sleep(e.seconds)
                    return "fail"
                except Exception as e:
                    self.log("直登转协议", f"[{phone}] 登录失败: {str(e)}")
                    return "fail"
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
            return result

        except Exception as e:
            self.log("直登转协议", f"[{phone}] 异常: {str(e)}")
            return "fail"

    def update_batch_progress(self):
        self.batch_progress_label.config(text=f"{self.batch_index}/{self.batch_total}")
        self.batch_success_label.config(text=str(self.batch_success_count))
        self.batch_fail_label.config(text=str(self.batch_fail_count))
        self.root.update_idletasks()

    def batch_complete(self):
        self.batch_start_btn.config(state="normal")
        self.batch_stop_btn.config(state="disabled")
        self.log("直登转协议", f"========== 批量登录完成 ==========")
        self.log("直登转协议", f"总计: {self.batch_total} | 成功: {self.batch_success_count} | 失败: {self.batch_fail_count}")
        self.show_centered_info("批量完成", f"总计: {self.batch_total}\n成功: {self.batch_success_count}\n失败: {self.batch_fail_count}")

    def batch_stop_login(self):
        self.batch_stop_flag = True
        self.batch_start_btn.config(state="normal")
        self.batch_stop_btn.config(state="disabled")
        self.log("直登转协议", "停止批量登录")

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
            self.refresh_account_list_filter()
            self.refresh_proxy_list()
            self.refresh_scrape_accounts()
            self.refresh_invite_group_filter()
            statuses = set(["全部"])
            for acc in self.accounts:
                status = acc.get('status', '待检测')
                statuses.add(status)
            self.account_list_status_filter['values'] = list(statuses)
            self.log("多账号管理", "配置已导入")

    def about(self):
        self.show_centered_info("关于", "良子TG全能营销系统\n联系@Liangzi1952\n版本: 2.0\n\n功能：\n- 多账号管理\n- 代理IP管理\n- 采集群成员\n- 批量拉人\n- 群发广告\n- 自动群聊+回复\n- 自动注册\n- 监听群组\n- 直登转协议")

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
