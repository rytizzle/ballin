from flask import Flask, render_template, request, Blueprint, send_from_directory,jsonify,abort, redirect, url_for
import os
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
cred = credentials.Certificate("ballin-338306-ad7c80988861.json") #test to see if you can remove before hosting to cloud run
firebase = firebase_admin.initialize_app(cred)
import pyrebase
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_key.json"



firebaseConfig = {
  'apiKey': "AIzaSyCfST8hcWjnAGwtNKsnd7vzUNJy22Qkyqo",
  'authDomain': "ballin-338306.firebaseapp.com",
  'projectId': "ballin-338306",
  'storageBucket': "ballin-338306.appspot.com",
  'messagingSenderId': "783132420898",
  'appId': "1:783132420898:web:714816832bceda3fa5d37b",
  'measurementId': "G-0FBFEGSGLS",
  'databaseURL':''
}

pb = pyrebase.initialize_app(firebaseConfig)


# client = bigquery.Client()
# query = f"""
# SELECT *
#     FROM `ballin-338306.ballin.parks`"""
# query_job = client.query(query)
# print(query_job.result())
app = Flask(__name__)

# def check_token(f):
#     @wraps(f)
#     def wrap(*args,**kwargs):
#         if not request.headers.get('authorization'):
#             return {'message': 'No token provided'},400
#         try:
#             user = auth.verify_id_token(request.headers['authorization'])
#             request.user = user
#         except:
#             return {'message':'Invalid token provided.'},400
#         return f(*args, **kwargs)
#     return wrap


@app.route("/home")
# @check_token
def home():
    client = bigquery.Client()
    #use pandas GBQ
    query = f"""
    SELECT *
     FROM `ballin-338306.ballin.parks`"""
    query_job = client.query(query)
    return render_template('home_page.html', results = query_job.result())

@app.route("/", methods=['GET', 'POST'])
def hello_kenny():
    if request.method == 'POST':
        #Handle login form
        if request.form['action'] == 'login':
            data = request.form
            email = data.get('user_email')
            password = data.get('user_password')
            try:
                signin_user = pb.auth().sign_in_with_email_and_password(email, password)
                token = signin_user['idToken']
                print('signing in')
                print(request.headers)
                # request.headers['authorization'] = token
                # return{'token':token}, 200
                return redirect(url_for('home'))
            except:
                return {'message':'There was an error logging in'}, 400

        #Handle signup form
        if request.form['action'] == 'create':
            data = request.form
            create_email = data.get('create_email')
            create_pw = data.get('create_password')
            check_create_password = data.get('check_create_password')
            if create_pw != check_create_password:
                pass
            elif len(create_pw) < 7:
                pass 

            else:
                #add user to FB
                try:
                    pb.auth().create_user_with_email_and_password(email =  create_email, password = create_pw)
                    print('Successfully created new account')
                except:
                    print('Email already exists')
                #input message flash logic here
                #redirect
    return render_template('index.html') #input KM html code here


# # users = [{'uid': 1, 'name': 'Noah Schairer'}]
# # @app.route('/api/userinfo')
# # def userinfo():
# #     return {'data': users}, 200   

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

