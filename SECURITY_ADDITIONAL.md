# 额外安全漏洞分析

## 🚨 新发现的安全漏洞

### 1. **SSRF攻击 (CRITICAL)**
```python
# app/monitor.py
response = requests.get(website.url, timeout=website.timeout)
```
**风险**: 攻击者可以通过添加内网URL进行SSRF攻击
**影响**: 访问内网服务、云元数据、本地文件

### 2. **默认凭据 (HIGH)**
```python
# app/__init__.py
admin.set_password('admin123')  # 硬编码默认密码
```
**风险**: 弱密码、默认凭据
**影响**: 系统完全被控制

### 3. **信息泄露 (HIGH)**
```python
# 错误信息直接返回给用户
flash(f'文件读取失败: {str(e)}')
return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})
```
**风险**: 系统路径、数据库结构泄露
**影响**: 信息收集、进一步攻击

### 4. **竞态条件 (MEDIUM)**
```python
# app/monitor.py - 并发访问数据库
website.status = status
db.session.commit()
```
**风险**: 数据不一致、状态混乱
**影响**: 数据完整性问题

### 5. **DoS攻击 (MEDIUM)**
```python
# 无请求频率限制
# 无并发连接限制
# 大文件上传可能导致内存耗尽
```
**风险**: 资源耗尽、服务不可用
**影响**: 拒绝服务攻击

### 6. **时序攻击 (LOW)**
```python
# app/models.py
return check_password_hash(self.password_hash, password)
```
**风险**: 通过响应时间推断用户存在性
**影响**: 用户枚举

### 7. **日志注入 (MEDIUM)**
```python
# 用户输入直接写入日志
print(f"检查网站: {website.name}")
```
**风险**: 日志污染、日志伪造
**影响**: 审计绕过

### 8. **XML/Excel炸弹 (HIGH)**
```python
# app/routes/main.py
df = pd.read_excel(file)  # 无内容验证
```
**风险**: ZIP炸弹、XML实体攻击
**影响**: 内存耗尽、CPU占用

### 9. **路径遍历 (MEDIUM)**
```python
# 虽然使用了secure_filename，但仍有风险
filename = secure_filename(file.filename)
```
**风险**: 文件系统访问
**影响**: 敏感文件读取

### 10. **会话固定 (MEDIUM)**
```python
# 登录后未重新生成session ID
# 无session安全配置
```
**风险**: 会话劫持
**影响**: 身份冒充