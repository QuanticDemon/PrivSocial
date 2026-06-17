from os.path import join
from posixpath import splitext
from re import U
from flask import * 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import  or_, func
import uuid 
import bcrypt
import os
from sqlalchemy.exc import IntegrityError
import string
import secrets
from datetime import *
app = Flask(__name__)
app.secret_key = "dkaokoqwkj190j329jd9xn2i398d9283"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///privsocial.db"

db = SQLAlchemy(app)


def generar_token(long):
    chars = string.ascii_letters + string.digits
    
    return "".join(secrets.choice(chars) for _ in range(long))


class Posts(db.Model):
    id_post = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    tittle = db.Column(
        db.String(100),
        nullable = False
    )

    content = db.Column(
        db.Text, 
        nullable = False
    )


    post_pass = db.Column(
        db.String(200),
        nullable = True
    )

    post_image = db.Column(
        db.String(300),
        nullable = True
    )


    @classmethod

    def creation_post(cls,tittle, content, password, post_image):
       hash_passToString = None
       if password:
        pass_encode = password.encode('utf-8')
        salts = bcrypt.gensalt(rounds=12)
        hash_pass = bcrypt.hashpw(pass_encode, salts)
        hash_passToString = hash_pass.decode('utf-8')
       new_post = cls(tittle=tittle, content=content, post_pass=hash_passToString,
       post_image = post_image)
       db.session.add(new_post)
       db.session.commit()

       return new_post

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
    mail = db.Column(                                                db.String(120),
             nullable = False,
             unique = True
        )
    password = db.Column(
            db.String(200),
            nullable = False
        )
    user_picture = db.Column(
        db.String(300),
        nullable = True
    )

    verified = db.Column(
        db.Boolean,
        default = False
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
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

            return False
       
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
    @classmethod
    def update_photo(cls, filename):
        userUpdatePhoto = db.session.get(cls, session.get("user_id"))
        userUpdatePhoto.user_picture = filename
        db.session.add(userUpdatePhoto)
        db.session.commit()
        
        return userUpdatePhoto

    @classmethod
    def update_data(cls, username, mail, password):
        userUpdate = db.session.get(cls, session.get("user_id"))

        if username is not None:
            userUpdate.username = username
            db.session.commit()
            session['username'] = username
        if mail is not None:
            userUpdate.mail = mail
           
            try:
                db.session.commit()
            except IntegrityError:
                return jsonify({"error": True})
            session['mail'] = mail
        if password:
            hashing = password.encode('utf-8')
            salts = bcrypt.gensalt(rounds=12)
            pass_priv = bcrypt.hashpw(hashing, salts)
            pass_priv_string = pass_priv.decode('utf-8')
            userUpdate.password = pass_priv_string
            db.session.commit()
    

        return userUpdate

class Tokens(db.Model):
    id_token = db.Column(
            db.String(36),
            primary_key = True,
            default=lambda:str(uuid.uuid4())

            )
    token = db.Column(
            db.String(6),
            nullable= False,
            default = lambda:generar_token(6)
            )
    type_token = db.Column(
            db.String(200),
            nullable = False
            )
    dtime_final = db.Column(
            db.DateTime, 
            nullable = False 
            )
    dtime_creation = db.Column(
            db.DateTime,
            nullable = False,
            default= datetime.utcnow()
            )

    @classmethod
    def create_token(cls, type_token, dtime_final):
        new_token = cls(
                type_token = type_token,
                dtime_final = dtime_final
                )
        db.session.add(new_token)
        db.session.commit()

        return new_token
class Bridge(db.Model):

    id_bridge = db.Column(
        db.String(36),
        primary_key = True,
        default= lambda:str(uuid.uuid4())
    )

    id_user = db.Column(
        db.String(36),
        db.ForeignKey('users.id')
    )

    id_post = db.Column(
        db.String(36),
        db.ForeignKey('posts.id_post')

    )

    id_token = db.Column(
            db.String(36),
            db.ForeignKey('tokens.id_token')
            )



    user = db.relationship('Users')
    post = db.relationship('Posts')
    token = db.relationship('Tokens')


@app.context_processor
def inject_data():
    user=None
    user_id = session.get('user_id')
    name = session.get('username')
    mail = session.get('mail')
    if 'user_id' in session: 
        user = Users.query.filter(Users.id == user_id).first()
    return{
        "username":name,
        "id":user_id,
        "mail": mail,
        "picture":user.user_picture if user else None,
        "verified":user.verified if user else None

    }

@app.route('/feed', methods=["GET", "POST"])
def feed():

    user_id = session.get('user_id') 
    user_posts = Bridge.query.filter_by(
                id_user=user_id).order_by(func.random()).all()
    if user_id is None:
        
        return redirect(url_for('sign_in'))

    
    return render_template("feed.html", user_posts = user_posts)

@app.route('/create-posts',methods=["GET", "POST"])
def create_posts():
    
    tittle=request.form.get('tittle')
    content=request.form.get('content')
    password_post=request.form.get('pass')
    post_image = request.files.get('image')
    
    if post_image:
        extension = os.path.splitext(post_image.filename)[1]
        filename = str(uuid.uuid4()) + extension

        path = os.path.join("static/post_images", filename)

        post_image.save(path)
    post = Posts.creation_post(tittle, content, None if password_post == "" else password_post, None if post_image == None else filename)

    bridge = Bridge(
        id_user = session.get("user_id"),
        id_post = post.id_post
    )

    db.session.add(bridge)
    db.session.commit()
    return {
            "success":True,
            "post":post.tittle
            }




@app.route('/user-changes', methods=["GET", "POST"])
def user_changes():
    
    
    userPhoto = request.files.get('userpic')



    if userPhoto:
        extension = os.path.splitext(userPhoto.filename)[1]
        filename = str(uuid.uuid4()) + extension

        path = os.path.join('static/userpic', filename)
        userPhoto.save(path)


    
    user = Users.update_photo(None if userPhoto == None else filename)
    
    if not user:
        return {"success":False}
    
    return jsonify({
        "success":True,
       
    })

@app.route('/user-changes/user-data', methods=["GET", "POST"])
def user_changes_data():
    if request.is_json:
        data = request.get_json();
        newUsername = data.get('new-username')
        newMail = data.get('new-mail')
        newPass = data.get('new-pass')
    userUpdateData = Users.update_data(None if newUsername == session.get('username') else newUsername, None if newMail == session.get('mail') else newMail, newPass)

    if not userUpdateData:
        return {"success":False}

    return jsonify({
        "success":True
    })
@app.route('/load', methods=["GET", "POST"])
def load():
    return render_template("load.html")

@app.route('/create-account', methods=["GET", "POST"])
def create_account():
    session.clear()
    if request.method == "POST":
        data = request.get_json()

        name = data['username']
        mail = data['mail']
        password = data['password']
        password = password.replace(" ","").strip().lower()
       
       

        user = Users.create_user(name,mail,password)
        verification_process = Tokens.create_token("email_verification", datetime.utcnow() + timedelta(minutes=15))
        print("code: ", verification_process.token)
        bridge = Bridge(
                id_user = user.id,
                id_token = verification_process.id_token
                )
        db.session.add(bridge)
        db.session.commit()


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
    session.clear()
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
    
@app.route('/create-account/verification/<email_to>', methods=["GET", "POST"])
def verify_email_via(email_to):
    mail = email_to
    return render_template("verify.html", mail = mail)


if __name__ == "__main__":
    os.makedirs('static/post_images', exist_ok=True)
    os.makedirs('static/userpic', exist_ok=True)
    with app.app_context():
        db.create_all()

    app.run(debug=True)


