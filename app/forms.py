from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SelectField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, URL, NumberRange

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('密码', validators=[DataRequired()])

class UserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    role = SelectField('角色', choices=[('user', '普通用户'), ('admin', '管理员')])

class WebsiteForm(FlaskForm):
    name = StringField('网站名称', validators=[DataRequired(), Length(max=100)])
    url = StringField('网站URL', validators=[DataRequired(), URL()])
    check_interval = IntegerField('检查间隔(秒)', validators=[DataRequired(), NumberRange(min=60, max=3600)], default=300)
    timeout = IntegerField('超时时间(秒)', validators=[DataRequired(), NumberRange(min=5, max=60)], default=10)

class AlertForm(FlaskForm):
    alert_enabled = BooleanField('启用告警通知', default=True)

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), Length(min=6)])

class ImportExcelForm(FlaskForm):
    excel_file = FileField('Excel文件', validators=[FileRequired(), FileAllowed(['xlsx', 'xls'], '只支持Excel文件!')])
    check_interval = IntegerField('默认检查间隔(秒)', validators=[DataRequired(), NumberRange(min=60, max=3600)], default=300)
    timeout = IntegerField('默认超时时间(秒)', validators=[DataRequired(), NumberRange(min=5, max=60)], default=10)

class GlobalAlertForm(FlaskForm):
    global_dingtalk_webhook = StringField('全局钉钉Webhook', validators=[DataRequired(), URL()])
    global_dingtalk_secret = StringField('钉钉机器人密钥', description='可选，如果使用签名验证则必填')
    global_alert_enabled = BooleanField('启用全局告警', default=True)