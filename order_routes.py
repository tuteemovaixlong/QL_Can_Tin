# QL/app/routes/order_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import MonAn, HoaDon, ChiTietHoaDon
from .. import db
import datetime
from ..models import MonAn, HoaDon, ChiTietHoaDon, Kho # thêm Kho
from .. import db
import datetime
from sqlalchemy import func
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from sqlalchemy import func

def _stock_map():
    """Map tên hàng (lower) -> tồn kho hiện tại"""
    return {k.TenHang.lower(): k for k in Kho.query.all()}

def _inv_for_dish(mon_an):
    """Tìm record kho theo tên món (lowercase)"""
    return Kho.query.filter(func.lower(Kho.TenHang) == func.lower(mon_an.TenMonAn)).first()

def _set_selling_state(mon_an, inv):
    """Tự động trạng thái bán dựa theo tồn kho"""
    if inv and inv.SoLuongTon <= 0:
        inv.SoLuongTon = 0
        mon_an.TrangThaiBan = 'Hết hàng'
    elif inv and inv.SoLuongTon > 0 and mon_an.TrangThaiBan == 'Hết hàng':
        mon_an.TrangThaiBan = 'Đang bán'


order_bp = Blueprint('order', __name__)
# (Toàn bộ code cho file này giữ nguyên như lần trước)
# ...

@order_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_order():
    dishes = MonAn.query.filter_by(TrangThaiBan='Đang bán').all()
    smap = _stock_map()

    if request.method == 'POST':
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')

        if not item_ids or not quantities or len(item_ids) != len(quantities):
            flash('Dữ liệu không hợp lệ.', 'danger')
            return redirect(url_for('order.create_order'))

        chi_tiet_list, tong_tien = [], 0
        for i in range(len(item_ids)):
            try:
                ma = int(item_ids[i]); qty = int(quantities[i])
            except: 
                continue
            if qty <= 0:
                continue
            mon = MonAn.query.get(ma)
            if not mon: 
                continue

            inv = _inv_for_dish(mon)
            if inv and qty > inv.SoLuongTon:
                flash(f"Số lượng '{mon.TenMonAn}' vượt tồn khả dụng ({inv.SoLuongTon}).", 'danger')
                return redirect(url_for('order.create_order'))

            chi_tiet_list.append((mon, qty, mon.DonGia))
            tong_tien += qty * mon.DonGia

        if not chi_tiet_list:
            flash('Vui lòng chọn ít nhất một món với số lượng > 0.', 'warning')
            return redirect(url_for('order.create_order'))

        try:
            hd = HoaDon(MaNguoiDung=current_user.MaNguoiDung, TongTien=tong_tien)
            db.session.add(hd); db.session.flush()

            for mon, qty, gia in chi_tiet_list:
                db.session.add(ChiTietHoaDon(MaHoaDon=hd.MaHoaDon, MaMonAn=mon.MaMonAn, SoLuong=qty, DonGia=gia))

            # Trừ tồn kho
            for mon, qty, _ in chi_tiet_list:
                inv = _inv_for_dish(mon)
                if inv:
                    inv.SoLuongTon -= qty
                    _set_selling_state(mon, inv)

            db.session.commit()
            flash('Tạo hóa đơn thành công!', 'success')
            return redirect(url_for('order.view_order', order_id=hd.MaHoaDon))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi tạo hóa đơn: {e}', 'danger')
            return redirect(url_for('order.create_order'))

    # GET: pass stock_map để client show tồn khả dụng
    stock_map = {d.TenMonAn.lower(): (smap.get(d.TenMonAn.lower()).SoLuongTon if smap.get(d.TenMonAn.lower()) else None) for d in dishes}
    return render_template('order/create.html', dishes=dishes, stock_map=stock_map)



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


# @order_bp.route('/delete/<int:order_id>', methods=['POST'])
# @login_required
# def delete_order(order_id):
#     order = HoaDon.query.get_or_404(order_id)
#     # Hoàn kho (nếu có Kho matching theo tên)
#     items = order.ChiTiet.all()  # lazy='dynamic' nên cần .all()
#     for it in items:
#         mon = MonAn.query.get(it.MaMonAn)
#         inv = Kho.query.filter(db.func.lower(Kho.TenHang) == db.func.lower(mon.TenMonAn)).first()
#         if inv:
#             inv.SoLuongTon += it.SoLuong
#             # Nếu có hàng trở lại, có thể bật bán
#             if mon.TrangThaiBan == 'Hết hàng' and inv.SoLuongTon > 0:
#                 mon.TrangThaiBan = 'Đang bán'

#     # Xoá chi tiết rồi xoá hoá đơn
#     for it in items:
#         db.session.delete(it)
#     db.session.delete(order)
#     db.session.commit()
#     flash('Đã hủy hóa đơn và hoàn kho (nếu có).', 'success')
#     return redirect(url_for('order.history'))


@order_bp.route('/edit/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = HoaDon.query.get_or_404(order_id)
    # hiện tại cho phép sửa tất cả món (kể cả món mới)
    dishes = MonAn.query.all()

    # map số lượng hiện có trong order
    current_qty = {ct.MaMonAn: ct.SoLuong for ct in order.ChiTiet.all()}

    if request.method == 'POST':
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')

        if not item_ids or not quantities or len(item_ids) != len(quantities):
            flash('Dữ liệu không hợp lệ.', 'danger')
            return redirect(url_for('order.edit_order', order_id=order_id))

        # Tính delta theo món
        new_qty = {}
        for i in range(len(item_ids)):
            try:
                ma = int(item_ids[i]); qty = int(quantities[i])
            except:
                continue
            if qty < 0: qty = 0
            if ma in new_qty: new_qty[ma] += qty
            else: new_qty[ma] = qty

        # Validate tồn kho: delta > 0 cần đủ tồn
        for ma, qty_new in new_qty.items():
            qty_old = current_qty.get(ma, 0)
            delta = qty_new - qty_old
            if delta > 0:
                mon = MonAn.query.get(ma)
                inv = _inv_for_dish(mon)
                if inv and delta > inv.SoLuongTon:
                    flash(f"Tăng '{mon.TenMonAn}' thêm {delta} vượt tồn ({inv.SoLuongTon}).", 'danger')
                    return redirect(url_for('order.edit_order', order_id=order_id))

        try:
            # Cập nhật chi tiết: add/update/delete
            # 1) Xóa các dòng trở về 0
            for ct in order.ChiTiet.all():
                if new_qty.get(ct.MaMonAn, 0) == 0:
                    # hoàn kho tương ứng
                    mon = MonAn.query.get(ct.MaMonAn)
                    inv = _inv_for_dish(mon)
                    if inv:
                        inv.SoLuongTon += ct.SoLuong
                        _set_selling_state(mon, inv)
                    db.session.delete(ct)

            # 2) Thêm mới hoặc cập nhật số lượng
            for ma, qty_new in new_qty.items():
                mon = MonAn.query.get(ma)
                ct = order.ChiTiet.filter_by(MaMonAn=ma).first()
                qty_old = current_qty.get(ma, 0)
                delta = qty_new - qty_old

                if ct and qty_new > 0:
                    ct.SoLuong = qty_new  # update
                elif not ct and qty_new > 0:
                    db.session.add(ChiTietHoaDon(
                        MaHoaDon=order.MaHoaDon, MaMonAn=ma, SoLuong=qty_new, DonGia=mon.DonGia
                    ))

                # Điều chỉnh tồn kho theo delta
                inv = _inv_for_dish(mon)
                if inv:
                    inv.SoLuongTon -= max(delta, 0)  # tăng bán → trừ
                    if delta < 0:
                        inv.SoLuongTon += (-delta)     # giảm bán → hoàn kho
                    _set_selling_state(mon, inv)

            # 3) Cập nhật tổng tiền
            new_total = 0
            for ct in order.ChiTiet.all():
                new_total += ct.SoLuong * ct.DonGia
            order.TongTien = new_total

            db.session.commit()
            flash('Cập nhật hóa đơn thành công!', 'success')
            return redirect(url_for('order.view_order', order_id=order_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi cập nhật: {e}', 'danger')
            return redirect(url_for('order.edit_order', order_id=order_id))

    # GET: render form (tái sử dụng create.html hoặc làm edit riêng)
    # Ở đây dùng create.html để tiết kiệm, prefill quantity = current
    stock_map = {d.TenMonAn.lower(): (_inv_for_dish(d).SoLuongTon if _inv_for_dish(d) else None) for d in dishes}
    # Trick: chuyền thêm dict 'prefill' để template gán sẵn số lượng
    prefill = current_qty
    return render_template('order/edit.html', dishes=dishes, order=order, stock_map=stock_map, prefill=prefill)

@order_bp.route('/delete/<int:order_id>', methods=['POST'], endpoint='delete_order')
def delete_order_post(order_id):
    order = HoaDon.query.get_or_404(order_id)
    try:
        # hoàn kho & xóa chi tiết + hóa đơn (ví dụ như mình gửi trước đó)
        for ct in order.ChiTiet.all():
            mon = MonAn.query.get(ct.MaMonAn)
            inv = _inv_for_dish(mon)
            if inv:
                inv.SoLuongTon += ct.SoLuong
                _set_selling_state(mon, inv)
            db.session.delete(ct)
        db.session.delete(order)
        db.session.commit()
        flash('Đã xóa hóa đơn và hoàn kho.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi xóa hóa đơn: {e}', 'danger')
    return redirect(url_for('order.history'))

