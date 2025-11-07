from flask import render_template, Blueprint
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from link import *
from api.sql import Analysis

analysis = Blueprint('analysis', __name__, template_folder='../templates')

@analysis.route('/dashboard')
@login_required
def dashboard():
    revenue = []
    dataa = []
    for i in range(1,13):
        row = Analysis.month_price(i)

        if not row:
            revenue.append(0)
        else:
            for j in row:
                revenue.append(j[1])
        
        row = Analysis.month_count(i)
        
        if not row:
            dataa.append(0)
        else:
            for k in row:
                dataa.append(k[1])
        
    row = Analysis.category_sale() or []  # 防止 None
    # 保留原始資料
    datab = [{'name': i[0] or 'Unknown', 'value': i[1] or 0} for i in row]
 
    
    row = Analysis.member_sale()
    datac = []
    nameList = []

    for r in row:
        datac.append(r[0])   # total_amount
        nameList.append(r[1]) # Name

    
    row = Analysis.member_sale_count()
    countList = []
    
    for i in row:
        countList.append(i[0])
        
    return render_template('dashboard.html', revenue = revenue, dataa = dataa, datab = datab, datac = datac, nameList = nameList, countList = countList)