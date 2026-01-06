"""
core/data_feed.py
==================
VNStock Data Feed Wrapper (VN100 Edition)

Uses vnstock3 API: Vnstock().stock().quote.history()
Supports VN100 universe (~100 liquid HOSE stocks)
"""

from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

try:
    from vnstock import Vnstock
    VNSTOCK_AVAILABLE = True
except ImportError:
    VNSTOCK_AVAILABLE = False
    print("[ERROR] vnstock not installed. Run: pip install vnstock")
    Vnstock = None


class VnStockClient:
    """
    VNStock Data Client (VN100 Edition).
    
    Provides clean OHLCV data with standardized column names.
    Supports VN100 universe of liquid Vietnamese stocks.
    """
    
    def get_stock_history(self, symbol: str, days: int = 730) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for any HOSE/HNX stock.
        
        Args:
            symbol: Stock ticker (e.g., 'VNM', 'FPT', 'VIC')
            days: Number of days of history to fetch (default: 730 = 2 years)
        
        Returns:
            DataFrame with standardized columns:
            - Open, High, Low, Close, Volume
            - Sorted by Date ascending (oldest first)
            
            Returns empty DataFrame on error.
        """
        if not VNSTOCK_AVAILABLE:
            return pd.DataFrame()
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Fetch using vnstock3 API
            stock = Vnstock().stock(symbol=symbol, source='VCI')
            df = stock.quote.history(
                start=start_str,
                end=end_str,
                interval='1D'
            )
            
            # Check if empty
            if df is None or df.empty:
                return pd.DataFrame()
            
            # ===== DATA CLEANING =====
            
            # Column mapping (vnstock3 uses lowercase)
            column_mapping = {
                'time': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                return pd.DataFrame()
            
            # Drop rows with NaN in OHLC
            df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
            
            # CRITICAL: Sort by Date ascending so iloc[-1] is the LATEST
            if 'Date' in df.columns:
                df = df.sort_values(by='Date', ascending=True)
            
            # Reset index
            df = df.reset_index(drop=True)
            
            return df
            
        except Exception as e:
            return pd.DataFrame()
    
    # Alias for backward compatibility
    def get_vn30_history(self, symbol: str, days: int = 730) -> pd.DataFrame:
        """Backward compatible alias for get_stock_history."""
        return self.get_stock_history(symbol, days)
    
    def get_vn100_tickers(self) -> list:
        """
        Get list of VN100 constituents and liquid HOSE stocks.
        
        Returns:
            List of ~100 ticker symbols for Vietnam's most liquid stocks
        """
        # VN30 Core (30 stocks)
        vn30 = [
            'ACB', 'BCM', 'BID', 'BVH', 'CTG',
            'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
            'MBB', 'MSN', 'MWG', 'PLX', 'POW',
            'SAB', 'SHB', 'SSB', 'SSI', 'STB',
            'TCB', 'TPB', 'VCB', 'VHM', 'VIB',
            'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
        ]
        
        # VN Midcap & Large Liquid Stocks (70+ stocks)
        midcap_liquid = [
            # Real Estate
            'DIG', 'DXG', 'KDH', 'NLG', 'PDR', 'KBC', 'DXS', 'NVL', 'CEO', 'HDG',
            'IJC', 'SCR', 'TDH', 'HAR', 'VRC', 'NHA', 'LDG', 'NBB', 'TIP', 'IDC',
            # Finance & Securities
            'VND', 'HCM', 'VCI', 'VIX', 'FTS', 'BSI', 'CTS', 'AGR', 'SHS', 'TVS',
            'APG', 'TCI', 'ART', 'EVF', 'ORS', 'DSC', 'BVS', 'PSI', 'MBS',
            # Industrial / Construction
            'GEX', 'PC1', 'REE', 'CTD', 'FCN', 'HBC', 'HHV', 'LCG', 'VCG', 'CII',
            'HT1', 'DGC', 'DCM', 'DPM', 'LAS', 'CSV', 'PVD', 'PVT', 'GIL', 'NT2',
            # Retail / Consumer
            'FRT', 'PNJ', 'DGW', 'MWG', 'VGC', 'PAN', 'HAG', 'HNG', 'ASM', 'AMV',
            # Technology / Telco
            'CMG', 'ELC', 'ITD', 'SAM', 'VGI', 'ONE', 'VTP',
            # Food / Agriculture
            'VHC', 'ANV', 'IDI', 'ABT', 'HSL', 'LSS', 'HAP', 'BBC',
            # Logistics / Transport
            'GMD', 'VOS', 'DVP', 'PHP', 'TMS', 'HAH', 'VSC'
        ]
        
        # Combine and deduplicate
        all_tickers = list(dict.fromkeys(vn30 + midcap_liquid))
        
        return all_tickers
    
    # Backward compatibility
    def get_vn30_tickers(self) -> list:
        """Get VN30 subset only (backward compatibility)."""
        return [
            'ACB', 'BCM', 'BID', 'BVH', 'CTG',
            'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
            'MBB', 'MSN', 'MWG', 'PLX', 'POW',
            'SAB', 'SHB', 'SSB', 'SSI', 'STB',
            'TCB', 'TPB', 'VCB', 'VHM', 'VIB',
            'VIC', 'VJC', 'VNM', 'VPB', 'VRE'
        ]
