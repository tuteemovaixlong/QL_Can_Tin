# QL/app/routes/auth_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from ..models import NguoiDung
from .. import db

# Dòng này tạo ra biến auth_bp mà __init__.py cần
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ten_dang_nhap = request.form.get('username')
        mat_khau = request.form.get('password')
        
        user = NguoiDung.query.filter_by(TenDangNhap=ten_dang_nhap).first()
        
        if user and user.check_password(mat_khau):
            if user.TrangThai != 'Hoạt động':
                flash('Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản lý.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            flash('Đăng nhập thành công!', 'success')
            # Chuyển hướng đến trang chủ
            return redirect(url_for('main.index')) 
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất.', 'success')
    return redirect(url_for('auth.login'))