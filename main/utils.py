import os
import re
import sqlite3

STOPWORDS = set([
        'i', 'my', 'you', 'we', 'me', 'this', 'that', 'there', 'here', 'where', 'when', 'how', 'why', 'all', 'any', 'some', 'much', 'each',
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'are', 'is', 'was', 'were',
        'and', 'or', 'but', 'if', 'then', 'else', 'do', 'does', 'did', 'done', 'to', 'from', 'in', 'on', 'at', 'by', 'for', 'with', 
        'as', 'be', 'by', 'up', 'down', 'out', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'where', 
        'why', 'how', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
        'day', 'today', 'yesterday', 'last', 'month', 'week', 'year', 'next', 'first', 'second', 'daily', 'monthly', 'weekly', 'yearly',
        'rupees', 'dollars', 'amount', 'transaction', 'transactions', 'spent', 'by',
        'spend', 'pay', 'paid', 'show', 'summarize', 'describe', 'please', 'can', 'could', 'will', 'would', 'shall'
    ])

def remove_stopwords(text):
    cleaned = re.sub(r'[^a-z\s]', '', text.lower())
    words = cleaned.split()
    return ' '.join([word for word in words if word not in STOPWORDS])

def clean_text(text):
    cleaned = text.lower()
    return re.sub(r'[^a-z\s]', '', cleaned)


def is_valid_client_id(client_id: int, db_name: str = "data/transactions.db"):
    try:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        db_path = os.path.join(root_dir, db_name)

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT EXISTS(SELECT 1 FROM transactions WHERE clnt_id = ? LIMIT 1)", (client_id,))
        exists = cur.fetchone()[0]
        conn.close()

        if exists:
            return True
        else:
            return False
    except Exception as e:
        return False
