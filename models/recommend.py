import pandas as pd

class RecommendSystem:
    def __init__(self, conn):
        self.conn = conn
        
    def get_popular_items(self, limit=10):
        """
        获取热门菜品（综合评分、点赞数、评论数量等因素，固定评分阈值为 4.25）
        """
        query = '''
            SELECT 
                menu, 
                AVG(star) AS avg_star, 
                SUM(CASE WHEN star >= 4.25 THEN like_count ELSE 0 END) AS total_likes, 
                COUNT(CASE WHEN star >= 4.25 THEN 1 ELSE NULL END) AS review_count,
                (AVG(star) * 0.5 + SUM(CASE WHEN star >= 4.25 THEN like_count ELSE 0 END) * 0.3 + COUNT(CASE WHEN star >= 4.25 THEN 1 ELSE NULL END) * 0.2) AS score,
                (SELECT avgPrice FROM takeout_products WHERE takeout_products.menu = meituan_reviews.menu) AS avgPrice
            FROM 
                meituan_reviews
            WHERE 
                star >= 4.25  -- 只考虑评分高于或等于 4.25 的评论
            GROUP BY 
                menu
            ORDER BY 
                score DESC
            LIMIT ?;
        '''
        return pd.read_sql_query(query, self.conn, params=[limit])
    
    def get_high_rated_items(self, limit=10):
        """
        获取高评分菜品（只看评分维度）
        """
        query = '''
            SELECT 
                menu, 
                AVG(star) AS avg_star,
                COUNT(*) AS review_count,
                (SELECT avgPrice FROM takeout_products WHERE takeout_products.menu = meituan_reviews.menu) AS avgPrice
            FROM 
                meituan_reviews
            WHERE 
                star >= 4.25  -- 固定评分阈值，只推荐高评分菜品
            GROUP BY 
                menu
            HAVING 
                review_count > 5  -- 确保至少有一定数量的评论
            ORDER BY 
                avg_star DESC  -- 按评分排序
            LIMIT ?;
        '''
        return pd.read_sql_query(query, self.conn, params=[limit])
    
    # （管理员）获取销量数据
    def get_sales_data_query(self):
        """
        获取菜品销量数据的 SQL 查询
        """
        query = '''
            SELECT 
                menu, 
                SUM(quantity) AS total_sales
            FROM 
                user_orders
            GROUP BY 
                menu
            ORDER BY 
                total_sales DESC;
        '''
        return query
     
    def get_similar_items(self, menu, limit=5):
        """获取相似菜品"""
        query = '''
            SELECT menu, avgPrice, star 
            FROM meituan_reviews 
            WHERE menu != ? 
            ORDER BY star DESC 
            LIMIT ?
        '''
        return pd.read_sql_query(query, self.conn, params=[menu, limit])
