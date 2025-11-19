from flask import render_template, Blueprint
from flask_login import login_required, current_user
from link import *
from api.sql import Analysis

analysis = Blueprint('analysis', __name__, template_folder='../templates')

@analysis.route('/dashboard')
@login_required
def dashboard():
    # 各月總銷售額 & 訂單數量
    revenue = []
    dataa = []
    for i in range(1, 13):
        # 每月總銷售額
        row = Analysis.month_price(i)
        if not row:
            revenue.append(0)
        else:
            for j in row:
                revenue.append(j[1])

        # 每月訂單數量
        row = Analysis.month_count(i)
        if not row:
            dataa.append(0)
        else:
            for k in row:
                dataa.append(k[1])

    # 供應商銷售分析
    row = Analysis.category_sale() or []
    datab = [{'name': i[0] or 'Unknown', 'value': i[1] or 0} for i in row]

    # 單一顧客消費總額
    row = Analysis.member_sale()
    datac = [r[0] for r in row]   # total_amount
    nameList = [r[1] for r in row] # Name

    # 顧客訂單數量
    row = Analysis.member_sale_count()
    countList = [r[0] for r in row]

    # 第四個按鈕：綠色運送 & 二手產品統計
    green_secondhand = Analysis.monthly_green_and_secondhand()  # 需在 api/sql.py 加這個方法
    green_counts = [r[1] for r in green_secondhand]       # Green_delivery = 'Y'
    secondhand_counts = [r[2] for r in green_secondhand]  # Pstatus = '二手'

    return render_template(
        'dashboard.html',
        revenue=revenue,
        dataa=dataa,
        datab=datab,
        datac=datac,
        nameList=nameList,
        countList=countList,
        green_counts=green_counts,
        secondhand_counts=secondhand_counts
    )
