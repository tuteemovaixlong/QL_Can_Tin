# QL/app/routes/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from ..models import NguoiDung
from .. import db
from ..forms import LoginForm  # Import lớp LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Tạo một đối tượng form

    if form.validate_on_submit():
        user = NguoiDung.query.filter_by(TenDangNhap=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if user.TrangThai != 'Hoạt động':
                flash('Tài khoản của bạn đã bị khóa.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('main.index')) 
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác.', 'danger')
            
    # DÒNG QUAN TRỌNG: Truyền biến 'form' sang cho template
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'success')
    return redirect(url_for('auth.login'))