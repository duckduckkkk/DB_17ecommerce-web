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
        book_row = cursor.fetchall()
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
        category = data[4]     
        description = data[5] 
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
@login_required  # 使用者登入後才可以看
def cart():
    # 防止管理者誤闖
    if request.method == 'GET' and current_user.role == 'manager':
        flash('No permission')
        return redirect(url_for('manager.home'))

    # 加入購物車
    if request.method == 'POST':
        # 新增商品
        if "pid" in request.form:
            pid = request.form.get("pid")
            print("接收到的 pid:", pid)
           

            if not pid:
                flash('Product ID is missing.')
                return redirect(url_for('bookstore.cart'))

            # 取得使用者購物車，若沒有就建立
            data = Cart.get_cart(current_user.id)
            if data is None:
                Cart.add_cart(current_user.id)
                data = Cart.get_cart(current_user.id)

            cart_id = data[1]  # (user_id, cart_id)
            product = Product.get_product(pid)
            if not product:
                flash('Product not found.')
                return redirect(url_for('bookstore.bookstore'))

            supplier_id = product[1]      # 假設 Product(supplier_id, product_id, stock_price, name, ...)
            price = product[2]            # 商品價格

            # 檢查購物車裡是否已有該商品
            exist = Cart_Info.check_product(cart_id, pid)
            if exist is None:
                # 沒有的話加入
                Cart_Info.add_product(cart_id, current_user.id, supplier_id, pid, 1)
                
            else:
                # 有的話數量+1
                new_amount = exist[4] + 1  # 假設 Amount 在第5欄
                Cart_Info.update_amount(cart_id, pid, new_amount)

            flash("商品已加入購物車！")
            

        # 刪除商品
        elif "delete" in request.form:
            pid = request.form.get("delete")
            data = Cart.get_cart(current_user.id)
            if data:
                cart_id = data[1]
                sql = 'DELETE FROM "Cart_Info" WHERE "Cart_id" = %s AND "Product_id" = %s'
                DB.execute_input(sql, (cart_id, pid))
                flash("商品已刪除")

        # 更新數量（使用者手動修改）
        elif "user_edit" in request.form:
            change_order()
            flash("已更新購物車")
            return redirect(url_for('store.cart'))

        # 結帳
        elif "buy" in request.form:
            flash("功能尚未實作：導向結帳頁")
            return redirect(url_for('bookstore.order'))

    # 顯示購物車內容
    product_data = only_cart()
    if product_data == 0:
        return render_template('empty.html', user=current_user.name)
    else:
        return render_template('cart.html', data=product_data, user=current_user.name)

@store.route('/order')
def order():
    data = Cart.get_cart(current_user.id)
    cart_id = data[1]
    

    product_rows = Cart_Info.get_cart_products(cart_id)  
    product_data = []

    total = 0
    for row in product_rows:
        product = {
            '商品編號': row[0],
            '商品名稱': row[1],
            '商品價格': float(row[2]),
            '數量': row[3]
        }
        total += float(row[2]) * int(row[3])
        product_data.append(product)
    


    return render_template('order.html', data=product_data, total=total, user=current_user.name)

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
        return 0

    cart_id = cart_data[1]  # (user_id, cart_id)
    product_rows = Cart_Info.get_cart_products(cart_id)

    if not product_rows:
        return 0

    product_data = []
    for row in product_rows:
        product_data.append({
            'Product_id': row[0],
            'Name': row[1],
            'Stock_price': row[2],
            'Amount': row[3]
        })

    return product_data