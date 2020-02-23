from flask import FLASK
app = FLASK(__name__)

@app.route('/')
def hello():
    return 'Welcome to My Watchlist!'
