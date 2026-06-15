from os.path import join
from posixpath import splitext
from re import U
from flask import * 
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import  or_, func
import uuid 
import bcrypt
import os
app = Flask(__name__)
app.secret_key = "dkaokoqwkj190j329jd9xn2i398d9283"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///privsocial.db"

db = SQLAlchemy(app)





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
    @classmethod
    def update_photo(cls, filename):
        userUpdatePhoto = db.session.get(cls, session.get("user_id"))
        userUpdatePhoto.user_picture = filename
        db.session.commit()

        return userUpdatePhoto
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

    user = db.relationship('Users')
    post = db.relationship('Posts')


@app.context_processor
def inject_data():
    user_id = session.get('user_id')
    name = session.get('username')
    mail = session.get('mail')
    
    user = Users.query.filter_by(id = user_id).first()
    return{
        "username":name,
        "id":id,
        "mail": mail,
        "user":user

    }

@app.route('/feed', methods=["GET", "POST"])
def feed():
    user_id = session.get('user_id') 
    user_posts = Bridge.query.order_by(func.random()).all()
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
        return {"success:False"}

    return jsonify({
        "success":True,
        "userData": user
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

        user = Users.create_user(name,mail,password)

        if not user:
            return {
                "success":False
            }
        
        return {
            "success":True,
            "username":user.username
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
    



if __name__ == "__main__":
    os.makedirs('static/post_images', exist_ok=True)
    os.makedirs('static/userpic', exist_ok=True)
    with app.app_context():
        db.create_all()

    app.run(debug=True)


