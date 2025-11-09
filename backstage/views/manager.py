from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from link import *
from api.sql import *
import imp, random, os, string
from werkzeug.utils import secure_filename
from flask import current_app

UPLOAD_FOLDER = 'static/product'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

manager = Blueprint('manager', __name__, template_folder='../templates')

def config():
    current_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    config = current_app.config['UPLOAD_FOLDER'] 
    return config

@manager.route('/', methods=['GET', 'POST'])
@login_required
def home():
    return redirect(url_for('manager.productManager'))

@manager.route('/productManager', methods=['GET', 'POST'])
@login_required
def productManager():
    if request.method == 'GET':
        if(current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('index'))
        
    if 'delete' in request.values:
        pid = request.values.get('delete')
        data = Record.delete_check(pid)
        
        if(data != None):
            flash('failed')
        else:
            data = Product.get_product(pid)
            Product.delete_product(pid)
    
    elif 'edit' in request.values:
        pid = request.values.get('edit')
        return redirect(url_for('manager.edit', pid=pid))
    
    book_data = book()
    return render_template('productManager.html', book_data = book_data, user=current_user.name)

def book():
    book_row = Product.get_all_product()
    book_data = []
    for i in book_row:
        book = {
            '商品編號': i[0],   # "Product_id"
            '商品名稱': i[3],   # "Name"
            '商品售價': i[2],   # "Stock_price"
            '商品類別': i[6],   # "Category"
            '商品狀態': i[4],   # "Pstatus"
            '供應商': i[1]      # "Supplier_id"
        }
        book_data.append(book)
    return book_data

@manager.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = ""
        while(data != None):
            number = str(random.randrange( 10000, 99999))
            en = random.choice(string.ascii_letters)
            pid = en + number
            data = Product.get_product(pid)

        pname = request.values.get('pname')
        price = request.values.get('price')
        category = request.values.get('category')
        pdesc = request.values.get('description')
        pstatus = request.values.get('pstatus')
        supplier_id = request.values.get('supplier_id')

        # 檢查是否正確獲取到所有欄位的數據
        if pname is None or price is None or category is None or pdesc is None or pstatus is None or supplier_id is None:
            flash('所有欄位都是必填的，請確認輸入內容。')
            return redirect(url_for('manager.productManager'))

        # 檢查欄位的長度
        if len(pname) < 1 or len(price) < 1 or len(pstatus) < 1 or len(supplier_id) < 1:
            flash('商品名稱、價格、商品狀態、供應商不可為空。')
            return redirect(url_for('manager.productManager'))


        if (len(pname) < 1 or len(price) < 1 or len(pstatus) < 1 or len(supplier_id) < 1):
            return redirect(url_for('manager.productManager'))
        
        Product.add_product(
            {'Product_id' : pid,
             'Name' : pname,
             'Stock_price' : price,
             'Category' : category,
             'Description':pdesc,
             'Pstatus': pstatus,
             'Supplier_id': supplier_id
            }
        )

        return redirect(url_for('manager.productManager'))

    return render_template('productManager.html')

@manager.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'GET':
        if(current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('bookstore'))

    if request.method == 'POST':
        Product.update_product(
            {
            'Name' : request.values.get('pname'),
            'Stock_price' : request.values.get('price'),
            'Category' : request.values.get('category'), 
            'Description' : request.values.get('description'),
            'Pstatus': request.values.get('pstatus'),
            'Supplier_id': request.values.get('supplier_id'),
            'Product_id' : request.values.get('pid')
            }
        )
        
        return redirect(url_for('manager.productManager'))

    else:
        product = show_info()
        return render_template('edit.html', data=product)


def show_info():
    pid = request.args['pid']
    data = Product.get_product(pid)
    pname = data[3]
    price = data[2]
    category = data[6]
    description = data[5]
    status = data[4]
    supplier = data[1]

    product = {
        '商品編號': pid,
        '商品名稱': pname,
        '單價': price,
        '類別': category,
        '商品敘述': description,
        '商品狀態': status,
        '供應商': supplier
    }
    return product


@manager.route('/orderManager', methods=['GET', 'POST'])
@login_required
def orderManager():
    if request.method == 'POST':
        pass
    else:
        order_row = Order_List.get_order()
        order_data = []
        for i in order_row:
            order = {
                '訂單編號': i[0],
                '訂購人': i[1],
                '訂單總價': i[2],
                '訂單時間': i[3]
            }
            order_data.append(order)
            
        orderdetail_row = Order_List.get_orderdetail()
        order_detail = []

        for j in orderdetail_row:
            orderdetail = {
                '訂單編號': j[0],
                '商品名稱': j[1],
                '商品單價': j[2],
                '訂購數量': j[3]
            }
            order_detail.append(orderdetail)

    return render_template('orderManager.html', orderData = order_data, orderDetail = order_detail, user=current_user.name)