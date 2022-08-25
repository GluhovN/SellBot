import sqlite3
from sqlite3 import connect

from bit import PrivateKeyTestnet


async def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


async def new_wallet():
    return PrivateKeyTestnet().to_wif()


class DB:
    def __init__(self):
        self.conn = connect('users_data.sqlite')
        self.cursor = self.conn.cursor()
        self.conn.row_factory = dict_factory
        self.init_tables()

    def init_tables(self):
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS admin_config (
        qiwi_balance REAL DEFAULT 0.0,
        bit_balance REAL DEFAULT 0.0,
        capitalist_balance REAL DEFAULT 0.0,
        earned REAL DEFAULT 0,
        commission REAL DEFAULT 30,
        support_group TEXT,
        log_check_time REAL DEFAULT 3600.0,
        referrals REAL DEFAULT 10.0
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INT,
        bit_wif TEXT,
        username TEXT,
        consent_to_mailing BOOLEAN DEFAULT TRUE,
        balance INTEGER DEFAULT 0,
        pay_id TEXT,
        apirone_pay_address TEXT,
        user_agreement BOOLEAN DEFAULT FALSE,
        purchases_count INTEGER DEFAULT 0,
        replenishment_amount INTEGER DEFAULT 0,
        referals INTEGER DEFAULT 0,
        earned_from_referrals INTEGER DEFAULT 0,
        qiwi_balance REAL DEFAULT 0.0,
        bit_balance REAL DEFAULT 0.0,
        capitalist_balance REAL DEFAULT 0.0,
        admin_gift REAL DEFAULT 0.0,
        last_payment REAL
        )
        """)

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sellers (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_tg_id INTEGER,
                seller_username TEXT,
                admin_approve BOOLEAN,
                answers TEXT,
                invalid_count INTEGER DEFAULT 0,
                all_goods INTER DEFAULT 0,
                qiwi_balance REAL DEFAULT 0.0,
                bit_balance REAL DEFAULT 0.0,
                capitalist_balance REAL DEFAULT 0.0,
                became_partner REAL,
                is_designer_only BOOLEAN DEFAULT TRUE,
                position_count INTEGER DEFAULT 0,
                commission REAL,
                positions_id INTEGER,
                last_mailing REAL,
                log_check_time REAL
                )
                """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS designers (
            position_id INTEGER PRIMARY KEY AUTOINCREMENT,
            designer_nick_name TEXT,
            designer_login TEXT,
            designer_price REAL,
            designer_portfolio_link TEXT,
            category_id INTEGER,
            rating INTEGER DEFAULT 0,
            creatives_quality INTEGER DEFAULT 0,
            professionalism INTEGER DEFAULT 0,
            creatives_count INTEGER DEFAULT 0,
            designer_banner TEXT,
            designer_banner_type TEXT,
            designer_tg_id TEXT,
            rating_count INTEGER DEFAULT 0
            )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY,
        category_name TEXT,
        category_desc TEXT,
        category_banner TEXT,
        category_banner_type TEXT,
        category_type TEXT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
        subcategory_id INTEGER PRIMARY KEY,
        subcategory_name TEXT,
        subcategory_desc TEXT,
        subcategory_banner TEXT,
        subcategory_banner_type TEXT,
        subcategory_type INT
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS positions (
        position_id INTEGER PRIMARY KEY,
        position_name TEXT,
        position_desc TEXT,
        position_banner TEXT,
        position_banner_type TEXT,
        position_price REAL,
        subcategory_id INT,
        seller_id INT 
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
        qiwi_number TEXT,
        qiwi_token TEXT,
        qiwi_priv_key TEXT,
        apirone_wallet_id TEXT,
        apirone_transfer_key TEXT,
        capitalist_login TEXT,
        capitalist_password TEXT,
        new_data BOOLEAN
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS mailing (
        from_id INTEGER,
        to_id INTEGER 
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS goods (
        product_id INTEGER PRIMARY KEY,
        product_description TEXT,
        product_file TEXT,
        seller_id INTEGER,
        position_id INTEGER,
        is_invalid BOOLEAN DEFAULT FALSE,
        product_price REAL,
        load_time REAL,
        is_sold BOOLEAN DEFAULT FALSE
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS holds (
        hold_id INTEGER PRIMARY KEY,
        seller_id INTEGER,
        purchase_id INTEGER,
        qiwi REAL,
        bitcoin REAL,
        capitalist REAL,
        test REAL,
        hold_start_date REAL 
        )""")
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS purchases (
        purchase_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        product_id INTEGER,
        buy_date REAL
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY,
        orderer_id INTEGER,
        designer_id INTEGER,
        order_price REAL,
        order_file TEXT,
        is_ended BOOLEAN DEFAULT FALSE
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS payment_requests(
        request_id INTEGER PRIMARY KEY,
        seller_id INTEGER,
        payment_amount REAL,
        payment_type TEXT,
        payment_requisites TEXT
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS designers_ratings (
        user_id INTEGER, 
        designer_id INTEGER 
        )
        """)
        self.cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS referrals (
        user_id INTEGER , 
        referral_login TEXT 
        )
        """)
        self.cursor.execute("INSERT INTO payments (new_data) VALUES (False)")
        self.init_admin_config()
        self.conn.commit()

    async def add_user(self, tg_id, username):
        self.cursor.execute(f"""
        INSERT INTO users (tg_id, bit_wif, username) VALUES (
        {tg_id}, '{await new_wallet()}', '{username}'
        )
        """)
        self.conn.commit()

    async def get_all_users(self):
        self.cursor.execute("""
        SELECT * FROM users WHERE 1
        """)
        return self.cursor.fetchall()

    async def get_user(self, tg_id):
        self.cursor.execute(f"""
        SELECT * FROM users WHERE tg_id = {tg_id}
        """)
        return self.cursor.fetchone()

    async def user_exists(self, tg_id):
        self.cursor.execute(f"""
        SELECT * FROM users WHERE
        tg_id = {tg_id}
        """)
        if self.cursor.fetchone() is None:
            return False
        return True

    async def add_category(self, category_name, category_desc, category_banner, category_banner_type, category_type):
        self.cursor.execute(f"""
        INSERT INTO categories (category_name, category_desc, category_banner, category_banner_type, category_type)
        VALUES ('{category_name}', '{category_desc}', '{category_banner}', '{category_banner_type}', '{category_type}')
        """)
        self.conn.commit()

    async def get_category(self, category_id):
        self.cursor.execute(f"""
        SELECT * FROM categories WHERE category_id = {category_id}
        """)
        return self.cursor.fetchone()

    async def get_all_categories(self, category_type):
        if category_type is None:
            self.cursor.execute(f"""
                    SELECT * FROM categories WHERE 1
                    """)
        else:
            self.cursor.execute(f"""
        SELECT * FROM categories WHERE category_type = '{category_type}'
        """)
        return self.cursor.fetchall()

    async def remove_category(self, category_id):
        self.cursor.execute(f"""
        DELETE FROM categories WHERE category_id = {category_id}
        """)
        self.cursor.execute(f"""
        DELETE FROM positions WHERE category_id = {category_id}
        """)
        self.cursor.execute(f"""
        DELETE FROM designers WHERE category_id = {category_id}
        """)
        self.conn.commit()

    async def add_position(self, position_name, position_desc, position_banner, position_banner_type, category_id):
        self.cursor.execute(f"SELECT * FROM positions WHERE position_name = '{position_name}'")
        res = self.cursor.fetchall()
        if len(res) != 0:
            self.cursor.execute(f"""
            UPDATE positions SET position_desc = '{position_desc}',
            position_banner = '{position_banner}',
            position_banner_type = '{position_banner_type}',
            category_id = {category_id}
            WHERE position_name = '{position_name}'
            """)
            self.conn.commit()
            return
        self.cursor.execute(f"""
        INSERT INTO positions (position_name, position_desc, position_banner, position_banner_type, category_id)
        VALUES ('{position_name}', '{position_desc}', '{position_banner}', 
        '{position_banner_type}', {category_id})
        """)
        self.conn.commit()

    async def add_seller_position(self, position_name, seller_id):
        self.cursor.execute(f"SELECT positions_id FROM sellers WHERE seller_tg_id = {seller_id}")
        positions = self.cursor.fetchone()[0]
        if positions != '' and positions is not None:
            positions_ids = positions.split(':')
            positions_names = []
            for pos in positions_ids:
                if pos != '':
                    res = await self.get_position_by_id(int(pos))
                    positions_names.insert(-1, res[1])
            if position_name in positions_names:
                return
            position = await self.get_position_by_name(position_name)
            self.cursor.execute(f"""
            UPDATE sellers SET positions_id = '{positions[0]}:{position[0]}:'
            WHERE seller_tg_id = {seller_id}
            """)
        else:
            position = await self.get_position_by_name(position_name)
            print(position)
            self.cursor.execute(f"""
                        UPDATE sellers SET positions_id = '{position[0]}:'
                        WHERE seller_tg_id = {seller_id}
                        """)
        self.conn.commit()

    async def get_position_by_name(self, position_name):
        self.cursor.execute(f"SELECT * FROM positions WHERE position_name = '{position_name}'")
        return self.cursor.fetchone()

    async def get_position(self, category_id):
        self.cursor.execute(f"""
        SELECT * FROM positions WHERE category_id = {category_id}
        """)
        return self.cursor.fetchone()

    async def get_position_by_id(self, position_id):
        self.cursor.execute(f"""
                SELECT * FROM positions WHERE position_id = {position_id}
                """)
        return self.cursor.fetchone()

    async def get_all_positions(self, category_id):
        self.cursor.execute(f"""
        SELECT * FROM positions WHERE category_id = {category_id}
        """)
        return self.cursor.fetchall()

    async def get_all_designers(self, category_id):
        self.cursor.execute(f"""
        SELECT * FROM designers WHERE category_id = {category_id}
        """)
        return self.cursor.fetchall()

    async def remove_position(self, position_id):
        self.cursor.execute(f"SELECT user_id FROM sellers WHERE positions_id LIKE '%{position_id}:%'")
        res = self.cursor.fetchall()
        for seller in res:
            self.cursor.execute(f"SELECT positions_id FROM sellers WHERE user_id = {seller[0]}")
            ids = self.cursor.fetchone()[0]
            self.cursor.execute(f"""
            UPDATE sellers SET positions_id = '{ids.replace(str(position_id) + ":", '')}'
            """)
            self.conn.commit()
        self.cursor.execute(f"""
        DELETE FROM positions WHERE position_id = {position_id}
        """)
        self.conn.commit()

    async def remove_designer_position(self, position_id):
        self.cursor.execute(f"""
        DELETE FROM designers WHERE position_id = {position_id}
        """)
        self.conn.commit()

    async def get_payments_data(self):
        self.cursor.execute("SELECT qiwi_number, qiwi_token FROM payments WHERE qiwi_number IS NOT NULL")
        qiwi = self.cursor.fetchone()
        self.cursor.execute(
            "SELECT apirone_wallet_id, apirone_transfer_key FROM payments WHERE apirone_wallet_id IS NOT NULL")
        apirone = self.cursor.fetchone()
        self.cursor.execute(
            "SELECT capitalist_login, capitalist_password FROM payments WHERE capitalist_login IS NOT NULL")
        capitalist = self.cursor.fetchone()
        return qiwi, apirone, capitalist

    # qiwi methods
    async def get_qiwi_data(self, new_data=False):
        self.cursor.execute(f"SELECT qiwi_token, qiwi_number, qiwi_priv_key FROM payments WHERE new_data = {new_data}")
        return self.cursor.fetchall()

    async def refresh_qiwi_token(self, token):
        _qiwi_data = await self.get_qiwi_data(True)
        if len(_qiwi_data) == 0:
            self.cursor.execute(f"INSERT INTO payments (qiwi_token, new_data) VALUES ('{token}', True)")
            self.conn.commit()
            return
        self.cursor.execute(f"UPDATE payments SET qiwi_token = '{token}' WHERE new_data = True")
        self.conn.commit()

    async def refresh_qiwi_number(self, number):
        self.cursor.execute(f"UPDATE payments SET qiwi_number = '{number}' WHERE new_data = True")
        self.conn.commit()

    async def refresh_qiwi_priv_key(self, key):
        self.cursor.execute(f"UPDATE payments SET qiwi_priv_key = '{key}' WHERE new_data IS TRUE")
        self.conn.commit()

    async def accept_new_qiwi_data(self):
        _new_qiwi_data = await self.get_qiwi_data(True)
        _new_token = _new_qiwi_data[0][0]
        _new_number = _new_qiwi_data[0][1]
        _new_qiwi_priv_key = _new_qiwi_data[0][2]
        self.cursor.execute(f"UPDATE payments SET qiwi_token = '{_new_token}', "
                            f"qiwi_number = {_new_number}, qiwi_priv_key = '{_new_qiwi_priv_key}'"
                            f" WHERE new_data = False")
        self.cursor.execute(f"""
        DELETE FROM payments WHERE new_data = True
        """)
        self.conn.commit()

    async def decline_new_data(self):
        self.cursor.execute(f"""
        DELETE FROM payments WHERE new_data = True
        """)
        self.conn.commit()

    # apirone methods
    async def get_apirone_data(self, new_data=False):
        self.cursor.execute(f"SELECT apirone_wallet_id, apirone_transfer_key FROM payments WHERE new_data = {new_data}")
        return self.cursor.fetchall()

    async def refresh_apirone_wallet_id(self, wallet_id):
        _apirone_data = await self.get_apirone_data(True)
        if len(_apirone_data) == 0:
            self.cursor.execute(f"INSERT INTO payments (apirone_wallet_id, new_data) VALUES ('{wallet_id}', True)")
            self.conn.commit()
            return
        self.cursor.execute(f"UPDATE payments SET apirone_wallet_id = '{wallet_id}' WHERE new_data = True")
        self.conn.commit()

    async def refresh_apirone_transfer_key(self, key):
        self.cursor.execute(f"UPDATE payments SET apirone_transfer_key = '{key}' WHERE new_data = True")
        self.conn.commit()

    async def accept_new_apirone_data(self):
        _new_apirone_data = await self.get_apirone_data(True)
        _new_wallet_id = _new_apirone_data[0][0]
        _new_key = _new_apirone_data[0][1]
        self.cursor.execute(
            f"UPDATE payments SET apirone_wallet_id = '{_new_wallet_id}', apirone_transfer_key = '{_new_key}' WHERE new_data = False")
        self.cursor.execute(f"""
        DELETE FROM payments WHERE new_data = True
        """)
        self.conn.commit()

    # capitalist methods
    async def get_capitalist_data(self, new_data=False):
        self.cursor.execute(f"SELECT capitalist_login, capitalist_password FROM payments WHERE new_data = {new_data}")
        return self.cursor.fetchall()

    async def refresh_capitalist_login(self, login):
        _capitalist_data = await self.get_capitalist_data(True)
        if len(_capitalist_data) == 0:
            self.cursor.execute(f"INSERT INTO payments (capitalist_login, new_data) VALUES ('{login}', True)")
            self.conn.commit()
            return
        self.cursor.execute(f"UPDATE payments SET capitalist_login = '{login}' WHERE new_data = True")
        self.conn.commit()

    async def refresh_capitalist_password(self, password):
        self.cursor.execute(f"UPDATE payments SET capitalist_password = '{password}' WHERE new_data = True")
        self.conn.commit()

    async def accept_new_capitalist_data(self):
        _new_capitalist_data = await self.get_capitalist_data(True)
        _new_login = _new_capitalist_data[0][0]
        _new_password = _new_capitalist_data[0][1]
        self.cursor.execute(f"UPDATE payments SET capitalist_login = '{_new_login}', "
                            f"capitalist_password = '{_new_password}' WHERE new_data = False")
        self.cursor.execute(f"""
        DELETE FROM payments WHERE new_data = True
        """)
        self.conn.commit()

    async def get_seller(self, seller_tg_id):
        self.cursor.execute(f"SELECT * FROM sellers WHERE seller_tg_id = {seller_tg_id}")
        return self.cursor.fetchone()

    async def get_seller_by_product(self, prod_id):
        self.cursor.execute(f"SELECT seller_id FROM goods WHERE product_id = {prod_id}")
        return self.cursor.fetchone()[0]

    async def create_new_seller_query(self, user_id, username, answers):
        seller = await self.get_seller(user_id)
        if seller is None:
            self.cursor.execute(
                f"INSERT INTO sellers (seller_tg_id, seller_username, answers) VALUES ({user_id}, '{username}', '{answers}')")
            self.conn.commit()
        else:
            if seller[11]:
                self.cursor.execute(f"""
                UPDATE sellers SET answers = '{answers}'
                WHERE seller_tg_id = {user_id}
                """)

    async def set_seller_status_to(self, user_id, commission=None):
        if commission is not None:
            self.cursor.execute(
                f"UPDATE sellers SET admin_approve = TRUE, is_designer_only = FALSE, commission = {commission} WHERE seller_tg_id = {user_id}")
        else:
            cfg = await self.get_config()
            default_commission = cfg[4]
            self.cursor.execute(
                f"UPDATE sellers SET admin_approve = TRUE, is_designer_only = FALSE, commission = {default_commission} WHERE seller_tg_id = {user_id}")
        self.conn.commit()

    async def get_seller_commission(self, seller_tg_id):
        self.cursor.execute(f"SELECT commission FROM sellers WHERE seller_tg_id = {seller_tg_id}")
        res = self.cursor.fetchone()
        cfg = await self.get_config()
        def_commission = cfg[4]
        return res[0] if res[0] is not None else def_commission

    async def get_seller_log_check_time(self, seller_tg_id):
        self.cursor.execute(f"SELECT log_check_time FROM sellers WHERE seller_tg_id = {seller_tg_id}")
        res = self.cursor.fetchone()
        cfg = await self.get_config()
        def_time = cfg[6]
        return res[0] if res[0] is not None else def_time

    async def get_designer_status(self, seller_id):
        self.cursor.execute(
            f"SELECT is_designer_only FROM sellers WHERE seller_id = {seller_id}"
        )
        return self.cursor.fetchone()

    async def delete_seller_query(self, user_id):
        self.cursor.execute(f"""
        DELETE FROM sellers WHERE seller_tg_id = {user_id}
        """)
        self.conn.commit()

    async def get_all_unapproved_sellers(self):
        self.cursor.execute("SELECT * FROM sellers WHERE admin_approve IS NULL")
        return self.cursor.fetchall()

    async def get_all_sellers(self):
        self.cursor.execute("SELECT * FROM sellers WHERE admin_approve IS TRUE")
        return self.cursor.fetchall()

    async def get_all_mailing_users(self):
        self.cursor.execute("SELECT * FROM users WHERE consent_to_mailing IS TRUE")
        return self.cursor.fetchall()

    async def cancel_mailing_subscription(self, user_id):
        self.cursor.execute(f"UPDATE users SET consent_to_mailing = FALSE WHERE tg_id = {user_id}")
        self.conn.commit()

    async def top_up_balance(self, amount, user_id):
        self.cursor.execute(f"SELECT balance FROM users WERE tg_id = {user_id}")
        balance = self.cursor.fetchone()
        self.cursor.execute(f"UPDATE users SET balance = {balance + amount}")
        self.conn.commit()

    async def get_balance(self, user_id):
        self.cursor.execute(
            f"SELECT qiwi_balance, bit_balance, capitalist_balance, admin_gift FROM users WHERE tg_id = {user_id}")
        all_balances = self.cursor.fetchone()
        balance = all_balances[0] + all_balances[1] + all_balances[2] + all_balances[3]
        return balance

    async def get_pay_id(self, user_id):
        self.cursor.execute(f"SELECT pay_id FROM users WHERE tg_id = {user_id}")
        return self.cursor.fetchone()

    async def set_user_balance(self, user_id, balance):
        self.cursor.execute(f"UPDATE users SET admin_gift = {balance} WHERE tg_id = {user_id}")
        self.conn.commit()

    async def set_apirone_pay_address(self, user_id, address):
        self.cursor.execute(f"UPDATE users SET apirone_pay_address = '{address}' WHERE tg_id = {user_id}")
        self.conn.commit()

    async def get_user_by_apirone_address(self, address):
        self.cursor.execute(f"SELECT tg_id FROM users WHERE apirone_pay_address = '{address}'")
        return self.cursor.fetchone()

    async def get_user_agreement_status(self, user_id):
        self.cursor.execute(f"SELECT user_agreement FROM users WHERE tg_id = {user_id}")
        return self.cursor.fetchone()

    async def confirm_user_agreement(self, user_id):
        self.cursor.execute(f"UPDATE users SET user_agreement = TRUE WHERE tg_id = {user_id}")
        self.conn.commit()

    async def add_designer_position(self, nick_name, login, price, portfolio_link, category_id, designer_banner,
                                    designer_banner_type):
        self.cursor.execute(f"""
        INSERT INTO designers (designer_nick_name, designer_login, designer_price, designer_portfolio_link, category_id, designer_banner, designer_banner_type)
        VALUES ('{nick_name}', '{login}', {price}, '{portfolio_link}', {category_id}, '{designer_banner}', '{designer_banner_type}')
        """)
        self.conn.commit()

    async def get_designer_profile(self, position_id):
        self.cursor.execute(
            f"SELECT rating, creatives_quality, professionalism, creatives_count, designer_banner, designer_banner_type, designer_nick_name, designer_portfolio_link, position_id, designer_tg_id, rating_count, category_id FROM designers WHERE position_id ={position_id}")
        return self.cursor.fetchone()

    async def add_new_mailing(self, from_id, to_id):
        self.cursor.execute(f"""
        INSERT INTO mailing (from_id, to_id)
        VALUES ({from_id}, {to_id})
        """)
        self.conn.commit()

    async def cancel_mailing(self, from_id, to_id):
        self.cursor.execute(f"""
        DELETE FROM mailing WHERE from_id = {from_id}
        AND to_id = {to_id}
        """)
        self.conn.commit()

    async def get_mailing_record(self, from_id, to_id):
        self.cursor.execute(f"SELECT * FROM mailing WHERE from_id = {from_id} AND to_id = {to_id}")
        return self.cursor.fetchone()

    async def get_subscribers_by_seller(self, seller_id):
        self.cursor.execute(f"SELECT from_id FROM mailing WHERE to_id = {seller_id}")
        return self.cursor.fetchall()

    async def add_product(self, product_desc, product_file, seller_id, position_id, product_price, load_time):
        self.cursor.execute(f"""
        INSERT INTO goods (product_description, product_file, seller_id, position_id, product_price, load_time)
        VALUES ('{product_desc}', '{product_file}', {seller_id}, {position_id}, {product_price}, {load_time})
        """)
        self.conn.commit()

    async def get_all_goods(self, pos_id):
        if pos_id is None:
            self.cursor.execute(f"SELECT * FROM goods WHERE 1")
        else:
            self.cursor.execute(f"SELECT * FROM goods WHERE position_id = {pos_id} AND is_sold IS FALSE")
        return self.cursor.fetchall()

    async def get_product(self, prod_id, is_sold=False):
        self.cursor.execute(f"SELECT * FROM goods WHERE product_id = {prod_id} AND is_sold = {is_sold}")
        return self.cursor.fetchone()

    async def set_sold_status(self, prod_id):
        self.cursor.execute(f"""
        UPDATE goods SET is_sold = TRUE 
        WHERE product_id = {prod_id}
        """)
        self.conn.commit()

    async def get_all_balances(self, user_id):
        self.cursor.execute(
            f"SELECT qiwi_balance, bit_balance, capitalist_balance, admin_gift FROM users WHERE tg_id = {user_id}")
        return self.cursor.fetchone()

    async def write_off_balances(self, write_off: list, user_id):
        balances = await self.get_all_balances(user_id)
        self.cursor.execute(f"""
        UPDATE users SET qiwi_balance = {balances[0] - write_off[0]},
        bit_balance = {balances[1] - write_off[1]},
        capitalist_balance = {balances[2] - write_off[2]},
        admin_gift = {balances[3] - write_off[3]} 
        WHERE tg_id = {user_id}
        """)
        self.conn.commit()

    async def create_hold(self, balances: list, purchase_id, seller_id, start_date):
        self.cursor.execute(f"""
        INSERT INTO holds (
        seller_id,
        purchase_id,
        qiwi,
        bitcoin,
        capitalist,
        test,
        hold_start_date
        )
        VALUES (
        {seller_id},
        {purchase_id},
        {balances[0]},
        {balances[1]},
        {balances[2]},
        {balances[3]},
        {start_date}
        )
        """)
        self.conn.commit()

    async def add_purchase(self, user_id, prod_id, date):
        self.cursor.execute(f"""
        INSERT INTO purchases (
        customer_id,
        product_id,
        buy_date
        )
        VALUES (
        {user_id},
        {prod_id},
        {date}
        )
        """)
        self.conn.commit()

    async def get_user_purchases(self, user_id):
        self.cursor.execute(f"SELECT * FROM purchases WHERE customer_id = {user_id}")
        return self.cursor.fetchall()

    async def get_purchase_by_prod_id(self, prod_id, user_id):
        self.cursor.execute(f"SELECT * FROM purchases WHERE product_id = {prod_id} AND customer_id = {user_id}")
        return self.cursor.fetchone()

    async def get_purchase_by_date(self, date, user_id):
        self.cursor.execute(f"SELECT * FROM purchases WHERE buy_date = {date} AND customer_id = {user_id}")
        return self.cursor.fetchone()

    async def get_hold(self, purchase_id):
        self.cursor.execute(f"SELECT * FROM holds WHERE purchase_id = {purchase_id}")
        return self.cursor.fetchall()

    async def get_hold_by_seller(self, seller_tg_id):
        self.cursor.execute(f"SELECT * FROM holds WHERE seller_id = {seller_tg_id}")
        return self.cursor.fetchall()

    async def get_purchase(self, purchase_id):
        self.cursor.execute(f"SELECT * FROM purchases WHERE purchase_id = {purchase_id}")
        return self.cursor.fetchone()

    async def remove_hold(self, purchase_id):
        self.cursor.execute(f"""
        DELETE FROM holds
        WHERE purchase_id = {purchase_id}
        """)
        self.conn.commit()

    async def top_up_balances(self, amounts: list, user_id):
        balances = await self.get_all_balances(user_id)
        self.cursor.execute(f"""
        UPDATE users SET
        qiwi_balance = {balances[0] + amounts[0]},
        bit_balance = {balances[1] + amounts[1]},
        capitalist_balance = {balances[2] + amounts[2]},
        admin_gift = {balances[3] + amounts[3]}
        WHERE tg_id = {user_id}
        """)
        self.conn.commit()

    async def increment_invalid(self, seller_id):
        self.cursor.execute(f"""
        UPDATE sellers SET invalid_count = invalid_count + 1
        WHERE seller_tg_id = {seller_id}
        """)
        self.conn.commit()

    async def increment_goods(self, seller_id):
        self.cursor.execute(f"""
        UPDATE sellers SET all_goods = all_goods + 1
        WHERE seller_tg_id = {seller_id}
        """)
        self.conn.commit()

    async def get_config(self):
        self.cursor.execute(f"SELECT * FROM admin_config")
        return self.cursor.fetchall()[0]

    def init_admin_config(self):
        self.cursor.execute(f"SELECT * FROM admin_config")
        cfg = self.cursor.fetchall()
        if not cfg:
            self.cursor.execute("""
            INSERT INTO admin_config (qiwi_balance) VALUES (0.0)
            """)
            self.conn.commit()

    async def get_commission(self):
        self.cursor.execute(f"SELECT commission FROM admin_config")
        return self.cursor.fetchone()[0]

    async def set_new_commission(self, commission):
        self.cursor.execute(f"""
        UPDATE admin_config SET commission = {commission}
        """)
        self.conn.commit()

    async def add_admin_balance(self, amount: list):
        self.cursor.execute(f"""
        UPDATE admin_config SET
        qiwi_balance = qiwi_balance + {amount[0]},
        bit_balance = bit_balance + {amount[1]},
        capitalist_balance = capitalist_balance + {amount[2]}
        """)
        self.conn.commit()

    async def get_holds_sum(self):
        self.cursor.execute("SELECT SUM(qiwi), SUM(bitcoin), SUM(capitalist) FROM holds")
        return self.cursor.fetchone()

    async def get_holds_sum_by_seller_id(self, seller_id):
        self.cursor.execute(
            f"SELECT SUM(qiwi), SUM(bitcoin), SUM(capitalist) FROM holds WHERE seller_id = {seller_id}")
        return self.cursor.fetchone()

    async def get_all_purchases(self):
        self.cursor.execute("SELECT * FROM purchases")
        return self.cursor.fetchall()

    async def get_invalid(self):
        self.cursor.execute("SELECT SUM(invalid_count) FROM sellers")
        return self.cursor.fetchone()[0]

    async def get_goods_by_seller(self, seller_id, is_sold=None):
        sold_data = '' if is_sold is None else f" AND is_sold = {is_sold}"
        self.cursor.execute(f"SELECT * FROM goods WHERE seller_id = {seller_id}{sold_data}")
        return self.cursor.fetchall()

    async def get_google_sellers(self):
        sellers = await self.get_all_sellers()
        count = 0
        for sel in sellers:
            sel_id = sel[1]
            goods = await self.get_goods_by_seller(sel_id)
            if not goods:
                continue
            for product in goods:
                pos = await self.get_position_by_id(product[4])
                cat_id = pos[6]
                cat = await self.get_category(cat_id)
                cat_type = cat[5]
                if cat_type == 'google':
                    count += 1
                    break
        return count

    async def get_facebook_sellers(self):
        sellers = await self.get_all_sellers()
        count = 0
        for sel in sellers:
            sel_id = sel[1]
            goods = await self.get_goods_by_seller(sel_id)
            if not goods:
                continue
            for product in goods:
                pos = await self.get_position_by_id(product[4])
                cat_id = pos[6]
                cat = await self.get_category(cat_id)
                cat_type = cat[5]
                if cat_type == 'facebook':
                    count += 1
                    break
        return count

    async def get_all_holds(self):
        self.cursor.execute("SELECT * FROM holds")
        return self.cursor.fetchall()

    async def get_seller_balances(self, seller_id):
        self.cursor.execute(
            f"SELECT qiwi_balance, bit_balance, capitalist_balance FROM sellers WHERE seller_tg_id = {seller_id}")
        return self.cursor.fetchone()

    async def top_up_seller_balances(self, seller_id, amount: list):
        self.cursor.execute(f"""
        UPDATE sellers SET
        qiwi_balance = qiwi_balance + {amount[0]},
        bit_balance = bit_balance + {amount[1]},
        capitalist_balance = capitalist_balance + {amount[2]}
        WHERE seller_tg_id = {seller_id}
        """)
        self.conn.commit()

    async def top_up_admin_balances(self, amount: list):
        self.cursor.execute(f"""
        UPDATE admin_config SET
        qiwi_balance = qiwi_balance + {amount[0]},
        bit_balance = bit_balance + {amount[1]},
        capitalist_balance = capitalist_balance + {amount[2]},
        earned = earned + {amount[0] + amount[1] + amount[2]}
        """)
        self.conn.commit()

    async def get_invalid_for_seller(self, seller_id):
        self.cursor.execute(f"SELECT invalid_count FROM sellers WHERE seller_tg_id = {seller_id}")
        return self.cursor.fetchone()[0]

    async def get_all_goods_for_seller(self, seller_id):
        self.cursor.execute(f"SELECT all_goods FROM sellers WHERE seller_tg_id = {seller_id}")
        return self.cursor.fetchone()[0]

    async def get_last_payment(self, user_id):
        self.cursor.execute(f"SELECT last_payment FROM users WHERE tg_id = {user_id}")
        return self.cursor.fetchone()[0]

    async def get_became_partner(self, user_id):
        self.cursor.execute(f"SELECT became_partner FROM sellers WHERE seller_tg_id = {user_id}")
        return self.cursor.fetchone()[0]

    async def set_became_partner_date(self, user_id, date):
        self.cursor.execute(f"""
        UPDATE sellers SET became_partner = {date} WHERE seller_tg_id = {user_id}
        """)
        self.conn.commit()

    async def set_invalid_product(self, product_id):
        self.cursor.execute(f'UPDATE goods SET is_invalid = TRUE WHERE product_id = {product_id}')
        self.conn.commit()

    async def get_invalid_goods(self, seller_id):
        self.cursor.execute(f"SELECT * FROM goods WHERE is_invalid = TRUE AND seller_id = {seller_id}")
        return self.cursor.fetchall()

    async def replace_invalid_file(self, prod_id, prod_file):
        self.cursor.execute(f"""
        UPDATE goods SET product_file = '{prod_file}', is_invalid = FALSE 
        WHERE product_id = {prod_id}
        """)
        self.conn.commit()

    async def remove_product(self, prod_id):
        self.cursor.execute(f"""
        DELETE FROM goods WHERE product_id = {prod_id}
        """)
        self.conn.commit()

    async def get_designer_by_login(self, login):
        self.cursor.execute(f"SELECT * FROM designers WHERE designer_login = '@{login}'")
        return self.cursor.fetchone()

    async def get_designer_by_id(self, designer_id):
        self.cursor.execute(f"SELECT * FROM designers WHERE designer_id = {designer_id}")
        return self.cursor.fetchone()

    async def set_new_portfolio_url(self, new_url, designer_login):
        self.cursor.execute(f"""
        UPDATE designers SET designer_portfolio_link = '{new_url}'
        WHERE designer_login = '@{designer_login}'
        """)
        self.conn.commit()

    async def set_designer_tg_id(self, login, tg_id):
        self.cursor.execute(f"""
        UPDATE designers SET designer_tg_id = {tg_id}
        WHERE designer_login = '{login}'
        """)
        self.conn.commit()

    async def get_designers_by_tg_id(self, designer_tg_id):
        self.cursor.execute(f"SELECT * FROM designers WHERE designer_tg_id = {designer_tg_id}")
        return self.cursor.fetchall()

    async def get_designer_tg_id_by_id(self, designer_id):
        self.cursor.execute(f"SELECT designer_tg_id FROM designers WHERE position_id = {designer_id}")
        return self.cursor.fetchone()[0]

    async def create_new_chat(self, orderer_id, designer_id, order_price):
        self.cursor.execute(f"""
        INSERT INTO chats (
        orderer_id,
        designer_id,
        order_price
        )
        VALUES (
        {orderer_id},
        {designer_id},
        {order_price}
        )
        """)
        self.conn.commit()

    async def get_designers_for_chat(self, orderer_id):
        self.cursor.execute(f"SELECT designer_id FROM chats WHERE orderer_id = {orderer_id} AND is_ended = FALSE")
        return self.cursor.fetchall()

    async def get_orderers_for_chat(self, designer_id):
        self.cursor.execute(f"SELECT orderer_id FROM chats WHERE designer_id = {designer_id} AND is_ended = FALSE")
        return self.cursor.fetchall()

    async def add_order_file_to_chat(self, designer_id, orderer_id, file_id):
        self.cursor.execute(f"""
        UPDATE chats SET order_file = '{file_id}'
        WHERE designer_id = {designer_id}
        AND orderer_id = {orderer_id}
        """)
        self.conn.commit()

    async def get_order_price_from_chat(self, orderer_id, designer_id):
        self.cursor.execute(
            f"SELECT order_price FROM chats WHERE orderer_id = {orderer_id} AND designer_id = {designer_id}")
        return self.cursor.fetchone()[0]

    async def get_order_price_from_chat_by_chat_id(self, chat_id):
        self.cursor.execute(
            f"SELECT order_price FROM chats WHERE chat_id = {chat_id}")
        return self.cursor.fetchone()[0]

    async def increment_creatives(self, designer):
        self.cursor.execute(f"""
        UPDATE designers SET creatives_count = creatives_count + 1
        WHERE designer_tg_id = {designer}
        """)
        self.conn.commit()

    async def get_order_file(self, chat_id):
        self.cursor.execute(f"SELECT order_file FROM chats WHERE chat_id = {chat_id}")
        return self.cursor.fetchone()[0]

    async def get_chat(self, designer_id, orderer_id, is_ended=False):
        self.cursor.execute(
            f"SELECT * FROM chats WHERE designer_id = {designer_id} AND orderer_id = {orderer_id} AND is_ended = {is_ended}")
        return self.cursor.fetchone()

    async def get_chat_by_chat_id(self, chat_id, is_ended=None):
        is_ended_flag = f" AND is_ended = {is_ended}" if is_ended is not None else ''
        self.cursor.execute(f"SELECT * FROM chats WHERE chat_id = {chat_id}{is_ended_flag}")
        return self.cursor.fetchone()

    async def remove_chat(self, chat_id):
        self.cursor.execute(f"""
        DELETE FROM chats WHERE chat_id = {chat_id}
        """)
        self.conn.commit()

    async def close_chat(self, chat_id):
        self.cursor.execute(f"""
        UPDATE chats SET is_ended = TRUE
        WHERE chat_id = {chat_id}
        """)
        self.conn.commit()

    async def create_payment_request(self, seller_id, payment_type, amount, requisites):
        self.cursor.execute(f"""
        INSERT INTO payment_requests (
        seller_id,
        payment_amount,
        payment_type,
        payment_requisites
        ) VALUES (
        {seller_id},
        {amount},
        '{payment_type}',
        '{requisites}'
        )
        """)
        self.conn.commit()
        self.cursor.execute(
            f"SELECT request_id FROM payment_requests WHERE seller_id = {seller_id} AND payment_amount = {amount} AND payment_type = '{payment_type}' AND payment_requisites = '{requisites}'")
        return self.cursor.fetchone()[0]

    async def get_payment_requests(self, by=None, value=None):
        where_data = f"WHERE {by} = {value}" if all([by, value]) else ''
        self.cursor.execute(f"SELECT * FROM payment_requests {where_data}")
        return self.cursor.fetchall()

    async def remove_payment_request(self, request_id):
        self.cursor.execute(f"""
        DELETE FROM payment_requests
        WHERE request_id = {request_id}
        """)
        self.conn.commit()

    async def get_position_count(self, seller_tg_id):
        self.cursor.execute(f"SELECT positions_id FROM sellers WHERE seller_tg_id = {seller_tg_id}")
        res = self.cursor.fetchone()[0]
        if res is None:
            return 0
        ids = res.split(':')
        count = 0
        for pos_id in ids:
            if pos_id == '':
                continue
            count += 1
        return count

    async def edit_position_name(self, pos_id, new_name):
        self.cursor.execute(f"""
        UPDATE positions SET position_name = '{new_name}'
        WHERE position_id = {pos_id}
        """)
        self.conn.commit()

    async def edit_seller_commission(self, seller_id, new_commission):
        self.cursor.execute(f"""
        UPDATE sellers SET commission = {new_commission}
        WHERE seller_tg_id = {seller_id}
        """)
        self.conn.commit()

    async def edit_seller_log_time_chek(self, seller_id, new_time):
        self.cursor.execute(f"""
        UPDATE sellers SET log_check_time = {new_time}
        WHERE seller_tg_id = {seller_id}
        """)
        self.conn.commit()

    async def get_positions_ids(self, seller_id):
        self.cursor.execute(f"SELECT positions_id FROM sellers WHERE seller_tg_id = {seller_id}")
        return self.cursor.fetchone()[0]

    async def get_support_group(self):
        self.cursor.execute(f"SELECT support_group FROM admin_config")
        return self.cursor.fetchone()

    async def set_support_group(self, new_group):
        self.cursor.execute(f"""
        UPDATE admin_config SET support_group = '{new_group}'
        """)
        self.conn.commit()

    async def get_last_logs(self, seller_id, now):
        self.cursor.execute(f"SELECT * FROM goods WHERE seller_id = {seller_id} AND {now} - load_time <= 10800.0")
        return self.cursor.fetchall()

    async def get_all_logs_for_mailing(self, seller_id, now):
        goods = await self.get_last_logs(seller_id, now)
        return len(goods)

    async def get_last_mailing(self, seller_id):
        self.cursor.execute(f"SELECT last_mailing FROM sellers WHERE seller_tg_id = {seller_id}")
        res = self.cursor.fetchone()
        return res[0] if res is not None else None

    async def add_new_rate(self, creatives_quality, professionalism, designer_id, user_id):
        self.cursor.execute(f"""
        UPDATE designers SET
        creatives_quality = creatives_quality + {creatives_quality},
        professionalism = professionalism + {professionalism},
        rating_count = rating_count + 1
        WHERE position_id = {designer_id}
        """)
        self.cursor.execute(f"""
        INSERT INTO designers_ratings (user_id, designer_id)
        VALUES ({user_id}, {designer_id})
        """)
        self.conn.commit()

    async def get_rating_exist(self, user_id, designer_id):
        self.cursor.execute(f"""
        SELECT * FROM designers_ratings
        WHERE user_id = {user_id}
        AND designer_id = {designer_id}
        """)
        res = self.cursor.fetchone()
        print(res)
        return True if res else False

    async def get_positions_for_category(self, category_id):
        self.cursor.execute(f"""
        SELECT position_id FROM positions
        WHERE category_id = {category_id}
        """)
        return self.cursor.fetchall()

    async def get_goods_for_position(self, position_id):
        self.cursor.execute(f"""
        SELECT product_id FROM goods
        WHERE position_id = {position_id} 
        AND is_sold = FALSE 
        """)
        return self.cursor.fetchall()

    async def set_invalid(self, product):
        self.cursor.execute(f"""
        UPDATE goods SET is_invalid = TRUE 
        WHERE product_id = {product}
        """)
        self.conn.commit()

    async def get_referrals(self, user_id):
        self.cursor.execute(f"""
        SELECT referral_login FROM referrals
        WHERE user_id = {user_id}
        """)
        return self.cursor.fetchall()

    async def get_inviter(self, referral_login):
        self.cursor.execute(f"""
        SELECT user_id FROM referrals
        WHERE referral_login = '{referral_login}'
        """)
        return self.cursor.fetchone()

    async def add_referral(self, user_id, referral_login):
        self.cursor.execute(f"""
        INSERT INTO referrals (user_id, referral_login)
        VALUES ({user_id}, '{referral_login}')
        """)
        self.conn.commit()

    async def get_user_by_login(self, login):
        self.cursor.execute(f"""
        SELECT * FROM users WHERE username = '{login}'
        """)
        return self.cursor.fetchall()

    async def set_cashback(self, cashback):
        self.cursor.execute(f"""
        UPDATE admin_config SET referrals = {cashback}
        """)
        self.conn.commit()

    async def add_new_ref_cashback(self, user_id, cashback):
        self.cursor.execute(f"""
        UPDATE users SET earned_from_referals = earned_from_referals + {cashback}
        WHERE user_id = {user_id}
        """)
        self.conn.commit()
