"""
ui/terminal.py
==============
Professional Terminal UI for TITAN VNStock Scanner (VN100 v3.0)

Features:
- Colored output using colorama
- Formatted tables with aligned columns
- Visual indicators for signals and alpha status
- Deep Dive ASCII parameter heatmap (1-40 range)
"""

import os
import sys
from typing import List, Dict

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class Fore:
        CYAN = GREEN = RED = YELLOW = WHITE = MAGENTA = ""
        LIGHTBLACK_EX = LIGHTGREEN_EX = LIGHTCYAN_EX = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the scanner header banner."""
    clear_screen()
    
    print()
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}       TITAN QUANT x VNSTOCK: VN100 ADAPTIVE SCANNER v3.0")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
    print()
    print(f"{Fore.WHITE}  Universe: {Fore.YELLOW}VN100 (~100 stocks){Fore.WHITE} | Data: {Fore.YELLOW}2 Years")
    print(f"{Fore.WHITE}  Strategy: {Fore.YELLOW}Impulse Ignition{Fore.WHITE} | DI Range: {Fore.YELLOW}1-40 Optimization")
    print(f"{Fore.WHITE}  Alpha Guardrails: {Fore.GREEN}Active")
    print()
    print(f"{Fore.CYAN}{'-' * 80}")
    print()


def print_results_table(results: List[Dict]):
    """
    Print formatted results table with optimal length column.
    
    Columns: Ticker | Price | Trend | Str | OptLen | Alpha | Valid | Signal
    """
    if not results:
        print(f"{Fore.YELLOW}  No results to display.")
        return
    
    # Table header
    header = (
        f"{'Ticker':<8} {'Price':>10} {'Trend':<8} {'Str':<6} "
        f"{'OptLen':>6} {'Alpha':>10} {'Valid':>6} {'Signal':<10}"
    )
    
    print(f"{Fore.WHITE}{Style.BRIGHT}{header}")
    print(f"{Fore.WHITE}{'-' * 80}")
    
    for r in results:
        ticker = r.get('symbol', 'N/A')
        price = r.get('close_price', 0)
        alpha = r.get('alpha', 0)
        is_valid = r.get('is_valid', False)
        is_buy = r.get('is_buy_signal', False)
        strength = r.get('trend_strength', 'N/A')
        opt_len = r.get('optimal_length', 14)
        plus_di = r.get('plus_di', 0)
        minus_di = r.get('minus_di', 0)
        
        trend = "BULL" if plus_di > minus_di else "BEAR"
        
        if is_buy and is_valid:
            color = f"{Fore.GREEN}{Style.BRIGHT}"
            action = "BUY"
            valid_str = "YES"
        elif is_valid:
            color = f"{Fore.CYAN}"
            action = "WATCH"
            valid_str = "YES"
        else:
            color = f"{Style.DIM}"
            action = "AVOID"
            valid_str = "NO"
        
        if price >= 1000:
            price_str = f"{price/1000:.1f}K"
        else:
            price_str = f"{price:.2f}"
        
        alpha_str = f"{alpha:+.1f}%"
        
        row = (
            f"{ticker:<8} {price_str:>10} {trend:<8} {strength:<6} "
            f"{opt_len:>6} {alpha_str:>10} {valid_str:>6} {action:<10}"
        )
        
        print(f"{color}{row}{Style.RESET_ALL}")
    
    print(f"{Fore.WHITE}{'-' * 80}")


def print_footer(results: List[Dict]):
    """Print scan summary footer."""
    total = len(results)
    valid = sum(1 for r in results if r.get('is_valid', False))
    signals = sum(1 for r in results if r.get('is_buy_signal', False) and r.get('is_valid', False))
    
    print()
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.WHITE}  SCAN COMPLETE")
    print(f"{Fore.WHITE}  Total: {Fore.YELLOW}{total}{Fore.WHITE} stocks | "
          f"Opportunities: {Fore.GREEN}{valid}{Fore.WHITE} | "
          f"Buy Signals: {Fore.GREEN}{Style.BRIGHT}{signals}")
    print(f"{Fore.CYAN}{'=' * 80}")
    print()


def print_progress(symbol: str, current: int, total: int):
    """Print progress indicator (overwrites line)."""
    progress = f"  Scanning: {symbol:<8} [{current}/{total}] (Testing DI 1-40...)"
    print(f"{Fore.YELLOW}{progress}", end='\r', flush=True)


def print_scan_complete():
    """Print completion message after progress."""
    print(f"{Fore.GREEN}  Scan complete!{' ' * 50}")


def print_parameter_heatmap(symbol: str, stability_data: List[Dict]):
    """
    Print deep dive ASCII heatmap showing alpha across DI lengths 1-40.
    
    Args:
        symbol: Stock ticker
        stability_data: List of dicts with 'length', 'alpha', 'is_valid', 'trades'
    """
    if not stability_data:
        print(f"{Fore.YELLOW}  No data to display for {symbol}.")
        return
    
    # Find best and worst
    best = max(stability_data, key=lambda x: x['alpha'])
    worst = min(stability_data, key=lambda x: x['alpha'])
    best_length = best['length']
    max_alpha = max(r['alpha'] for r in stability_data)
    min_alpha = min(r['alpha'] for r in stability_data)
    max_abs = max(abs(max_alpha), abs(min_alpha), 1)
    
    # Header
    print()
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 75}")
    print(f"{Fore.CYAN}{Style.BRIGHT}  DEEP DIVE INSPECTION: {symbol}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'=' * 75}")
    print()
    print(f"{Fore.WHITE}  DI Length Range: {Fore.YELLOW}1-40")
    print(f"{Fore.WHITE}  Best: {Fore.GREEN}DI={best_length}{Fore.WHITE} (Alpha: {Fore.GREEN}{best['alpha']:+.1f}%{Fore.WHITE})")
    print(f"{Fore.WHITE}  Worst: {Fore.RED}DI={worst['length']}{Fore.WHITE} (Alpha: {Fore.RED}{worst['alpha']:+.1f}%{Fore.WHITE})")
    print()
    
    # Table header
    print(f"{Fore.WHITE}{Style.BRIGHT}  {'Len':<4} {'Alpha':<10} {'Trades':<7} {'Chart':<40}")
    print(f"{Fore.WHITE}  {'-' * 70}")
    
    # Bar chart settings
    bar_max_width = 35
    
    for r in stability_data:
        length = r['length']
        alpha = r['alpha']
        is_valid = r['is_valid']
        trades = r.get('trades', 0)
        
        # Calculate bar width (normalized to max absolute alpha)
        bar_width = int((abs(alpha) / max_abs) * bar_max_width) if max_abs > 0 else 0
        bar_width = max(bar_width, 1)
        
        # Build bar and determine color
        if length == best_length:
            bar = '█' * bar_width + ' << MAX'
            color = f"{Fore.GREEN}{Style.BRIGHT}"
        elif alpha > 0 and is_valid:
            bar = '█' * bar_width
            color = f"{Fore.GREEN}"
        elif alpha > 0:
            bar = '▓' * bar_width
            color = f"{Fore.YELLOW}"
        elif alpha == 0:
            bar = '░'
            color = f"{Fore.WHITE}"
        else:
            bar = '░' * bar_width
            color = f"{Fore.RED}{Style.DIM}"
        
        alpha_str = f"{alpha:+.1f}%"
        
        row = f"  {length:<4} {alpha_str:<10} {trades:<7} {bar}"
        print(f"{color}{row}{Style.RESET_ALL}")
    
    print(f"{Fore.WHITE}  {'-' * 70}")
    
    # Summary stats
    valid_count = sum(1 for r in stability_data if r['is_valid'])
    positive_count = sum(1 for r in stability_data if r['alpha'] > 0)
    avg_alpha = sum(r['alpha'] for r in stability_data) / len(stability_data)
    
    print()
    print(f"{Fore.WHITE}  Valid Lengths: {Fore.GREEN}{valid_count}/{len(stability_data)}")
    print(f"{Fore.WHITE}  Positive Alpha: {Fore.CYAN}{positive_count}/{len(stability_data)}")
    print(f"{Fore.WHITE}  Alpha Range: {Fore.YELLOW}{min_alpha:+.1f}% to {max_alpha:+.1f}%")
    print(f"{Fore.WHITE}  Average Alpha: {Fore.CYAN}{avg_alpha:+.1f}%")
    print()
    
    # Recommendation
    print(f"{Fore.CYAN}{Style.BRIGHT}  RECOMMENDATION:")
    if best['is_valid']:
        print(f"{Fore.GREEN}{Style.BRIGHT}  Use DI Length = {best_length} for optimal Alpha ({best['alpha']:+.1f}%)")
    else:
        print(f"{Fore.YELLOW}  Best DI = {best_length} but fails guardrails. Consider other stocks.")
    
    print()
    print(f"{Fore.CYAN}{'=' * 75}")
    print()
