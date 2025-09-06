## Real-Time Options Signal Bot

This project provides a modular, real-time signal bot for options trading. It includes:

- A synthetic real-time data provider for candles (no broker access required)
- Pluggable strategies (e.g., RSI + EMA crossover) that emit CALL/PUT signals
- Pluggable sinks (console, webhook) to consume signals
- A simple CLI runner and YAML configuration

Note: Integrations with specific brokers (e.g., IQ Option) are not included by default. You can implement a provider adapter to bridge live broker data to this bot.

### Quick start

1) Install dependencies

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Create a configuration file `config.example.yaml` (already provided) or copy it:

```bash
cp config.example.yaml config.yaml
```

3) Run the bot

```bash
python -m signals_bot.cli --config config.yaml
```

### Configuration

See `config.example.yaml` for an annotated example. Key sections:

- `provider`: Selects the market data provider and parameters
- `instruments`: List of instruments and timeframe to subscribe
- `strategies`: Strategy list with parameters
- `sinks`: Where to send generated signals

### Extending

- Add a broker adapter by implementing `signals_bot.data_provider.base.AbstractMarketDataProvider`
- Add new strategies by deriving from `signals_bot.strategies.base.AbstractStrategy`
- Add sinks by deriving from `signals_bot.sinks.base.AbstractSignalSink`

### Disclaimer

This software is provided for educational purposes only. It does not constitute financial advice. Use at your own risk.

# tracking