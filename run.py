from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from datetime import datetime

from db_model import Database
from db_model import database_manager

app = Flask(__name__)


def write_to_db(package):
    '''
    this is a helper function that does a database insert for 
    an incoming sms message
    logging the phone number it came from and the body of the text
    '''
    db_controller = database_manager({'sms': 'sms_response.db'})
    db_controller.initialize_connections()
    name, structure = package
    db_controller.insert_to(name, structure)

    db_controller.close_all()

@app.route('/sms', methods=['POST'])
def log_sms():
    '''
    catches incoming sms messages and logs them into a database

    '''
    # from
    # https://www.twilio.com/blog/2017/03/building-python-web-apps-with-flask.html
    message = request.form['Body']
    from_number = request.form['From']
    # to_number = request.form['To']
    now = str(datetime.now())
    # database insert
    sms_response = ('sms',  # db label
                    {'sms_message': # table name
                     ([(from_number, message, now)], # value to insert
                       '(?,?,?)') # fields
                    }
                   )
    write_to_db(sms_response)
    return str(message)


@app.route("/answer", methods=['GET', 'POST'])
def answer_call():
    """Respond to incoming phone calls with a brief message.
    https://www.twilio.com/docs/voice/quickstart/python#respond-to-incoming-calls-with-twilio
    """

    # Start our TwiML response
    resp = VoiceResponse()
    greet_ = 'Hello. Thank you for your call. This is an automated message'
    direction_ = 'If you have questions about your Christmas Hamper. Please call.'
    call_ = '519-742-5860.'
    fin = 'Goodbye'
    test_ = 'Hello. I am a robot. Welcome to the future'
    production_text = f'{greet_} {direction_} {call_} thats {call_} {fin}'
    
    # Read a message aloud to the caller
    resp.say(production_text, voice='alice')

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
