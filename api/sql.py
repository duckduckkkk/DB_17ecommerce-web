import os
from typing import Optional
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
DBNAME = os.getenv('DB_NAME')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')

class DB:
    connection_pool = pool.SimpleConnectionPool(
        1, 100,  # 最小和最大連線數
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )

    @staticmethod
    def connect():
        return DB.connection_pool.getconn()

    @staticmethod
    def release(connection):
        DB.connection_pool.putconn(connection)

    @staticmethod
    def execute_input(sql, input):
        if not isinstance(input, (tuple, list)):
            raise TypeError(f"Input should be a tuple or list, got: {type(input).__name__}")
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                connection.commit()
        except psycopg2.Error as e:
            print(f"Error executing SQL: {e}")
            connection.rollback()
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def execute(sql):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
        except psycopg2.Error as e:
            print(f"Error executing SQL: {e}")
            connection.rollback()
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def fetchall(sql, input=None):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise e
        finally:
            DB.release(connection)

    @staticmethod
    def fetchone(sql, input=None):
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                return cursor.fetchone()
        except psycopg2.Error as e:
            print(f"Error fetching data: {e}")
            raise e
        finally:
            DB.release(connection)
    @staticmethod
    def execute_return(sql, input=None):
        """
        執行 INSERT/UPDATE/DELETE 並回傳 RETURNING 的結果
        用法:
            sql = 'INSERT INTO "Order" ("Total_amount","Green_delivery","Cart_id","User_id") VALUES (%s,%s,%s,%s) RETURNING "Order_id"'
            order_id = DB.execute_return(sql, (total, green_delivery, cart_id, user_id))
        """
        connection = DB.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, input)
                result = cursor.fetchone()  # 取第一列
                connection.commit()
                return result[0] if result else None
        except psycopg2.Error as e:
            print(f"Error executing return query: {e}")
            raise e
        finally:
            DB.release(connection)

    
class Supplier:
    @staticmethod
    def get_supplier_name(supplier_id):
        sql = 'SELECT "Supplier_id" FROM "Supplier" WHERE "Supplier_id" = %s'
        return DB.fetchall(sql, (supplier_id,))

    @staticmethod
    def get_supplier_by_name(name):
        """依廠商名稱查詢廠商資訊"""
        sql = 'SELECT "Supplier_id", "Sname", "Contact_info" FROM "Supplier" WHERE "Sname" = %s'
        return DB.fetchone(sql, (name,))

    @staticmethod
    def get_max_supplier_id():
        """取得當前最大 Supplier_id"""
        sql = 'SELECT MAX("Supplier_id") FROM "Supplier"'
        result = DB.fetchone(sql)
        if result and result[0] is not None:
            return int(result[0])
        else:
            return 0

    @staticmethod
    def add_supplier(data):
        """新增一筆廠商資料"""
        sql = '''
            INSERT INTO "Supplier" ("Supplier_id", "Sname", "Contact_info")
            VALUES (%s, %s, %s)
        '''
        # 使用 execute_input 因為需要帶參數
        DB.execute_input(sql, (data['Supplier_id'], data['Sname'], data['Contact_info']))

class Member:
    @staticmethod
    def get_member(account):
        sql = 'SELECT "Account", "Password", "User_id", "Identity", "Name" FROM "User" WHERE "Account" = %s'
        return DB.fetchall(sql, (account,))

    @staticmethod
    def get_all_account():
        sql = 'SELECT "Account" FROM "User"'
        return DB.fetchall(sql)

    @staticmethod
    def create_member(input_data):
        sql = '''
            INSERT INTO "User" ("User_id", "Name", "Account", "Password", phone, address, "Identity")
            VALUES (
                (SELECT COALESCE(MAX("User_id"), 0) + 1 FROM "User"),
                %s, %s, %s, %s, %s, %s
            );
        '''
        DB.execute_input(sql, (
            input_data['name'],
            input_data['account'],    # <-- 這裡一定要是使用者輸入的 account
            input_data['password'],
            input_data['phone'],
            input_data['address'],
            input_data['identity']
        ))


    @staticmethod
    def delete_product(tno, pid):
        sql = 'DELETE FROM record WHERE tno = %s and pid = %s'
        DB.execute_input(sql, (tno, pid))

    @staticmethod
    def get_order(userid):
        sql = 'SELECT * FROM "Order" WHERE "User_id" = %s ORDER BY "Order_date" DESC'
        return DB.fetchall(sql, (userid,))

    @staticmethod
    def get_role(userid):
        sql = 'SELECT "Identity", "Name" FROM "User" WHERE "User_id" = %s'
        return DB.fetchone(sql, (userid,))


class Cart:
    @staticmethod
    def check(user_id):
        sql = '''SELECT * FROM "Cart", "Cart_info"
                 WHERE "Cart"."User_id" = %s::bigint 
                 AND "Cart"."Cart_id" = "Cart_info"."Cart_id"::bigint'''
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def get_cart(user_id):
        """取得指定使用者的購物車"""
        sql = 'SELECT * FROM "Cart" WHERE "User_id" = %s'
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def add_cart(user_id):
        """新增購物車"""
        sql = 'INSERT INTO "Cart" ("User_id") VALUES (%s)'
        DB.execute_input(sql, (user_id,))

    @staticmethod
    def clear_cart(user_id):
        """清空購物車"""
        sql = 'DELETE FROM "Cart" WHERE "User_id" = %s'
        DB.execute_input(sql, (user_id,))


class Product:
    @staticmethod
    def get_max_product_id():
        """取得 Product 表最大 Product_id"""
        sql = 'SELECT MAX("Product_id") FROM "Product"'
        result = DB.fetchone(sql)
        if result and result[0] is not None:
            return int(result[0])
        else:
            return 0

    @staticmethod
    def add_product(data):
        sql = '''
            INSERT INTO "Product" 
            ("Product_id", "Supplier_id", "Stock_price", "Name", "Pstatus", "Description", "Category")
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (
            data['Product_id'], data['Supplier_id'], data['Stock_price'],
            data['Name'], data['Pstatus'], data['Description'], data['Category']
        ))



    @staticmethod
    def count():
        sql = 'SELECT COUNT(*) FROM "Product"'
        return DB.fetchone(sql)

    @staticmethod
    def get_product(product_id):
        sql = '''
        SELECT p.*, s."Sname"
        FROM "Product" p
        JOIN "Supplier" s ON p."Supplier_id" = s."Supplier_id"
        WHERE p."Product_id" = %s
    '''
        return DB.fetchone(sql, (product_id,))
    
    @staticmethod
    def get_product_by_pid(product_id):
        # 假設 "Product_id" 在資料庫中是唯一的
        sql = 'SELECT * FROM "Product" WHERE "Product_id" = %s'
        return DB.fetchone(sql, (product_id,))
    
    @staticmethod
    def get_all_product():
        sql = 'SELECT * FROM "Product"'
        return DB.fetchall(sql)

    @staticmethod
    def get_name(product_id):
        sql = 'SELECT "Name" FROM "Product" WHERE "Product_id" = %s'
        result = DB.fetchone(sql, (product_id,))
        return result[0] if result else None

    @staticmethod
    def delete_product(product_id):
        sql = 'DELETE FROM "Product" WHERE "Product_id" = %s'
        DB.execute_input(sql, (product_id,))


    @staticmethod
    def update_product(input_data):
        sql = '''
            UPDATE "Product"
            SET "Stock_price" = %s, 
                "Name" = %s, 
                "Pstatus" = %s, 
                "Description" = %s,
                "Supplier_id" = %s,
                "Category" = %s
            WHERE "Product_id" = %s
        '''
        
        # 2. 傳入的 tuple 資料也加入 "Category"
        # (鍵名 'Category' 必須和 manager.py 傳來的一致)
        val = (
            input_data['Stock_price'],
            input_data['Name'],
            input_data['Pstatus'],
            input_data['Description'],
            input_data['Supplier_id'],
            input_data['Category'], # 新增 'Category'
            input_data['Product_id'] # Product_id 放在最後對應 WHERE
        )
        DB.execute_input(sql, val)
    
class Cart_Info:
    @staticmethod
    def check_product(cart_id, product_id):
        """檢查購物車裡是否已經有這個商品"""
        sql = 'SELECT * FROM "Cart_Info" WHERE "Cart_id" = %s AND "Product_id" = %s'
        return DB.fetchone(sql, (cart_id, product_id))

    @staticmethod
    def add_product(cart_id, user_id, supplier_id, product_id, amount=1):
        """把商品加入購物車"""
        sql = '''
            INSERT INTO "Cart_Info" ("Cart_id", "User_id", "Supplier_id", "Product_id", "Amount")
            VALUES (%s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (cart_id, user_id, supplier_id, product_id, amount))

    @staticmethod
    def update_amount(cart_id, product_id, amount):
        """更新商品數量"""
        sql = 'UPDATE "Cart_Info" SET "Amount" = %s WHERE "Cart_id" = %s AND "Product_id" = %s'
        DB.execute_input(sql, (amount, cart_id, product_id))

    @staticmethod
    def get_cart_products(cart_id):
        """取得購物車裡所有商品"""
        sql = '''
            SELECT ci."Product_id", p."Name", p."Stock_price", ci."Amount", p."Supplier_id"
            FROM "Cart_Info" ci
            JOIN "Product" p ON ci."Product_id" = p."Product_id"
            WHERE ci."Cart_id" = %s
        '''
        return DB.fetchall(sql, (cart_id,))

    @staticmethod
    def update_product_info(cart_id, product_id, amount, green, condition, base_price):
        """
        更新購物車商品資訊
        cart_id: 購物車編號
        product_id: 商品編號
        amount: 商品數量
        green: 'Y' 或 'N'
        condition: '全新' 或 '二手'
        base_price: 商品原價
        """
        # 計算折扣後價格
        price = base_price
        if condition == '二手':
            price = price * 0.6  # 打 0.6 折

        # 加上運費
        if green == 'Y':
            shipping = 30
        else:
            shipping = 50

        total_price = price + shipping

        sql = '''UPDATE "Cart_Info"
                 SET "Amount" = %s,
                     "Green" = %s,
                     "Condition" = %s,
                     "Price" = %s
                 WHERE "Cart_id" = %s AND "Product_id" = %s'''
        DB.execute_input(sql, (amount, green, condition, total_price, cart_id, product_id))


class Record:
    @staticmethod
    def get_total_money(tno):
        sql = 'SELECT SUM(total) FROM record WHERE tno = %s'
        return DB.fetchone(sql, (tno,))[0]

    @staticmethod
    def check_product(pid, tno):
        sql = 'SELECT * FROM record WHERE pid = %s and tno = %s'
        return DB.fetchone(sql, (pid, tno))

    @staticmethod
    def get_price(pid):
        sql = 'SELECT price FROM product WHERE pid = %s'
        return DB.fetchone(sql, (pid,))[0]

    @staticmethod
    def add_product(input_data):
        sql = 'INSERT INTO record (pid, tno, amount, saleprice, total) VALUES (%s, %s, 1, %s, %s)'
        DB.execute_input(sql, (input_data['pid'], input_data['tno'], input_data['saleprice'], input_data['total']))

    @staticmethod
    def get_record(tno):
        sql = 'SELECT * FROM record WHERE tno = %s'
        return DB.fetchall(sql, (tno,))

    @staticmethod
    def get_amount(tno, pid):
        sql = 'SELECT amount FROM record WHERE tno = %s and pid = %s'
        return DB.fetchone(sql, (tno, pid))[0]

    @staticmethod
    def update_product(input_data):
        sql = 'UPDATE record SET amount = %s, total = %s WHERE pid = %s and tno = %s'
        DB.execute_input(sql, (input_data['amount'], input_data['total'], input_data['pid'], input_data['tno']))

    @staticmethod
    def delete_check(pid):
        sql = 'SELECT * FROM record WHERE pid = %s'
        return DB.fetchone(sql, (pid,))

    @staticmethod
    def get_total(tno):
        sql = 'SELECT SUM(total) FROM record WHERE tno = %s'
        return DB.fetchone(sql, (tno,))[0]


class Order_List:
    @staticmethod
    def add_order(input_data):
        sql = 'INSERT INTO order_list (oid, mid, ordertime, price, tno) VALUES (DEFAULT, %s, TO_TIMESTAMP(%s, %s), %s, %s)'
        DB.execute_input(sql, (input_data['mid'], input_data['ordertime'], input_data['format'], input_data['total'], input_data['tno']))

    @staticmethod
    def get_order():
        sql = '''
            SELECT O."Order_id" AS 訂單編號,
                   U."Name" AS 訂購人,
                   O."Total_amount" AS 訂單總價,
                   O."Order_date" AS 訂單時間,
                   O."Green_delivery" AS 綠色運送            
            FROM "Order" O
            JOIN "User" U ON O."User_id"= U."User_id"
            ORDER BY O."Order_date" DESC
        '''
        return DB.fetchall(sql)

    @staticmethod
    def get_orderdetail():
        sql = '''
        SELECT O."Order_id", P."Name", P."Stock_price" , O."Quantity" 
        FROM "Order_Item" O
        JOIN "Product" P ON O."Product_id" = P."Product_id"
        '''
        return DB.fetchall(sql)


class Analysis:
    @staticmethod
    def month_price(i):
        sql = 'SELECT EXTRACT(MONTH FROM "Order_date"), SUM("Total_amount") FROM "Order" WHERE EXTRACT(MONTH FROM "Order_date") = %s GROUP BY EXTRACT(MONTH FROM "Order_date")'
        return DB.fetchall(sql, (i,))

    @staticmethod
    def month_count(i):
        sql = 'SELECT EXTRACT(MONTH FROM "Order_date"), COUNT("Order_id") FROM "Order" WHERE EXTRACT(MONTH FROM "Order_date") = %s GROUP BY EXTRACT(MONTH FROM "Order_date")'
        return DB.fetchall(sql, (i,))

    @staticmethod
    # api/sql.py
    def category_sale():
        sql = '''
            SELECT 
                s."Sname" AS name,
                COALESCE(SUM(oi."Quantity" * p."Stock_price"), 0) AS value
            FROM "Supplier" s
            LEFT JOIN "Product" p ON p."Supplier_id" = s."Supplier_id"
            LEFT JOIN "Order_Item" oi ON oi."Product_id" = p."Product_id"
            GROUP BY s."Sname"
            ORDER BY value DESC;
        '''
        return DB.fetchall(sql)


    @staticmethod
    def member_sale():
        sql = '''
            SELECT SUM(O."Total_amount") AS total_amount, U."Name"
            FROM "Order" O
            JOIN "User" U ON O."User_id" = U."User_id"
            WHERE U."Identity" = 'user'
            GROUP BY U."User_id", U."Name"
            ORDER BY total_amount DESC
        '''
        return DB.fetchall(sql, ('user',))

    @staticmethod
    def member_sale_count():
        sql = '''
            SELECT COUNT(*) AS order_count, U."User_id", U."Name"
            FROM "Order" O
            JOIN "User" U ON O."User_id" = U."User_id"
            WHERE U."Identity" = 'user'
            GROUP BY U."User_id", U."Name"
            ORDER BY order_count DESC
        '''
        return DB.fetchall(sql, ('user',))