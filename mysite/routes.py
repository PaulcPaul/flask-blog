import secrets
import os

from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, send_from_directory, current_app
from sqlalchemy import desc

from mysite.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RespostaForm
from mysite.models import User, Post, Resposta, Scores
from flask_login import login_user, current_user, logout_user, login_required

from mysite import app, db, bcrypt
from mysite.pdf_gen import generate_posts, generate_users

@app.route("/")
def home():
    posts = Post.query.order_by(desc(Post.id)).all()
    popular = Post.query.order_by(desc(Post.total_score)).limit(3)
    return render_template('home.html', posts = posts, popular_posts = popular)

@app.route("/about")
def about():
    popular = Post.query.order_by(desc(Post.total_score)).limit(3)
    return render_template('about.html', title = 'About', popular_posts = popular)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada com sucesso.', 'success')
        return redirect(url_for('login'))

    popular = Post.query.order_by(desc(Post.total_score)).limit(3)
    return render_template('register.html', title = 'Register', form = form, popular_posts = popular)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))

        flash('Login não foi possível. Verifique as credenciais.', 'danger')

    popular = Post.query.order_by(desc(Post.total_score)).limit(3)
    return render_template('login.html', title = 'Login', form = form, popular_posts = popular)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)

    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics/' + picture_fn)

    output_size = (120, 120)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()

    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Sua conta foi modificada.', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    popular = Post.query.order_by(desc(Post.total_score)).limit(3)
    image_file = url_for('static', filename=f"profile_pics/{current_user.image_file}")
    return render_template('account.html', 
                            title = 'Account', 
                            image_file = image_file, 
                            form = form,
                            popular_posts = popular)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title = form.title.data, content = form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('O seu post foi criado!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', 
                            title = 'New Post',
                            form = form, legend='New Post')

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
@login_required
def post(post_id):
    form = RespostaForm()
    if form.validate_on_submit():
        resposta = Resposta(content=form.content.data, responser=current_user, post=Post.query.get(post_id))
        db.session.add(resposta)
        db.session.commit()
        flash('Resposta enviada!', 'success')
        return redirect(url_for('post', post_id=post_id))

    respostas = Resposta.query.filter_by(post_id=post_id)

    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title = post.title,
                            post = post,
                            form = form,
                            respostas = respostas)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)

    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Post atualizado!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', 
                            title = 'Update Post',
                            form = form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user and current_user.user_type != "A":
        abort(403)

    scores = Scores.query.filter_by(post_id=post.id)

    for score in scores:
        db.session.delete(score)
    
    db.session.delete(post)
    db.session.commit()
    flash('Post deletado com sucesso!', 'success')

    return redirect(url_for('home'))

@app.route("/resposta/<int:post_id>/<int:resposta_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_resposta(resposta_id, post_id):
    res = Resposta.query.get_or_404(resposta_id)

    if current_user.user_type == "U":
        abort(403)
    
    db.session.delete(res)
    db.session.commit()
    flash('Comentário deletado com sucesso!', 'success')

    return redirect(url_for('post', post_id=post_id))

@app.route('/upvote/<int:post_id>/<int:user_id>')
@login_required
def upvote(post_id,user_id):
    vote_type = 'L'
    post = Post.query.get_or_404(post_id)

    if Scores.query.filter_by(post_id=post_id, user_id=user_id, score_type=vote_type).count() > 0:
        score = Scores.query.filter_by(post_id=post_id, user_id=user_id, score_type=vote_type).first()
        post.total_score -= 1
        db.session.delete(score)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        score = Scores(user_id=user_id, post_id=post_id, score_type=vote_type)
        post.total_score += 1
        db.session.add(score)
        db.session.commit()
        return redirect(url_for('home'))

    return redirect(url_for('home'))

@app.route('/downvote/<int:post_id>/<int:user_id>')
@login_required
def downvote(post_id,user_id):
    vote_type = 'D'
    post = Post.query.get_or_404(post_id)

    if Scores.query.filter_by(post_id=post_id, user_id=user_id, score_type=vote_type).count() > 0:
        score = Scores.query.filter_by(post_id=post_id, user_id=user_id, score_type=vote_type).first()
        post.total_score += 1
        db.session.delete(score)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        score = Scores(user_id=user_id, post_id=post_id, score_type=vote_type)
        post.total_score -= 1
        db.session.add(score)
        db.session.commit()
        return redirect(url_for('home'))

    return redirect(url_for('home'))

@app.route("/control_panel")
@login_required
def control_panel():
    if current_user.user_type == "U":
        abort(403)
    
    posts = Post.query.order_by(desc(Post.id)).all()
    users = User.query.all()
    respostas = Resposta.query.all()
    scores = Scores.query.all()
    return render_template('control_panel.html', posts = posts, users = users, respostas = respostas, scores = scores)

@app.route("/user/<int:user_id>/delete", methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if current_user.user_type != "A":
        abort(403)
    
    db.session.delete(user)
    db.session.commit()
    flash('Usuário deletado com sucesso!', 'success')

    return redirect(url_for('control_panel'))

@app.route("/scores/<int:post_id>/delete", methods=['GET','POST'])
@login_required
def delete_scores(post_id):
    post = Post.query.get_or_404(post_id)
    scores = Scores.query.filter_by(post_id=post.id)

    if current_user.user_type != "A":
        abort(403)
    
    post.total_score = 0

    for score in scores:
        db.session.delete(score)
    
    db.session.commit()
    
    flash('Votos deletado com sucesso!', 'success')

    return redirect(url_for('control_panel'))

@app.route("/pdfusers", methods=['GET', 'POST'])
@login_required
def generate_user_pdf():
    users = User.query.all()

    if current_user.user_type != "A":
        abort(403)
    
    path = generate_users(users)
        
    flash('PDF gerado com sucesso!', 'success')

    filename = 'lista_usuarios.pdf'

    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])

    return send_from_directory(directory=uploads, filename=filename)

@app.route("/pdfposts", methods=['GET', 'POST'])
@login_required
def generate_posts_pdf():
    posts = Post.query.all()

    if current_user.user_type != "A":
        abort(403)
    
    path = generate_posts(posts)

    filename = 'lista_posts.pdf'

    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])

    return send_from_directory(directory=uploads, filename=filename)

@app.route("/user/<int:user_id>/makemod", methods=['GET', 'POST'])
@login_required
def make_moderator(user_id):
    user = User.query.get_or_404(user_id)

    if current_user.user_type != "A":
        abort(403)

    if user.user_type != "M":
        user.user_type = "M"
    else:
        user.user_type = "U"

    db.session.commit()

    return redirect(url_for('control_panel'))