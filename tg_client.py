import requests
import json
import os

# 服务器地址（改成你的服务器IP）
SERVER = "http://172.98.23.64:5000"

def call_api(endpoint, data=None):
    url = f"{SERVER}{endpoint}"
    try:
        if data:
            resp = requests.post(url, json=data, timeout=60)
        else:
            resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception as e:
        print(f"连接失败: {e}")
        return None

def login():
    print("📱 发送验证码到Telegram...")
    result = call_api("/login", {})
    if result and result.get("status") == "code_sent":
        code = input("请输入验证码: ")
        result2 = call_api("/login", {"code": code})
        if result2 and result2.get("status") == "success":
            print(f"✅ 登录成功: {result2['user']}")
            return True
    return False

def scrape_group():
    group = input("群组链接 (如 https://t.me/xxx): ")
    limit = input("采集数量 (默认200): ")
    limit = int(limit) if limit else 200
    
    print(f"🔍 采集中...")
    result = call_api("/scrape", {"group": group, "limit": limit})
    if result:
        members = result.get("members", [])
        print(f"✅ 采集到 {len(members)} 个成员")
        with open("members.json", "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=2)
        print("💾 已保存到 members.json")
        print("\n前5个成员:")
        for i, m in enumerate(members[:5], 1):
            name = m.get('first_name') or m.get('username') or str(m.get('id'))
            print(f"  {i}. {name}")

def batch_send():
    if not os.path.exists("members.json"):
        print("❌ 请先采集成员")
        return
    
    with open("members.json", "r") as f:
        members = json.load(f)
    
    print(f"📋 当前成员列表: {len(members)} 人")
    msg = input("消息内容: ")
    delay = input("间隔秒数 (默认30): ")
    delay = int(delay) if delay else 30
    
    print(f"📨 发送给 {len(members)} 人...")
    result = call_api("/batch_send", {
        "members": members,
        "message": msg,
        "delay": delay
    })
    if result:
        print(f"✅ 成功: {result['success']}")
        print(f"❌ 失败: {result['fail']}")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 50)
    print("🤖 Telegram 控制端 v1.0")
    print(f"📡 服务器: {SERVER}")
    print("=" * 50)
    
    # 检查连接
    print("正在连接服务器...")
    status = call_api("/status")
    if status is None:
        print("❌ 无法连接服务器")
        input("按回车退出...")
        return
    print(f"✅ 服务器状态: {status.get('status')}")
    
    # 登录
    need_login = input("\n是否需要登录? (y/n): ").strip().lower()
    if need_login == 'y':
        if not login():
            print("❌ 登录失败")
            input("按回车退出...")
            return
    
    while True:
        print("\n" + "-" * 40)
        print("📋 功能菜单:")
        print("  1. 采集群成员")
        print("  2. 批量发送私信")
        print("  3. 退出")
        print("-" * 40)
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == "1":
            scrape_group()
        elif choice == "2":
            batch_send()
        elif choice == "3":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择")
        
        input("\n按回车继续...")

if __name__ == "__main__":
    main()
