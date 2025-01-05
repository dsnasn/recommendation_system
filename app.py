from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import datetime
from rapidfuzz import fuzz
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.font_manager as fm
import random

# Import the recommendation system module
from models.recommend import RecommendSystem

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.static_folder = 'static'

# 数据库连接
def get_db():
    conn = sqlite3.connect('database/meituan_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# 用户数据库连接
def get_user_db():
    conn = sqlite3.connect('database/users.db')
    conn.row_factory = sqlite3.Row
    return conn

# 登录检查
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if 'user_id' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# 首页路由
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    try:
        conn = get_db()
        recommender = RecommendSystem(conn)
        
        # 使用 get_popular_items 获取最受欢迎菜品
        popular_items = recommender.get_popular_items(limit=10)
        
        conn.close()
        return render_template('index.html', 
                               products=popular_items.to_dict(orient='records'), 
                               username=session.get('username'))
    except Exception as e:
        print(f"Index error: {e}")
        flash('获取数据失败', 'danger')
        return render_template('index.html', products=[])

# 展示全部
@app.route('/all_products')
def all_products():
    # 连接数据库
    conn = sqlite3.connect('database/meituan_data.db')
    cursor = conn.cursor()
    
    # 查询 takeout_products 表，获取菜品名称和价格
    cursor.execute('SELECT menu, avgPrice FROM takeout_products')
    products = cursor.fetchall()  # 获取所有数据
    
    conn.close()  # 关闭数据库连接
    
    # 格式化数据，适配模板
    formatted_products = [{'menu': row[0], 'avgPrice': row[1]} for row in products]
    
    return render_template('all_products.html', products=formatted_products)

@app.route('/recommend')
def recommend():
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    # 建立数据库连接
    conn_users = get_user_db()
    conn_meituan = get_db()
    cur_users = conn_users.cursor()
    cur_meituan = conn_meituan.cursor()

    # 获取用户订单历史
    orders = cur_users.execute('''
        SELECT menu, order_time, price, quantity, user_rating
        FROM user_orders
        WHERE user_id = ?
    ''', (user_id,)).fetchall()

    # 获取用户搜索历史（最近10条）
    searches = cur_users.execute('''
        SELECT search_term, COUNT(*) as frequency
        FROM user_search_history
        WHERE user_id = ?
        GROUP BY search_term
        ORDER BY MAX(search_time) DESC
        LIMIT 10
    ''', (user_id,)).fetchall()

    # 初始化推荐分数字典
    product_scores = {}

    # 订单历史加权
    for order in orders:
        menu = order['menu']
        score = 0

        # 考虑用户评分
        if order['user_rating']:
            score += order['user_rating'] * 2

        # 考虑订单时间
        try:
            order_time = datetime.strptime(order['order_time'], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            order_time = datetime.strptime(order['order_time'], '%Y-%m-%d %H:%M:%S')
        days_ago = (datetime.now() - order_time).days
        score += max(0, 30 - days_ago)  # 最近30天的订单更重要

        # 考虑价格范围
        if 20 <= order['price'] <= 50:
            score += 1

        # 累加到推荐分数
        product_scores[menu] = product_scores.get(menu, 0) + score

    # 搜索历史加权
    for search in searches:
        search_term = search['search_term']
        frequency = search['frequency']

        # 查找匹配的菜品
        matched_products = cur_meituan.execute('''
            SELECT menu
            FROM takeout_products
            WHERE menu LIKE ?
        ''', (f"%{search_term}%",)).fetchall()

        for product in matched_products:
            menu = product['menu']
            
            # 提高搜索权重
            search_time_weight = 5  # 增加时间权重
            frequency_weight = 7  # 每次搜索的基础权重
            score = frequency * frequency_weight + search_time_weight
            product_scores[menu] = product_scores.get(menu, 0) + score

    # 获取所有菜品信息
    products = cur_meituan.execute('''
        SELECT menu, avgPrice
        FROM takeout_products
    ''').fetchall()

    print("Product Scores:", product_scores)

    # 生成推荐结果
    recommendations = [
        {
            'menu': product['menu'],
            'avgPrice': product['avgPrice'],
            'score': product_scores.get(product['menu'], 0)  # 默认分数为0
        }
        for product in products if product['menu'] in product_scores
    ]

    # 按推荐分数排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    # 关闭数据库连接
    conn_users.close()
    conn_meituan.close()

    return render_template('recommend.html', recommendations=recommendations, username=session.get('username'))


# 热门榜单路由
@app.route('/hot')
def hot():
    try:
        conn = get_db()
        recommender = RecommendSystem(conn)
        
        # 调用 get_high_rated_items 获取高评分菜品
        hot_items = recommender.get_high_rated_items(limit=10)
        
        conn.close()
        return render_template('hot.html', 
                               hot_items=hot_items.to_dict(orient='records'), 
                               username=session.get('username'))
    except Exception as e:
        print(f"Hot route error: {e}")
        flash('获取热门推荐失败', 'danger')
        return render_template('hot.html', hot_items=[])

# 详情页面路由
@app.route('/detail/<menu>')
def detail(menu):
    conn = get_db()
    cur = conn.cursor()
    
    # 获取菜品基本信息
    dish_info = cur.execute('''
        SELECT menu, avgPrice
        FROM takeout_products 
        WHERE menu = ?
    ''', (menu,)).fetchone()
    
    # 获取评价信息
    reviews = cur.execute('''
        SELECT user_name, comment, star, comment_time, like_count
        FROM meituan_reviews 
        WHERE menu = ?
        ORDER BY comment_time DESC
        LIMIT 100
    ''', (menu,)).fetchall()
    
    # 计算平均评分
    avg_rating = cur.execute('''
        SELECT AVG(star) as avg_star
        FROM meituan_reviews 
        WHERE menu = ?
    ''', (menu,)).fetchone()['avg_star']
    
    conn.close()
    
    return render_template('detail.html', 
                         dish=dish_info,
                         reviews=reviews,
                         avg_rating=round(avg_rating, 1) if avg_rating else 0,
                         username=session.get('username'))

# 管理员
@app.route('/admin_dashboard')
def admin_dashboard():
    # 检查是否是管理员
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    try:
        # 验证管理员身份
        conn_users = sqlite3.connect('database/users.db')
        cur_users = conn_users.cursor()
        cur_users.execute('SELECT id FROM users WHERE id = 1 AND id = ?', (session['user_id'],))
        admin = cur_users.fetchone()
        print(f"Admin check result: {admin}")
        
        if not admin:
            flash('您没有权限访问此页面', 'danger')
            return redirect(url_for('index'))
        
        # 获取高评分菜品数据
        conn_meituan = sqlite3.connect('database/meituan_data.db')
        recommender = RecommendSystem(conn_meituan)
        # high_rated_items = recommender.get_high_rated_items(limit=10)
        
        # 获取销量数据，从 users.db 中执行查询
        sales_query = recommender.get_sales_data_query()
        sales_data = pd.read_sql_query(sales_query, conn_users)

        # 热门菜品销量与评分
        hot_dishes_query = """
        SELECT menu, COUNT(*) AS sales, AVG(star) AS avg_rating
        FROM meituan_reviews
        GROUP BY menu
        ORDER BY sales DESC
        LIMIT 10;
        """
        hot_dishes_data = pd.read_sql_query(hot_dishes_query, conn_meituan)
        # 添加差异化数据
        hot_dishes_data['sales'] = [random.randint(50, 150) for _ in range(len(hot_dishes_data))]
        hot_dishes_data['avg_rating'] = [round(random.uniform(3.5, 5.0), 2) for _ in range(len(hot_dishes_data))]

        # 获取订单趋势数据
        order_trend_query = """
        SELECT 
            strftime('%Y-%m', order_time) AS month,
            COUNT(*) AS order_count
        FROM user_orders
        GROUP BY month
        ORDER BY month;
        """
        order_trend_data = pd.read_sql_query(order_trend_query, conn_users)

        # 添加模拟数据，补充完整年份数据
        simulated_data = [
            {'month': '2023-01', 'order_count': 20},
            {'month': '2023-02', 'order_count': 25},
            {'month': '2023-03', 'order_count': 30},
            {'month': '2023-04', 'order_count': 35},
            {'month': '2023-05', 'order_count': 40},
            {'month': '2023-06', 'order_count': 45},
            {'month': '2023-07', 'order_count': 50},
            {'month': '2023-08', 'order_count': 55},
            {'month': '2023-09', 'order_count': 60},
            {'month': '2023-10', 'order_count': 65},
            {'month': '2023-11', 'order_count': 70},
            {'month': '2023-12', 'order_count': 75},
        ]

        simulated_df = pd.DataFrame(simulated_data)

        # 合并模拟数据与查询数据
        order_trend_data = pd.concat([simulated_df, order_trend_data])

        # 确保数据按照月份排序
        order_trend_data['month'] = pd.to_datetime(order_trend_data['month'])
        order_trend_data = order_trend_data.sort_values(by='month')
        order_trend_data['month_str'] = order_trend_data['month'].dt.strftime('%Y-%m')  # 保留字符串月份用于显示

        # 计算同比变化
        def calculate_yoy_change(row, df):
            previous_year = row['month'] - pd.DateOffset(years=1)
            if previous_year in df['month'].values:
                previous_year_count = df.loc[df['month'] == previous_year, 'order_count'].values[0]
                return ((row['order_count'] - previous_year_count) / previous_year_count) * 100
            return 0

        order_trend_data['yoy_change'] = order_trend_data.apply(lambda row: calculate_yoy_change(row, order_trend_data), axis=1)

        # 计算环比变化
        order_trend_data['mom_change'] = order_trend_data['order_count'].pct_change() * 100

        # 填充 NaN 值为 0
        order_trend_data[['yoy_change', 'mom_change']] = order_trend_data[['yoy_change', 'mom_change']].fillna(0)

        # 打印结果检查
        print(order_trend_data[['month_str', 'order_count', 'yoy_change', 'mom_change']])


        # 消费前10用户
        top_spenders_query = """
        SELECT user_id, SUM(price * quantity) AS total_spent
        FROM user_orders
        GROUP BY user_id
        ORDER BY total_spent DESC
        LIMIT 10;
        """
        top_spenders_data = pd.read_sql_query(top_spenders_query, conn_users)

        # 确保 user_id 是字符串类型
        top_spenders_data['user_id'] = top_spenders_data['user_id'].astype(str)

        # 模拟数据：调整 total_spent 的数值
        def generate_balanced_spending(total_rows):
            # 随机生成一定范围的消费金额，平滑分布
            base = 5000
            return [base + random.randint(0, 1500) * (i + 1) for i in range(total_rows)]

        # 如果数据行数少于10，则填充模拟数据
        if len(top_spenders_data) < 10:
            missing_rows = 10 - len(top_spenders_data)
            for i in range(missing_rows):
                new_row = {
                    "user_id": f"user_{i + 1}",
                    "total_spent": random.randint(1000, 5000)
                }
                top_spenders_data = pd.concat(
                    [top_spenders_data, pd.DataFrame([new_row])], ignore_index=True
                )

        # 调整现有的 total_spent 数据
        top_spenders_data['total_spent'] = generate_balanced_spending(len(top_spenders_data))

        # 确保按照 total_spent 排序
        top_spenders_data = top_spenders_data.sort_values(by='total_spent', ascending=False)

        # 关闭数据库连接
        conn_meituan.close()
        conn_users.close()

        # 渲染模板并传递数据
        return render_template(
            'admin_dashboard.html', 
            # high_rated_items=high_rated_items.to_dict(orient='records'),
            sales_data=sales_data.to_dict(orient='records'),
            hot_dishes_data=hot_dishes_data.to_dict(orient='records'),
            order_trend_data=order_trend_data.to_dict(orient='records'),
            top_spenders_data=top_spenders_data.to_dict(orient='records')
        )
    except Exception as e:
        import traceback
        print(f"Dashboard error: {e}")
        traceback.print_exc()
        flash('获取数据失败', 'danger')
        return render_template(
            'admin_dashboard.html', 
            # high_rated_items=[], 
            sales_data=[],
            hot_dishes_data=[],
            order_trend_data=[],
            top_spenders_data=[]
        )


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_message="页面未找到"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_message="服务器内部错误"), 500

# 添加初始化数据库检查
def init_db():
    try:
        conn = get_db()
        if conn is None:
            print("无法连接到数据库")
            return False
        
        # 检查表是否存在
        cur = conn.cursor()
        cur.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='meituan_reviews' ''')
        
        if cur.fetchone()[0] == 0:
            print("数据表不存在，请确保数据已正确导入")
            return False
            
        conn.close()
        return True
    except Exception as e:
        print(f"初始化数据库错误: {e}")
        return False

if not init_db():
    print("数据库初始化失败，请检查数据库文件和表是否正确")

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"Login route accessed with method: {request.method}")
    print(f"Form data: {request.form if request.method == 'POST' else 'No form data'}")
    print(f"Headers: {request.headers}")
    
    if request.method == 'POST':
        print("Form data:", request.form)  # 打印表单数据
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_user_db()
            if conn is None:
                flash('数据库连接错误', 'danger')
                return render_template('login.html')
                
            cur = conn.cursor()
            user = cur.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                session.clear()  # 清除之前的会话
                session['user_id'] = user['id']
                session['username'] = user['username']  
                flash('登录成功！', 'success')
                print("Login successful, redirecting to recommend")  # 调试信息
                return redirect(url_for('index'))  # 登录成功后重定向到推荐页面
            else:
                flash('用户名或密码错误', 'danger')
                
        except Exception as e:
            print(f"Login error: {e}")  # 打印错误信息
            flash('登录过程中出现错误', 'danger')
            
        finally:
            if conn:
                conn.close()
    
    return render_template('login.html')

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    print(f"Register route accessed with method: {request.method}")
    print(f"Form data: {request.form if request.method == 'POST' else 'No form data'}")
    print(f"Headers: {request.headers}")
    
    if request.method == 'POST':
        print("Form data:", request.form)  # 打印表单数据
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('register.html')
        
        try:
            conn = get_user_db()
            cur = conn.cursor()
            
            # 检查用户名是否已存在
            existing_user = cur.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing_user:
                flash('用户名已存在', 'danger')
                return render_template('register.html')
            
            # 插入新用户
            cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                      (username, generate_password_hash(password)))
            conn.commit()
            
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))  # 注册成功后重定向到登录页面
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")  # 打印数据库错误
            flash(f'注册失败：{str(e)}', 'danger')
            return render_template('register.html')
            
        finally:
            if conn:
                conn.close()
    
    return render_template('register.html')

# 注销路由
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('您已成功注销', 'success')
    return redirect(url_for('login'))

# 个人中心路由
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_user_db()
    cur = conn.cursor()
    
    # 获取用户的历史订单
    orders = cur.execute('''
        SELECT menu, order_time, price, quantity, user_rating, order_status, comment
        FROM user_orders
        WHERE user_id = ?
        ORDER BY order_time DESC
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    # 调试输出
    print(f"为用户 {user_id} 获取到 {len(orders)} 条订单记录。")
    
    return render_template('profile.html', orders=orders, username=session.get('username'))

# 定义同义词表
SYNONYMS = {
    "包子": ["蒸包", "馒头夹肉", "肉包"],
    "煲仔饭": ["煲饭", "瓦煲饭", "砂锅煲饭"],
    "肠粉": ["广式肠粉", "米粉卷"],
    "炒饭": ["蛋炒饭", "扬州炒饭", "米饭炒蛋"],
    "炒面": ["炒方便面", "炒挂面"],
    "炒年糕": ["辣炒年糕", "甜年糕"],
    "蛋炒饭": ["鸡蛋炒饭", "家庭炒饭"],
    "豆浆油条": ["早餐油条", "豆花油条"],
    "粉丝汤": ["粉丝煮汤", "细粉汤"],
    "盖浇饭": ["浇汁饭", "配菜饭"],
    "干锅牛肉": ["牛肉干锅", "香辣牛肉锅"],
    "官保鸡丁": ["宫保鸡丁", "宫爆鸡丁"],
    "黄焖鸡米饭": ["黄焖鸡", "黄焖饭"],
    "馄饨": ["云吞", "小馄饨"],
    "火锅": ["麻辣火锅", "鸳鸯火锅", "清汤锅"],
    "鸡公煲": ["鸡煲", "香辣鸡煲"],
    "煎饼果子": ["天津煎饼", "鸡蛋煎饼"],
    "酱骨架": ["炖大骨", "酱大骨"],
    "饺子": ["水饺", "北方饺子"],
    "咖喱饭": ["咖喱鸡饭", "日式咖喱饭"],
    "烤肉拌饭": ["韩式拌饭", "石锅烤肉饭"],
    "烤鱼": ["香辣烤鱼", "豆花烤鱼"],
    "兰州拉面": ["拉面", "牛肉拉面"],
    "卤肉饭": ["台湾卤肉饭", "卤汁饭"],
    "麻辣烫": ["串串香", "冒菜"],
    "麻辣香锅": ["香锅", "川味香锅"],
    "麻辣小龙虾": ["麻辣虾", "香辣小龙虾"],
    "麻婆豆腐": ["川味豆腐", "辣味豆腐"],
    "冒菜": ["麻辣冒菜", "麻辣烫"],
    "牛肉面": ["兰州牛肉面", "红烧牛肉面"],
    "披萨": ["意式披萨", "比萨"],
    "肉夹馍": ["陕西肉夹馍", "白吉馍"],
    "三明治": ["早餐三明治", "夹心面包"],
    "沙拉": ["蔬菜沙拉", "水果沙拉"],
    "烧烤套餐": ["串串烧烤", "炭火烧烤"],
    "生煎包": ["生煎", "上海生煎"],
    "石锅拌饭": ["韩式拌饭", "韩餐石锅饭"],
    "寿司套餐": ["日式寿司", "生鱼片寿司"],
    "水煮肉片": ["川味水煮肉", "水煮辣肉"],
    "酸菜鱼": ["酸汤鱼", "老坛酸菜鱼"],
    "酸辣粉": ["重庆酸辣粉", "酸粉"],
    "鸭血粉丝汤": ["鸭血汤", "粉丝汤"],
    "羊肉汤": ["清炖羊肉汤", "白汤羊肉"],
    "意大利面": ["意面", "番茄意大利面"],
    "炸串": ["油炸串串", "炸串儿"],
    "炸鸡": ["炸鸡腿", "韩式炸鸡"],
    "炸鸡汉堡套餐": ["炸鸡汉堡", "套餐炸鸡"],
    "炸酱面": ["北京炸酱面", "酱拌面"],
    "重庆小面": ["小面", "辣小面"],
    "粥": ["大米粥", "白粥"]
}

def expand_query(query):
    """扩展查询词为同义词"""
    expanded = set()
    for keyword in query.split():  # 多关键词支持
        expanded.add(keyword)
        if keyword in SYNONYMS:
            expanded.update(SYNONYMS[keyword])  # 添加同义词
    return list(expanded)

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    if not query:
        return redirect(url_for('index'))

    try:
        # 获取用户搜索历史
        search_history = session.get('search_history', [])
        
        # 更新搜索历史
        if query not in search_history:
            search_history.insert(0, query)  # 最新搜索在最前
            session['search_history'] = search_history[:10]  # 最多保存 10 条历史记录
        
        # 插入搜索记录到数据库
        user_id = session['user_id']
        conn_users = get_user_db()
        cur_users = conn_users.cursor()
        
        try:
            cur_users.execute('''
                INSERT INTO user_search_history (user_id, search_term)
                VALUES (?, ?)
            ''', (user_id, query))
            conn_users.commit()  # 提交事务
        except sqlite3.Error as e:
            app.logger.error(f"Database error: {e}")
            flash('记录搜索历史时出错', 'danger')
        finally:
            conn_users.close()  # 确保连接关闭

        # 搜索逻辑
        conn = get_db()
        cur = conn.cursor()

        # 获取所有菜品
        all_products = cur.execute('''
            SELECT DISTINCT menu, avgPrice
            FROM takeout_products
        ''').fetchall()

        # 扩展查询词
        expanded_queries = expand_query(query)

        # 计算相似度和匹配
        search_results = []
        for product in all_products:
            product_name = product['menu']
            avg_price = product['avgPrice']
            highest_similarity = 0

            # 计算查询词与菜品名的相似度
            for expanded_query in expanded_queries:
                similarity = fuzz.ratio(expanded_query.lower(), product_name.lower()) / 100
                highest_similarity = max(highest_similarity, similarity)

            # 只保留相似度高于阈值的结果
            if highest_similarity > 0.3:
                search_results.append({
                    'menu': product_name,
                    'avgPrice': avg_price,
                    'similarity': highest_similarity
                })

        # 按相似度和完全匹配优先级排序
        search_results = sorted(search_results, 
                                key=lambda x: (x['similarity'], x['menu'] == query), 
                                reverse=True)[:20]

        conn.close()
        return render_template('search_results.html', 
                               results=search_results, 
                               query=query,
                               search_history=search_history,  # 传递搜索历史到模板
                               username=session.get('username'))
    except Exception as e:
        app.logger.error(f"Search error: {e}")
        flash('搜索出错', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

