import pandas as pd
import numpy as np
from src.strategy.base import BaseStrategy
from src.utils.logger import log_trade


def _prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names and ensure datetime index."""
    df = df.copy()
    
    # Map lowercase column names to canonical names
    col_map = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
    }
    for src, dst in col_map.items():
        if src in df.columns:
            df[dst] = df[src]
    
    # Ensure timestamp column
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    elif "Date" in df.columns:
        df["timestamp"] = pd.to_datetime(df["Date"])
    
    # Ensure all required columns exist
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Sort by timestamp and reset index
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df[required]


class BacktestSession:
    """Manual backtesting engine that walks through historical data bar-by-bar."""
    
    def __init__(self, data, initial_cash=100000, commission=0.002):
        self.data = data
        self.initial_cash = initial_cash
        self.commission = commission
        
        # Account state
        self.cash = initial_cash
        self.btc = 0.0
        self.trades = []
        
        # Position tracking
        self.position = None  # None, "LONG", or "SHORT"
        self.entry_price = None
        self.entry_bar = None
        self.entry_quantity = None
        
        # Strategy
        self.strategy = BaseStrategy()
        
    def run(self):
        """Execute backtest by iterating through all bars."""
        total_bars = len(self.data)
        
        for bar_idx in range(total_bars):
            # Get data up to current bar (for strategy calculation)
            current_df = self.data.iloc[:bar_idx + 1].copy()
            current_bar = self.data.iloc[bar_idx]
            current_price = float(current_bar['close'])
            
            # Check exit first if in position
            if self.position:
                exit_signal = self.strategy.generate_exit_signal(current_df)
                
                if (self.position == "LONG" and exit_signal == "CLOSE_LONG") or \
                   (self.position == "SHORT" and exit_signal == "CLOSE_SHORT"):
                    self._execute_exit(bar_idx, current_price, current_bar)
                    continue
            
            # Check entry if no position
            if not self.position:
                entry_signal = self.strategy.generate_entry_signal(current_df)
                
                if entry_signal == "BUY":
                    self._execute_entry(bar_idx, current_price, current_bar, "LONG")
                elif entry_signal == "SELL":
                    self._execute_entry(bar_idx, current_price, current_bar, "SHORT")
    
    def _execute_entry(self, bar_idx, price, bar_data, position_type):
        """Execute entry order."""
        if position_type == "LONG":
            # Use 1% of cash for each trade
            cash_to_use = self.cash * 0.01
            commission_cost = cash_to_use * self.commission
            
            qty = (cash_to_use - commission_cost) / price
            if qty > 0:
                self.btc += qty
                self.cash -= (qty * price + commission_cost)
                
                self.position = "LONG"
                self.entry_price = price
                self.entry_bar = bar_idx
                self.entry_quantity = qty
        
        elif position_type == "SHORT":
            # For demo, track shorts (would need margin in real trading)
            cash_to_use = self.cash * 0.01
            commission_cost = cash_to_use * self.commission
            
            qty = (cash_to_use - commission_cost) / price
            if qty > 0:
                self.btc -= qty
                self.cash -= commission_cost
                
                self.position = "SHORT"
                self.entry_price = price
                self.entry_bar = bar_idx
                self.entry_quantity = qty
    
    def _execute_exit(self, bar_idx, price, bar_data):
        """Execute exit order and record trade."""
        if self.position == "LONG":
            exit_value = self.entry_quantity * price
            commission_cost = exit_value * self.commission
            profit = exit_value - commission_cost - (self.entry_quantity * self.entry_price)
            
            self.btc -= self.entry_quantity
            self.cash += (exit_value - commission_cost)
            
        elif self.position == "SHORT":
            # Buyback the short
            buyback_cost = self.entry_quantity * price
            commission_cost = buyback_cost * self.commission
            profit = (self.entry_quantity * self.entry_price) - buyback_cost - commission_cost
            
            self.btc += self.entry_quantity
            self.cash -= (buyback_cost + commission_cost)
        
        # Record trade
        duration = bar_idx - self.entry_bar
        trade = {
            'position': self.position,
            'entry_bar': self.entry_bar,
            'exit_bar': bar_idx,
            'entry_price': self.entry_price,
            'exit_price': price,
            'quantity': self.entry_quantity,
            'pnl': profit,
            'duration_bars': duration,
            'entry_time': str(self.data.iloc[self.entry_bar]['timestamp']),
            'exit_time': str(bar_data['timestamp'])
        }
        self.trades.append(trade)
        
        # Log to CSV
        log_trade([
            self.data.iloc[self.entry_bar]['timestamp'],
            self.entry_quantity,
            self.entry_bar,
            self.entry_price,
            bar_idx,
            price,
            profit,
            duration
        ], "data/backtest_trades.csv")
        
        # Reset position
        self.position = None
        self.entry_price = None
        self.entry_bar = None
        self.entry_quantity = None
    
    def get_stats(self):
        """Calculate and return backtest statistics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'max_drawdown': 0.0,
                'final_balance': self.cash,
                'total_return': 0.0,
                'return_pct': 0.0
            }
        
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t['pnl'] > 0)
        losing_trades = sum(1 for t in self.trades if t['pnl'] <= 0)
        total_pnl = sum(t['pnl'] for t in self.trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Calculate max drawdown (simplified)
        cumulative = 0
        peak = 0
        max_dd = 0
        for trade in self.trades:
            cumulative += trade['pnl']
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        final_balance = self.cash + (self.btc * self.data.iloc[-1]['close'])
        total_return = final_balance - self.initial_cash
        return_pct = (total_return / self.initial_cash * 100) if self.initial_cash > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'max_drawdown': max_dd,
            'final_balance': final_balance,
            'total_return': total_return,
            'return_pct': return_pct,
            'trades': self.trades
        }


def run_backtest(data: pd.DataFrame):
    """Run backtest on historical data."""
    df = _prepare_data(data)
    session = BacktestSession(df, initial_cash=100000, commission=0.002)
    session.run()
    return session.get_stats()
