# QL/app/routes/order_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import MonAn, HoaDon, ChiTietHoaDon
from .. import db
import datetime

order_bp = Blueprint('order', __name__)

@order_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_order():
    # Lấy danh sách các món ăn đang được bán
    dishes = MonAn.query.filter_by(TrangThaiBan='Đang bán').all()

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')
        
        if not item_ids:
            flash('Vui lòng chọn ít nhất một món ăn.', 'warning')
            return redirect(url_for('order.create_order'))

        chi_tiet_list = []
        tong_tien = 0

        for i in range(len(item_ids)):
            ma_mon_an = int(item_ids[i])
            so_luong = int(quantities[i])
            
            if so_luong > 0:
                mon_an = MonAn.query.get(ma_mon_an)
                if mon_an:
                    thanh_tien = so_luong * mon_an.DonGia
                    tong_tien += thanh_tien
                    chi_tiet_list.append({
                        'ma_mon_an': ma_mon_an,
                        'so_luong': so_luong,
                        'don_gia': mon_an.DonGia
                    })
        
        if not chi_tiet_list:
            flash('Số lượng các món ăn phải lớn hơn 0.', 'warning')
            return redirect(url_for('order.create_order'))
            
        try:
            # Tạo hóa đơn mới
            new_hoadon = HoaDon(
                MaNguoiDung=current_user.MaNguoiDung,
                TongTien=tong_tien
            )
            db.session.add(new_hoadon)
            db.session.flush() # Lấy MaHoaDon vừa tạo

            # Thêm chi tiết hóa đơn
            for item in chi_tiet_list:
                chi_tiet = ChiTietHoaDon(
                    MaHoaDon=new_hoadon.MaHoaDon,
                    MaMonAn=item['ma_mon_an'],
                    SoLuong=item['so_luong'],
                    DonGia=item['don_gia']
                )
                db.session.add(chi_tiet)

            db.session.commit()
            flash('Tạo hóa đơn thành công!', 'success')
            return redirect(url_for('order.view_order', order_id=new_hoadon.MaHoaDon))
        except Exception as e:
            db.session.rollback()
            flash(f'Đã xảy ra lỗi khi tạo hóa đơn: {e}', 'danger')

    return render_template('order/create.html', dishes=dishes)

@order_bp.route('/history')
@login_required
def history():
    # Lấy lịch sử hóa đơn, sắp xếp mới nhất lên đầu
    orders = HoaDon.query.order_by(HoaDon.NgayTao.desc()).all()
    return render_template('order/history.html', orders=orders)

@order_bp.route('/view/<int:order_id>')
@login_required
def view_order(order_id):
    order = HoaDon.query.get_or_404(order_id)
    return render_template('order/view.html', order=order)