"""
core/titan_math.py
==================
TITAN v9.1 Math Logic - EXACT PORT

This module contains the core mathematical calculations for the TITAN trading system.
All functions are designed to exactly match the original v9.1 implementation.

CRITICAL: The stateful trend count logic uses an iterative loop to maintain
state across bars, which cannot be vectorized without changing behavior.
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd


class TitanMath:
    """
    TITAN v9.1 Mathematical Engine.
    
    Contains all indicator calculations and backtesting logic
    used by the TITAN trading system.
    
    Methods:
        rma: Wilder's Relative Moving Average
        calculate_di: Directional Indicator (+DI/-DI)
        calculate_trend_count: Stateful impulse counter
        check_alpha_validity: Vectorized backtest for alpha validation
    """
    
    @staticmethod
    def rma(series: pd.Series, length: int) -> pd.Series:
        """
        Wilder's Relative Moving Average (RMA).
        
        This is equivalent to an EMA with alpha = 1/length.
        Used for smoothing True Range and Directional Movement.
        
        Args:
            series: Input price series
            length: Smoothing period
        
        Returns:
            Smoothed series using Wilder's method
        
        Formula:
            RMA = EWM(alpha=1/length, adjust=False)
        """
        return series.ewm(alpha=1.0/length, adjust=False).mean()
    
    @staticmethod
    def calculate_di(df: pd.DataFrame, length: int = 9) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Directional Indicators (+DI and -DI).
        
        Based on Welles Wilder's ADX system, these indicators measure
        the strength of upward vs downward price movement.
        
        Args:
            df: DataFrame with 'High', 'Low', 'Close' columns
            length: Smoothing period (default: 9)
        
        Returns:
            Tuple of (plus_di, minus_di) as percentage values (0-100)
        
        Calculation:
            1. True Range = max(H-L, |H-Prev_C|, |L-Prev_C|)
            2. +DM = H - Prev_H if (H-Prev_H > Prev_L-L and H-Prev_H > 0) else 0
            3. -DM = Prev_L - L if (Prev_L-L > H-Prev_H and Prev_L-L > 0) else 0
            4. +DI = RMA(+DM) / RMA(TR) * 100
            5. -DI = RMA(-DM) / RMA(TR) * 100
        """
        high = df['High']
        low = df['Low']
        close = df['Close']
        prev_close = close.shift(1)
        
        # True Range: Maximum of three ranges
        tr = pd.concat([
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        ], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        # +DM: Upward movement > downward movement AND positive
        plus_dm = pd.Series(
            np.where((up_move > down_move) & (up_move > 0), up_move, 0),
            index=high.index
        )
        
        # -DM: Downward movement > upward movement AND positive
        minus_dm = pd.Series(
            np.where((down_move > up_move) & (down_move > 0), down_move, 0),
            index=high.index
        )
        
        # Smooth using Wilder's RMA
        tr_smooth = TitanMath.rma(tr, length)
        plus_smooth = TitanMath.rma(plus_dm, length)
        minus_smooth = TitanMath.rma(minus_dm, length)
        
        # Calculate DI as percentage
        plus_di = (plus_smooth / tr_smooth.replace(0, np.nan)) * 100
        minus_di = (minus_smooth / tr_smooth.replace(0, np.nan)) * 100
        
        return plus_di.fillna(0), minus_di.fillna(0)
    
    @staticmethod
    def calculate_trend_count(plus_di: pd.Series, minus_di: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stateful Trend Count (Impulse Detection).
        
        CRITICAL: This function uses an ITERATIVE LOOP to maintain state.
        DO NOT attempt to vectorize - the stateful logic requires sequential processing.
        
        The count tracks consecutive bars where:
        - Bullish: +DI is rising AND dominant
        - Bearish: -DI is rising AND dominant
        
        Args:
            plus_di: Positive Directional Indicator series
            minus_di: Negative Directional Indicator series
        
        Returns:
            Tuple of (positive_count, negative_count) as Series
        
        State Logic:
            For each bar i (starting from 1):
            - IF (+DI[i] > +DI[i-1]) AND (+DI[i] > -DI[i]):
                pos_count[i] = pos_count[i-1] + 1
                neg_count[i] = 0
            - ELIF (-DI[i] > -DI[i-1]) AND (-DI[i] > +DI[i]):
                neg_count[i] = neg_count[i-1] + 1
                pos_count[i] = 0
            - ELSE:
                pos_count[i] = pos_count[i-1]  # Hold previous
                neg_count[i] = neg_count[i-1]  # Hold previous
        """
        n = len(plus_di)
        positive_count = np.zeros(n)
        negative_count = np.zeros(n)
        
        # STATEFUL LOOP - Must be sequential
        for i in range(1, n):
            prev_plus = plus_di.iloc[i-1]
            prev_minus = minus_di.iloc[i-1]
            curr_plus = plus_di.iloc[i]
            curr_minus = minus_di.iloc[i]
            
            # Bullish Impulse: +DI rising AND dominant
            if curr_plus > prev_plus and curr_plus > curr_minus:
                positive_count[i] = positive_count[i-1] + 1
                negative_count[i] = 0
            # Bearish Impulse: -DI rising AND dominant
            elif curr_minus > prev_minus and curr_minus > curr_plus:
                negative_count[i] = negative_count[i-1] + 1
                positive_count[i] = 0
            # No impulse: Hold previous counts
            else:
                positive_count[i] = positive_count[i-1]
                negative_count[i] = negative_count[i-1]
        
        return (
            pd.Series(positive_count, index=plus_di.index),
            pd.Series(negative_count, index=minus_di.index)
        )
    
    @staticmethod
    def check_alpha_validity(df: pd.DataFrame, di_length: int = 9) -> Dict:
        """
        Vectorized Backtest to Validate Alpha.
        
        Runs a simulation of the Impulse strategy on historical data
        to determine if the asset has positive alpha.
        
        Args:
            df: DataFrame with 'High', 'Low', 'Close' columns
            di_length: DI smoothing period (default: 9)
        
        Returns:
            Dictionary containing:
            - is_valid: bool - True if strategy beats buy & hold
            - alpha: float - Strategy return minus buy & hold
            - algo_ret: float - Strategy cumulative return %
            - buy_hold: float - Buy & hold return %
            - total_trades: int - Number of round-trip trades
        
        Signal Logic:
            - ENTRY: pos_count transitions from 0 to 1 (impulse ignition)
            - EXIT: neg_count transitions from 0 to 1 (reversal signal)
        
        Validation Criteria (Dual Guardrail):
            1. algo_return > 0 (Strategy must be profitable)
            2. algo_return > buy_hold (Strategy must beat market)
        """
        if len(df) < 50:
            return {
                'is_valid': False,
                'alpha': 0.0,
                'algo_ret': 0.0,
                'buy_hold': 0.0,
                'total_trades': 0,
                'reason': 'Insufficient data'
            }
        
        # Calculate indicators
        plus_di, minus_di = TitanMath.calculate_di(df, di_length)
        pos_count, neg_count = TitanMath.calculate_trend_count(plus_di, minus_di)
        
        # Vectorized signal detection
        # Entry: pos_count goes from 0 to 1
        entry_signal = (pos_count == 1) & (pos_count.shift(1) == 0)
        # Exit: neg_count goes from 0 to 1
        exit_signal = (neg_count == 1) & (neg_count.shift(1) == 0)
        
        # Simulate trades
        in_position = False
        entry_price = 0.0
        total_return = 1.0
        trades = 0
        
        for i in range(1, len(df)):
            price = df['Close'].iloc[i]
            
            # Check for entry
            if not in_position and entry_signal.iloc[i]:
                in_position = True
                entry_price = price
            
            # Check for exit
            elif in_position and exit_signal.iloc[i]:
                pnl = (price - entry_price) / entry_price
                total_return *= (1 + pnl)
                trades += 1
                in_position = False
        
        # Close any open position at end
        if in_position:
            price = df['Close'].iloc[-1]
            pnl = (price - entry_price) / entry_price
            total_return *= (1 + pnl)
            trades += 1
        
        # Calculate returns
        algo_return_pct = (total_return - 1) * 100
        buy_hold_pct = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
        alpha = algo_return_pct - buy_hold_pct
        
        # Dual Guardrail Validation
        guardrail_1 = algo_return_pct > 0  # Must be profitable
        guardrail_2 = algo_return_pct > buy_hold_pct  # Must beat market
        is_valid = guardrail_1 and guardrail_2
        
        return {
            'is_valid': is_valid,
            'alpha': alpha,
            'algo_ret': algo_return_pct,
            'buy_hold': buy_hold_pct,
            'total_trades': trades
        }
