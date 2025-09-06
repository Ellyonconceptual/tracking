# Signal Bolt - Real-time Trading Signal Tracker

Signal Bolt is a powerful real-time trading signal tracking system designed for options trading platforms like IQ Options. It provides real-time signal analysis, filtering, and distribution to help traders make informed decisions.

## Features

- **Real-time Signal Tracking**: Monitor live market data and generate trading signals
- **Multi-Platform Support**: Compatible with IQ Options and other trading platforms
- **Technical Analysis**: Built-in RSI, MACD, and other technical indicators
- **Signal Filtering**: Advanced filtering based on confidence, strength, and other criteria
- **WebSocket API**: Real-time signal delivery via WebSocket
- **REST API**: Complete REST API for signal management
- **Client Library**: Easy-to-use Python client library
- **Trading Bot Integration**: Example trading bot implementation
- **Signal History**: Track and analyze historical signals
- **Statistics & Monitoring**: Comprehensive system statistics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Market Data   │───▶│   Signal Bolt    │───▶│   Trading Bot   │
│   Sources       │    │   Core Engine    │    │   / Client      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   WebSocket      │
                       │   / REST API     │
                       └──────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd signal-bolt

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your configuration:

```env
# API Configuration
API_HOST=localhost
API_PORT=8000
WS_HOST=localhost
WS_PORT=8765

# Platform Configuration
IQ_OPTIONS_ENABLED=true
IQ_OPTIONS_API_KEY=your_api_key
IQ_OPTIONS_USERNAME=your_username
IQ_OPTIONS_PASSWORD=your_password

# Signal Configuration
SIGNAL_EXPIRY_MINUTES=30
MAX_ACTIVE_SIGNALS=1000
```

### 3. Start the Signal Bolt

```bash
# Start the main Signal Bolt service
python signal_bolt.py

# In another terminal, start the API server
python api.py
```

### 4. Test the System

```bash
# Test the API
curl http://localhost:8000/health

# Test WebSocket connection
python client.py
```

## Usage Examples

### Basic Client Usage

```python
import asyncio
from client import SignalBoltClient, SignalBoltConfig

async def main():
    config = SignalBoltConfig(
        api_url="http://localhost:8000",
        ws_url="ws://localhost:8765"
    )
    
    async with SignalBoltClient(config) as client:
        # Add signal callback
        def on_signal(signal):
            print(f"New signal: {signal.symbol} {signal.signal_type.value}")
        
        client.add_signal_callback(on_signal)
        
        # Get active signals
        signals = await client.get_active_signals()
        print(f"Active signals: {len(signals)}")
        
        # Keep running
        await asyncio.sleep(60)

asyncio.run(main())
```

### Trading Bot Integration

```python
from example_trading_bot import TradingBot
from client import SignalBoltConfig

async def main():
    config = SignalBoltConfig()
    bot = TradingBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()

asyncio.run(main())
```

## API Endpoints

### REST API

- `GET /` - API information
- `GET /health` - Health check
- `GET /signals/active` - Get active signals
- `GET /signals/history` - Get signal history
- `GET /signals/{id}` - Get specific signal
- `GET /stats` - Get system statistics
- `GET /platforms` - Get available platforms
- `GET /symbols` - Get available symbols
- `POST /filters` - Update signal filters
- `POST /signals/simulate` - Simulate a signal

### WebSocket

- `ws://localhost:8765/ws` - Real-time signal updates

## Signal Types

- **BUY**: Buy signal
- **SELL**: Sell signal
- **HOLD**: Hold position
- **STRONG_BUY**: Strong buy signal
- **STRONG_SELL**: Strong sell signal

## Signal Strength Levels

- **WEAK** (1): Low confidence signal
- **MODERATE** (2): Medium confidence signal
- **STRONG** (3): High confidence signal
- **VERY_STRONG** (4): Very high confidence signal
- **EXTREME** (5): Maximum confidence signal

## Technical Indicators

Signal Bolt uses several technical indicators for signal generation:

- **RSI (Relative Strength Index)**: Momentum oscillator
- **MACD (Moving Average Convergence Divergence)**: Trend following indicator
- **Volume Analysis**: Volume confirmation
- **Price Action**: Support and resistance levels

## Configuration Options

### Signal Filters

```python
from signal_bolt import SignalFilter, SignalType

filter = SignalFilter(
    min_confidence=0.7,        # Minimum confidence level
    min_strength=3,            # Minimum signal strength
    max_age_minutes=30,        # Maximum signal age
    platforms=['iq_options'],  # Allowed platforms
    symbols=['EURUSD', 'GBPUSD'],  # Allowed symbols
    signal_types=[SignalType.BUY, SignalType.SELL]  # Allowed signal types
)
```

### Platform Configuration

```python
platforms = {
    'iq_options': {
        'name': 'IQ Options',
        'enabled': True,
        'websocket_url': 'wss://api.iqoption.com/ws/',
        'api_url': 'https://api.iqoption.com/api/',
        'api_key': 'your_api_key',
        'username': 'your_username',
        'password': 'your_password'
    }
}
```

## Advanced Features

### Custom Signal Handlers

```python
async def custom_signal_handler(signal: TradingSignal):
    # Custom logic for handling signals
    if signal.confidence > 0.8:
        # Send notification
        await send_notification(signal)
    
    # Log to database
    await log_signal_to_db(signal)
    
    # Execute trade
    await execute_trade(signal)

client.add_signal_callback(custom_signal_handler)
```

### Signal Filtering

```python
# Update filters via API
filters = {
    "min_confidence": 0.8,
    "min_strength": 4,
    "platforms": ["iq_options"],
    "symbols": ["EURUSD", "GBPUSD"]
}

await client.update_filters(filters)
```

### Statistics and Monitoring

```python
# Get system statistics
stats = await client.get_stats()
print(f"Signals generated: {stats['signals_generated']}")
print(f"Active signals: {stats['active_signals']}")
print(f"Uptime: {stats['uptime_hours']:.2f} hours")
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8765

CMD ["python", "api.py"]
```

### Production Considerations

1. **Redis**: Use Redis for distributed signal sharing
2. **Database**: Use PostgreSQL for signal history
3. **Monitoring**: Implement health checks and monitoring
4. **Scaling**: Use load balancers for multiple instances
5. **Security**: Implement authentication and rate limiting

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if Signal Bolt is running
   - Verify WebSocket URL and port
   - Check firewall settings

2. **No Signals Generated**
   - Check platform configuration
   - Verify API keys and credentials
   - Check signal filters

3. **High Memory Usage**
   - Reduce `MAX_ACTIVE_SIGNALS`
   - Increase cleanup frequency
   - Monitor signal expiry

### Logs

Check the `signal_bolt.log` file for detailed logs:

```bash
tail -f signal_bolt.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the documentation
- Review the example code

## Disclaimer

This software is for educational and research purposes only. Trading involves risk, and past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor before making trading decisions.