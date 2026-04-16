import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ========== 1. 注册 ==========
print("=" * 60)
print("1. 注册用户")
print("=" * 60)
start = time.time()
r = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "testuser",
    "email": "test@test.com",
    "password": "12345678",
    "security_answer": "绿萝",
    "location_city": "北京"
})
print(f"状态码: {r.status_code}")
print(f"响应: {r.json()}")
print(f"耗时: {(time.time() - start) * 1000:.2f}ms\n")

# ========== 2. 登录 ==========
print("=" * 60)
print("2. 登录获取 Token")
print("=" * 60)
start = time.time()
r = requests.post(f"{BASE_URL}/auth/login", json={
    "account": "testuser",
    "password": "12345678"
})
print(f"状态码: {r.status_code}")
print(f"响应: {r.json()}")

if r.status_code != 200:
    print("❌ 登录失败，请检查用户名密码")
    exit()

data = r.json()
token = data["data"]["access_token"]
print(f"✅ 获取到 Token: {token[:50]}...")
print(f"耗时: {(time.time() - start) * 1000:.2f}ms\n")

# 确保 headers 格式正确
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# ========== 3. 创建植物 ==========
print("=" * 60)
print("3. 创建植物")
print("=" * 60)
start = time.time()
r = requests.post(f"{BASE_URL}/plants",
                  headers=headers,
                  json={
                      "nickname": "小绿",
                      "species": "绿萝",
                      "water_cycle": 7,
                      "fertilize_cycle": 30
                  })
print(f"状态码: {r.status_code}")
print(f"响应: {r.json()}")

if r.status_code != 200:
    print("❌ 创建植物失败")
    exit()

plant_id = r.json()["data"]["plant_id"]
print(f"✅ 植物 ID: {plant_id}")
print(f"耗时: {(time.time() - start) * 1000:.2f}ms\n")

# ========== 4. 获取智能提醒列表 ==========
print("=" * 60)
print("4. 获取智能提醒列表（个性化养护提醒）")
print("=" * 60)
start = time.time()

# 直接使用 /reminders 路径
url = f"{BASE_URL}/reminders"
print(f"请求 URL: {url}")
print(f"请求 Headers: {headers}")

try:
    r = requests.get(url, headers=headers)
    print(f"状态码: {r.status_code}")
    print(f"响应内容: {r.text}")

    if r.status_code == 200:
        data = r.json()
        if data.get("code") == 200:
            reminder_data = data["data"]

            print(f"\n📊 环境信息:")
            print(f"   🌡️  当前空气湿度: {reminder_data.get('current_humidity', 'N/A')}%")
            print(f"   💧 湿度级别: {reminder_data.get('humidity_level', 'N/A')}")
            print(f"   📋 提醒总数: {reminder_data.get('total', 0)}")

            print(f"\n{'=' * 60}")
            print("🎯 个性化提醒详情")
            print(f"{'=' * 60}")

            for idx, reminder in enumerate(reminder_data.get('reminders', []), 1):
                print(f"\n【提醒 {idx}】")
                print(f"   🌿 植物名称: {reminder['plant_name']}")
                print(f"   📌 提醒类型: {'💧 浇水' if reminder['type'] == 'water' else '🌱 施肥'}")
                print(f"   ⚡ 紧急程度: {reminder['urgency']}")
                print(f"   📅 逾期天数: {reminder['days_overdue']}天")
                print(f"   🗓️  建议日期: {reminder['due_date']}")
                print(f"   🔔 标准提醒: {reminder['message']}")
                print(f"   🎯 AI个性化提醒: {reminder['ai_message']}")
                print(f"   🎨 图标: {reminder['icon']}")

                if reminder['type'] == 'water':
                    print(f"\n   📊 动态周期分析:")
                    print(f"      基础周期: {reminder.get('base_cycle', 'N/A')}天")
                    print(f"      动态周期: {reminder.get('dynamic_cycle', 'N/A')}天")
                    print(f"      调整原因: {reminder.get('adjustment_reason', 'N/A')}")
                    print(f"      养护建议: {reminder.get('recommendation', 'N/A')}")
                    print(f"      浇水质量: {reminder.get('quality_advice', 'N/A')}")

            # 打印完整 JSON
            print(f"\n{'=' * 60}")
            print("📄 完整返回数据（JSON格式）")
            print(f"{'=' * 60}")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"响应异常: {data}")
    elif r.status_code == 422:
        print(f"❌ 422 错误，可能需要额外参数")
        print(f"错误详情: {r.text}")

        # 尝试带空参数
        print("\n尝试带空参数...")
        r2 = requests.get(url, headers=headers, params={})
        print(f"状态码: {r2.status_code}")
        if r2.status_code == 200:
            print("✅ 带空参数成功！")
            print(json.dumps(r2.json(), ensure_ascii=False, indent=2))
    else:
        print(f"❌ 请求失败: {r.status_code}")
        print(f"响应: {r.text}")

except Exception as e:
    print(f"请求异常: {e}")

print(f"\n⏱️  耗时: {(time.time() - start) * 1000:.2f}ms\n")

# ========== 5. 浇水打卡 ==========
print("=" * 60)
print("5. 浇水打卡")
print("=" * 60)
start = time.time()
r = requests.post(f"{BASE_URL}/plants/{plant_id}/water",
                  headers=headers)
print(f"状态码: {r.status_code}")
print(f"响应: {r.json()}")
print(f"耗时: {(time.time() - start) * 1000:.2f}ms\n")

# ========== 6. 再次获取提醒 ==========
print("=" * 60)
print("6. 打卡后再次获取提醒")
print("=" * 60)
start = time.time()
r = requests.get(f"{BASE_URL}/reminders", headers=headers)
print(f"状态码: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    if data.get("code") == 200:
        total = data["data"]["total"]
        print(f"提醒总数: {total}")
        if total == 0:
            print("✅ 浇水打卡成功，浇水提醒已消失")
        else:
            print(f"⚠️ 仍有 {total} 条提醒")
print(f"耗时: {(time.time() - start) * 1000:.2f}ms\n")



print("=" * 60)
print("✅ 测试完成")
print("=" * 60)