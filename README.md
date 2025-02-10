# Quant Sector Rotation Strategy 📈

A sophisticated quantitative trading strategy leveraging momentum and volatility signals for ETF sector rotation, enhanced with LLM-powered strategy analysis.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://quantrotation.streamlit.app/)

## 🚀 Try It Now!

Experience the strategy in action: [Quant Sector Rotation App](https://quantrotation.streamlit.app/)

## 🚀 Strategy Overview

This project implements a systematic sector rotation strategy using ETFs, combining momentum signals with intelligent risk management. The strategy employs a unique "Moving Average Energy" indicator for momentum measurement and incorporates VIX-based position sizing.

### 🎯 Key Features

- **MA Energy Indicator**: Proprietary momentum indicator using multiple timeframe moving averages, normalized by price volatility
- **Dynamic Risk Management**: VIX-based position sizing with adaptive thresholds
- **LLM Strategy Review**: AI-powered performance analysis and strategy behavior insights
- **Interactive Dashboard**: Real-time strategy monitoring and backtesting visualization

## 📊 Backtest Results (2010-2024)

- **Annual Return**: 18.5%
- **Sharpe Ratio**: 1.45
- **Information Ratio**: 0.82

## 🛠️ Technical Architecture

1. **Signal Generation**
   - Multi-timeframe MA Energy calculation
   - Cross-asset momentum comparison
   - Volatility normalization

2. **Risk Management**
   - VIX-based position sizing
   - Trailing stop implementation
   - Maximum drawdown control

3. **Strategy Review**
   - LLM-powered strategy behavior analysis
   - Historical context integration
   - Performance attribution

## 📦 Installation

```bash
git clone https://github.com/garroshub/Quant_Sector_Rotation_Strategy.git
cd Quant_Sector_Rotation_Strategy
pip install -r requirements.txt
```

## 🚀 Quick Start

```bash
streamlit run app.py
```

## 📊 Dashboard Features

1. **Strategy Parameters**
   - MA windows customization
   - Risk thresholds adjustment
   - Universe selection

2. **Performance Analytics**
   - Rolling window analysis
   - Risk metrics visualization
   - Position history tracking

3. **AI Strategy Review**
   - Strategy behavior analysis
   - Performance attribution
   - Improvement suggestions

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

GitHub: [@garroshub](https://github.com/garroshub)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=garroshub/Quant_Sector_Rotation_Strategy&type=Date)](https://star-history.com/#garroshub/Quant_Sector_Rotation_Strategy&Date)

---
**Disclaimer**: This strategy is for educational purposes only. Past performance does not guarantee future results. Always do your own research and consider your risk tolerance before trading.
