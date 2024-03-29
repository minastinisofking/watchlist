# 为了简化数据库操作，我们将使用 SQLAlchemy——一个 Python 数据库工具（ORM，即对象关系映射）。
# 借助 SQLAlchemy，你可以通过定义 Python 类来表示数据库里的一张表（类属性表示表中的字段 / 列），
# 通过对这个类进行各种操作来代替写 SQL 语句。这个类我们称之为模型类，类中的属性我们将称之为字段。

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash
import click
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
# flash() 函数在内部会把消息存储到 Flask 提供的 session 对象里。session 用来在请求间存储数据，
# 它会把数据签名后存储到浏览器的 Cookie 中，所以我们需要设置签名所需的密钥
app.config['SECRET_KEY'] = '123456'
login_manager = LoginManager(app) # 实例化扩展类
login_manager.login_view = 'login'

@app.cli.command()                                                  # 注册为命令
@click.option('--drop', is_flag=True, help='Create after drop.')    # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:                                                        # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')                             # 输出提示信息

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.name = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name=username)
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')

@app.cli.command()
def forge():
    """Generate fake data."""
    db.create_all()

    # 全局的两个变量移动到这个函数内
    # name = 'minastinis'
    movies = [
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)

    db.session.commit()
    click.echo('Done.')

# 判断电脑的操作系统
WIN = sys.platform.startswith('win')
if WIN:                     # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:                       # 否则使用四个斜线
    prefix = 'sqlite:////'

# 为了设置 Flask、扩展或是我们程序本身的一些行为，我们需要设置和定义一些配置变量。
# 写入了一个 SQLALCHEMY_DATABASE_URI 变量来告诉 SQLAlchemy 数据库连接地址
# sqlite:////数据库文件的绝对地址
# app.root_path 返回程序实例所在模块的路径（目前来说，即项目根目录）
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONs'] = False    # 关闭对模型修改的监控
db = SQLAlchemy(app)                                    # 初始化扩展，传入程序实例app

# 目前我们有两类信息要保存：用户信息和电影条目信息。下面分别创建了两个模型类来表示这两张表
# 模型类要声明继承 db.Model
# 继承UserMixin类会让 User 类拥有几个用于判断认证状态的属性和方法，其中最常用的是 is_authenticated 属性：
# 如果当前用户已经登录，那么 current_user.is_authenticated 会返回 True， 否则返回 False
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))                             # 用户名
    password_hash = db.Column(db.String(128))                       # 密码散列值

    def set_password(self, password):                               # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)       # 将生成的密码保持到对应字段

    def validate_password(self, user_pwd):                          # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, user_pwd)    # 返回布尔值

class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)    # 主键
    title = db.Column(db.String(60))                # 电影标题
    year = db.Column(db.String(4))                  # 电影年份

# 注册这个函数的目的是，当程序运行后，如果用户已登录，
# current_user 变量的值会是当前用户的用户模型类记录。
@login_manager.user_loader
def load_user(user_id):                             # 创建用户加载回调函数，接受用户ID作为参数
    user = User.query.get(int(user_id))             # 用ID作为User模型的主键查询对应的用户
    return user

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':                    # 判断是否是 POST 请求
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 重定向到主页
        # 获取表单数据
        title = request.form.get('title')           # 传入表单对应输入字段的 name 值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')                 # 显示错误提示
            return redirect(url_for('index'))       # 重定向回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year)       # 创建记录
        db.session.add(movie)                       # 添加到数据库会话
        db.session.commit()                         # 提交数据库会话
        flash('Item created.')                      # 显示成功创建的提示
        return redirect(url_for('index'))           # 重定向回主页

    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required # 登录保护
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST':                    # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year)>4 or len(title) > 60:
            flash('Invalid input')
            return redirect(url_for('edit', movie_id=movie_id))# 重定向回对应的编辑页面

        movie.title = title                         # 更新标题
        movie.year = year                           # 更新年份
        db.session.commit()                         # 提交数据库会话
        flash('Item update.')
        return redirect(url_for('index'))           # 重定向回主页

    return render_template('edit.html', movie=movie) # 传出被编辑的电影记录

# 删除条目，表面上是直接进行删除的，但实际上却是跳转到/delete页面，很快执行完删除操作后，又跳转了回来
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
@login_required
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)    # 获取电影记录
    db.session.delete(movie)                    # 删除对应的记录
    db.session.commit()                         # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))           # 重定向回主页

# 用户登录函数
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 验证用户名和密码一致
        if username == user.username and user.validate_password(password):
            login_user(user)                    # 登入用户
            flash('Login success.')
            return redirect(url_for('index'))   # 重定向到主页

        flash('Invalid username or password.')  # 如果验证失败，显示错误消息
        return redirect(url_for('login'))       # 重定向回登录页面

    return render_template('login.html')

@app.route('/logout')
@login_required                                 # 用于视图保护
def logout():
    logout_user()                               # 登出用户
    flash('Goodbye')
    return redirect(url_for('index'))           # 重定向回首页


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))

    return render_template('settings.html')

# 使用装饰器注册一个错误处理函数
@app.errorhandler(404)                          # 传入要处理的错误代码
def page_not_found(e):                          # 接受异常对象作为参数
    return render_template('404.html'), 404     # 返回模板和状态码
# 和我们前面编写的视图函数相比，这个函数返回了状态码作为第二个参数，普通的视图函数之所以不用写出状态码，
# 是因为默认会使用 200 状态码，表示成功。

# 使用 app.context_processor 装饰器注册一个模板上下文处理函数
# 这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。
@app.context_processor
def inject_user():      # 函数名可以随意更改
    user = User.query.first()
    return dict(user=user) # 需要返回字典，等同于return {'user': user}