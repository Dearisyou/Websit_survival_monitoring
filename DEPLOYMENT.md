# 部署文档

## 🚀 生产环境部署指南

### 系统要求
- Python 3.8+
- 2GB+ RAM
- 10GB+ 磁盘空间
- Linux/Windows Server

### 部署步骤

#### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 环境变量配置
```bash
# 创建环境变量文件
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
ADMIN_PASSWORD=your-admin-password
DATABASE_URL=sqlite:///monitor.db
EOF

# 加载环境变量
source .env
```

#### 3. 数据库初始化
```bash
# 启动应用（自动创建数据库）
python run.py

# 检查管理员密码
cat admin_password.txt
```

#### 4. 生产环境启动

##### 方式一：直接启动（开发/测试）
```bash
python run.py
```

##### 方式二：Gunicorn（推荐）
```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 run:app

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 run:app > app.log 2>&1 &
```

##### 方式三：Systemd服务（Linux）
```bash
# 创建服务文件
sudo tee /etc/systemd/system/monitor.service << EOF
[Unit]
Description=Website Monitor
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/网站存活探测
Environment=PATH=/path/to/网站存活探测/venv/bin
ExecStart=/path/to/网站存活探测/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable monitor
sudo systemctl start monitor
```

### 反向代理配置

#### Nginx配置
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Apache配置
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5000/
    ProxyPassReverse / http://127.0.0.1:5000/
</VirtualHost>
```

### 安全配置

#### 1. 防火墙设置
```bash
# Ubuntu/Debian
sudo ufw allow 5000
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

#### 2. SSL证书（推荐）
```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 3. 文件权限
```bash
chmod 644 monitor.db
chmod 600 admin_password.txt
chmod 600 .env
```

### 监控和维护

#### 1. 日志管理
```bash
# 查看应用日志
tail -f app.log

# 查看审计日志
tail -f audit.log

# 日志轮转
sudo logrotate -f /etc/logrotate.conf
```

#### 2. 数据库备份
```bash
# 创建备份脚本
cat > backup.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp monitor.db backups/monitor_$DATE.db
find backups/ -name "monitor_*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

#### 3. 性能监控
```bash
# 安装监控工具
pip install psutil

# 系统资源监控
python production_fix.py
```

### 故障排除

#### 常见问题

1. **密码输入无反应**
   ```bash
   # 检查环境配置
   python production_fix.py
   
   # 设置开发模式（HTTP环境）
   export FLASK_ENV=development
   ```

2. **数据库锁定**
   ```bash
   # 重启应用
   sudo systemctl restart monitor
   ```

3. **内存不足**
   ```bash
   # 减少worker数量
   gunicorn -w 2 -b 0.0.0.0:5000 run:app
   ```

4. **端口占用**
   ```bash
   # 查找占用进程
   sudo lsof -i :5000
   
   # 杀死进程
   sudo kill -9 <PID>
   ```

### 升级指南

#### 1. 备份数据
```bash
cp monitor.db monitor.db.backup
cp admin_password.txt admin_password.txt.backup
```

#### 2. 更新代码
```bash
git pull origin main
pip install -r requirements.txt
```

#### 3. 重启服务
```bash
sudo systemctl restart monitor
```

### 性能优化

#### 1. 数据库优化
- 定期清理旧日志
- 添加数据库索引
- 使用PostgreSQL（大规模部署）

#### 2. 缓存配置
- 启用Redis缓存
- 配置静态文件缓存

#### 3. 负载均衡
- 多实例部署
- 使用负载均衡器

### 联系支持
- 查看 `SECURITY.md` 了解安全配置
- 运行 `python production_fix.py` 进行环境诊断
- 检查 `audit.log` 查看操作记录