import re
from typing_extensions import Self
from flask import Flask, request, template_rendered, Blueprint
from flask import url_for, redirect, flash
from flask import render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from numpy import identity, prod
import random, string
from sqlalchemy import null
from flask import session
from link import *
import math
from api.sql import DB

from base64 import b64encode
from api.sql import Member, Order_List, Product, Cart_Info, Cart,Supplier

store = Blueprint('bookstore', __name__, template_folder='../templates')

@store.route('/', methods=['GET', 'POST'])
@login_required
def bookstore():
    result = Product.count()
    count = math.ceil(result[0]/9)
    flag = 0
    
    if request.method == 'GET':
        if(current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager.home'))

    if 'keyword' in request.args and 'page' in request.args:
        total = 0
        single = 1
        page = int(request.args['page'])
        start = (page - 1) * 9
        end = page * 9
        search = request.values.get('keyword')
        keyword = search
        
        cursor.execute('SELECT * FROM "Product" WHERE "Name" LIKE %s', ('%' + search + '%',)) 
        book_row = cursor.fetchall()  # <- 加上這行
        book_data = []
        final_data = []
        
        for i in book_row:
            book = {
                'Product_id': i[0],
                'Name': i[3],
                'Stock_price': i[2],
                'Supplier_id': i[1],
                'Pstatus': i[4],
                'Description': i[5]
            }
            book_data.append(book)
            total = total + 1
        
        if(len(book_data) < end):
            end = len(book_data)
            flag = 1
            
        for j in range(start, end):
            final_data.append(book_data[j])
            
        count = math.ceil(total/9)
        
        return render_template('bookstore.html', single=single, keyword=search, product_data=book_data, user=current_user.name, page=1, flag=flag, count=count) 

    
    elif 'pid' in request.args: 
        pid = int(request.args['pid'])
        data = Product.get_product(pid)
        
        
      
        pname = data[3]      
        price = data[2]      
        category = data[5]     
        description = data[4] 
        Sname=data[7]
        image = 'sdg.jpg'
        
        product = {
            'Product_id': pid,  
            'Name': pname,
            'Stock_price': price,
            'Pstatus': category,
            'Description': description,
            '商品圖片': image,
            'Sname':Sname,
            'Amount': 1
        }

        return render_template('product.html', data = product, user=current_user.name)
    
    elif 'page' in request.args:
        page = int(request.args['page'])
        start = (page - 1) * 9
        end = page * 9
        
        book_row = Product.get_all_product() 
        book_data = []
        final_data = []
        
        for i in book_row:
            book = {
                'Product_id': i[0],
                'Name': i[3],
                'Stock_price': i[2],
                'Supplier_id': i[1],
                'Pstatus': i[4],
                'Description': i[5]
            }
            book_data.append(book)
            
        if(len(book_data) < end):
            end = len(book_data)
            flag = 1
            
        for j in range(start, end):
            final_data.append(book_data[j])
        
        return render_template('bookstore.html', product_data=final_data, user=current_user.name, page=page, flag=flag, count=count) 
    
    elif 'keyword' in request.args:
        single = 1
        search = request.values.get('keyword')
        keyword = search
        cursor.execute('SELECT * FROM "Product" WHERE "Name" LIKE %s', ('%' + search + '%',)) 
        book_data = []
        total = 0
        
        for i in book_row:
            book = {
                'Product_id': i[0],
                'Name': i[3],
                'Stock_price': i[2],
                'Supplier_id': i[1],
                'Pstatus': i[4],
                'Description': i[5]
            }

            book_data.append(book)
            total = total + 1
            
        if(len(book_data) < 9):
            flag = 1
        
        count = math.ceil(total/9)    
        
        return render_template('bookstore.html', keyword=search, single=single, product_data=book_data, user=current_user.name, page=1, flag=flag, count=count)  # MODIFIED   
    
    else:
        book_row = Product.get_all_product()
        book_data = []
        temp = 0
        for i in book_row:
            book = {
                'Product_id': i[0],
                'Name': i[3],
                'Stock_price': i[2],
                'Supplier_id': i[1],
                'Pstatus': i[4],
                'Description': i[5]
            }
            if len(book_data) < 9:
                book_data.append(book)
        
        return render_template('bookstore.html', product_data=book_data, user=current_user.name, page=1, flag=flag, count=count)  # MODIFIED

# 會員購物車
@store.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    # 防止管理者誤闖
    if current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    # 處理 POST 請求
    if request.method == 'POST':
        # 新增商品到購物車
        if "pid" in request.form:
            pid = request.form.get("pid")
            if not pid:
                flash('Product ID is missing.')
                return redirect(url_for('bookstore.cart'))

            # 取得使用者購物車，若沒有就建立
            data = Cart.get_cart(current_user.id)
            if data is None:
                Cart.add_cart(current_user.id)
                data = Cart.get_cart(current_user.id)

            cart_id = data[0]  # <-- 確認抓 cart_id
            product = Product.get_product(pid)
            if not product:
                flash('Product not found.')
                return redirect(url_for('bookstore.bookstore'))

            supplier_id = product[1]
            price = product[2]

            exist = Cart_Info.check_product(cart_id, pid)
            if exist is None:
                Cart_Info.add_product(cart_id, current_user.id, supplier_id, pid, 1)
            else:
                new_amount = exist[4] + 1
                Cart_Info.update_amount(cart_id, pid, new_amount)

            flash("商品已加入購物車！")

        # 刪除商品
        elif "delete" in request.form:
            pid = request.form.get("delete")
            data = Cart.get_cart(current_user.id)
            if data:
                cart_id = data[0]  # <-- 一樣抓正確 cart_id
                sql = 'DELETE FROM "Cart_Info" WHERE "Cart_id" = %s AND "Product_id" = %s'
                DB.execute_input(sql, (cart_id, pid))
                flash("商品已刪除")

        # 更新數量
        elif "user_edit" in request.form:
            change_order()
            flash("已更新購物車")
            return redirect(url_for('bookstore.cart'))

        # 結帳
        elif "buy" in request.form:
            cart_data = Cart.get_cart(current_user.id)
            cart_id = cart_data[0]
            green_delivery = request.form.get('green_delivery', 'N')
            condition_dict = {pid.replace('condition_', ''): request.form[pid] 
                              for pid in request.form if pid.startswith('condition_')}
            session['green_delivery'] = green_delivery
            session['condition_dict'] = condition_dict
            return redirect(url_for('bookstore.order'))

    # 顯示購物車內容
    product_data = only_cart()
    
    # 空購物車直接導向 empty.html
    if not product_data:
        return render_template('empty.html', user=current_user.name)

    # 如果有商品，顯示 cart.html
    return render_template('cart.html', data=product_data, user=current_user.name)

@store.route('/order', methods=['GET', 'POST'])
@login_required
def order():

    data = Cart.get_cart(current_user.id)
    cart_id = data[1]
    product_rows = Cart_Info.get_cart_products(cart_id) 
    green_delivery = session.get('green_delivery', 'N')
    condition_dict = session.get('condition_dict', {})

    

    product_data = []
    total = 0        # 訂單總價
    used_discount = 0  # 二手折扣金額
    green_discount = 0 # 綠色運輸折扣金額
    ttotal=0

    for row in product_rows:
        pid = str(row[0])
        condition = condition_dict.get(pid, 'new')  # 預設為全新

        price = float(row[2])
        amount = int(row[3])
        ttotal += price * amount


        # 如果是二手商品，打0.6折
        discounted_price = price * 0.6 if condition == 'used' else price
        if condition == 'used':
            used_discount += price * amount - discounted_price * amount

        # 計算訂單總價
        total += discounted_price * amount
      

        product_data.append({
            '商品編號': row[0],
            '商品名稱': row[1],
            '商品價格': price,
            '數量': amount,
            '商品狀態': condition,
            '綠色運送': green_delivery
        })

    # 計算綠色運輸運費折扣
    if green_delivery == 'Y':
        green_discount = 60 - 30  # 原本運費50，綠色運送30
        total += 30  # 實際運費30
    else:
        total += 60  # 不選綠色運送

    return render_template(
        'order.html',
        data=product_data,
        total=total,
        used_discount=used_discount,
        green_discount=green_discount,
        user=current_user.name,
        ttotal=ttotal
    )
@store.route('/confirm_order', methods=['POST'])
@login_required
def confirm_order():
    print("🟢 使用者按下下訂單")

    user_id = current_user.id
    cart_data = Cart.get_cart(user_id)
    if not cart_data:
        flash("購物車為空，無法建立訂單")
        return redirect(url_for('bookstore.cart'))

    cart_id = cart_data[0]
    green_delivery = session.get('green_delivery', 'N')

    # 取得購物車商品
    product_rows = Cart_Info.get_cart_products(cart_id)
    if not product_rows:
        flash("購物車無商品")
        return redirect(url_for('bookstore.cart'))

    # 計算總金額（不含運費與折扣）
    total = 0
    for row in product_rows:
        price = float(row[2])
        amount = int(row[3])
        total += price * amount

    # 運費
    shipping_fee = 30 if green_delivery == 'Y' else 60
    total_amount = total + shipping_fee

    # 取得下一個 Order_id（如果表沒有自動遞增）
    max_order_id = DB.fetchone('SELECT MAX("Order_id") FROM "Order"')[0] or 0
    next_order_id = max_order_id + 1

    # 建立訂單
    sql_order = '''
        INSERT INTO "Order" ("Order_id", "Total_amount", "Order_date", "Green_delivery", "Cart_id", "User_id")
        VALUES (%s, %s, NOW(), %s, %s, %s);
    '''
    DB.execute_input(sql_order, (next_order_id, total_amount, green_delivery, cart_id, user_id))
    print(f"✅ 新訂單建立成功，Order_id={next_order_id}")

    # 從 session 拿商品狀態
    condition_dict = session.get('condition_dict', {})

    # 建立 Order_Item
    for row in product_rows:
        product_id = row[0]
        supplier_id = Product.get_product(product_id)[1]
        amount = row[3]
        # 從 condition_dict 取得狀態，預設 new
        item_condition = condition_dict.get(str(product_id), 'new')

        # 取得下一個 OrderIItem_id
        max_item_id = DB.fetchone('SELECT MAX("OrderItem_id") FROM "Order_Item"')[0] or 0
        next_item_id = max_item_id + 1

        sql_item = '''
            INSERT INTO "Order_Item" 
            ("OrderItem_id", "Order_id", "Product_id", "Supplier_id", "User_id", "Cart_id", "Shipping_fee", "Quantity", "Condition")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''
        DB.execute_input(sql_item, (next_item_id, next_order_id, product_id, supplier_id, user_id, cart_id, shipping_fee, amount, item_condition))

    print("📦 所有商品已寫入 Order_Item")
            # 清空購物車
    sql_clear_cart = 'DELETE FROM "Cart_Info" WHERE "Cart_id" = %s'
    DB.execute_input(sql_clear_cart, (cart_id,))
    print("🗑 購物車已清空")

    flash("訂單建立成功！")
    return render_template('complete.html', message="訂單建立成功！")


@store.route('/orderlist')
def orderlist():
    if "OrderItem_id" in request.args :
        pass
    
    user_id = current_user.id

    data = Member.get_order(user_id)
    orderlist = []

    for i in data:
        temp = {
            '訂單編號': i[0],
            '訂單總價': i[1],
            '訂單時間': i[2],
            '綠色運送': i[3],
        }
        orderlist.append(temp)
    
    orderdetail_row = Order_List.get_orderdetail()
    orderdetail = []

    for j in orderdetail_row:
        temp = {
            '訂單編號': j[0],
            '商品名稱': j[1],
            '商品單價': j[2],
            '訂購數量': j[3],
        }
        orderdetail.append(temp)


    return render_template('orderlist.html', data=orderlist, detail=orderdetail, user=current_user.name)
def change_order():
    data = Cart.get_cart(current_user.id)
    cart_id = data[1]
    product_rows = Cart_Info.get_cart_products(cart_id)

    for row in product_rows:
        product_id = row[0]
        current_amount = row[3]
        new_amount = int(request.form.get(str(product_id), current_amount))
        if new_amount != current_amount:
            Cart_Info.update_amount(cart_id, product_id, new_amount)
            print(f'Product {product_id} amount changed: {current_amount} -> {new_amount}')

    return 0


def only_cart():
    cart_data = Cart.get_cart(current_user.id)
    if not cart_data:
        return []

    cart_id = cart_data[1]
    product_rows = Cart_Info.get_cart_products(cart_id)

    if not product_rows:
        return []

    product_data = []
    for row in product_rows:
        product_data.append({
            'Product_id': row[0],
            'Name': row[1],
            'Stock_price': row[2],
            'Amount': row[3]
        })

    return product_data