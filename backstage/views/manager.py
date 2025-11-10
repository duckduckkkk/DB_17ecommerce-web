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
    book_row = Product.get_all_product_with_supplier()
    book_data = []
    for i in book_row:
        book = {
            '商品編號': i[0],   # Product_id
            '商品名稱': i[1],   # Name
            '商品售價': i[2],   # Stock_price
            '商品類別': i[3],   # Category
            '供應商名稱': i[6],  # Sname
            '供應商編號': i[5]   # Supplier_id
        }
        book_data.append(book)
    return book_data


@manager.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        pname = request.values.get('pname')
        price = request.values.get('price')
        category = request.values.get('category')
        pdesc = request.values.get('description')
        supplier_name = request.values.get('supplier_name')
        supplier_contact = request.values.get('supplier_contact')

        # === 檢查必填欄位 ===
        if not all([pname, price, category, pdesc, supplier_name, supplier_contact]):
            flash('所有欄位都是必填的，請確認輸入內容。')
            return redirect(url_for('manager.productManager'))

        # === 查詢是否有相同廠商 ===
        existing_supplier = Supplier.get_supplier_by_name(supplier_name)

        if existing_supplier:
            existing_id = existing_supplier[0]
            existing_name = existing_supplier[1]
            existing_contact = existing_supplier[2]

            if existing_contact != supplier_contact:
                flash('廠商名稱或聯絡資訊錯誤，請重新確認。')
                return redirect(url_for('manager.productManager'))

            supplier_id = existing_id  # 直接沿用原本 Supplier_id
        else:
            # 沒有找到 → 新增新廠商
            max_id = Supplier.get_max_supplier_id()
            supplier_id = max_id + 1 if max_id else 1

            Supplier.add_supplier({
                'Supplier_id': supplier_id,
                'Sname': supplier_name,
                'Contact_info': supplier_contact
            })

        # === 生成新的商品 ID ===
        max_pid = Product.get_max_product_id()
        pid = max_pid + 1 if max_pid else 1

        # === 寫入 Product ===
        Product.add_product({
            'Product_id': pid,
            'Supplier_id': supplier_id,
            'Stock_price': price,
            'Name': pname,
            'Description': pdesc,
            'Category': category,
        })

        flash('商品新增成功！')
        return redirect(url_for('manager.productManager'))

    return render_template('productManager.html')

@manager.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if current_user.role == 'user':
        flash('No permission')
        return redirect(url_for('bookstore'))

    if request.method == 'POST':
        pid = request.values.get('pid')
        Product.update_product({
            'Name': request.values.get('pname'),
            'Stock_price': request.values.get('price'),
            'Category': request.values.get('Category'),
            'Description': request.values.get('description'),
            'Product_id': pid
            # 不要改 Supplier_id
        })

        # 更新 Supplier 資訊
        product = Product.get_product_by_pid(pid)
        supplier_id = product[1]  # Product 表的 Supplier_id

        supplier_name = request.values.get('supplier_name')
        supplier_contact = request.values.get('supplier_contact')

        sql = '''
            UPDATE "Supplier"
            SET "Sname" = %s,
                "Contact_info" = %s
            WHERE "Supplier_id" = %s
        '''
        DB.execute_input(sql, (supplier_name, supplier_contact, supplier_id))

        flash('商品及供應商資訊更新成功！')
        return redirect(url_for('manager.productManager'))


    # GET 方法：顯示商品資訊
    product = show_info()
    if not product:
        flash('找不到該商品')
        return redirect(url_for('manager.productManager'))

    return render_template('edit.html', data=product)


def show_info():
    pid = request.args.get('pid')
    data = Product.get_product(pid)
    if not data:
        return None
    product = {
        '商品編號': data[0],
        '供應商編號': data[1],
        '單價': data[2],
        '商品名稱': data[3],
        '商品敘述': data[4],
        '類別': data[5],
        '供應商名稱': data[6],
        '供應商聯絡資訊': data[7]
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
                '訂單時間': i[3],
                '綠色運送': i[4],
            }
            order_data.append(order)
            
        orderdetail_row = Order_List.get_orderdetail()
        order_detail = []

        for j in orderdetail_row:
            orderdetail = {
                '訂單編號': j[0],
                '商品名稱': j[1],
                '商品單價': j[2],
                '訂購數量': j[3],
            }
            order_detail.append(orderdetail)

    return render_template('orderManager.html', orderData = order_data, orderDetail = order_detail, user=current_user.name)