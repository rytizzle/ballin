from flask import Flask, render_template, request, Blueprint, send_from_directory,jsonify,abort, redirect, url_for, session
import os
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
cred = credentials.Certificate("ballin-338306-ad7c80988861.json") #test to see if you can remove before hosting to cloud run
firebase = firebase_admin.initialize_app(cred)
import pyrebase
from google.cloud import bigquery
import uuid
# from datetime import datetime
import datetime



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


app = Flask(__name__)
app.secret_key = str(uuid.uuid4())


def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if session['token'] == None:
            return {'message': 'No token provided'},400
        try:
            user = auth.verify_id_token(session['token'])
            request.user = user
            # print('user_id', user.get('user_id'))
            session['user_id'] = user.get('user_id')
        except:
            return {'message':'Invalid token provided.'},400
        return f(*args, **kwargs)
    return wrap


@app.route("/home", methods = ['GET', 'POST'])
@check_token
def home():
    client = bigquery.Client()
    #use pandas GBQ
    query = f"""
    SELECT *
     FROM `ballin-338306.ballin.parks`
     ORDER BY park_id asc"""
    query_job = client.query(query)
    print(session['user_id'])
    # Accept Kenny Post Request to add into BQ
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        table_id = "ballin-338306.ballin.events"
        signup_id = str(uuid.uuid4())
        print(signup_id)
        user_id = session['user_id']
        print(user_id)
        park_id = data.get('park_id')
        print(park_id)
        play_timestamp = data.get('signup_time')
        print(play_timestamp)
        created_ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        print(created_ts)
        num_of_players = data.get('count')
        print(num_of_players)

        rows_to_insert = [
            {u"signup_id": signup_id, 
            u"user_id": user_id, 
            u"park_id": park_id, 
            u"play_timestamp": play_timestamp, 
            u"created_ts": created_ts, 
            u"num_of_players": num_of_players},
            ]

        errors = client.insert_rows_json(table_id, rows_to_insert)  # Make an API request.
        if errors == []:
            print("New rows have been added.")
        else:
            print("Encountered errors while inserting rows: {}".format(errors))

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
                test = session['token'] = token
                # print(session)
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

