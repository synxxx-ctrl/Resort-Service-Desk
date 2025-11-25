from db import query

class TransactionController:
    def __init__(self, app):
        self.app = app

    def show_transactions(self):
        # Fetch cashier_name from billing
        rows = query("""
            SELECT p.payment_id, p.payment_method, p.amount, p.payment_date, c.full_name, b.cashier_name
            FROM payment p
            JOIN customer c ON c.customer_id = p.customer_id
            JOIN billing b ON b.billing_id = p.billing_id
            ORDER BY p.payment_date DESC
        """, fetchall=True)
        
        if not rows:
            self.app.window_manager.open_text_window("Transactions", "No transactions available.")
            return

        lines = []
        for r in rows:
            cashier = r['cashier_name'] if r['cashier_name'] else "Admin Cashier"
            line = f"ID: {r['payment_id']} | Date: {r['payment_date']}\n   Customer: {r['full_name']}\n   Amount: ₱{r['amount']:.2f} ({r['payment_method']})\n   Cashier: {cashier}\n" + ("-"*40)
            lines.append(line)

        txt = "\n".join(lines)
        self.app.window_manager.open_text_window("Transactions", txt)