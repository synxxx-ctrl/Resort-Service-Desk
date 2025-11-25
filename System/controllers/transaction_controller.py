from db import query

class TransactionController:
    def __init__(self, app):
        """
        Initialize the TransactionController.
        :param app: Reference to the main application class.
        """
        self.app = app

    def show_transactions(self):
        rows = query("""
            SELECT p.payment_id, p.payment_method, p.amount, p.payment_date, c.full_name
            FROM payment p
            JOIN customer c ON c.customer_id = p.customer_id
            ORDER BY p.payment_date DESC
        """, fetchall=True)
        
        if not rows:
            self.app.window_manager.open_text_window("Transactions", "No transactions available.")
            return

        txt = "\n".join([
            f"{r['payment_id']}: {r['full_name']} — {r['payment_method']} — ₱{r['amount']:.2f} — {r['payment_date']}"
            for r in rows
        ])
        
        self.app.window_manager.open_text_window("Transactions", txt)