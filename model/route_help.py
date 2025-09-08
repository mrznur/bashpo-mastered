import sqlite3
from flask import *
import uuid
import base64
import os
from flask_apscheduler import APScheduler
from datetime import datetime
import logging
from datetime import timedelta
from sslcommerz_lib import SSLCOMMERZ
import random

def SearchQueryMaker(ordertype,query_filter):
    query_filter=query_filter
    if ordertype=='game_genre':
        strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage,yt_embed  FROM game_list ORDER BY CASE WHEN game_genre = "+"'"+query_filter+"'"+ " THEN 1 ELSE 2 END, game_name"
        
    elif ordertype=='release_year':
        if query_filter=='ascending':
            strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage,yt_embed FROM game_list ORDER BY release_year ASC"

        elif query_filter=='descending':
            strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage,yt_embed FROM game_list ORDER BY release_year DESC"   
    elif ordertype=='actual_price':
        if query_filter=="low-to-high":
           strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage,yt_embed FROM game_list ORDER BY actual_price ASC"  
        elif query_filter=="high-to-low":
            strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage,yt_embed FROM game_list ORDER BY actual_price DESC" 


             
    return strings



     
def dev_dashboard():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT username,company_name,publisher_name,email FROM USERS WHERE user_type ='developer' and username=?",(session['username'],))
        dev_data = c.fetchone()
        dev_username=dev_data[0]
        company_name=dev_data[1]
        publisher_name=dev_data[2]
        dev_email=dev_data[3]
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)

        c.execute("SELECT game_name, status,payment_status from GAME_PUBLISH_REQUEST WHERE username=?",(session['username'],))
        game_req_data = c.fetchall()
        c.execute("SELECT game_name,game_status, base_price,copies_sold,sale_status,actual_price,sale_end_time FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        game_list_data=c.fetchall()
        print(game_list_data)
        c.execute("SELECT COUNT(*) FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        no_of_total_games=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM GAME_LIST WHERE dev_username=? AND game_status='Active'",(dev_username,))
        no_of_games_active=c.fetchone()[0]
        c.execute("SELECT SUM(copies_sold) FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        no_of_total__games_sold=c.fetchone()[0]
        delisted_games_count=no_of_total_games-no_of_games_active
        c.execute("SELECT game_name, copies_sold, revenue_generated FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        revenue_data=c.fetchall()
        c.execute("SELECT k.game_key, g.game_name FROM GAME_KEY k INNER JOIN GAME_LIST G ON g.game_name=k.game_name WHERE k.STATUS='ACTIVE' and g.dev_username=?",(dev_username,))
        game_key_active=c.fetchall()
        return dev_username, balance,company_name,publisher_name.upper(),dev_email,game_req_data,game_list_data, no_of_total__games_sold, no_of_total_games,no_of_games_active, delisted_games_count,revenue_data,game_key_active
def gen_key(game_name,no_of_keys):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        for i in range(no_of_keys):
            game_key = uuid.uuid4().hex
            c.execute("INSERT INTO game_key values (?, ?, ?)", (game_key, game_name, "ACTIVE"))
            db.commit()
        return True
def buyer_dash_query():
    buyer_username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()

        # Fetch wallet balance
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?", (buyer_username,))
        balance = round(c.fetchone()[0],2)


        # Fetch the three most recently added games
        c.execute("""
            SELECT game_name, game_genre, img_path_ss1
            FROM GAME_LIST
            WHERE game_status = 'Active'
            ORDER BY rowid DESC
            LIMIT 3
        """)
        featured_games = c.fetchall()

        for i in range(len(featured_games)):
            featured_games[i]=list(featured_games[i])
        print(featured_games)
        
        c.execute("SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage,yt_embed FROM game_list where game_status='Active'")
        game_list = c.fetchall()
        
        
        for i in range(len(game_list)):
            game_list[i] = list(game_list[i])
        print(game_list)
        
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*.8,2)
                game_list[i] [4] = round(game_list[i] [4]*.8,2)
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [2] =round(game_list[i] [2]*1,2)
                game_list[i] [4] =round(game_list[i] [4]*1,2)
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*.9,2)
                game_list[i] [4] = round(game_list[i] [4]*.9,2)
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                game_list[i] [4] = round(game_list[i] [4]*1.1,2)
            print(game_list)
  
        c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_value=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        cart_value=c.fetchone()[0]
        if cart_value==0:
            cart_status='0'
        else:
            cart_status='1'    

        c.execute("SELECT g.game_name, g.game_genre, g.actual_price, g.base_price, g.sale_status, g.sale_percentage FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE w.username=?",(buyer_username,))
        wishlist_user=c.fetchall()
        print(wishlist_user)
        for i in range(len(wishlist_user)):
                wishlist_user[i] = list(wishlist_user[i])
        if session['store_region'] == 'ASI':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'NA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'LA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'EU':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2)  
        return buyer_username,balance, featured_games, game_list, wishlist_value,wishlist_user,cart_value, cart_status

def update_request_query(status,request_id):
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute(
        "UPDATE GAME_PUBLISH_REQUEST SET status=? WHERE request_id=?",
        (status, request_id),
    )
    db.commit()

def getRequests_admin_query():
    c = sqlite3.connect("bashpos_--definitely--_secured_database.db").cursor()
    c.execute("SELECT * FROM GAME_PUBLISH_REQUEST where status='Pending'")
    data=c.fetchall()
    return data
def getPub_Req_avail_query(game_name):
    c = sqlite3.connect("bashpos_--definitely--_secured_database.db").cursor()
    c.execute("SELECT * FROM GAME_PUBLISH_REQUEST where game_name=? and status!='Rejected'",(game_name,))
    data=c.fetchall()
    return data

def upload_game_data_query(game_name,game_genre,game_description,base_price,game_status,dev_username,rating_yes,rating_no,copies_sold,revenue_generated,img_path_logo,img_path_ss1,img_path_ss2,game_file_path,sale_status,actual_price,sale_end_time,sale_percentage,release_year,yt_embed):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("  INSERT INTO GAME_LIST VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (game_name,game_genre,game_description,base_price,game_status,dev_username,rating_yes,rating_no,copies_sold,revenue_generated,img_path_logo,img_path_ss1,img_path_ss2,game_file_path,sale_status,actual_price,sale_end_time,sale_percentage,release_year,yt_embed))
    db.commit()
    c.execute("UPDATE GAME_PUBLISH_REQUEST SET status = 'Completed' WHERE username = ? and game_name=?", (dev_username, game_name))
    db.commit()

def start_sale_query(game_name,sale_percentage_value,sale_percentage,sale_end_date):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("SELECT actual_price FROM GAME_LIST WHERE game_name=?",(game_name,))
    actual_price_current=c.fetchone()[0]
    new_actual_price=actual_price_current-actual_price_current*sale_percentage
    c.execute("UPDATE GAME_LIST SET actual_price=?, sale_status=?,sale_end_time=?,sale_percentage=? WHERE game_name=?",(new_actual_price,True,sale_end_date,sale_percentage_value,game_name))
    db.commit()
    db.close()



def wishlist_check(gamename):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("SELECT username FROM WISHLIST WHERE game_name=?",(gamename,))
    data=c.fetchall()
    if len(data)==0:
        return False
    else:
        return data
    
def wishlist_retrieve_email(username):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("SELECT email FROM USERS WHERE username=?",(username,))
    data=c.fetchone()
    return data[0]



def Send_Publishing_Request_query(request_id,username,game_name,game_genre,estimated_release_year,basic_description,status,payment_status):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("INSERT INTO GAME_PUBLISH_REQUEST VALUES (?,?,?,?,?,?,?,?)",
                  (request_id,username,game_name,game_genre,estimated_release_year,basic_description,status,payment_status))
    db.commit()
    db.close()

def View_Buyer_Profile_query(buyer_username):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT email,account_status FROM USERS WHERE username=?",(buyer_username,))
        buyer_data=c.fetchone()
        c.execute("SELECT game_name, username from OWNED_GAMES  where username=?",(buyer_username,))
        friends_games=c.fetchall()
        c.execute("""
        SELECT u.username, w.balance
        FROM USERS u
        INNER JOIN WALLET_BALANCE w ON u.username = w.username
        WHERE u.user_type = 'developer';
    """)
        

        developer_earnings=c.fetchall()
        c.execute("""
        SELECT SUM(w.balance) FROM WALLET_BALANCE w INNER JOIN USERS u on 
                  u.username=w.username
    """)
        total_cash_flow=c.fetchone()[0] 

        
        c.execute("SELECT game_name, revenue_generated FROM GAME_LIST order by revenue_generated desc")
        highest_game=c.fetchone()
        c.execute("SELECT w.username, w.balance FROM wallet_balance w INNER JOIN USERS U on u.username=w.username where user_type='developer' order by balance desc")
        highest_dev=c.fetchone()
        return buyer_username,balance,buyer_data,friends_games,developer_earnings,total_cash_flow,highest_game,highest_dev

def view_friend_profile_query(friend_username):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT email,account_status FROM USERS WHERE username=?",(friend_username,))
        friend_data=c.fetchone()
        # Pass the friend's username to the template
        c.execute("SELECT game_name, username from OWNED_GAMES  where username=?",(friend_username,))
        friends_games=c.fetchall()
        return friend_username,balance,friend_data,friends_games
    
########################### FRIEND REQUESTS ###############################
def friend_req_friend_email_verification(friend_email):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("SELECT username FROM USERS where email LIKE ? and user_type='buyer'",(friend_email,))
    friend_username=c.fetchone()
    return friend_username


def send_friend_req_duplicate_finder(sender_username,friend_username):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()
    c.execute("SELECT request_status FROM SENT_FRIEND_REQUEST WHERE username_from=? and username_to=? and request_status!='Rejected'",(sender_username,friend_username))
    check_duplicate=c.fetchall()
    return check_duplicate

def send_friend_req_query(sender_username,friend_username):
    db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c=db.cursor()


    c.execute("INSERT INTO SENT_FRIEND_REQUEST VALUES (?,?,?)",(sender_username,friend_username,'Pending'))
    db.commit()
    







def update_friend_req_query(friends_username,status):
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute(
        "UPDATE SENT_FRIEND_REQUEST SET request_status=? WHERE username_from=? and username_to=?",
        (status, friends_username,session['username']),
    )
    if status=='Accepted':
        c.execute("INSERT INTO FRIENDS VALUES (?,?)",(session['username'],friends_username))
        db.commit()
        c.execute("INSERT INTO FRIENDS VALUES (?,?)",(friends_username,session['username']))
    db.commit()

def refund_game_query(buyer_username,game_name,game_price):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE WALLET_BALANCE SET balance = balance+? WHERE username= ?", (game_price,buyer_username))
            c.execute("SELECT dev_username FROM GAME_LIST WHERE game_name=?",(game_name,))
            dev_username=c.fetchone()[0]
           
            dev_cut=round(game_price*0.9,2)
            admin_cut=round(game_price*0.1,2)
            c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold-1, revenue_generated=revenue_generated-? where game_name=?",(dev_cut,game_name))
           
            c.execute("UPDATE WALLET_BALANCE SET balance=balance-? where username=?",(dev_cut,dev_username))
            c.execute("UPDATE WALLET_BALANCE SET balance=balance-? where username=?",(admin_cut,'LordGaben'))
            c.execute("DELETE FROM OWNED_GAMES where game_name=? and username=?",(game_name,buyer_username))
            db.commit()

def delist_game_query(game_name):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE GAME_LIST SET game_status = 'Delisted' WHERE game_name = ?", (game_name,))
            db.commit()
def terminate_buyer_query(username):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE USERS SET account_status = 'terminated' WHERE username = ?", (username,))
            db.commit()

def get_active_buyer_query():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("SELECT username FROM USERS WHERE user_type = 'buyer' AND account_status = 'active'")
            buyers = c.fetchall()
            return buyers

def prod_key_validation(product_key):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT * FROM GAME_KEY WHERE game_key=?",(product_key,))
        check_product_key=c.fetchall()
        return check_product_key
def prod_key_already_own(game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT * FROM OWNED_GAMES WHERE game_name=? and username=?",(game_name,session['username']))
                    
        game_already_owned=c.fetchall()
        return game_already_owned
def prod_key_activation_confirm(game_name,product_key):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT dev_username,base_price FROM GAME_LIST WHERE game_name=?",(game_name,))
        data=c.fetchone()
        dev_username=data[0]
        price=data[1]*0.85
        if len(c.execute("select * from reviews WHERE game_name=? and username=?",(game_name,session['username'])).fetchall())==0:
            c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,price,'Product_key','no'))
        else:
            c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,price,'Product_key','yes'))
        dev_cut=round(price*0.9,2)
        admin_cut=round(price*0.1,2)
        c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold+1, revenue_generated=revenue_generated+? where game_name=?",(dev_cut,game_name))
        c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(dev_cut,dev_username))
        c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(admin_cut,'LordGaben'))
        c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,session['username']))
        c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,session['username']))
        c.execute("UPDATE GAME_KEY SET status='USED' where GAME_key=?", (product_key,))
        
        db.commit()

def wallet_code_validation(gift_card):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT * FROM WALLET_CODE WHERE wallet_key=?",(gift_card,))
        check_card=c.fetchall()
        return check_card 

def wallet_code_activation_confirm(gift_card,check_card):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        denomination=check_card[1]
               
        c.execute("UPDATE WALLET_BALANCE SET balance=balance+? WHERE username=?",(denomination,session['username'])) 
        c.execute("UPDATE WALLET_CODE SET status='USED' where wallet_key=?", (gift_card,))
        db.commit()

def generate_wallet_query(value,no_of_cards):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        for i in range(no_of_cards):
            wallet_code = uuid.uuid4().hex
            c.execute("INSERT INTO WALLET_CODE values (?, ?, ?)", (wallet_code, value, "ACTIVE"))
            db.commit()

def admin_dashboard_query():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM USERS WHERE user_type ='buyer' and account_status = 'active'")
        active_users = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM USERS WHERE user_type = 'developer'")
        developers = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM USERS WHERE user_type ='buyer' and account_status = 'terminated'")
        terminated_users = c.fetchone()[0]
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT username FROM USERS WHERE user_type ='buyer' and account_status = 'active'")
        all_users = c.fetchall()
        c.execute("SELECT username,company_name FROM USERS WHERE user_type ='developer' and account_status = 'active'")
        all_devs = c.fetchall()       
        c.execute("""
        SELECT u.username, w.balance
        FROM USERS u
        INNER JOIN WALLET_BALANCE w ON u.username = w.username
        WHERE u.user_type = 'developer';
    """)
        

        developer_earnings=c.fetchall()
        c.execute("""
        SELECT SUM(w.balance) FROM WALLET_BALANCE w INNER JOIN USERS u on 
                  u.username=w.username
    """)
        total_cash_flow=c.fetchone()[0] 

        
        c.execute("SELECT game_name, revenue_generated FROM GAME_LIST order by revenue_generated desc")
        highest_game=c.fetchone()
        c.execute("SELECT w.username, w.balance FROM wallet_balance w INNER JOIN USERS U on u.username=w.username where user_type='developer' order by balance desc")
        highest_dev=c.fetchone()
        
        if highest_dev==None:
            highest_dev=['none',0]
        if highest_game==None:
            highest_game=['None',0]
        c.execute("SELECT wallet_key, amount FROM WALLET_CODE WHERE STATUS='ACTIVE'")
        wallet_codes_active=c.fetchall()
        print(highest_game,highest_dev)
        return active_users, developers, terminated_users, balance, all_users, all_devs, developer_earnings,total_cash_flow,highest_game,highest_dev,wallet_codes_active

def post_review_query(buyer_username,game_name,rating,review):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            print('test',game_name,rating,review)
            c.execute("INSERT INTO REVIEWS values (?,?,?,?)",(game_name,buyer_username,review,rating))
            if rating=='yes':
                c.execute("UPDATE GAME_LIST SET rating_yes=rating_yes+1 where game_name=?", (game_name,))
                db.commit()
            elif rating=='no':
                c.execute("UPDATE GAME_LIST SET rating_no=rating_no+1 where game_name=?", (game_name,))
                db.commit()
            c.execute("UPDATE OWNED_GAMES SET posted_review='yes' where game_name=? and username=?",(game_name,buyer_username))
            db.commit()
def buyer_dashboard_query(buyer_username):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT username,email,buyer_address,store_region,card_info, account_status FROM USERS where username=?",(session['username'],))
        buyer_details=c.fetchone()
        status=buyer_details[5].upper()
        card_info=str(buyer_details[4])
        c.execute("SELECT username_from FROM SENT_FRIEND_REQUEST where username_to=? and request_status='Pending'",(session['username'],))
        pending_requests=c.fetchall()
        c.execute("SELECT username_friendswith FROM FRIENDS where username_me=?",(session['username'],))
        my_friends=c.fetchall() 
        c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_value=c.fetchone()[0]
        c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
        wishlist_user=c.fetchall()
        print(wishlist_user)
        for i in range(len(wishlist_user)):
                wishlist_user[i] = list(wishlist_user[i])
        if session['store_region'] == 'ASI':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'NA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'LA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'EU':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2)  
        
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        cart_value=c.fetchone()[0]
        if cart_value==0:
            cart_status='0'
        else:
            cart_status='1'  
          
        c.execute("SELECT o.game_name, o.username, g.game_file_path,o.posted_review from OWNED_GAMES o INNER JOIN GAME_LIST g on g.game_name=o.game_name where o.username=?",(buyer_username,))
        owned_games=c.fetchall()
        print(owned_games)
        return balance,buyer_username,buyer_details,status,card_info,pending_requests,my_friends,wishlist_value,wishlist_user,cart_status, cart_value,owned_games



def RatingCalculator(ratings_yes,ratings_no):
    if ratings_no==0 and ratings_yes==0:
        return 'Not enough ratings'
    elif ratings_yes>0 and ratings_no==0:
        if ratings_yes>10:
            return "Overwhelmingly Positive"
        else:
            return "Very Positive"
    elif ratings_yes>0 and ratings_no>0:
        total_ratings=ratings_yes+ratings_no
        ratings_percentage=(ratings_yes/total_ratings)*100
        if ratings_percentage>=96:
            return "Overwhelmingly Positive"
        elif ratings_percentage<96 and ratings_percentage>=84:
            return "Very Positive"
        elif ratings_percentage<84 and ratings_percentage>=75:
            return "Positive"
        elif ratings_percentage<75 and ratings_percentage>=65:
            return "Mostly Positive"
        elif ratings_percentage<65 and ratings_percentage>=55:
            return "Mixed"
        elif ratings_percentage<55 and ratings_percentage>=45:
            return "Negative"
        elif ratings_percentage<45 and ratings_percentage>=35:
            return "Very Negative"
        elif ratings_percentage<35:
            return "Overwhelmingly Negative"
        

    
def view_game_page_query(game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("SELECT * from game_list where game_name = ?", (game_name,))
            
            game_info = c.fetchall()
            c.execute("SELECT * from owned_games where game_name = ? and username=?", (game_name,session['username']))
            game_bought=c.fetchone()
            print('bought check',game_bought)
            if game_bought==None or len(game_bought)==0:
                bought_check='0'
            else:
                bought_check='1' 
            print(bought_check)       
            for i in range(len(game_info)):
                game_info[i] = list(game_info[i])
            print(game_info)
            game_info=game_info[0]
            print(game_info)
            rating_yes=game_info[6]
            rating_no=game_info[7]
            rating=RatingCalculator(rating_yes,rating_no)
            if session['store_region'] == 'ASI':
               
                    game_info[3] = round(game_info[3]*.8,2)
                    game_info [15] = round(game_info [15]*.8,2)
                
                
            elif session['store_region'] == 'NA':
                
                    game_info [3] = round(game_info [3]*1,2)
                    game_info[15] =round(game_info [15]*1,2)
          
                
            elif session['store_region'] == 'LA':
              
                game_info [3] =round(game_info[3]*.9,2)
                game_info [15] = round(game_info [15]*.9,2)
               
                
            elif session['store_region'] == 'EU':
              
                    game_info [3] = round(game_info [3]*1.1,2)
                    game_info [15] = round(game_info [15]*1.1,2)
            
        
            c.execute("SELECT publisher_name from users where username = ?", (game_info[5],))
            publisher_name = c.fetchone()[0]
            buyer_username = session['username']
            c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
            balance = round(c.fetchone()[0],2)
            c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
            wishlist_value=c.fetchone()[0]
            c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
            wishlist_user=c.fetchall()
            print(wishlist_user)
            for i in range(len(wishlist_user)):
                 wishlist_user[i] = list(wishlist_user[i])
            if session['store_region'] == 'ASI':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                    wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
                print(wishlist_user)
                
            elif session['store_region'] == 'NA':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                    wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
                print(wishlist_user)
                
            elif session['store_region'] == 'LA':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                    wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
                print(wishlist_user)
                
            elif session['store_region'] == 'EU':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                    wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2)   
            c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
            cart_value=c.fetchone()[0]
            if cart_value==0:
                cart_status='0'
            else:
                cart_status='1'   
            c.execute("SELECT username,review, rating from Reviews where game_name=?",(game_name,))
            reviews=c.fetchall()
            return  game_info, publisher_name,rating,buyer_username, balance, wishlist_value, wishlist_user,bought_check, cart_status, cart_value,reviews
    

def review_filter_query(query_type,game_name):
    
        if query_type=='positive':
            return "SELECT username,review, rating FROM REVIEWS where game_name="+"'"+ game_name+"'"+"and rating='yes'"
        elif query_type=='negative':
            return "SELECT username,review, rating FROM REVIEWS where game_name="+"'"+ game_name+"'"+"and rating='no'"
        elif query_type=='all':
            return "SELECT username,review, rating FROM REVIEWS where game_name="+"'"+ game_name+"'"

def ReturnReviewFilter_query(sqlcommand):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute(sqlcommand)
            print('sqlll',sqlcommand)
            reviews_sorted=c.fetchall()
            return reviews_sorted




def search_filter_returner_query(sqlcommand):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute(sqlcommand)
            game_list=c.fetchall()
            for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
            print(game_list)
        
            if session['store_region'] == 'ASI':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*.8,2)
                    game_list[i] [4] = round(game_list[i] [4]*.8,2)
                print(game_list)
                
            elif session['store_region'] == 'NA':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*1,2)
                    game_list[i] [4] =round(game_list[i] [4]*1,2)
                print(game_list)
                
            elif session['store_region'] == 'LA':
                for i in range(len(game_list)):
                    game_list[i] [2] =round(game_list[i] [2]*.9,2)
                    game_list[i] [4] = round(game_list[i] [4]*.9,2)
                print(game_list)
                
            elif session['store_region'] == 'EU':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                    game_list[i] [4] = round(game_list[i] [4]*1.1,2)
            return game_list

def payment_success_card_purchase():
     buyer_username=session['username']
     store_region_multiplier={"NA":1,"ASI":0.8,"LA":0.9,"EU":1.1}
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("SELECT c.game_name, g.actual_price FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(buyer_username,))
            game_list=c.fetchall()
            for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*store_region_multiplier[session['store_region']],2)
                    
            for i in game_list:
                game_name=i[0]
                paying_amount=round(i[1],2)
                c.execute("SELECT dev_username FROM GAME_LIST WHERE game_name=?",(game_name,))
                dev_username=c.fetchone()[0]
                if len(c.execute("select * from reviews WHERE game_name=? and username=?",(game_name,session['username'])).fetchall())==0:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','no'))
                else:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','yes'))
                dev_cut=round(paying_amount*0.9,2)
                admin_cut=round(paying_amount*0.1,2)
                c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold+1, revenue_generated=revenue_generated+? where game_name=?",(dev_cut,game_name))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(dev_cut,dev_username))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(admin_cut,'LordGaben'))
                c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,buyer_username))
                c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,buyer_username))
                db.commit()

def purchase_success_card_wallet(response):
    buyer_username=session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            initital=response.split("-")
            amount=round(float(initital[1]),3)
            c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?", (amount,buyer_username))
            db.commit()

def purchase_success_card_dev(game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE WALLET_BALANCE SET balance=balance+100 where username='LordGaben'")
            c.execute("UPDATE GAME_PUBLISH_REQUEST SET payment_status=? where game_name=?",(True,game_name,))
            db.commit()

def pay_with_card_query(buyer_username):
   with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT c.game_name, g.actual_price FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(buyer_username,))
        
        game_list=c.fetchall()
        for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
               game_list[i] [1] = round(game_list[i] [1]*.8,2)
             
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*1,2)
             
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [1] =round(game_list[i] [1]*.9,2)
            
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*1.1,2)
        
        return game_list
   


def pay_with_wallet_balance_check(buyer_username):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(buyer_username,))
        balance = round(c.fetchone()[0],2)
        return balance
     

def pay_with_wallet_query(buyer_username,game_list):
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()
    for i in game_list:
                game_name=i[0]
                paying_amount=round(i[1],2)
                c.execute("SELECT dev_username FROM GAME_LIST WHERE game_name=?",(game_name,))
                dev_username=c.fetchone()[0]
                if len(c.execute("select * from reviews WHERE game_name=? and username=?",(game_name,session['username'])).fetchall())==0:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','no'))
                else:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','yes'))
                dev_cut=round(paying_amount*0.9,2)
                admin_cut=round(paying_amount*0.1,2)
                c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold+1, revenue_generated=revenue_generated+? where game_name=?",(dev_cut,game_name))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance-? where username=?",(paying_amount,buyer_username))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(dev_cut,dev_username))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(admin_cut,'LordGaben'))
                c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,buyer_username))
                c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,buyer_username))
                db.commit()
    

def remove_from_wishlist_query(username,game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,username))
            db.commit()

def cart_empty_check_query(username):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT * FROM CART_SYSTEM WHERE username=?",(username,))
        is_empty=c.fetchall()
        return is_empty 



         
def delete_from_cart_query(username,game_name):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            
            c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,username))
            db.commit()


def view_cart_query(buyer_username):
      with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT c.game_name, c.was_it_on_sale, g.base_price, g.actual_price, g.sale_status,g.img_path_logo,g.sale_percentage FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(buyer_username,))
        
        game_list=c.fetchall()
        for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
               game_list[i] [2] = round(game_list[i] [2]*.8,2)
               game_list[i] [3] = round(game_list[i] [3]*.8,2)
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*1,2)
                game_list[i] [3] =round(game_list[i] [3]*1,2)
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [2] =round(game_list[i] [2]*.9,2)
                game_list[i] [3] = round(game_list[i] [3]*.9,2)
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                game_list[i] [3] = round(game_list[i] [3]*1.1,2)
        total_price=0
        for i in game_list:
            total_price+=i[3]
        c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_value=c.fetchone()[0]    
        c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
        wishlist_user=c.fetchall()
        print(wishlist_user)
        for i in range(len(wishlist_user)):
                wishlist_user[i] = list(wishlist_user[i])
        if session['store_region'] == 'ASI':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'NA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'LA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'EU':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2) 
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        cart_value=c.fetchone()[0]
        return buyer_username,balance,game_list,total_price,wishlist_value,wishlist_user,cart_value

def in_cart_validation(username,game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            c.execute("SELECT * FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,username))
                    
            already_check=c.fetchall()
            return already_check
def add_to_cart_query(username,game_name,was_it_on_sale):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            c.execute("INSERT INTO CART_SYSTEM VALUES (?,?,?)",(username,game_name,was_it_on_sale))
            db.commit()

def in_wishlist_validation(username,game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            c.execute("SELECT * FROM WISHLIST WHERE game_name=? and username=?",(game_name,username))
                    
            already_check=c.fetchall()
            return already_check

def in_owned_validation(username,game_name):
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            c.execute("SELECT * FROM OWNED_GAMES WHERE game_name=? and username=?",(game_name,username))
                    
            already_check=c.fetchall()
            return already_check

def add_to_wishlist_query(username,game_name):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            c.execute("INSERT INTO WISHLIST VALUES (?,?)",(username,game_name))
            db.commit()
def add_monitor_wallet_query(buyer_username):
      with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()

        # Fetch wallet balance
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?", (buyer_username,))
        balance = c.fetchone()[0]
        c.execute("SELECT game_name,amount_paid,purchase_type from OWNED_GAMES where username=?",(buyer_username,))
        game_info=c.fetchall()
        return balance,game_info

def check_user_query(username,email):
    c = sqlite3.connect("bashpos_--definitely--_secured_database.db").cursor()
    c.execute("SELECT * FROM USERS WHERE username = ? OR email LIKE ?", (username, email))
    data=c.fetchall()
    return data


def create_dev_query(username,email,password,company_name,publisher_name,user_type):
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()
    c.execute("""
            INSERT INTO USERS (username, email, password, company_name, publisher_name, user_type,account_status)
            VALUES (?, ?, ?, ?, ?, ?,?)
        """, (username, email, password, 
                company_name, publisher_name, 
                user_type,'active'))
    c.execute("""
    INSERT INTO WALLET_BALANCE VALUES (?,?)
                  """,(username,0))
    db.commit()
    db.close()

def create_buyer_query(username,email,password,buyer_address,store_region,card_info,user_type):
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()
    c.execute("""
            INSERT INTO USERS (username, email, password, buyer_address, store_region, card_info, user_type,account_status)
            VALUES (?, ?, ?, ?, ?, ?, ?,?)
        """, (username, email, password, 
                buyer_address, store_region, card_info, 
                user_type,'active'))
    c.execute("""
    INSERT INTO WALLET_BALANCE VALUES (?,?)
                  """,(username,0))
    db.commit()
    db.close()

def searchbar_query(query):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT game_name, img_path_logo FROM game_list WHERE LOWER(game_name) LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()
        return results