from flask import Flask
from routes.clients import clients_blueprint

def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False
    app.register_blueprint(clients_blueprint)
    return app

# הפתרון – ליצור אובייקט app לשימוש ב־Gunicorn
app = create_app()
