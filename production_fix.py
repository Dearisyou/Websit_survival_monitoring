#!/usr/bin/env python3
"""
生产环境修复脚本
解决密码输入无反应问题
"""

import os
import sys

def check_environment():
    """检查生产环境配置"""
    print("=== 生产环境诊断 ===")
    
    # 检查环境变量
    flask_env = os.environ.get('FLASK_ENV', 'development')
    secret_key = os.environ.get('SECRET_KEY')
    
    print(f"FLASK_ENV: {flask_env}")
    print(f"SECRET_KEY: {'已设置' if secret_key else '未设置'}")
    
    # 检查HTTPS
    if flask_env == 'production':
        print("⚠️  生产环境建议使用HTTPS")
        print("   如果使用HTTP，请设置 FLASK_ENV=development")
    
    # 检查文件权限
    try:
        with open('monitor.db', 'r') as f:
            print("✅ 数据库文件可读")
    except:
        print("❌ 数据库文件不可读")
    
    # 检查密码文件
    if os.path.exists('admin_password.txt'):
        print("✅ 管理员密码文件存在")
        with open('admin_password.txt', 'r') as f:
            print(f"   内容: {f.read().strip()}")
    else:
        print("❌ 管理员密码文件不存在")

def fix_production():
    """修复生产环境问题"""
    print("\n=== 修复建议 ===")
    
    # 1. 环境变量设置
    print("1. 设置环境变量:")
    print("   export FLASK_ENV=development  # 如果不使用HTTPS")
    print("   export SECRET_KEY=your-random-secret-key")
    
    # 2. 启动命令
    print("\n2. 推荐启动命令:")
    print("   # 开发环境")
    print("   python run.py")
    print("   # 生产环境(使用gunicorn)")
    print("   gunicorn -w 4 -b 0.0.0.0:5000 run:app")
    
    # 3. 防火墙设置
    print("\n3. 防火墙设置:")
    print("   # 开放5000端口")
    print("   sudo ufw allow 5000")
    
    # 4. 权限设置
    print("\n4. 文件权限:")
    print("   chmod 644 monitor.db")
    print("   chmod 644 admin_password.txt")

if __name__ == "__main__":
    check_environment()
    fix_production()