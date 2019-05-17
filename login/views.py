import hashlib
import datetime
from django.shortcuts import render
from django.shortcuts import redirect
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from .models import ConfirmString
from .models import User
from . import forms

# Create your views here.


def hash_code(s, salt='xining'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def index(request):
    if not request.session.get('is_login', None):
        return redirect('/login/')
    return render(request, 'login/index.html')


def login(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = "请检查填写内容！"
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            try:
                user = User.objects.get(name=username)
            except Exception as e:
                message = "用户不存在！"
                return render(request, 'login/login.html', locals())
            if not user.has_confirm:
                message = "邮箱未验证"
                return render(request, 'login/login.html', locals())
            password_hash = hash_code(password, username)
            if user.password == password_hash:
                request.session['is_login'] = True
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                return redirect('/index/')
            else:
                message = "密码不正确！"
                return render(request, 'login/login.html', locals())
            return render(request, 'login/login.html', locals())
        else:
            return render(request, 'login/login.html', locals())
    login_form = forms.UserForm()
    return render(request, 'login/login.html', locals())


def register(request):
    if request.session.get('is_login', None):
        return redirect('/index/')

    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写内容！"
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password1 = register_form.cleaned_data.get('password1')
            password2 = register_form.cleaned_data.get('password2')
            email = register_form.cleaned_data.get('email')
            sex = register_form.cleaned_data.get('sex')
            if password1 != password2:
                message = "两次输入的密码不一致"
                return render(request, 'login/register.html', locals())
            else:
                same_name_user = User.objects.filter(name=username)
                if same_name_user:
                    message = "用户名已经存在"
                    return render(request, 'login/register.html', locals())
                same_email_user = User.objects.filter(email=email)
                if same_email_user:
                    message = "邮箱地址已经存在"
                    return render(request, 'login/register.html', locals())

                new_user = User()
                new_user.name = username
                new_user.password = hash_code(password1, username)
                new_user.email = email
                new_user.sex = sex
                new_user.save()
                code = make_confirm_string(new_user)
                send_email(email, code)
                message = '请登录邮箱进行验证'
                return render(request, 'login/confirm.html', locals())

                return redirect('/login/')
        else:
            return render(request, 'login/register.html', locals())
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return redirect('/login/')
    request.session.flush()
    return redirect("/login/")


def user_confirm(request):
    code = request.GET.get('code', None)
    message = ""
    try:
        confirm = ConfirmString.objects.get(code=code)
    except Exception as e:
        message = "无效的确认请求"
        return render(request, 'login/confirm.html', locals())

    c_time = confirm.c_time
    now = timezone.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm.user.delete()
        message = "邮箱验证已过期"
        return render(request, 'login/confirm.html', locals())
    else:
        pass
        confirm.user.has_confirm = True
        confirm.user.save()
        message = '感谢注册'
        return render(request, 'login/confirm.html', locals())


def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name, now)
    ConfirmString.objects.create(code=code, user=user,)
    return code


def send_email(email, code):
    subject = '来自www.yanansoft.com的注册确认邮件！'
    text_content = '''
        感谢注册www.yanansoft.com,如果您看到这封邮件，说明您的邮箱不提供HTML链接功能，请联系管理员！
    '''
    html_content = '''
        <p>感谢注册<a href="http://{}/confirm/?code={}" traget=blank>www.yanansoft.com</a></p>
        <p>此链接有效期为{}天！</p>
    '''.format('127.0.0.1', code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(
        subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
