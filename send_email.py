import os
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail


os.environ['DJANGO_SETTINGS_MODULE'] = 'useradmin.settings'


if __name__ == '__main__':
    subject, from_email, to = 'Django 自动发送邮件测试', 'vixiaoan@163.com', '106865801@qq.com'
    text_content = '欢迎访问www.yanansoft.com'
    html_content = '<p>Welcom to <a href="http://www.yanansoft.com">炎安软件</a></p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
