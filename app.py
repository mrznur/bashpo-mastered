from flask import *
import sqlite3
import uuid
from functools import wraps
import base64
import os
from flask_apscheduler import APScheduler
from datetime import datetime
import logging
from datetime import timedelta
from sslcommerz_lib import SSLCOMMERZ
import random
from model.route_help import *
from model.req_auth import *


import requests



app = Flask(__name__)
scheduler = APScheduler()
app.secret_key = 'your-secret-key'  # Replace with a strong, unique key
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the folder if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Print the absolute path for debugging
print(f"Absolute UPLOAD_FOLDER path: {os.path.abspath(UPLOAD_FOLDER)}")
#gamelord
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
class GlobalVar:
    def __init__(self,value):
        self.value=value

global_var=GlobalVar('First')

review_filter_global=GlobalVar('ReviewSQL')

Mailroo_api_key=GlobalVar("7041b51838bf5de44b2e743aa4cc86633042f375fae62e95f6239f1d514ada9b")

sslcz = SSLCOMMERZ({
    'store_id': 'teste68010316a4e09',
    'store_pass': 'teste68010316a4e09@ssl',
    'issandbox': True
})

class User:
    def __init__(self,username,email,password,user_type):
        self.username=username
        self.email=email
        self.password=password
        self.buyer_address=''
        self.store_region=''
        self.card_info=''
        self.company_name=''
        self.publisher_name=''
        self.user_type=user_type
        self.account_status='active'

class Game_publish_request:
      def __init__(self,game_name,game_genre,estimated_release_year,basic_description):
   
            self.request_id=uuid.uuid4().hex
            self.username=''
            self.game_name=game_name
            self.game_genre=game_genre
            self.estimated_release_year=estimated_release_year
            self.basic_description=basic_description
            self.status='Pending'  

class Games_List:
    def __init__(self,game_name,game_genre,game_description,base_price):
        self.game_name=game_name
        self.game_genre=game_genre
        self.game_description=game_description
        self.base_price=base_price



          



@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static','new_account_buyer','new_account_developer','forgot_pass','forgot_password','checkUser','create_buyer','create_developer','index']  
    print(request.endpoint)
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect(url_for('login'))  



@app.route('/')
def index():
    connect_db()

    if 'user_type' in session:
        if session['user_type'] == 'buyer':
            return redirect(url_for('buyer_dashboard'))
        elif session['user_type'] == 'developer':
            return redirect(url_for('developer_dashboard'))
        elif session['user_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))

    # Fetch only approved games for carousel
    games = get_all_games_for_homepage()
    print("Loaded")
    return render_template('index.html', games=games)


@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'GET':
        games = get_all_games_for_homepage()
        return render_template('index.html', games=games)
    

    if request.is_json:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        print(f"Username: {username}, Password: {password}")

      
        
        user = retrieve_user(username,password)
        
        user_active_check = active_users(username,password)
        print("Fetched user:", user)

        if user:
            if user_active_check:
                session.permanent = True
        
                session['username'] = user[0]
                session['user_type'] = user[1]
                session['store_region']=user[2]
            else:
                 return jsonify({"error": "Account Terminated due to fraudent activities"}), 401    

            return jsonify({
                "success": True,
                "redirect_url": url_for(f"{user[1]}_dashboard") 
            }), 200  
        else:
         
            return jsonify({"error": "Invalid credentials"}), 401  
   
    games = get_all_games_for_homepage()
    return render_template('index.html', games=games)

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login')) 


@app.route('/current_user')
def current_user():
    if 'user_type' in session:
        username = session['username']
        user_data = current_user_query(username)
        
        
        if user_data:
            return jsonify({"username": username, "user_type": session['user_type'], "email": user_data[0]})
        else:
            return jsonify({"error": "User data not found"})
        
    else:
        return jsonify({"error": "Not logged in"})

@app.route('/newacc', methods=['GET'])
def new_account_buyer():

    return render_template('newacc.html')  

@app.route('/forgotpass', methods=['GET'])
def forgot_pass():

    return render_template('forgotpass.html')



@app.route('/forgot_password', methods=['POST'])
def forgot_password():

    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

  
    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400  

   
    user = forget_password_email_verification(email)


    if not user:
        return jsonify({"error": "Email not found."}), 404  

    forget_password_update_pasword(email,new_password)


    return jsonify({"success": "Password reset successfully."}), 200 






@app.route('/devacc', methods=['GET'])
def new_account_developer():
 
    return render_template('devacc.html') 



@app.route('/create_buyer', methods=['POST'])
def create_buyer():
   
    if not request.is_json:
        return jsonify({"error": "Invalid request. Please send data as JSON."}), 400

   
    data = request.json
    username = data.get('user_name')
    email = data.get('email')
    password = data.get('password')
    buyer_address = data.get('buyer_address')
    store_region = data.get('store_region')
    card_info = data.get('card_info')
    print(username,email)
    
    if not (username and email and password and buyer_address and store_region and card_info):
        return jsonify({"error": "All fields are required."}), 400


    new_buyer = User(username, email, password, "buyer")
    new_buyer.buyer_address = buyer_address
    new_buyer.store_region = store_region
    new_buyer.card_info = card_info
    print(new_buyer.username)
  

    user_check=checkUser()  
    print(user_check)  
    if len(user_check)!=0:
        return jsonify({"error": "Username or email already exists."}), 400

    else: 

        create_buyer_query(new_buyer.username, new_buyer.email, new_buyer.password, 
                new_buyer.buyer_address, new_buyer.store_region, new_buyer.card_info, 
                new_buyer.user_type)

    # If successful, return success response
        return jsonify({"success": "Buyer account created successfully.", "redirect_url": url_for('index')}), 200



@app.route('/create_developer', methods=['POST'])
def create_developer():
    

    if not request.is_json:
        return jsonify({"error": "Invalid request. Please send data as JSON."}), 400

   
    data = request.json
    username = data.get('user_name')
    email = data.get('email')
    password = data.get('password')
    company_name = data.get('company_name')
    publisher_name = data.get('publisher_name')
   
    print(username,email)
   
    if not (username and email and password and company_name and publisher_name ):
        return jsonify({"error": "All fields are required."}), 400

    new_developer = User(username, email, password, "developer")
    new_developer.company_name = company_name
    new_developer.publisher_name = publisher_name
    
    print(new_developer.username)
  

    user_check=checkUser()  
    print(user_check)  
    if len(user_check)!=0:
        return jsonify({"error": "Username or email already exists."}), 400

 
    else: 
        create_dev_query(new_developer.username, new_developer.email, new_developer.password, new_developer.company_name, new_developer.publisher_name, new_developer.user_type)

        return jsonify({"success": "Developer account created successfully.", "redirect_url": url_for('index')}), 200






@app.route('/checkUser', methods=['GET'])
def checkUser():
    data = request.json
    username = data.get('user_name')
    email = data.get('email')
    data=check_user_query(username,email)
    return data




def login_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_type' not in session:
                return redirect(url_for('login'))  
            if session['user_type'] != role:
                return "Unauthorized Access", 403  
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/dev_dashboard', methods=['GET','POST'])
@login_required('developer')
def developer_dashboard():
    connect_db()
    dev_username, balance,company_name,publisher_name,dev_email,game_req_data,game_list_data,no_of_total__games_sold,no_of_total_games,no_of_games_active,delisted_games_count,revenue_data,game_key_active=dev_dashboard()

       
    return render_template('dev_dashboard.html',dev_username=dev_username, balance=balance,company_name=company_name,
                           publisher_name=publisher_name.upper(),dev_email=dev_email,game_req_data=game_req_data,game_list_data=game_list_data,
                           no_of_total__games_sold=no_of_total__games_sold, no_of_total_games= no_of_total_games,no_of_games_active=no_of_games_active,
                           delisted_games_count=delisted_games_count,revenue_data=revenue_data,game_key_active=game_key_active)


@app.route('/GenerateGameKey', methods=['GET','POST'])

def generate_game_key():
    
    req_json = request.json
    game_name = req_json.get('game_name')
    no_of_keys = req_json.get('numberofkeys')
    key_generation=gen_key(game_name,no_of_keys)
    if key_generation:
        return jsonify({'ok':True})

@app.route('/buyer_dashboard', methods=['GET', 'POST'])
@login_required('buyer')
def buyer_dashboard():
    connect_db()
    buyer_username,balance,featured_games,game_list,wishlist_value,wishlist_user,cart_value,cart_status=buyer_dash_query()
    return render_template(
        'buyer_storefront.html',
        buyer_username=buyer_username,
        balance=balance,
        featured_games=featured_games, 
        game_list = game_list, wishlist_value=wishlist_value,wishlist_user=wishlist_user,cart_value=cart_value,cart_status=cart_status )


@app.route('/AddMonitorWallet', methods=['GET', 'POST'])
@login_required('buyer')
def wallet_purchase():
    connect_db()
    buyer_username = session['username']

    # Get wallet info
    balance,game_info=add_monitor_wallet_query(buyer_username)

    # Get cart and wishlist info
    # Reuse buyer_dash_query to get all needed context
    (
        _buyer_username, _balance, featured_games, game_list, wishlist_value,
        wishlist_user, cart_value, cart_status
    ) = buyer_dash_query()

    return render_template(
        'wallet&purchase.html',
        buyer_username=buyer_username,
        balance=balance,
        game_info=game_info,
        featured_games=featured_games,
        game_list=game_list,
        wishlist_value=wishlist_value,
        wishlist_games=wishlist_user,
        cart_value=cart_value,
        cart_status=cart_status
    )

@app.route('/AddtoWishlist',methods=['GET','POST'])
def Add_to_Wishlist():
    if request.method=='POST':
        
            req_json=request.json
            game_name=req_json.get('game_name')
            username=session['username']
            #check if game already in user wishlist

            already_check=in_wishlist_validation(username,game_name)
            #check if game already in owned games

            ALREADY_OWNED=in_owned_validation(username,game_name)
            
            
            print('wishlisted',already_check)
            if len(already_check)>0:
                return jsonify({"success": False, "message": f"{game_name} cannot be added as it already exists in your wishlist."})
            elif len(ALREADY_OWNED)>0:
                return jsonify({"success": False, "message": f"{game_name} cannot be added as you already own it."})
            else:
                add_to_wishlist_query(username,game_name)
                return jsonify({"success": True, "message": f"{game_name} added to wishlist!"})


@app.route('/AddtoCart',methods=['GET','POST'])
def Add_to_Cart():
    if request.method=='POST':
        
            req_json=request.json
            game_name=req_json.get('game_name')
            username=session['username']
            was_it_on_sale=req_json.get('was_it_on_sale')
            already_check=in_cart_validation(username,game_name)
            print('wishlisted',already_check)
            if len(already_check)>0:
                return jsonify({"success": False, "message": f"{game_name} cannot be added as it already in your cart."})
            else:
                add_to_cart_query(username,game_name,was_it_on_sale)
            return jsonify({"success": True, "message": f"{game_name} added to cart!"})

@app.route('/get_cart_count',methods=['GET'])
def get_cart_count():
    username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(username,))
        cart_count = c.fetchone()[0]
    return jsonify({"success": True, "cart_count": cart_count})

@app.route('/get_wishlist',methods=['GET'])
def get_wishlist():
    buyer_username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT w.username, g.game_name, g.base_price, g.actual_price, g.sale_status, g.sale_percentage FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_games=c.fetchall()
        
        # Convert to list for modification
        wishlist_games = [list(item) for item in wishlist_games]
        
        # Apply regional pricing
        if session['store_region'] == 'ASI':
            for item in wishlist_games:
                item[2] = round(item[2]*.8,2)
                item[3] = round(item[3]*.8,2)
        elif session['store_region'] == 'NA':
            for item in wishlist_games:
                item[2] = round(item[2]*1,2)
                item[3] = round(item[3]*1,2)
        elif session['store_region'] == 'LA':
            for item in wishlist_games:
                item[2] = round(item[2]*.9,2)
                item[3] = round(item[3]*.9,2)
        elif session['store_region'] == 'EU':
            for item in wishlist_games:
                item[2] = round(item[2]*1.1,2)
                item[3] = round(item[3]*1.1,2)
                
    return jsonify({"success": True, "wishlist_games": wishlist_games})

@app.route('/ViewCart',methods=['GET','POST'])
def View_Cart():
        buyer_username = session['username']
    
        buyer_username,balance,game_list,total_price,wishlist_value,wishlist_user,cart_value=view_cart_query(buyer_username)

        return render_template('cart.html',buyer_username=buyer_username,balance=balance,game_list=game_list,total_price=total_price,store_region=session['store_region'],
                               wishlist_user=wishlist_user,wishlist_value=wishlist_value,cart_value=cart_value)

@app.route('/RemoveFromCart',methods=['GET','POST'])
def RemoveFromCart():
    if request.method=='POST':
        req_json=request.json
        username=req_json.get('username')
        game_name=req_json.get('game_name')
        db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
        c=db.cursor()
        delete_from_cart_query(username,game_name)
        
        is_empty=cart_empty_check_query(username)
        print(is_empty)
        if len(is_empty)>0:
            return jsonify({"success": True,"empty_check":False, "message": "Game removed from cart"})
        else:
            return jsonify({"success": True,"empty_check":True, "message": "Game removed from cart"})

@app.route('/RemoveFromWishlist',methods=['GET','POST'])
def RemoveFromWishlist():
    if request.method=='POST':
        req_json=request.json
        username=session['username']
        game_name=req_json.get('game_name')
       
        remove_from_wishlist_query(username,game_name)
        return jsonify({"success": True, "message": "Game removed from wishlist"})

@app.route('/PayUsingWallet',methods=['GET','POST'])
def Pay_Using_Wallet():
        buyer_username=session['username']
        game_list=pay_with_card_query(buyer_username)
        total_price=0
        for i in game_list:
            total_price+=i[1]
        
        balance = pay_with_wallet_balance_check(buyer_username)
        if balance<total_price:
             return jsonify({"success": False, "message": "Insufficient funds"})
        else:
            pay_with_wallet_query(buyer_username,game_list)
            return jsonify({"success": True, "message": "All games  bought successfully"})

@app.route('/PayUsingCard' , methods=['GET','POST'])
def Pay_With_Card():
    
        buyer_username=session['username']
        game_list=pay_with_card_query(buyer_username)
        total_price=0
        for i in game_list:
            total_price+=i[1]
        
        trx_id="TX"+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))
        print(trx_id)
        post_body = {
        'total_amount': total_price,
        'currency': "USD",
        'tran_id': trx_id,
        'success_url': "http://127.0.0.1:1097/paymentBuyer/success",
        'fail_url': "http://127.0.0.1:1097/paymentBuyer/fail",
        'cancel_url': "http://127.0.0.1:1097/paymentBuyer/cancel",
        'cus_name': buyer_username,
        'cus_email': "john@example.com",
        'cus_add1': "Address",
        'cus_city': "Dhaka",
        'cus_country': "USA",
        'cus_phone': "01700000000",
        'shipping_method': "NO",
        'product_name': "multiple or one",
        'product_category': "software",
        'product_profile': "general"
    }

        response = sslcz.createSession(post_body)
        print("Gateway Response:", response)
        print(total_price)

        if 'GatewayPageURL' in response:
            return redirect(response['GatewayPageURL'])
        else:
            return f"<h3>Payment session error:</h3><pre>{response}</pre>"
            

@app.route('/paymentBuyer/<response>', methods=['GET', 'POST'])
def payment_status_buyer(response):
    buyer_username=session['username']
    store_region_multiplier={"NA":1,"ASI":0.8,"LA":0.9,"EU":1.1}
    print(response)
    if response in [ "failure","cancel"]:
        return render_template("buyer_game_card_status.html", response=False)  # or False

    elif response=="success":
        payment_success_card_purchase()
    
        return render_template("buyer_game_card_status.html", response=True)  # or False
    elif response.startswith("successWallet"):
        print('enetered')
        purchase_success_card_wallet(response)

        return render_template("buyer_game_card_status.html", response="walletTrue")
    elif response.startswith("failWallet") or response.startswith('cancelWallet'):
       
        return render_template("buyer_game_card_status.html", response="walletFalse")
    elif response.startswith("successDev"):
        game_name_init=response.split("-")[1]
        game_name=" ".join(game_name_init.split("%"))

        purchase_success_card_dev(game_name)
        return render_template("buyer_game_card_status.html", response="devTrue")
    elif response in ["failDev","cancelDev"]:
        return render_template("buyer_game_card_status.html", response="devFalse")

        
            






    



@app.route('/SearchFilterApi',methods=['GET','POST'])
def SearchFilter():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()

            req_json=request.json
            print(req_json)
            ordertype=req_json.get('ordertype')
            secondcondition=req_json.get('query_filter')
            sqlcommand=SearchQueryMaker(ordertype,secondcondition)
            print(sqlcommand)
            global_var.value=sqlcommand
        return ""

    

@app.route('/SearchFilterReturner',methods=['GET','POST'])
def ReturnFilter():
   
    sqlcommand=global_var.value
    print(sqlcommand)
    game_list=search_filter_returner_query(sqlcommand)                
    return render_template('game_list_jinga.html',game_list_sort=game_list)


@app.route('/ReviewFilterApi',methods=['GET','POST'])
def ReviewFilter():
    if request.method=='POST':
        

            req_json=request.json
            
           
            query_type=req_json.get('query_filter')
            game_name=req_json.get('game_name')
            print(query_type)
            review_filter_global.value=review_filter_query(query_type,game_name)
            
            
            return ""
@app.route('/ReviewFilterReturner',methods=['GET','POST'])
def ReturnReviewFilter():
   
    sqlcommand=review_filter_global.value
   
    reviews_sorted=ReturnReviewFilter_query(sqlcommand)
            
                    
    return render_template('review_list_jinja.html',reviews_sorted=reviews_sorted)


@app.route('/ViewGamePage/<game_name>',methods=['GET','POST'])
def View_Game_Page(game_name):
     if request.method=='GET':
            game_info, publisher_name,rating,buyer_username, balance, wishlist_value, wishlist_user,bought_check, cart_status, cart_value,reviews=view_game_page_query(game_name)
            return render_template('game_page.html', game_info = game_info, publisher_name = publisher_name,rating=rating,
                                   buyer_username=buyer_username,balance=balance,wishlist_value=wishlist_value,
                                   wishlist_user=wishlist_user,bought_check=bought_check,cart_status=cart_status,cart_value=cart_value,reviews=reviews)






@app.route('/PostReview', methods=['GET','POST'])
def Post_Review():
    buyer_username = session['username']
    if request.method=='POST':
       
            req_json=request.json
            game_name=req_json.get('game_name')
            rating=req_json.get('rating')
            review=req_json.get('review')

            post_review_query(buyer_username,game_name,rating,review)
            return jsonify({'success': True, 'message':'Review for '+game_name+' posted successfully'})

#killedd route not in use
@app.route('/UpdateCreditCard-depreciated', methods=['POST','GET'])
def Update_card():
    if request.method=='POST':
        buyer_username = session['username']
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            req_json=request.json
            card_number=req_json.get('card_number')
           
            db.commit()
            return jsonify({'success': True  })
        
@app.route('/WallettoCreditCard', methods=['GET','POST'])
def Wallet2Credit():
     if request.method=='POST':
        buyer_username = session['username']
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            amount = request.form.get('wallet')
           
            trx_id="TX"+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))
        print(trx_id)
        post_body = {
        'total_amount': amount,
        'currency': "USD",
        'tran_id': trx_id,
        'success_url': "http://127.0.0.1:5000/paymentBuyer/successWallet-"+str(amount),
        'fail_url': "http://127.0.0.1:5000/paymentBuyer/failWallet",
        'cancel_url': "http://127.0.0.1:5000/paymentBuyer/cancelWallet",
        'cus_name': buyer_username,
        'cus_email': "john@example.com",
        'cus_add1': "Address",
        'cus_city': "Dhaka",
        'cus_country': "USA",
        'cus_phone': "01700000000",
        'shipping_method': "NO",
        'product_name': "multiple or one",
        'product_category': "software",
        'product_profile': "general"
    }

        response = sslcz.createSession(post_body)
        print("Gateway Response:", response)
     

        if 'GatewayPageURL' in response:
            return redirect(response['GatewayPageURL'])
        else:
            return f"<h3>Payment session error:</h3><pre>{response}</pre>"
         
           
    
        

            

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').lower()

    # Query the database for matching games
    

    results=searchbar_query(query)
    
    return jsonify({
        'results': [
            {
                'name': row[0],
                'logo': url_for('static', filename=row[1])  # Converts to a full URL (e.g., "/static/uploads/elden_ring_logo.png")
            }
            for row in results
        ]
    })




@app.route('/admin_dashboard')
@login_required('admin')
def admin_dashboard():
    connect_db()
    active_users,developers,terminated_users,balance,all_users,all_devs,developer_earnings,total_cash_flow,highest_game,highest_dev,wallet_codes_active=admin_dashboard_query()
    all_requests=getRequests_admin()

    return render_template('admin_dashboard.html', username=session['username'], active_users=active_users, developers=developers, terminated_users=terminated_users, 
                           balance=balance,all_users=all_users,
                           developer_earnings=developer_earnings,all_devs=all_devs,all_requests=all_requests,
                           total_cash_flow=total_cash_flow, highest_game=highest_game,highest_dev=highest_dev,wallet_codes_active=wallet_codes_active)

@app.route('/generatewallet', methods=['GET','POST'])
@login_required('admin')
def generate_wallet():
    
        req_json = request.json
        value = req_json.get('amount')
        no_of_cards = req_json.get('numberOfCards')
        generate_wallet_query(value,no_of_cards)
        return jsonify({'ok':True})

@app.route('/RedeemGiftCard', methods=['GET','POST'])
def redeem_wallet():
    
        req_json=request.json
        gift_card=req_json.get('gift_code')
        check_card=wallet_code_validation(gift_card)
        if len(check_card)==0:
            return jsonify({'success':False, 'message':'Please enter a valid card key'})
        else:
           
            check_card=check_card[0]
            print(check_card)
            if check_card[2]=='USED':
                return jsonify({'success':False, 'message':'This card key has been used'})
            else:
                wallet_code_activation_confirm(gift_card,check_card)
            return jsonify({'success':True, 'message':str(check_card[1])+' $ added to account successfully'})

@app.route('/ActivateProductKey', methods=['GET','POST'])
def activate_game_key():
   
 
        req_json=request.json
        product_key=req_json.get('product_key')
       
        check_product_key=prod_key_validation(product_key)
        if len(check_product_key)==0:
            return jsonify({'success':False, 'message':'Please enter a valid game key'})
        else:
            check_product_key=check_product_key[0]
            if check_product_key[2]=='USED':
                return jsonify({'success':False, 'message':'This game key has been used already'})
            else:
                
                game_name=check_product_key[1]
                print(game_name)
                game_already_owned=prod_key_already_own(game_name)
                print(game_already_owned)
                if len(game_already_owned)>0:
                    return jsonify({'success':False, 'message':'You already own this game'})
                else:
                    prod_key_activation_confirm(game_name,product_key)
                return jsonify({'success':True, 'message':str(game_name)+' added to account successfully'})
        




@app.route('/get_active_buyers', methods=['GET'])
def get_active_buyers():
    buyers= get_active_buyer_query()
    return jsonify(buyers)  

@app.route('/terminate_buyer', methods=['POST'])
def terminate_buyer():
    data = request.json  
    username = data.get('username')

    if username:
        terminate_buyer_query(username)
        return jsonify({"message": f"User {username} terminated successfully."})
    else:
        return jsonify({"error": "Invalid request"}), 400

@app.route('/DelistGame', methods=['POST'])
def Delist_game():
    data = request.json  
    game_name = data.get('game_name')

    if game_name:
        delist_game_query(game_name)
        return jsonify({"message": f"{game_name} delisted successfully."})
    else:
        return jsonify({"error": "Invalid request"}), 400
@app.route('/RefundGame', methods=['POST'])
def Refund_game():
    buyer_username=session['username']
    data = request.json  
    game_name = data.get('game_name')
    game_price=round(float(data.get('price')),2)
   
    if game_name:
        refund_game_query(buyer_username,game_name,game_price)
        return jsonify({"message": f"{game_name} refunded successfully."})
    else:
        return jsonify({"error": "Invalid request"}), 400


@app.route('/SendFriendRequest', methods=['GET','POST'])
@login_required('buyer')
def Send_Friend_Request():
     if request.method == 'POST':
       
        req_json = request.json
        friend_email=req_json.get('email').lower()
        print(friend_email)
        sender_username=session['username']
        friend_username=friend_req_friend_email_verification(friend_email)
        if  friend_username==None:
            return jsonify({"success": False, "message": "This email doesn't belong to a buyer or doesn't exist"})
        else:
            friend_username=friend_username[0]   
        if friend_username==session['username']:
             return jsonify({"success": False, "message": "You cannot send a friend request to yourself"})
        print(friend_username)
        #checking if a request is pending or accepted
        check_duplicate=send_friend_req_duplicate_finder(sender_username,friend_username)
        
        check_duplicate_2=send_friend_req_duplicate_finder(friend_username,sender_username)
        if len(check_duplicate)!=0:
            return jsonify({"success": False, "message": "Cannot send friend request as currently a request is "+check_duplicate[0][0]})
        elif len(check_duplicate_2)!=0:
            return jsonify({"success": False, "message": "Cannot send friend request as currently a request is "+check_duplicate_2[0][0]})
        else:
            send_friend_req_query(sender_username,friend_username)
            return jsonify({"success": True, "message": "Friend Request sent succesfully"})


@app.route('/updateFriendRequest', methods=['POST'])
@login_required('buyer')
def update_FriendRequest():
 
    req_json = request.json
    friends_username = req_json.get('username_from')
    status = req_json.get('request_status')

    if not friends_username or status not in ['Accepted', 'Rejected']:
        return jsonify({"response": "Invalid request data"}), 400
   
    update_friend_req_query(friends_username,status)
    return jsonify({"message": "Request updated to "+status})        


@app.route('/ViewFriendProfile/<friend_username>')
def view_friend_profile(friend_username):
    friend_username,balance,friend_data,friends_games=view_friend_profile_query(friend_username)
    return render_template('ViewFriendProfile.html', friendusername=friend_username,buyer_username=session['username'],balance=balance,friend_email=friend_data[0],
                            friend_account_status=friend_data[1].upper(),friends_games=friends_games)
    
@app.route('/UploadGameDataForm/<game_name>')
@login_required('developer')
def uploadgamedta_formpage(game_name):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        print(game_name)

        
        # Pass the friend's username to the template
        return render_template('upload_game_data.html',game_name=game_name,dev_username=session['username'])
     
@app.route('/ViewMyProfile')
@login_required('buyer')
def view_my_profile():
    balance,buyer_username,buyer_details,status,card_info,pending_requests,my_friends,wishlist_value,wishlist_user,cart_status, cart_value,owned_games = buyer_dashboard_query(session['username'])
    return render_template('Buyer_profile.html', buyer_username=buyer_username, balance=balance, cart_status=cart_status, cart_value=cart_value, wishlist_value=wishlist_value, owned_games=owned_games, buyer_data=buyer_details, store_region=session['store_region'], account_status=status, pending_requests=pending_requests, my_friends=my_friends, wishlist_user=wishlist_user)

@app.route('/ViewBuyerProfile/<buyer_username>')
def view_buyer_profile(buyer_username):

        all_requests=getRequests_admin()
        buyer_username,balance,buyer_data,friends_games,developer_earnings,total_cash_flow,highest_game,highest_dev=View_Buyer_Profile_query(buyer_username)
        if highest_dev==None:
            highest_dev=['none',0]
        if highest_game==None:
            highest_game=['None',0]
        # Pass the friend's username to the template
        return render_template('ViewBuyerProfile.html', friendusername=buyer_username,username=session['username'],balance=balance,friend_email=buyer_data[0],
                               friend_account_status=buyer_data[1].upper(),friends_games=friends_games,developer_earnings=developer_earnings,total_cash_flow=total_cash_flow,
                               all_requests=all_requests,highest_game=highest_game,highest_dev=highest_dev)


@app.route('/SendPublishingRequest', methods=['GET','POST'])

def Send_Publishing_Request():
    if request.method == 'POST':
        db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
        c=db.cursor()
        req_json = request.json
        Pub_request=Game_publish_request(req_json["game_name"],req_json["game_genre"],req_json["estimated_release_year"],req_json["basic_description"])
        print(Pub_request)
        game_avail_check=getPub_Req_Avail(req_json["game_name"])
        if len(game_avail_check)!=0:
            return jsonify({"success": False, "message": "Cannot send request as request for a game with the same name has already been accepted or waiting for approval"})
        else:
            Send_Publishing_Request_query(Pub_request.request_id,session['username'],Pub_request.game_name,Pub_request.game_genre,
                        Pub_request.estimated_release_year,Pub_request.basic_description
                        , Pub_request.status,False)
        
            return  jsonify({"success": True,"message": "Publishing request for "+req_json['game_name']+ " sent successfully"})


@app.route('/PayPublishingFee', methods=['GET','POST'])
@login_required('developer')
def Pay_Publishing_Fee():
    DEV_USERNAME=session['username']
    game_name_init = request.form.get('game_name').split(" ")
    trx_id="TX"+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))+str(random.randint(0,9))
    print(trx_id)
    game_name="%".join(game_name_init)
    post_body = {
    'total_amount': 100,
    'currency': "USD",
    'tran_id': trx_id,
    'success_url': "http://127.0.0.1:1097/paymentBuyer/successDev-"+game_name,
    'fail_url': "http://127.0.0.1:1097/paymentBuyer/failDev",
    'cancel_url': "http://127.0.0.1:1097/paymentBuyer/cancelDev",
    'cus_name': DEV_USERNAME,
    'cus_email': "john@example.com",
    'cus_add1': "Address",
    'cus_city': "Dhaka",
    'cus_country': "USA",
    'cus_phone': "01700000000",
    'shipping_method': "NO",
    'product_name': "multiple or one",
    'product_category': "software",
    'product_profile': "general"
}

    response = sslcz.createSession(post_body)
    print("Gateway Response:", response)
   

    if 'GatewayPageURL' in response:
        return redirect(response['GatewayPageURL'])
    else:
        return f"<h3>Payment session error:</h3><pre>{response}</pre>"


        

@app.route('/StartSaleRequest', methods=['GET','POST'])

def Send_Sale_Request():
    if request.method == 'POST':
        
        req_json = request.json
        print(req_json)
     
        game_name=req_json.get('game_name')
        sale_percentage_value=req_json.get('sale_percentage')
        sale_percentage=int(req_json.get('sale_percentage'))/100
       
        sale_end_date=req_json.get('sale_end_date')
        if not req_json:
            return jsonify({"success": False, "message": "Cannot send request as request for a game with the same name has already been accepted or waiting for approval"})
        else:
            start_sale_query(game_name,sale_percentage_value,sale_percentage,sale_end_date)
            users_on_wishlist=wishlist_check(game_name)
            if users_on_wishlist==False:
                pass
            else:
                for users in users_on_wishlist:
                    email=wishlist_retrieve_email(users[0])
                    send_wishlist_notfification_email(users[0],email,game_name,sale_percentage_value,sale_end_date)


                    
                    
        
            return  jsonify({"success": True,"message": "Sale for "+req_json['game_name']+ " started successfully"})


def send_wishlist_notfification_email(username,email,game_name,sale_percentage_value,sale_end_date):
    # Send an email to the user about the sale
    

    url = "https://smtp.maileroo.com/send"

    payload = {
        'from': 'bashpo-noreply@b75300127eed9386.maileroo.org',
        'to': f'To {username} <{email}>',
        'subject': f'{game_name} just went on sale!',
        'plain': 'Game on sale!',
        'html': f'<b>Hello {username}</b><p>We are excited to inform you that the game <b>{game_name}</b> is now on sale for <b>{sale_percentage_value}%</b> off! The sale ends on <b>{sale_end_date}</b>.</p>'
                '<p>Don\'t miss out on this opportunity to grab your favorite game at a discounted price!</p>'
    }

    headers = {
        'X-API-Key': Mailroo_api_key.value,
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)

        
@app.route('/uploadgamedata', methods=['GET','POST'])
def uploadgamedata():
     if request.method == 'POST':
        db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
        c=db.cursor()
        req_json = request.json
        game_name=req_json.get('game_name')
        game_genre=req_json.get('game_genre')
        dev_username=req_json.get('dev_username')
        game_description=req_json.get('game_description')
        base_price=req_json.get('base_price')
        logo=req_json.get('logo')
        screenshot1=req_json.get('screenshot1')
        screenshot2=req_json.get('screenshot2')
        game_file=req_json.get('game_file')
        release_year=req_json.get('release_year')
        yt_embed=req_json.get('yt_embed')
        
        print(release_year)
        logo_data = base64.b64decode(logo)

        # Generate a safe filename for the image to find em properlyy
        logo_filename = f"{game_name.replace(' ', '_').lower()}_logo.png"
        logo_file_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        
        # Save the image to the upload folder
        with open(logo_file_path, 'wb') as f:
            f.write(logo_data)
        
        ss1_data = base64.b64decode(screenshot1)

        # Generate a safe filename for the image  to find em properlyy
        ss1_filename = f"{game_name.replace(' ', '_').lower()}_ss1.png"
        ss1_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ss1_filename)
        
        # Save the image to the upload folder
        with open(ss1_file_path, 'wb') as f:
            f.write(ss1_data)

        ss2_data = base64.b64decode(screenshot2)

        # Generate a safe filename for the image  to find em properlyy
        ss2_filename = f"{game_name.replace(' ', '_').lower()}_ss2.png"
        ss2_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ss2_filename)
        
        # Save the image to the upload folder
        with open(ss2_file_path, 'wb') as f:
            f.write(ss2_data) 
        
        game_file_data = base64.b64decode(game_file)

        # Generate a safe filename for the zipped file
        game_file_filename = f"{game_name.replace(' ', '_').lower()}_file.zip"
        game_file_path = os.path.join(app.config['UPLOAD_FOLDER'], game_file_filename)
        
        # Save the files to the upload folder
        with open(game_file_path, 'wb') as f:
            f.write(game_file_data)     
        logo_file_url = f"uploads/{logo_filename}"
        ss1_file_url = f"uploads/{ss1_filename}"
        ss2_file_url = f"uploads/{ss2_filename}"
        game_file_url = f"uploads/{game_file_filename}"

 #########images send to  static/upload AND we will save the path data in DB
                 # def __init__(self,game_name,game_genre,game_description,base_price):
        game_data=Games_List(game_name,game_genre,game_description,base_price)
        upload_game_data_query(game_data.game_name,game_data.game_genre,
                game_data.game_description,game_data.base_price,'Active',dev_username,0,0,0,0,logo_file_url,ss1_file_url,ss2_file_url,game_file_url,False,game_data.base_price,None,None,release_year,yt_embed)  
        return jsonify({"message": "Data for "+game_name+" uploaded successfully"})


@app.route('/getPubReq', methods=['GET'])
def getPub_Req_Avail(game_name):
    game_name=game_name
    data=getPub_Req_avail_query(game_name)
    return data


@app.route('/getRequests', methods=['GET'])
def getRequests_admin():
    data=getRequests_admin_query()
    return data


@app.route('/updateRequest', methods=['POST'])
@login_required('admin')
def update_request():
 
    req_json = request.json
    request_id = req_json.get('request_id')
    status = req_json.get('status')
    print(request_id,status)

    if not request_id or status not in ['Accepted', 'Rejected']:
        return jsonify({"response": "Invalid request data"}), 400
    update_request_query(status,request_id)
   
        
    return jsonify({"message": "Request updated to "+status})

    
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        username = session['username']
        stored_password=update_password_existing()

        if stored_password and stored_password[0] == current_password:
            # Update the password
            update_password_passed_check(new_password ,username)

            return jsonify({"success": True, "message": "Password updated successfully!"})
        else:
            return jsonify({"success": False, "error": "Incorrect current password!"})

    return redirect(url_for('logout'))

@app.route('/check_session')
def check_session():
    if 'user' in session:
        return f"User: {session['username']}"
    else:
        return "Session has expired."


def reset_expired_sales():
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    
    sale_reset_query(current_time)
    

scheduler.add_job(id='reset_sales', func=reset_expired_sales, trigger='interval', seconds=20)
scheduler.start()







if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))  # use port 5001
    app.run(host="0.0.0.0", port=port)
