from flask import * 
from flask_sqlalchemy import SQLAlchemy 
import uuid 

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///privsocial.db"

db = SQLAlchemy(app)


@app.route('/feed', methods=["GET", "POST"])
def guess_feed():
    guess_id = str(uuid.uuid4())

    return render_template("feed.html", guess = guess_id)

@app.route('/load', methods=["GET", "POST"])
def load():
    return render_template("load.html")

@app.route('/create-account', methods=["GET", "POST"])
def create_account():
    return render_template("create_acc.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)


