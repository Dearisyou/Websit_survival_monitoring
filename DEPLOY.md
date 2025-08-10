# 网站存活监控系统 - 部署文档

## 🚀 快速部署

### 环境要求
- Python 3.8+
- pip 包管理器

### 1. 下载项目
```bash
git clone <项目地址>
cd 网站存活探测
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动应用
```bash
python run.py
```

或直接运行：
```bash
start.bat  # Windows
```

### 4. 访问系统
- 地址：http://localhost:5000
- 默认账号：admin / admin123

## 🐳 Docker 部署

### 创建 Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run.py"]
```

### 构建和运行
```bash
docker build -t website-monitor .
docker run -d -p 5000:5000 -v $(pwd)/data:/app website-monitor
```

## 🌐 生产环境部署

### 使用 Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 使用 Nginx 反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 系统服务配置
创建 `/etc/systemd/system/website-monitor.service`：
```ini
[Unit]
Description=Website Monitor
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/website-monitor
ExecStart=/usr/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable website-monitor
sudo systemctl start website-monitor
```

## ⚙️ 配置说明

### 环境变量
```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///monitor.db"
export FLASK_ENV="production"
```

### 数据库备份
```bash
# 备份
cp monitor.db monitor_backup_$(date +%Y%m%d).db

# 恢复
cp monitor_backup_20240101.db monitor.db
```

## 🔧 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -ano | findstr :5000
   # 修改端口
   app.run(port=8080)
   ```

2. **数据库错误**
   ```bash
   # 重置数据库
   python reset_db.py
   ```

3. **依赖安装失败**
   ```bash
   # 使用国内镜像
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

### 性能优化

1. **调整监控间隔**
   - 建议设置为 5-10 分钟
   - 避免过于频繁的检查

2. **数据库优化**
   - 定期清理旧日志
   - 考虑使用 PostgreSQL 替代 SQLite

3. **内存使用**
   - 监控进程内存使用
   - 必要时重启应用

## 📊 监控和维护

### 日志查看
```bash
# 应用日志
tail -f app.log

# 系统服务日志
journalctl -u website-monitor -f
```

### 健康检查
```bash
# 检查应用状态
curl http://localhost:5000/

# 检查数据库
sqlite3 monitor.db ".tables"
```

### 定期维护
- 每周备份数据库
- 每月清理过期日志
- 定期更新依赖包

## 🔒 安全建议

1. **修改默认密码**
   - 首次部署后立即修改 admin 密码

2. **使用 HTTPS**
   - 生产环境建议配置 SSL 证书

3. **防火墙配置**
   - 只开放必要端口
   - 限制访问来源

4. **定期更新**
   - 及时更新系统和依赖包
   - 关注安全漏洞公告

## 📞 技术支持

如遇到部署问题，请检查：
1. Python 版本是否符合要求
2. 依赖包是否完整安装
3. 端口是否被占用
4. 数据库文件权限是否正确

更多问题请参考项目 README.md 或提交 Issue。