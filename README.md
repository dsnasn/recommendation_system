# 🍴 Food Recommendation System | A Smart Takeout Recommendation Platform

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **✨ Discover, Recommend, and Analyze Takeout Options with Intelligent Recommendations!**   
> A complete web-based platform showcasing data science capabilities, personalized recommendations, and insightful visualizations.

---

### 🌟 Key Features

- **Personalized Recommendations**: Dynamic food suggestions adapting to user orders, ratings, and searches.  
- **Cold Start Solution**: Global recommendations showcasing trending dishes for new users.  
- **Enhanced Search**: Supports fuzzy matching, typo correction, and synonym expansion for precise results.  
- **Actionable Insights**: Interactive visualizations for order trends, popular dishes, and user spending.  
- **Admin Dashboard**: A centralized hub for managing analytics and uncovering business insights.  

---

## 🚀 Quick Start Guide

### Step 1: Clone the repository
```bash
git clone https://github.com/dsnasn/recommendation_system.git
cd recommendation_system
```
### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```
### Step 3: Run the application
```bash
python app.py
```
### Step 4: Open in your browser
Visit http://127.0.0.1:5000 to start exploring.

---

## 🎥 Key Demonstrations

Explore the core functionalities of the system through these dynamic visualizations:

---

### 🧠 **Dynamic Personalized Recommendations**
- Recommendations dynamically adapt to **user search behavior** in real time.  
- Observe how repeated searches for "pizza" gradually shift recommendations from spicy dishes to pizza-related options, with **increasing recommendation scores** as search frequency rises.

![Personalized Recommendations](Visualization_Results/Personalized-Recommendations.gif)

---

### 🔍 **Intelligent Search Optimization**
- Supports **fuzzy matching** for typos and **synonym expansion**.
- Dynamically loads **search history** for quick redirection to relevant results.

![Search Function](Visualization_Results/search-function.gif)

---

### 📊 **Admin Analytics Dashboard**
- Visualize **order trends**, **top dishes**, and **high-spending users**.
- Gain actionable insights with interactive charts powered by Plotly.

![Admin Dashboard](Visualization_Results/dashboard.gif)

---

### ❄️ **Global Recommendations for Cold-Start Users**
- Handles the **cold-start problem** by displaying globally popular dishes for new users.
- Seamlessly transitions to **personalized recommendations** as user data grows.

![Cold Start Recommendations](Visualization_Results/cold-start.gif)

---

## 📊 **Outcomes and Impact**

### 🔍 **Search Efficiency**
| Metric               | Before Optimization | After Optimization |
|----------------------|---------------------|--------------------|
| Query Accuracy (%)   | 70%                | **85%**            |
| Avg Time to Result (sec) | 10 sec           | **5 sec**          |

Enhanced query accuracy and reduced response time through advanced search optimizations like fuzzy matching and synonym expansion.

---

### 📈 **Increased Engagement**
| Metric               | Before Recommendations | After Recommendations |
|----------------------|-------------------------|------------------------|
| User Retention (%)   | 65%                    | **75%**                |
| Returning Users      | 6,500                  | **7,500**              |

Personalized recommendations significantly improved user retention and increased repeat interactions.

---

### 🍴 **Top Dishes**
| Rank | Dish Name        | Weighted Score |
|------|------------------|----------------|
| 1    | Spicy Hot Pot    | 92.5           |
| 2    | Sichuan Noodles  | 89.3           |
| 3    | Fried Rice       | 86.7           |
| 4    | Grilled Fish     | 83.4           |
| 5    | Dumplings        | 81.2           |

The most popular dishes were identified using a weighted analysis of sales volume, ratings, and reviews, providing actionable insights for menu optimization.

---

**Note**: Metrics are based on simulated user data to demonstrate potential system capabilities in a realistic business context.

---

## 📂 Project Structure

```plaintext
.
├── app.py                 # Main application logic
├── visualizations.py      # Scripts for data visualizations
├── requirements.txt       # Python dependencies
├── README.md              # Project description
├── SimHei.ttf             # Font file for visualizations
├── database/              # SQLite database files
│   ├── meituan_data.db
│   ├── users.db
├── models/                # Recommendation algorithms
│   ├── recommend.py
├── static/                # Static assets
│   ├── css/               # Stylesheets
│   ├── images/            # Image assets
│   ├── js/                # JavaScript files
├── templates/             # HTML templates for the frontend

```
---
## 🛠️ Technology Stack

- **Languages**: Python
- **Framework**: Flask
- **Database**: SQLite
- **Libraries**: Pandas, Matplotlib, FuzzyWuzzy (RapidFuzz)
- **Algorithms**: Collaborative filtering, text similarity scoring

---

