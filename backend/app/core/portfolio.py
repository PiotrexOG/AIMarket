from collections import defaultdict


class Portfolio:
    def __init__(self, cash):
        self.cash = cash
        self.shares = defaultdict(int)
        self.history = []

    def buy(self, ticker, amount, price):
        cost = amount * price
        if cost <= self.cash:
            self.cash -= cost
            self.shares[ticker] += amount
            return True
        return False

    def sell(self, ticker, amount, price):
        if amount <= self.shares.get(ticker, 0):
            self.cash += amount * price
            self.shares[ticker] -= amount
            return True
        return False

    def evaluate(self, date_time):
        self.history.append({
            'datetime': date_time,
            'cash': self.cash,
            'shares': self.shares.copy()
        })

    def get_portfolio_state(self, target_datetime):
        # Filtrujemy tylko wpisy historyczne przed lub równo z target_datetime
        valid_entries = [
            entry for entry in self.history
            if entry['datetime'] <= target_datetime
        ]

        if not valid_entries:
            return None  # lub domyślne wartości, jeśli historia jest pusta

        # Znajdujemy wpis z najbliższą datą (największą mniejszą lub równą target_datetime)
        closest_entry = max(valid_entries, key=lambda x: x['datetime'])

        return {
            'datetime': closest_entry['datetime'],
            'cash': closest_entry['cash'],
            'shares': closest_entry['shares'].copy()  # Zwracamy kopię, aby uniknąć modyfikacji oryginału
        }


