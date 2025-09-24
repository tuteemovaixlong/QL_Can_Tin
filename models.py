# QL/app/models.py
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class VaiTro(db.Model):
    __tablename__ = 'VaiTro'
    MaVaiTro = db.Column(db.Integer, primary_key=True)
    TenVaiTro = db.Column(db.String(50), nullable=False)
    NguoiDung = db.relationship('NguoiDung', backref='vai_tro', lazy=True)

class NguoiDung(db.Model, UserMixin):
    __tablename__ = 'NguoiDung'
    MaNguoiDung = db.Column(db.Integer, primary_key=True)
    HoTen = db.Column(db.String(100), nullable=False)
    TenDangNhap = db.Column(db.String(50), unique=True, nullable=False)
    MatKhau = db.Column(db.String(255), nullable=False)
    MaVaiTro = db.Column(db.Integer, db.ForeignKey('VaiTro.MaVaiTro'))
    TrangThai = db.Column(db.String(50), default='Hoạt động')

    # Flask-Login yêu cầu một phương thức get_id
    def get_id(self):
        return str(self.MaNguoiDung)

    # Hàm để băm mật khẩu
    def set_password(self, password):
        self.MatKhau = generate_password_hash(password)

    # Hàm để kiểm tra mật khẩu
    def check_password(self, password):
        return check_password_hash(self.MatKhau, password)

class MonAn(db.Model):
    __tablename__ = 'MonAn'
    MaMonAn = db.Column(db.Integer, primary_key=True)
    TenMonAn = db.Column(db.String(150), nullable=False)
    DonGia = db.Column(db.Numeric(18, 0), nullable=False)
    MoTa = db.Column(db.String(500))
    TrangThaiBan = db.Column(db.String(50), default='Đang bán')

class Kho(db.Model):
    __tablename__ = 'Kho'
    MaHang = db.Column(db.Integer, primary_key=True)
    TenHang = db.Column(db.String(150), nullable=False)
    SoLuongTon = db.Column(db.Integer, nullable=False, default=0)
    DonViTinh = db.Column(db.String(20))
    NguongCanhBao = db.Column(db.Integer, default=10)
    MaNguoiCapNhatCuoi = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaNguoiDung'), nullable=True)
    ThoiGianCapNhatCuoi = db.Column(db.DateTime, nullable=True)

class HoaDon(db.Model):
    __tablename__ = 'HoaDon'
    MaHoaDon = db.Column(db.Integer, primary_key=True)
    NgayTao = db.Column(db.DateTime, server_default=db.func.now())
    MaNguoiDung = db.Column(db.Integer, db.ForeignKey('NguoiDung.MaNguoiDung'))
    TongTien = db.Column(db.Numeric(18, 0), nullable=False)
    ChiTiet = db.relationship('ChiTietHoaDon', backref='hoa_don', lazy='dynamic')
    # Trong HoaDon
    nguoi_dung = db.relationship('NguoiDung', backref='hoa_don', lazy=True)



class ChiTietHoaDon(db.Model):
    __tablename__ = 'ChiTietHoaDon'
    MaChiTietHD = db.Column(db.Integer, primary_key=True)
    MaHoaDon = db.Column(db.Integer, db.ForeignKey('HoaDon.MaHoaDon'))
    MaMonAn = db.Column(db.Integer, db.ForeignKey('MonAn.MaMonAn'))
    SoLuong = db.Column(db.Integer, nullable=False)
    DonGia = db.Column(db.Numeric(18, 0), nullable=False)
    # Trong ChiTietHoaDon
    mon_an = db.relationship('MonAn', backref='chi_tiet_hoa_don', lazy=True)

    @property
    def ThanhTien(self):
        return self.SoLuong * self.DonGia