import sqlite3
from contextlib import closing
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "resort.db")

def get_conn():
    # ADDED timeout=10 to wait for locks to clear instead of failing immediately
    conn = sqlite3.connect(DB_PATH, timeout=10, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def query(sql, params=(), fetchone=False, fetchall=False):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)

        if fetchone:
            return cur.fetchone()

        if fetchall:
            return cur.fetchall()
        
        return cur.fetchall()

def execute(sql, params=()):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid