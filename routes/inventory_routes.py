# QL/app/routes/inventory_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import Kho
from .. import db
import datetime

inventory_bp = Blueprint('inventory', __name__)

# Route để xem danh sách tồn kho (UC07)
@inventory_bp.route('/')
@login_required
def list_items():
    items = Kho.query.all()
    return render_template('inventory/list.html', items=items)

# Route để nhập hàng (UC08)
@inventory_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_item():
    if request.method == 'POST':
        ten_hang = request.form.get('ten_hang')
        so_luong = int(request.form.get('so_luong', 0))
        don_vi_tinh = request.form.get('don_vi_tinh')
        nguong_canh_bao = int(request.form.get('nguong_canh_bao', 10))

        # Kiểm tra xem mặt hàng đã tồn tại chưa
        item = Kho.query.filter_by(TenHang=ten_hang).first()
        if item:
            # Nếu đã tồn tại thì cộng dồn số lượng
            item.SoLuongTon += so_luong
            flash(f'Đã cập nhật số lượng cho mặt hàng "{ten_hang}".', 'success')
        else:
            # Nếu chưa có thì tạo mới
            item = Kho(
                TenHang=ten_hang,
                SoLuongTon=so_luong,
                DonViTinh=don_vi_tinh,
                NguongCanhBao=nguong_canh_bao
            )
            db.session.add(item)
            flash(f'Đã thêm mặt hàng mới "{ten_hang}" vào kho.', 'success')
        
        # Cập nhật thông tin người thao tác
        item.MaNguoiCapNhatCuoi = current_user.MaNguoiDung
        item.ThoiGianCapNhatCuoi = datetime.datetime.now()
        
        db.session.commit()
        return redirect(url_for('inventory.list_items'))

    return render_template('inventory/import_adjust.html', action="Nhập hàng")

# Route để điều chỉnh/xuất kho (UC09)
@inventory_bp.route('/adjust/<int:item_id>', methods=['GET', 'POST'])
@login_required
def adjust_item(item_id):
    item = Kho.query.get_or_404(item_id)
    if request.method == 'POST':
        so_luong_dieu_chinh = int(request.form.get('so_luong', 0))
        
        if so_luong_dieu_chinh > item.SoLuongTon:
            flash('Số lượng điều chỉnh/xuất không được lớn hơn số lượng tồn kho.', 'danger')
        else:
            item.SoLuongTon -= so_luong_dieu_chinh
            item.MaNguoiCapNhatCuoi = current_user.MaNguoiDung
            item.ThoiGianCapNhatCuoi = datetime.datetime.now()
            db.session.commit()
            flash('Điều chỉnh/xuất kho thành công!', 'success')
            return redirect(url_for('inventory.list_items'))
            
    return render_template('inventory/import_adjust.html', item=item, action="Điều chỉnh / Xuất kho")