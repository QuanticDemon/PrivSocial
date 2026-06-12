from flask import * 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import  or_
import uuid 
import bcrypt

app = Flask(__name__)
app.secret_key = "dkaokoqwkj190j329jd9xn2i398d9283"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///privsocial.db"

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(
        db.String(36),
        primary_key = True,
        default=lambda:str(uuid.uuid4())
    )
    username = db.Column(
        db.String(50),
        nullable=False,
        unique = True
    )

    mail = db.Column(
        db.String(120),
        nullable = False,
        unique = True
    )

    password = db.Column(
        db.String(200),
        nullable = False
    )

    @classmethod
    def create_user(cls, username, mail, password):
        pass_priv_encode = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hash_pass = bcrypt.hashpw(pass_priv_encode, salt)
        hash_toString = hash_pass.decode('utf-8')
        user = cls(
            username = username,
            mail = mail,
            password = hash_toString

        )

        db.session.add(user)
        db.session.commit()
        return user
    @classmethod
    def consult_user(cls, userToken, passwordConsult):

        user = cls.query.filter(
            or_(cls.username == userToken, cls.mail == userToken)
        ).first()

        if not user:
            return False, None

        try:
            password_input = passwordConsult.encode('utf-8')

            password_inDB = user.password.encode('utf-8')

            if bcrypt.checkpw(password_input, password_inDB ):

                return True, user
            else:
                return False, None
            
        except (ValueError, AttributeError, TypeError):
            return False,None
        return None

@app.context_processor
def inject_data():
    id = session.get('user_id')
    name = session.get('username')
    mail = session.get('mail')

    return{
        "username":name,
        "id":id,
        "mail": mail

    }

@app.route('/feed', methods=["GET", "POST"])
def feed():
    

    return render_template("feed.html")

@app.route('/load', methods=["GET", "POST"])
def load():
    return render_template("load.html")

@app.route('/create-account', methods=["GET", "POST"])
def create_account():

    if request.method == "POST":
        data = request.get_json()

        name = data['username']
        mail = data['mail']
        password = data['password']

        user = Users.create_user(name,mail,password)

        if not user:
            return {
                "success":False
            }
        
        return {
            "success":True
        }


    return render_template("create_acc.html")


@app.route('/sign-in', methods=["GET", "POST"])
def sign_in():
    if request.method == "POST":
        data = request.get_json()
        name = data.get('userToken')
        password = data.get('password')

        verification, user = Users.consult_user(name, password)

        if not verification or not user:
            return {
                'success':False
            }
        session['user_id'] = user.id
        session['username'] = user.username
        session['mail'] = user.mail
        
        return {
            'success':True
        }


    

    return render_template('login.html')
    



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)


