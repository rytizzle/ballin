from flask import Flask, render_template, request, Blueprint, send_from_directory,jsonify,abort
import os


app = Flask(__name__)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route("/kenny", methods=['GET', 'POST'])
def hello_kenny():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password1')
        password2 = request.form.get('password2')
    return render_template() #input KM html code here


users = [{'uid': 1, 'name': 'Noah Schairer'}]
@app.route('/api/userinfo')
def userinfo():
    return {'data': users}, 200   

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

