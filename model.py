import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import time

# ----------------- Strategy Parameters -----------------
START_DATE = '2000-01-01'  # Backtest start date
WINDOW = 120  # Window for calculating moving average energy
INITIAL_CAPITAL = 100000.0  # Initial capital for backtesting
MIN_HISTORY = WINDOW  # Minimum history required for signal generation

# ----------------- Signal Generation Parameters -----------------
BASE_THRESHOLD = 0.1  # Base threshold for signal strength
VOL_WINDOW = 30  # Window for volatility calculation
MA_WINDOWS = [10, 40, 140]  # Moving average windows for trend analysis

# ----------------- Stop Loss Parameters -----------------
TRAILING_STOP = 0.05  # Trailing stop loss percentage
MAX_DRAWDOWN_STOP = 0.20  # Maximum drawdown stop loss percentage
VIX_HIGH_THRESHOLD = 25  # VIX high threshold
VIX_EXTREME_THRESHOLD = 50  # VIX extreme threshold

def download_data(start_date):
    """
    Download historical data for ETFs and VIX
    
    Args:
        start_date: Start date for data download
    
    Returns:
        DataFrame with adjusted close prices for ETFs and VIX
    """
    # List of ETFs to trade
    etfs = ['SPY', 'XLK', 'XLV', 'XLE', 'XLF', 'XLI', 'XLY']
    
    # Download data for ETFs
    data = pd.DataFrame()
    download_failed = False
    
    for etf in etfs:
        try:
            print(f"Downloading data for {etf}...")
            ticker = yf.Ticker(etf)
            hist = ticker.history(start=start_date, end=datetime.now().strftime('%Y-%m-%d'))['Close']
            if len(hist) == 0:
                print(f"Warning: No data available for {etf}")
                download_failed = True
                break
            else:
                print(f"Downloaded {len(hist)} data points for {etf}")
                # Convert index to date only (remove time and timezone info)
                hist.index = hist.index.date
                data[etf] = hist
        except Exception as e:
            print(f"Error downloading {etf}: {str(e)}")
            download_failed = True
            break
    
    if download_failed:
        print("Failed to download complete ETF data")
        return None
        
    # Download VIX data
    try:
        print("Downloading VIX data...")
        vix = yf.Ticker('^VIX')
        vix_hist = vix.history(start=start_date, end=datetime.now().strftime('%Y-%m-%d'))['Close']
        if len(vix_hist) == 0:
            print("Warning: No VIX data available")
            return None
        else:
            print(f"Downloaded {len(vix_hist)} data points for VIX")
            # Convert index to date only (remove time and timezone info)
            vix_hist.index = vix_hist.index.date
            data['VIX'] = vix_hist
    except Exception as e:
        print(f"Error downloading VIX: {str(e)}")
        return None
    
    # Check for missing values before cleaning
    print("\nMissing values before cleaning:")
    print(data.isnull().sum())
    
    # Drop any rows with missing data
    data_cleaned = data.dropna()
    
    # Check for missing values after cleaning
    print("\nMissing values after cleaning:")
    print(data_cleaned.isnull().sum())
    
    if len(data_cleaned) == 0:
        print("No valid data after cleaning")
        # Try to identify why we lost all data
        print("\nSample of raw data:")
        print(data.head())
        print("\nDates with missing values:")
        print(data[data.isnull().any(axis=1)].head())
        return None
        
    print(f"\nFinal dataset shape after cleaning: {data_cleaned.shape}")
    print(f"Date range: {data_cleaned.index[0]} to {data_cleaned.index[-1]}")
    
    return data_cleaned

def ma_energy(prices, window):
    """
    Calculate moving average energy indicator
    
    Args:
        prices: Price series
        window: Rolling window size
    
    Returns:
        Series of MA energy values
    """
    ma = prices.rolling(window=window).mean()
    energy = (prices - ma) / ma
    return energy

def generate_signals(data):
    """
    Generate trading signals based on MA energy
    
    Args:
        data: Price data for ETFs
    
    Returns:
        DataFrame with signal strengths for each ETF
    """
    signals = pd.DataFrame(0, index=data.index, columns=data.columns)
    for etf in data.columns:
        if etf == 'SPY':
            continue
        signals[etf] = ma_energy(data[etf], WINDOW)
    return signals

def get_target_weights(signals, current_date, current_positions, data, entry_prices):
    """
    Calculate target portfolio weights based on signals and risk management rules
    
    Args:
        signals: Signal strengths for ETFs
        current_date: Current trading date
        current_positions: Current portfolio positions
        data: Price data for ETFs
        entry_prices: Entry prices for current positions
    
    Returns:
        Dictionary of target weights for each ETF
    """
    target_weights = {}
    
    # Get current VIX level and calculate volatility adjustment
    vix_level = data.loc[current_date, 'VIX']
    vol_adj = 1.0
    
    if vix_level > VIX_EXTREME_THRESHOLD:
        # Exit all positions in extreme volatility
        return target_weights
    elif vix_level > VIX_HIGH_THRESHOLD:
        # Reduce position sizes in high volatility
        vol_adj = 0.5
    
    # Calculate dynamic threshold based on market conditions
    current_threshold = BASE_THRESHOLD
    
    # Check stop loss conditions for current positions
    for etf, shares in current_positions.items():
        if shares > 0:
            current_price = data.loc[current_date, etf]
            entry_price = entry_prices[etf]
            drawdown = (current_price - entry_price) / entry_price
            
            # Apply trailing stop and maximum drawdown stop
            if drawdown < -MAX_DRAWDOWN_STOP:
                continue
    
    # Find strongest signal above threshold
    current_signals = signals.loc[current_date]
    max_signal = current_signals.max()
    
    if max_signal > current_threshold:
        best_etf = current_signals.idxmax()
        target_weights[best_etf] = 1.0 * vol_adj
    
    return target_weights

def backtest(data, signals):
    """
    Perform strategy backtest
    
    Args:
        data: Price data for ETFs and VIX
        signals: Signal strengths for ETFs
    
    Returns:
        DataFrame with portfolio values and returns
    """
    portfolio = pd.DataFrame(index=data.index)
    portfolio['value'] = 0.0
    portfolio['return'] = 0.0
    
    current_positions = {}  # Dictionary to track current positions
    entry_prices = {}      # Dictionary to track entry prices
    cash = INITIAL_CAPITAL  # Initial cash
    
    # Create positions DataFrame only for ETFs (exclude VIX)
    etf_columns = [col for col in data.columns if col != 'VIX']
    positions = pd.DataFrame(0, index=data.index, columns=etf_columns)
    
    for i, current_date in enumerate(data.index):
        if i < MIN_HISTORY:
            portfolio.loc[current_date, 'value'] = cash
            continue
        
        # Update portfolio value
        total_value = cash
        for etf, shares in current_positions.items():
            total_value += shares * data.loc[current_date, etf]
        
        portfolio.loc[current_date, 'value'] = total_value
        
        # Calculate returns
        if i > 0:
            portfolio.loc[current_date, 'return'] = (
                portfolio.loc[current_date, 'value'] / 
                portfolio.loc[data.index[i-1], 'value'] - 1
            )
        
        # Record current positions (only for ETFs)
        for etf in etf_columns:
            positions.loc[current_date, etf] = current_positions.get(etf, 0.0)
        
        # Get target weights
        target_weights = get_target_weights(signals, current_date, current_positions, 
                                          data, entry_prices)
        
        # Adjust positions based on target weights
        for etf, target_weight in target_weights.items():
            target_value = total_value * target_weight
            current_price = data.loc[current_date, etf]
            target_shares = int(target_value / current_price)
            
            # Update positions and cash
            current_positions[etf] = target_shares
            entry_prices[etf] = current_price
            
        # Update cash after all position adjustments
        cash = total_value - sum(shares * data.loc[current_date, etf] 
                               for etf, shares in current_positions.items())
    
    return portfolio, positions

def rolling_backtest(data, window_years=5):
    """
    Perform rolling window backtest with non-overlapping windows
    
    Args:
        data: DataFrame with price data
        window_years: Length of each window in years
    """
    results = []
    window_days = window_years * 252  # Approximate trading days in a year
    
    # Calculate non-overlapping windows
    start_idx = 0
    while start_idx + window_days <= len(data):
        window_data = data.iloc[start_idx:start_idx + window_days]
        
        # Run backtest for this window
        signals = generate_signals(window_data)
        portfolio, positions = backtest(window_data, signals)
        
        # Calculate metrics for this window
        strategy_return = calculate_annual_return(portfolio['value'])
        strategy_vol = calculate_annual_volatility(portfolio['return'])
        strategy_sharpe = calculate_sharpe_ratio(portfolio['return'])
        strategy_max_dd = calculate_max_drawdown(portfolio['value'])
        
        # Calculate benchmark (SPY) metrics
        spy_returns = window_data['SPY'].pct_change().fillna(0)
        spy_return = calculate_annual_return(window_data['SPY'])
        spy_vol = calculate_annual_volatility(spy_returns)
        spy_sharpe = calculate_sharpe_ratio(spy_returns)
        spy_max_dd = calculate_max_drawdown(window_data['SPY'])
        
        # Calculate average turnover
        avg_turnover = calculate_average_turnover(portfolio['value'])
        
        results.append({
            'Start Date': window_data.index[0],
            'End Date': window_data.index[-1],
            'Window Days': len(window_data),
            'Strategy Return': strategy_return,
            'Strategy Volatility': strategy_vol,
            'Strategy Sharpe': strategy_sharpe,
            'Strategy Max Drawdown': strategy_max_dd,
            'SPY Return': spy_return,
            'SPY Volatility': spy_vol,
            'SPY Sharpe': spy_sharpe,
            'SPY Max Drawdown': spy_max_dd,
            'Average Turnover': avg_turnover
        })
        
        # Move to next non-overlapping window
        start_idx += window_days
    
    return pd.DataFrame(results)

def calculate_annual_volatility(returns):
    """Calculate annualized volatility"""
    return returns.std() * np.sqrt(252)

def calculate_annual_return(portfolio_values):
    """
    Calculate annualized return from a series of portfolio values
    
    Args:
        portfolio_values: Series of portfolio values
        
    Returns:
        Annualized return as a decimal (not percentage)
    """
    if len(portfolio_values) < 2:
        return 0.0
        
    start_value = portfolio_values.iloc[0]
    end_value = portfolio_values.iloc[-1]
    years = len(portfolio_values) / 252  # Assuming 252 trading days per year
    
    total_return = (end_value / start_value) - 1
    annual_return = (1 + total_return) ** (1 / years) - 1
    
    return annual_return  # Return as decimal, not percentage

def calculate_average_turnover(portfolio_values):
    """Calculate average portfolio turnover"""
    daily_change = portfolio_values.pct_change().abs()
    return daily_change.mean() * 252

def calculate_sharpe_ratio(returns):
    """
    Calculate annualized Sharpe ratio
    
    Args:
        returns: Series of daily returns
        
    Returns:
        Annualized Sharpe ratio
    """
    # Annualize returns and volatility
    annual_return = returns.mean() * 252
    annual_vol = returns.std() * np.sqrt(252)
    risk_free_rate = 0.02  # Assuming 2% annual risk-free rate
    
    if annual_vol == 0:
        return 0.0
        
    return (annual_return - risk_free_rate) / annual_vol

def calculate_max_drawdown(values):
    """
    Calculate maximum drawdown using rolling maximum
    
    Args:
        values: Series of values
        
    Returns:
        Maximum drawdown as a decimal (not percentage)
    """
    rolling_max = values.expanding().max()
    drawdowns = (values - rolling_max) / rolling_max
    return abs(drawdowns.min())

def plot_rolling_metrics(results):
    """
    Plot rolling window performance metrics
    
    Args:
        results: DataFrame with rolling window results
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot Returns
    axes[0, 0].plot(results['End Date'], results['Strategy Return'], 
                    label='Strategy', marker='o')
    axes[0, 0].plot(results['End Date'], results['SPY Return'], 
                    label='SPY', marker='o')
    axes[0, 0].set_title('Annual Returns')
    axes[0, 0].legend()
    
    # Plot Sharpe Ratios
    axes[0, 1].plot(results['End Date'], results['Strategy Sharpe'], 
                    label='Strategy', marker='o')
    axes[0, 1].plot(results['End Date'], results['SPY Sharpe'], 
                    label='SPY', marker='o')
    axes[0, 1].set_title('Sharpe Ratios')
    axes[0, 1].legend()
    
    # Plot Maximum Drawdowns
    axes[1, 0].plot(results['End Date'], results['Strategy Max Drawdown'], 
                    label='Strategy', marker='o')
    axes[1, 0].plot(results['End Date'], results['SPY Max Drawdown'], 
                    label='SPY', marker='o')
    axes[1, 0].set_title('Maximum Drawdowns')
    axes[1, 0].legend()
    
    # Plot Average Turnover
    axes[1, 1].plot(results['End Date'], results['Average Turnover'], 
                    label='Strategy', marker='o')
    axes[1, 1].set_title('Average Turnover')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig('rolling_metrics.png', bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    # Download data
    data = download_data(start_date=START_DATE)
    
    # Execute rolling window backtest
    print("\n=== Rolling Window Backtest (5-Year Windows) ===")
    rolling_results = rolling_backtest(data)
    
    # Print detailed statistics for each window
    pd.set_option('display.float_format', '{:.2%}'.format)
    print("\nDetailed Statistics for Each Window:")
    print(rolling_results.to_string(index=False))
    
    # Plot metrics
    plot_rolling_metrics(rolling_results)
    print("\nPlot saved as 'rolling_metrics.png'")