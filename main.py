from flask import Flask, render_template, redirect, url_for, flash ,abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm ,CommentForm
from flask_gravatar import Gravatar
from functools import wraps
from dotenv import load_dotenv
from models import User , BlogPost, Comment
import os

load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if  not current_user.is_authenticated or current_user.id!=1:
            abort(403)
        return f(*args,**kwargs)
    return decorated_function



@app.route('/')
def get_all_posts():
    
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts,logged_in=current_user.is_authenticated,user=current_user)


@app.route('/register',methods=["GET","POST"])
def register():

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        name = form.name.data
        hashed_pass =generate_password_hash(password=password,method='pbkdf2:sha256',
                                            salt_length=8)
        existing_email = User.query.filter_by(email=email).first()

        if existing_email:
            flash("You Have Already Signed Up with this email! Log In!")
            return redirect(url_for('login'))                                    
        else:

            user = User(email=email,password=hashed_pass,name=name)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("register.html",form=form,logged_in=current_user.is_authenticated)


@app.route('/login',methods=["GET","POST"])
def login():
    
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("That Email does not Exist!")
            return redirect(url_for('login'))
        else:
            if check_password_hash(user.password,password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash("Wrong Password, Try Again!")
                return redirect(url_for('login'))

    return render_template("login.html",form=form,logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["GET","POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            text = comment_form.body.data
            author_id = current_user.id
            post_idd = post_id
            comment = Comment(author_id=author_id,post_id=post_idd,text=text)
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('get_all_posts'))
        else:
            flash("You need to login or register!")
            return redirect(url_for('login'))

    return render_template("post.html", post=requested_post,user = current_user,
                           logged_in=current_user.is_authenticated,comment_form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post",methods=["GET","POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author_id=current_user.id,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,logged_in=current_user.is_authenticated)


@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000,debug=True)
