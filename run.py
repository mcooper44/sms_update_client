from flask import Flask, request

app = Flask(__name__)

@app.route('/sms', methods=['POST'])
def hello():
    # Grab the song title from the body of the text message.
    message = request.form['Body']
    from_number = request.form['From']
    to_number = request.form['To']

if __name__ == '__main__':
    app.run(debug=True)
