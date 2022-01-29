from flask import Flask, render_template, request, Blueprint, send_from_directory,jsonify,abort, redirect, url_for, session
import os
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
cred = credentials.Certificate("ballin-338306-ad7c80988861.json") #test to see if you can remove before hosting to cloud run
firebase = firebase_admin.initialize_app(cred)
import pyrebase
from google.cloud import bigquery
from google.cloud import secretmanager
import uuid
# from datetime import datetime
import datetime
import pandas as pd
import pyarrow
import json


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_key.json"

#Secret Manager to host Keys
def access_secret_version(PROJECT_ID,secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

firebase_secret = eval(access_secret_version('ballin-338306', 'firebaseConfig', version_id = 'latest'))

pb = pyrebase.initialize_app(firebase_secret)

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())

def events_query_func(park_id = 1):
    client = bigquery.Client()
    sql_query = f"""
    SELECT park_id, DATETIME_TRUNC(play_timestamp, MINUTE) as play_timestamp, sum(num_of_players) as tot_players
    FROM `ballin-338306.ballin.events`
    WHERE park_id = {park_id}
    GROUP BY 1,2
    ORDER BY 2 ASC """
    query_job = client.query(sql_query)
    return query_job.result()

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

    def create_query_obj(sql_query, park_filter = False, park = 1):
        if park_filter == False:
            query_job = client.query(sql_query)
            return query_job.result() 
        elif park_filter == True:
            where_clause = f"WHERE park_id = {park}"

    # def jsonify_bigquery(bigquery_iterator):
    #     return bigquery_iterator.to_dataframe().to_json(orient='records')

    parks_query = f"""
    SELECT *
     FROM `ballin-338306.ballin.parks`
     ORDER BY park_id asc"""

    # event_agg_query = f"""
    # SELECT park_id, play_timestamp, sum(num_of_players) as tot_players
    # FROM `ballin-338306.ballin.events`
    # GROUP BY 1,2
    # ORDER BY park_id asc """

    park_obj = create_query_obj(parks_query)
    # event_obj_json = jsonify_bigquery(create_query_obj(event_agg_query))
    
    # Accept Kenny Post Request to add into BQ
    if request.method == 'POST':
        data = request.get_json()
        if data['action'] == 'select_event':
            print(data)
            event_obj = events_query_func(park_id = data.get('park_id'))
            print(data.get('park_id'))
            return event_obj.to_dataframe().to_json(orient='records')

        elif data['action'] == 'insert_event':
            table_id = "ballin-338306.ballin.events"
            signup_id = str(uuid.uuid4())
            user_id = session['user_id']
            park_id = data.get('park_id')
            play_timestamp = data.get('signup_time')
            created_ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
            num_of_players = data.get('count')

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
    return render_template('home_page.html', results = {'parks_query':park_obj})

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

        #HANDLE PASSWORD RESET HERE
        if request.form['action'] == 'reset-password':
            data = request.form
            try:
                pb.auth().send_password_reset_email(data.get('user_email'))
            except:
                pass
            #some code to display an email has been sent for a password reset

    return render_template('index.html') #input KM html code here
  

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

