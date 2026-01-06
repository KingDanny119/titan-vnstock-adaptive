# TITAN x VNSTOCK: VN100 ADAPTIVE SCANNER (v3.0)

A quantitative tool demonstrating the **Impulse Ignition** strategy on Vietnam's stock market, powered by `vnstock`.

## Key Features

### VN100 Universe
Scans ~100 of Vietnam's most liquid stocks including:
- VN30 Core (30 blue chips)
- Midcap & Liquid Stocks (70+ tickers)

### Deep Scan Optimization (DI 1-40)
- Tests 40 different DI Length parameters
- Automatically finds optimal length per stock
- Extended range captures both short and long cycles

### Inspection Mode
- Deep dive any ticker
- Visual ASCII heatmap of parameter stability
- Identifies optimal settings at a glance

## Technical Core

### Algorithm
Ported from TITAN Crypto Bot (v9.1):
- **Indicators**: Wilder's Smoothed +DI/-DI
- **State Machine**: Stateful Trend Counter
- **Entry Signal**: Impulse count transitions 0 → 1

### Alpha Guardrails
Real-time vectorized backtest on 2 years of data:
1. Strategy return > 0%
2. Strategy return > Buy & Hold return

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Full VN100 scan (100 stocks, DI 1-40)
python main.py

# Deep dive inspection on single stock
python main.py --inspect SSI
python main.py -i FPT
```

## Output

### Scan Mode
Color-coded table showing:
- **GREEN**: Active buy signal + positive alpha
- **CYAN**: Positive alpha (watchlist)
- **DIM**: Negative alpha (avoid)

### Inspection Mode
ASCII heatmap showing alpha for each DI length:
```
  Len   Alpha      Trades   Chart
  ------------------------------------------------------------
  7     +45.6%     23       █████████████████████████████ << MAX
  8     +40.2%     20       ████████████████████████
  ...
  40    -5.0%      8        ░░░
```

## Project Structure

```
titan_vnstock_core/
├── core/            
│   ├── data_feed.py    # VN100 data fetcher
│   └── titan_math.py   # TITAN v9.1 engine
├── strategies/      
│   └── alpha_scanner.py # Adaptive optimizer
├── ui/              
│   └── terminal.py     # Colored output
└── main.py          # Entry point
```

## Credits

Developed for the XNO Quant integration showcase.  
Based on TITAN Quant Fund trading algorithms.
