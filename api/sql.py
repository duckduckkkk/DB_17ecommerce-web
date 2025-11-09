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
            INSERT INTO "User" ("Name", "Account", "Password", "phone", "address", "Identity") 
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (input_data['name'], input_data['account'], input_data['password'], input_data['phone'], input_data['address'], input_data['identity']))
    
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
        sql = '''SELECT * FROM cart, record 
                 WHERE cart.mid = %s::bigint 
                 AND cart.tno = record.tno::bigint'''
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def get_cart(user_id):
        sql = 'SELECT * FROM cart WHERE mid = %s'
        return DB.fetchone(sql, (user_id,))

    @staticmethod
    def add_cart(user_id, time):
        sql = 'INSERT INTO cart (mid, carttime, tno) VALUES (%s, %s, nextval(\'cart_tno_seq\'))'
        DB.execute_input(sql, (user_id, time))

    @staticmethod
    def clear_cart(user_id):
        sql = 'DELETE FROM cart WHERE mid = %s'
        DB.execute_input(sql, (user_id,))


class Product:

    @staticmethod
    def count():
        sql = 'SELECT COUNT(*) FROM "Product"'
        return DB.fetchone(sql)

    @staticmethod
    def get_product(product_id):
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
    def add_product(input_data):
        sql = '''
            INSERT INTO "Product" ("Product_id", "Stock_price", "Name", "Pstatus", "Description")
            VALUES (%s, %s, %s, %s, %s)
        '''
        DB.execute_input(sql, (
            input_data['Product_id'],
            input_data['Stock_price'],
            input_data['Name'],
            input_data['Pstatus'],
            input_data['Description']
        ))

    @staticmethod
    def delete_product(product_id):
        sql = 'DELETE FROM "Product" WHERE "Product_id" = %s'
        DB.execute_input(sql, (product_id,))


    @staticmethod
    def update_product(input_data):
        sql = '''
            UPDATE "Product"
            SET "Stock_price" = %s, "Name" = %s, "Pstatus" = %s, "Description" = %s
            WHERE "Product_id" = %s
        '''
        DB.execute_input(sql, (
            input_data['Stock_price'],
            input_data['Name'],
            input_data['Pstatus'],
            input_data['Description'],
            input_data['Product_id']
        ))

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
