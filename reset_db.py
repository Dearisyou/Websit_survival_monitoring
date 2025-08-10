#!/usr/bin/env python3
"""
数据库重置脚本
如果遇到数据库结构问题，运行此脚本重新创建数据库
"""

import os
from app import create_app, db

def reset_database():
    app = create_app()
    
    with app.app_context():
        # 删除现有数据库文件
        db_file = 'monitor.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"已删除数据库文件: {db_file}")
        
        # 重新创建数据库
        db.create_all()
        print("数据库重新创建完成")
        
        # 创建默认管理员账号
        from app.models import User
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账号创建完成: admin/admin123")

if __name__ == '__main__':
    reset_database()