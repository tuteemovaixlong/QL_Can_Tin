# QL/app/routes/report_routes.py

from flask import Blueprint, render_template, request
from flask_login import login_required
from ..models import HoaDon, ChiTietHoaDon, MonAn
from .. import db
from sqlalchemy import func
from datetime import datetime, timedelta

report_bp = Blueprint('report', __name__)

# Route cho báo cáo doanh thu (UC10)
@report_bp.route('/revenue')
@login_required
def revenue_report():
    period = request.args.get('period', 'today')
    today = datetime.now().date()
    
    if period == 'today':
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        title = "Hôm nay"
    elif period == 'weekly':
        start_date = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
        end_date = datetime.combine(start_date.date() + timedelta(days=6), datetime.max.time())
        title = "Tuần này"
    elif period == 'monthly':
        start_date = datetime.combine(today.replace(day=1), datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        title = "Tháng này"
    else: # Mặc định là hôm nay
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        title = "Hôm nay"

    # Truy vấn doanh thu
    revenue_data = db.session.query(
        func.sum(HoaDon.TongTien)
    ).filter(
        HoaDon.NgayTao >= start_date,
        HoaDon.NgayTao <= end_date
    ).scalar() or 0

    orders_in_period = HoaDon.query.filter(
        HoaDon.NgayTao >= start_date,
        HoaDon.NgayTao <= end_date
    ).all()

    return render_template('report/revenue.html', 
                           total_revenue=revenue_data, 
                           orders=orders_in_period,
                           title=title,
                           current_period=period)

# Route cho thống kê món bán chạy (UC11)
@report_bp.route('/bestsellers')
@login_required
def bestsellers_report():
    # Thống kê món ăn bán chạy nhất theo số lượng
    bestsellers = db.session.query(
        MonAn.TenMonAn,
        func.sum(ChiTietHoaDon.SoLuong).label('total_quantity')
    ).join(MonAn, MonAn.MaMonAn == ChiTietHoaDon.MaMonAn)\
    .group_by(MonAn.TenMonAn)\
    .order_by(func.sum(ChiTietHoaDon.SoLuong).desc())\
    .limit(10).all()

    return render_template('report/bestsellers.html', bestsellers=bestsellers)

# UC12 - Xuất báo cáo sẽ cần các thư viện ngoài như Pandas hoặc tạo file CSV.
# Đây là một ví dụ đơn giản, các chức năng phức tạp hơn sẽ được phát triển sau.
@report_bp.route('/export')
@login_required
def export_report():
    # Chức năng này sẽ được xây dựng sau
    flash('Chức năng xuất báo cáo đang được phát triển.', 'info')
    return redirect(request.referrer or url_for('main.index'))