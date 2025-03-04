from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://Emmanuel:Ope12yemi@localhost/fincom_web_info'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
