import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.font_manager as fm
import random

# 手动加载中文字体文件
font_path = "./SimHei.ttf"  # 替换为系统中的中文字体路径
font_prop = fm.FontProperties(fname=font_path)

# 设置 Matplotlib 参数
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 模拟生成差异化数据
def generate_modified_data():
    conn = sqlite3.connect('database/meituan_data.db')
    query = """
    SELECT menu, COUNT(*) AS sales, AVG(star) AS avg_rating
    FROM meituan_reviews
    GROUP BY menu
    ORDER BY sales DESC
    LIMIT 10;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 在销量和评分上增加差异
    df['sales'] = [random.randint(50, 150) for _ in range(len(df))]
    df['avg_rating'] = [round(random.uniform(3.5, 5.0), 2) for _ in range(len(df))]
    return df

# 热门菜品销量与评分
def hot_dishes_visual():
    df = generate_modified_data()
    
    plt.figure(figsize=(12, 6))
    plt.bar(df['menu'], df['sales'], color='orange', alpha=0.7, label='销量')
    plt.plot(df['menu'], df['avg_rating'], color='blue', marker='o', label='平均评分')
    plt.title('热门菜品销量与评分（模拟差异化数据）', fontsize=18, fontproperties=font_prop)
    plt.xlabel('菜品', fontsize=14, fontproperties=font_prop)
    plt.ylabel('销量 / 平均评分', fontsize=14, fontproperties=font_prop)
    plt.xticks(rotation=45, fontsize=12, fontproperties=font_prop)
    plt.yticks(fontsize=12, fontproperties=font_prop)
    plt.legend(fontsize=12, prop=font_prop)
    plt.tight_layout()
    plt.show()

# 用户订单趋势
def order_trend_visual():
    conn = sqlite3.connect('database/users.db')
    query = """
    SELECT strftime('%Y-%m', order_time) AS month, COUNT(*) AS order_count
    FROM user_orders
    GROUP BY month
    ORDER BY month;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    plt.figure(figsize=(10, 6))
    plt.plot(df['month'], df['order_count'], marker='o', color='green')
    plt.title('用户订单趋势', fontsize=18, fontproperties=font_prop)
    plt.xlabel('月份', fontsize=14, fontproperties=font_prop)
    plt.ylabel('订单量', fontsize=14, fontproperties=font_prop)
    plt.xticks(rotation=45, fontsize=12, fontproperties=font_prop)
    plt.yticks(fontsize=12, fontproperties=font_prop)
    plt.grid()
    plt.tight_layout()
    plt.show()

# 用户消费分布
def top_spenders_visual():
    conn = sqlite3.connect('database/users.db')
    query = """
    SELECT user_id, SUM(price * quantity) AS total_spent
    FROM user_orders
    GROUP BY user_id
    ORDER BY total_spent DESC
    LIMIT 10;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    plt.figure(figsize=(10, 6))
    plt.bar(df['user_id'], df['total_spent'], color='purple', alpha=0.7)
    plt.title('用户总消费金额（前 10)', fontsize=18, fontproperties=font_prop)
    plt.xlabel('用户 ID', fontsize=14, fontproperties=font_prop)
    plt.ylabel('总消费金额', fontsize=14, fontproperties=font_prop)
    plt.xticks(rotation=45, fontsize=12, fontproperties=font_prop)
    plt.yticks(fontsize=12, fontproperties=font_prop)
    plt.tight_layout()
    plt.show()
