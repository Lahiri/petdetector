from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, Blueprint
import json
import requests
import os.path
from werkzeug.utils import secure_filename

# Custom Vision
ENDPOINT = 'https://custom-vision-lahiri.cognitiveservices.azure.com/customvision/v3.0/Prediction'
resource_id = 'edb431a1-4a81-4e6c-bd9e-92e6fe4047da'
iteration = 'Iteration1'
base_url = ENDPOINT + '/' + resource_id + '/classify/iterations/' + iteration + '/'
# the prediction key is read from an untracked file to prevent if being shared publicly
prediction_key = open("prediction_key.txt").read()
headers = {
    'Prediction-Key': prediction_key,
    'Content-Type': 'application/json'
}
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'ah23has9jasda8dasdì8dasn2'


@app.route('/')
def home():
    return render_template('home.html', images=session)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    def prediction(resp):
        results = resp["predictions"]
        winner = None
        for category in results:
            if winner is None:
                winner = category
            elif category['probability'] > winner['probability']:
                winner = category
        return winner

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if request.method == 'POST':
        cookie = {}

        if os.path.exists('cookie.json'):
            with open('cookie.json') as cookie_file:
                cookie = json.load(cookie_file)

        if 'url' in request.form.keys():
            cv_url = base_url + 'url'
            payload = "{\"Url\": \"" + request.form['url'] + "\"}"
            img_src = request.form['url']
        else:
            cv_url = base_url + 'image'
            f = request.files['file']
            full_name = secure_filename(f.filename)
            img_file = 'static/user_files/' + full_name
            f.save(img_file)
            with open(img_file, 'rb') as f:
                payload = f.read()
            img_src = url_for('static', filename='user_files/' + full_name)

        try:
            response_j = requests.request("POST", cv_url, headers=headers, data=payload)
            response = json.loads(response_j.text)
            label = prediction(response)
            confidence = str(round(label['probability'] * 100))

            cookie[img_src] = {'result': label['tagName'] + ': ' + confidence + '%'}
            with open('cookie.json', 'w') as cookie_file:
                json.dump(cookie, cookie_file)
                session[img_src] = label['tagName'] + ': ' + confidence + '%'
            return render_template('prediction.html', img_src=img_src, pet_type=label['tagName'], confidence=confidence)
        except NameError:
            return "Name Error. img_src:" + img_src
        except KeyError:
            return "KeyError"


@app.route('/api')
def session_api():
    api = {}
    for k in session.keys():
        api[k] = session[k]
    return jsonify(api)
