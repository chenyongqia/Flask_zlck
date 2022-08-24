from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, flash
from exts import mail, db
from flask_mail import Message
from models import EmailCaptchaModel, UserModel
import string
import random
from datetime import datetime
from .forms import RegisterForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash


bp = Blueprint('user', __name__, url_prefix='/user')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        form = LoginForm(request.form)
        if form.validate():
            email = form.email.data
            password = form.password.data
            user = UserModel.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect('/')
            else:
                flash('邮箱和密码不匹配！')
                return redirect(url_for('user.login'))
        else:
            flash('邮箱或密码格式错误！')
            return redirect(url_for('user.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        form = RegisterForm(request.form)
        if form.validate():
            email = form.email.data
            username = form.username.data
            password = form.password.data

            # 密码加密：就是将你传入的数据变成一个固定长度的一串乱码。
            hash_password = generate_password_hash(password)
            user = UserModel(email=email, username=username, password=hash_password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('user.login'))
        else:
            return redirect(url_for('user.register'))


@bp.route('/logout')
def logout():
    # 清楚session中所有的数据
    session.clear()
    return redirect(url_for('user.login'))


@bp.route('/captcha', methods=['POST'])
def get_captcha():
    # GET, POST接受用户输入的邮箱
    email = request.form.get('email')

    letters = string.ascii_letters + string.digits
    captcha = ''.join(random.sample(letters, 4))
    if email:

        message = Message(
            subject='邮箱测试',
            recipients=[email],
            body=f'【知了问答】您的注册验证码是：{captcha}， 请不要告诉任何人哦！'
        )
        mail.send(message)
        captcha_model = EmailCaptchaModel.query.filter_by(email=email).first()  # 提取数据库中第一条email的数据
        if captcha_model:
            captcha_model.captcha = captcha  # 修改数据库中的验证码为新验证码
            captcha_model.captcha_time = datetime.now()  # 设置当前时间
            db.session.commit()
        else:  # 如果数据库中没有email字段为email的数据，则添加这个数据并上传
            captcha_model = EmailCaptchaModel(email=email, captcha=captcha)
            db.session.add(captcha_model)
            db.session.commit()
        print('captcha', captcha)
        # 返回code: 200 说明是一个成功的正确的请求
        return jsonify({'code': 200})
    else:
        # 返回code：400 说明是客户端错误
        return jsonify({'code': 400, 'message': '请先传递邮箱！'})