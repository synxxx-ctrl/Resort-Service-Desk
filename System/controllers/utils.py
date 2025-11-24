import re, random
from db import query

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(email):
    return bool(EMAIL_RE.match(email.strip()))

def is_valid_phone(phone):
    p = ''.join(ch for ch in phone if ch.isdigit())
    return p.isdigit() and 7 <= len(p) <= 13

def generate_unique_customer_code():
    for _ in range(1000):
        code = "{:04d}".format(random.randint(0, 9999))
        existing = query("SELECT customer_id FROM customer WHERE username = ?", (code,), fetchone=True)
        if not existing:
            return code
    raise RuntimeError("Unable to generate unique code - try again")
