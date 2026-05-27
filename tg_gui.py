import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import os

SERVER = "http://172.98.23.64:5000"

class TelegramBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram 控制端 v2.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 服务器配置框架
        frame_server = tk.LabelFrame(root, text="服务器配置", padx=10, pady=5)
        frame_server.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_server, text="服务器地址:").grid(row=0, column=0, sticky="w")
        self.server_entry = tk.Entry(frame_server, width=40)
        self.server_entry.insert(0, SERVER)
        self.server_entry.grid(row=0, column=1, padx=5)
        
        self.status_btn = tk.Button(frame_server, text="测试连接", command=self.test_connection)
        self.status_btn.grid(row=0, column=2, padx=5)
        
        self.status_label = tk.Label(frame_server, text="未连接", fg="red")
        self.status_label.grid(row=0, column=3, padx=10)
        
        # 登录框架
        frame_login = tk.LabelFrame(root, text="登录", padx=10, pady=5)
        frame_login.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_login, text="验证码:").grid(row=0, column=0, sticky="w")
        self.code_entry = tk.Entry(frame_login, width=20)
        self.code_entry.grid(row=0, column=1, padx=5)
        
        self.login_btn = tk.Button(frame_login, text="发送验证码", command=self.send_code)
        self.login_btn.grid(row=0, column=2, padx=5)
        
        self.login_status = tk.Label(frame_login, text="未登录", fg="red")
        self.login_status.grid(row=0, column=3, padx=10)
        
        # 采集框架
        frame_scrape = tk.LabelFrame(root, text="采集群成员", padx=10, pady=5)
        frame_scrape.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_scrape, text="群组链接:").grid(row=0, column=0, sticky="w")
        self.group_entry = tk.Entry(frame_scrape, width=40)
        self.group_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(frame_scrape, text="数量:").grid(row=1, column=0, sticky="w")
        self.limit_entry = tk.Entry(frame_scrape, width=10)
        self.limit_entry.insert(0, "200")
        self.limit_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        self.scrape_btn = tk.Button(frame_scrape, text="开始采集", command=self.scrape_members)
        self.scrape_btn.grid(row=1, column=2, padx=5)
        
        # 群发框架
        frame_send = tk.LabelFrame(root, text="批量发送私信", padx=10, pady=5)
        frame_send.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_send, text="消息内容:").grid(row=0, column=0, sticky="nw")
        self.message_text = scrolledtext.ScrolledText(frame_send, width=50, height=4)
        self.message_text.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame_send, text="间隔(秒):").grid(row=1, column=0, sticky="w")
        self.delay_entry = tk.Entry(frame_send, width=10)
        self.delay_entry.insert(0, "30")
        self.delay_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        self.send_btn = tk.Button(frame_send, text="开始发送", command=self.batch_send)
        self.send_btn.grid(row=1, column=2, padx=5)
        
        # 日志框架
        frame_log = tk.LabelFrame(root, text="运行日志", padx=10, pady=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(frame_log, width=80, height=10)
        self.log_text.pack(fill="both", expand=True)
        
        self.log("程序已启动")
        
    def log(self, msg):
        """添加日志"""
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def call_api(self, endpoint, data=None):
        """调用API"""
        server = self.server_entry.get()
        url = f"{server}{endpoint}"
        try:
            if data:
                resp = requests.post(url, json=data, timeout=60, proxies={"http": None, "https": None})
            else:
                resp = requests.get(url, timeout=10, proxies={"http": None, "https": None})
            return resp.json()
        except Exception as e:
            self.log(f"API错误: {e}")
            return None
    
    def test_connection(self):
        """测试连接"""
        self.log("正在测试连接...")
        result = self.call_api("/status")
        if result:
            self.status_label.config(text="已连接", fg="green")
            self.log(f"✅ 连接成功: {result}")
        else:
            self.status_label.config(text="连接失败", fg="red")
            self.log("❌ 连接失败，请检查服务器")
    
    def send_code(self):
        """发送验证码"""
        self.log("正在发送验证码...")
        result = self.call_api("/login", {})
        if result and result.get("status") == "code_sent":
            self.log("✅ 验证码已发送到Telegram")
            code = self.code_entry.get()
            if code:
                self.verify_code(code)
        else:
            self.log("❌ 发送失败")
    
    def verify_code(self, code):
        """验证验证码"""
        self.log(f"正在验证: {code}")
        result = self.call_api("/login", {"code": code})
        if result and result.get("status") == "success":
            self.login_status.config(text=f"已登录: {result['user']}", fg="green")
            self.log(f"✅ 登录成功: {result['user']}")
        else:
            self.log("❌ 登录失败")
    
    def scrape_members(self):
        """采集成员"""
        group = self.group_entry.get()
        limit = self.limit_entry.get()
        
        if not group:
            self.log("❌ 请输入群组链接")
            return
        
        self.log(f"正在采集: {group} (数量: {limit})")
        self.scrape_btn.config(state="disabled")
        
        def do_scrape():
            result = self.call_api("/scrape", {"group": group, "limit": int(limit)})
            if result:
                members = result.get("members", [])
                self.log(f"✅ 采集到 {len(members)} 个成员")
                with open("members.json", "w", encoding="utf-8") as f:
                    json.dump(members, f, ensure_ascii=False, indent=2)
                self.log("💾 已保存到 members.json")
            else:
                self.log("❌ 采集失败")
            self.scrape_btn.config(state="normal")
        
        threading.Thread(target=do_scrape, daemon=True).start()
    
    def batch_send(self):
        """批量发送"""
        msg = self.message_text.get("1.0", tk.END).strip()
        delay = self.delay_entry.get()
        
        if not msg:
            self.log("❌ 请输入消息内容")
            return
        
        if not os.path.exists("members.json"):
            self.log("❌ 请先采集成员")
            return
        
        with open("members.json", "r") as f:
            members = json.load(f)
        
        self.log(f"正在发送给 {len(members)} 人...")
        self.send_btn.config(state="disabled")
        
        def do_send():
            result = self.call_api("/batch_send", {
                "members": members,
                "message": msg,
                "delay": int(delay)
            })
            if result:
                self.log(f"✅ 成功: {result['success']}, ❌ 失败: {result['fail']}")
            else:
                self.log("❌ 发送失败")
            self.send_btn.config(state="normal")
        
        threading.Thread(target=do_send, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramBotGUI(root)
    root.mainloop()