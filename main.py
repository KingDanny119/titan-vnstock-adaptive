"""
TITAN QUANT x VNSTOCK: VN100 Adaptive Scanner v3.0
==================================================
Entry point for the VN100 Alpha Scanner.

Usage:
    python main.py                  # Full VN100 scan (~100 stocks)
    python main.py --inspect SSI    # Deep dive inspection (DI 1-40)
    python main.py -i FPT           # Short form
    
Features:
    - VN100 Universe (~100 liquid stocks)
    - Extended DI optimization (1-40)
    - Alpha validation (2-year backtest)
    - Deep dive inspection mode
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from strategies.alpha_scanner import AlphaScanner
from ui.terminal import (
    print_header, 
    print_results_table, 
    print_footer,
    print_progress,
    print_scan_complete,
    print_parameter_heatmap
)


def run_scan():
    """Run full VN100 scan."""
    print_header()
    
    scanner = AlphaScanner()
    tickers = scanner.client.get_vn100_tickers()
    
    print(f"  Starting scan of {len(tickers)} VN100 stocks...")
    print()
    
    results = []
    for idx, symbol in enumerate(tickers, 1):
        print_progress(symbol, idx, len(tickers))
        
        result = scanner.analyze_symbol(symbol)
        if result:
            results.append(result)
    
    print_scan_complete()
    print()
    
    # Sort: Buy signals first, then valid, then by alpha
    def sort_key(r):
        is_buy = r.get('is_buy_signal', False) and r.get('is_valid', False)
        is_valid = r.get('is_valid', False)
        alpha = r.get('alpha', 0)
        return (-int(is_buy), -int(is_valid), -alpha)
    
    results.sort(key=sort_key)
    
    print_results_table(results)
    print_footer(results)


def run_inspect(symbol: str):
    """Run deep dive inspection for a single stock."""
    try:
        from colorama import Fore, Style
    except ImportError:
        class Fore:
            CYAN = GREEN = YELLOW = WHITE = ""
        class Style:
            BRIGHT = ""
    
    print()
    print(f"{Fore.CYAN}{Style.BRIGHT}  TITAN QUANT x VNSTOCK: DEEP DIVE MODE")
    print(f"{Fore.WHITE}  Analyzing: {Fore.YELLOW}{symbol}{Fore.WHITE} (DI Lengths 1-40)")
    print()
    
    scanner = AlphaScanner()
    
    print(f"{Fore.YELLOW}  Fetching data and testing all 40 DI lengths...")
    stability_data = scanner.inspect_ticker_stability(symbol)
    
    if not stability_data:
        print(f"{Fore.RED}  Failed to analyze {symbol}. Check ticker symbol.")
        return
    
    print_parameter_heatmap(symbol, stability_data)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="TITAN x VNSTOCK: VN100 Adaptive Alpha Scanner v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  # Scan all VN100 stocks
  python main.py --inspect SSI    # Deep dive SSI (test DI 1-40)
  python main.py -i FPT           # Deep dive FPT
        """
    )
    parser.add_argument(
        '--inspect', '-i',
        type=str,
        metavar='SYMBOL',
        help='Deep dive inspection for a single stock (DI 1-40)'
    )
    
    args = parser.parse_args()
    
    if args.inspect:
        run_inspect(args.inspect.upper())
    else:
        run_scan()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [INTERRUPTED] Scan cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n  [FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
