import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import json
import threading
import os
import time
from datetime import datetime

SERVER = "http://172.98.23.64:5000"

class TelegramFullGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram 全能营销系统 v3.0")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.create_server_page()
        self.create_account_page()
        self.create_scrape_page()
        self.create_invite_page()
        self.create_group_chat_page()
        self.create_auto_register_page()
        self.create_monitor_page()
        self.create_script_page()
        self.create_log_page()
        
        self.running_tasks = {}
        self.accounts = []
        self.keywords = {}
        
        self.log("系统启动完成")
    
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
    
    def create_account_page(self):
        page = ttk.Frame(self.notebook)
        self.notebook.add(page, text="多账号管理")
        
        frame = ttk.LabelFrame(page, text="账号列表")
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("序号", "手机号", "状态")
        self.account_tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.account_tree.heading(col, text=col)
            self.account_tree.column(col, width=120)
        self.account_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="添加账号", command=self.add_account).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="删除账号", command=self.del_account).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="导入账号", command=self.import_accounts).pack(side="left", padx=5)
        
        freq_frame = ttk.LabelFrame(page, text="频率控制（防风控）")
        freq_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(freq_frame, text="发言间隔(秒):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.chat_delay = ttk.Entry(freq_frame, width=10)
        self.chat_delay.insert(0, "30")
        self.chat_delay.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(freq_frame, text="拉人间隔(秒):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.invite_delay = ttk.Entry(freq_frame, width=10)
        self.invite_delay.insert(0, "60")
        self.invite_delay.grid(row=0, column=3, padx=5, pady=5)
    
    def add_account(self):
        phone = messagebox.askstring("添加账号", "请输入手机号:")
        if phone:
            self.accounts.append({"phone": phone, "status": "未登录"})
            self.refresh_account_list()
            self.log(f"添加账号: {phone}")
    
    def del_account(self):
        selected = self.account_tree.selection()
        if selected:
            for item in selected:
                idx = int(self.account_tree.item(item)['values'][0]) - 1
                self.accounts.pop(idx)
            self.refresh_account_list()
            self.log("删除账号")
    
    def import_accounts(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.log(f"导入账号文件: {file_path}")
    
    def refresh_account_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        for i, acc in enumerate(self.accounts, 1):
            self.account_tree.insert("", "end", values=(i, acc['phone'], acc['status']))
    
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
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
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
        self.keywords = json.loads(content) if content.strip() else {}
        with open("keywords.json", "w", encoding="utf-8") as f:
            json.dump(self.keywords, f, ensure_ascii=False, indent=2)
        self.log(f"保存 {len(self.keywords)} 个关键词规则")
    
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
        messagebox.showinfo("提示", "批量注册功能需要对接具体接码平台API")
    
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
        messagebox.showinfo("提示", "监听功能需要服务器端支持实时消息推送")
    
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

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramFullGUI(root)
    root.mainloop()
