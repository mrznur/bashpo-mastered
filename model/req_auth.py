from flask import *
import sqlite3
import uuid
from functools import wraps
from flask_apscheduler import APScheduler
from datetime import datetime
import logging
from datetime import timedelta
from sslcommerz_lib import SSLCOMMERZ
import random


def connect_db():
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS USERS(
        username TEXT PRIMARY KEY UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        buyer_address TEXT,
        store_region TEXT CHECK(store_region IN('NA','LA','EU','ASI','')),
        card_info INT,
        company_name TEXT,
        publisher_name TEXT CHECK(publisher_name IN('bandai_namco','playstation_publishing','xbox_game_studios','square_enix','sega','self','')),
        user_type TEXT CHECK(user_type IN('buyer','developer','admin')) NOT NULL,
        account_status TEXT CHECK(account_status IN('active','terminated')) NOT NULL
    )
""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS WALLET_BALANCE (
            username TEXT PRIMARY KEY,
            balance REAL DEFAULT 0,
            FOREIGN KEY (username) REFERENCES USERS(username)
        )
    """)

    c.execute("SELECT * FROM USERS WHERE username = 'LordGaben'")
    existing_user = c.fetchone()

    if existing_user is None:
        # Insert the user with the password for the first time
        c.execute("""
            INSERT INTO USERS (username, email, password, user_type, account_status)
            VALUES ('LordGaben', 'newell@steampowered.com', '123456', 'admin', 'active')
        """)
        db.commit()


    c.execute("""
    INSERT INTO WALLET_BALANCE (username, balance)
    SELECT ?, ?
    WHERE NOT EXISTS (
        SELECT 1 FROM WALLET_BALANCE WHERE username = ?
    )
""", ('LordGaben', 0, 'LordGaben'))
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS GAME_PUBLISH_REQUEST(
        request_id TEXT, 
        username TEXT,
        game_name TEXT, 
        game_genre TEXT, 
        estimated_release_year INT(4), 
        basic_description TEXT, 
        status TEXT CHECK(status IN ('Pending', 'Accepted', 'Rejected','Completed')),
        payment_status INT CHECK(payment_status IN (True,False))
    )
""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS SENT_FRIEND_REQUEST (
        username_from TEXT,
        username_to TEXT,
        request_status TEXT CHECK (request_status IN ('Pending', 'Accepted', 'Rejected')),
        FOREIGN KEY (username_from) REFERENCES USERS(username),
        FOREIGN KEY (username_to) REFERENCES USERS(username)
    )
""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS FRIENDS (
        username_me TEXT,
        username_friendswith TEXT,
        
        FOREIGN KEY (username_me) REFERENCES USERS(username),
        FOREIGN KEY (username_friendswith) REFERENCES USERS(username)
    )
""")
    #CREATIING GAME LIST TABLE
    c.execute("""
            CREATE TABLE IF NOT EXISTS GAME_LIST(
              game_name TEXT UNIQUE NOT NULL,
              game_genre TEXT NOT NULL,
              game_description TEXT NOT NULL,
              base_price INT NOT NULL
              CHECK(base_price between 0 AND 120),
              game_status TEXT CHECK(game_status in ('Active','Delisted')) NOT NULL,
              dev_username TEXT NOT NULL,
              rating_yes INT NOT NULL,
              rating_no INT NOT NULL, 
              copies_sold INT NOT NULL,
              revenue_generated INT NOT NULL,
              img_path_logo TEXT NOT NULL,
              img_path_ss1 TEXT NOT NULL,
              img_path_ss2 TEXT NOT NULL,
              game_file_path TEXT NOT NULL,
              sale_status TEXT CHECK(sale_status in(True,False)),
              actual_price INT NOT NULL CHECK(actual_price between 0 AND 120),
              sale_end_time DATETIME,
              sale_percentage INT CHECK(sale_percentage between 0 AND 90),
              release_year INT NOT NULL,
              yt_embed TEXT NOT NULL,
              FOREIGN KEY (dev_username) REFERENCES USERS(username)


              )

""")
    c.execute("""
                CREATE TABLE IF NOT EXISTS WISHLIST(
              username TEXT NOT NULL,
              game_name TEXT NOT NULL,
              FOREIGN KEY (username) REFERENCES USERS(username),
              FOREIGN KEY (game_name) REFERENCES game_list(game_name)

              )
        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS CART_SYSTEM (
              username TEXT NOT NULL,
              game_name TEXT NOT NULL,
              was_it_on_sale TEXT check(was_it_on_sale in(True,False)),
              FOREIGN KEY (username) REFERENCES USERS(username),
              FOREIGN KEY (game_name) REFERENCES game_list(game_name)

              )
            """)
    c.execute(""" 
            CREATE TABLE IF NOT EXISTS OWNED_GAMES(
              
              username TEXT NOT NULL,
              game_name TEXT NOT NULL,
              amount_paid INT NOT NULL,
              purchase_type TEXT NOT NULL CHECK (purchase_type in ('Digital','Product_key')),
              posted_review TEXT NOT NULL CHECK (posted_review in ('yes','no')),
              FOREIGN KEY (username) REFERENCES USERS(username),
              FOREIGN KEY (game_name) REFERENCES game_list(game_name)
              )

        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS WALLET_CODE(
                wallet_key TEXT NOT NULL,
                amount INT NOT NULL,
                status TEXT CHECK (status in('ACTIVE','USED'))
            )          
              """
        
        
    )
    c.execute("""
            CREATE TABLE IF NOT EXISTS GAME_KEY(
                game_key TEXT NOT NULL,
                game_name TEXT NOT NULL,
                status TEXT CHECK (status in('ACTIVE','USED')),
                FOREIGN KEY (game_name) REFERENCES game_list(game_name)
            )          
              """
        
        
    )
    c.execute("""
            CREATE TABLE IF NOT EXISTS Reviews(
                game_name TEXT NOT NULL,
                username TEXT NOT NULL,
              
                review TEXT NOT NULL,
              rating TEXT NOT NULL CHECK(rating IN('yes','no')),
                FOREIGN KEY (username) REFERENCES USERS(username),
                FOREIGN KEY (game_name) REFERENCES game_list(game_name)
            )          
              """
        
        
    )
    

    

    db.commit()
    c.connection.close()

def retrieve_user(username,password):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c=db.cursor()
        c.execute("SELECT username, user_type,store_region FROM USERS WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        return user



def active_users(username,password):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c=db.cursor()
        c.execute("SELECT username, user_type FROM USERS WHERE username = ? AND password = ? AND account_status='active'", (username, password))
        user_active_check = c.fetchone()
        return user_active_check

def current_user_query(username):
        db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
        c = db.cursor()
        

        c.execute("SELECT email FROM USERS WHERE username = ?", (username,))
        user_data = c.fetchone()
        return user_data

def forget_password_email_verification(email):
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute("SELECT email FROM USERS WHERE email = ?", (email,))
    user = c.fetchone()
    return user
def forget_password_update_pasword(email,new_password):
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute("UPDATE USERS SET password = ? WHERE email = ?", (new_password, email))
    db.commit()
    db.close()

def update_password_existing():
        username = session['username']
        db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
        c = db.cursor()

        
        c.execute("SELECT password FROM USERS WHERE username = ?", (username,))
        stored_password = c.fetchone()
        return stored_password
def update_password_passed_check(newpassword,username):
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    print('newpass: ',newpassword,username)
    c.execute("UPDATE USERS SET password = ? WHERE username = ?", (newpassword, username))
    db.commit()
    db.close()

def get_all_games_for_homepage():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT game_name, game_genre, actual_price, img_path_logo, base_price, sale_status, sale_percentage FROM game_list WHERE game_status='Active' ORDER BY rowid DESC")
        games = c.fetchall()
        return games



################# SCHEDULER #######################
def sale_reset_query(current_time):
    db = sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c = db.cursor()
  
    
    c.execute("""
        UPDATE GAME_LIST SET actual_price = base_price, sale_status = ?, sale_end_time=?,sale_percentage=? 
        WHERE sale_end_time IS NOT NULL AND sale_end_time <= ?
    """, (False, None,None,current_time))
    db.commit()
    db.close()