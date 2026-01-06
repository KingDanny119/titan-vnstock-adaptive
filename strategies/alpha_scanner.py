"""
strategies/alpha_scanner.py
============================
TITAN Alpha Scanner Orchestrator (VN100 v3.0)

Features:
- VN100 Universe (~100 liquid stocks)
- Extended DI Optimization (1-40)
- Deep Dive Inspection Mode
"""

from typing import Dict, Optional, List
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.titan_math import TitanMath
from core.data_feed import VnStockClient


# Extended Optimization Range (1-40)
DI_LENGTH_MIN = 1
DI_LENGTH_MAX = 40


class AlphaScanner:
    """
    TITAN Alpha Scanner (VN100 v3.0).
    
    Features:
    - Scans ~100 liquid Vietnamese stocks
    - Adaptive DI optimization (1-40)
    - Deep inspection mode for parameter stability
    """
    
    def __init__(self):
        """Initialize the Alpha Scanner with data client."""
        self.client = VnStockClient()
    
    def analyze_symbol(self, symbol: str, days: int = 730) -> Optional[Dict]:
        """
        Analyze a single symbol with extended parameter optimization.
        
        Iterates DI Lengths from 1 to 40 and selects the configuration
        that produces the HIGHEST historical Alpha.
        
        Args:
            symbol: Stock ticker (e.g., 'FPT', 'VNM')
            days: Days of history for alpha calculation (default: 730)
        
        Returns:
            Dictionary with OPTIMAL configuration or None on failure.
        """
        try:
            # Fetch data
            df = self.client.get_stock_history(symbol, days=days)
            
            if df.empty or len(df) < 50:
                return None
            
            # Extended grid search (1-40)
            best_result = None
            best_alpha = -float('inf')
            best_length = 14  # Default
            
            for length in range(DI_LENGTH_MIN, DI_LENGTH_MAX + 1):
                try:
                    alpha_stats = TitanMath.check_alpha_validity(df, di_length=length)
                    current_alpha = alpha_stats.get('alpha', -float('inf'))
                    
                    if current_alpha > best_alpha:
                        best_alpha = current_alpha
                        best_length = length
                        best_result = alpha_stats
                        
                except Exception:
                    continue
            
            if best_result is None:
                return None
            
            # Signal generation with optimal length
            plus_di, minus_di = TitanMath.calculate_di(df, length=best_length)
            pos_count, neg_count = TitanMath.calculate_trend_count(plus_di, minus_di)
            
            current_pos = pos_count.iloc[-1]
            previous_pos = pos_count.iloc[-2] if len(pos_count) > 1 else 0
            is_buy_signal = (current_pos == 1) and (previous_pos == 0)
            
            strength_val = abs(plus_di.iloc[-1] - minus_di.iloc[-1])
            if strength_val > 20:
                trend_strength = "Strong"
            elif strength_val > 10:
                trend_strength = "Mod"
            else:
                trend_strength = "Weak"
            
            close_price = float(df['Close'].iloc[-1])
            
            return {
                'symbol': symbol,
                'close_price': close_price,
                'is_valid': best_result['is_valid'],
                'alpha': best_result['alpha'],
                'algo_ret': best_result['algo_ret'],
                'buy_hold': best_result['buy_hold'],
                'total_trades': best_result['total_trades'],
                'is_buy_signal': is_buy_signal,
                'trend_strength': trend_strength,
                'plus_di': float(plus_di.iloc[-1]),
                'minus_di': float(minus_di.iloc[-1]),
                'optimal_length': best_length,
                'scan_range': f'{DI_LENGTH_MIN}-{DI_LENGTH_MAX}'
            }
            
        except Exception as e:
            return None
    
    def scan_vn100(self, days: int = 730) -> List[Dict]:
        """
        Scan all VN100 stocks with adaptive optimization.
        
        Returns:
            List of analysis results, sorted by alpha (descending)
        """
        tickers = self.client.get_vn100_tickers()
        
        if not tickers:
            print("[ERROR] No tickers found.")
            return []
        
        results = []
        
        for symbol in tickers:
            result = self.analyze_symbol(symbol, days)
            if result:
                results.append(result)
        
        results.sort(key=lambda x: x['alpha'], reverse=True)
        
        return results
    
    # Backward compatibility
    def scan_vn30(self, days: int = 730) -> List[Dict]:
        """Scan VN30 subset only."""
        tickers = self.client.get_vn30_tickers()
        results = []
        for symbol in tickers:
            result = self.analyze_symbol(symbol, days)
            if result:
                results.append(result)
        results.sort(key=lambda x: x['alpha'], reverse=True)
        return results
    
    def get_opportunities(self, days: int = 730) -> List[Dict]:
        """Get tradeable opportunities (positive alpha only)."""
        all_results = self.scan_vn100(days)
        return [r for r in all_results if r['is_valid']]
    
    def get_signals(self, days: int = 730) -> List[Dict]:
        """Get current buy signals (impulse entry triggered)."""
        all_results = self.scan_vn100(days)
        return [r for r in all_results if r['is_buy_signal'] and r['is_valid']]
    
    def inspect_ticker_stability(self, symbol: str, days: int = 730) -> List[Dict]:
        """
        Deep inspection of parameter stability for a single stock.
        
        Tests ALL DI lengths from 1 to 40 and returns detailed stats.
        
        Args:
            symbol: Stock ticker
            days: Days of history
        
        Returns:
            List of dicts with length, alpha, is_valid, etc.
            Sorted by length ascending.
        """
        try:
            df = self.client.get_stock_history(symbol, days=days)
            
            if df.empty or len(df) < 50:
                print(f"[ERROR] Insufficient data for {symbol}")
                return []
            
            results = []
            
            for length in range(DI_LENGTH_MIN, DI_LENGTH_MAX + 1):
                try:
                    alpha_stats = TitanMath.check_alpha_validity(df, di_length=length)
                    
                    results.append({
                        'length': length,
                        'alpha': alpha_stats.get('alpha', 0),
                        'is_valid': alpha_stats.get('is_valid', False),
                        'algo_ret': alpha_stats.get('algo_ret', 0),
                        'buy_hold': alpha_stats.get('buy_hold', 0),
                        'trades': alpha_stats.get('total_trades', 0)
                    })
                except Exception:
                    continue
            
            results.sort(key=lambda x: x['length'])
            
            return results
            
        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")
            return []
