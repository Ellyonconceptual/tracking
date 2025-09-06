"""
Example Trading Bot using Signal Bolt
Demonstrates how to integrate Signal Bolt with a trading bot
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json

from signal_bolt import TradingSignal, SignalType, SignalStrength
from client import SignalBoltClient, SignalBoltConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBot:
    """Example trading bot that uses Signal Bolt signals"""
    
    def __init__(self, config: SignalBoltConfig = None):
        self.config = config or SignalBoltConfig()
        self.client = SignalBoltClient(self.config)
        self.positions = {}  # Track open positions
        self.balance = 10000.0  # Starting balance
        self.max_position_size = 1000.0  # Maximum position size
        self.risk_per_trade = 0.02  # 2% risk per trade
        
        # Trading rules
        self.min_confidence = 0.7
        self.min_strength = 3
        self.max_positions = 5
        
        # Statistics
        self.stats = {
            'trades_taken': 0,
            'wins': 0,
            'losses': 0,
            'total_pnl': 0.0
        }
    
    async def start(self):
        """Start the trading bot"""
        logger.info("Starting Trading Bot...")
        
        # Connect to Signal Bolt
        await self.client.connect()
        
        # Add signal callback
        self.client.add_signal_callback(self.on_signal)
        
        # Start monitoring
        await self.monitor_positions()
    
    async def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping Trading Bot...")
        await self.client.disconnect()
        self.print_stats()
    
    async def on_signal(self, signal: TradingSignal):
        """Handle incoming trading signals"""
        logger.info(f"Received signal: {signal.symbol} {signal.signal_type.value} "
                   f"(confidence: {signal.confidence:.2f}, strength: {signal.strength.name})")
        
        # Check if signal meets our criteria
        if not self.should_take_signal(signal):
            logger.debug(f"Signal rejected: {signal.id}")
            return
        
        # Check if we can take a new position
        if len(self.positions) >= self.max_positions:
            logger.warning("Maximum positions reached, skipping signal")
            return
        
        # Calculate position size
        position_size = self.calculate_position_size(signal)
        if position_size <= 0:
            logger.warning("Position size too small, skipping signal")
            return
        
        # Take position
        await self.take_position(signal, position_size)
    
    def should_take_signal(self, signal: TradingSignal) -> bool:
        """Determine if we should take this signal"""
        # Check confidence
        if signal.confidence < self.min_confidence:
            return False
        
        # Check strength
        if signal.strength.value < self.min_strength:
            return False
        
        # Check if we already have a position in this symbol
        if signal.symbol in self.positions:
            return False
        
        # Check signal type
        if signal.signal_type not in [SignalType.BUY, SignalType.SELL, SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
            return False
        
        return True
    
    def calculate_position_size(self, signal: TradingSignal) -> float:
        """Calculate position size based on risk management"""
        # Calculate risk amount
        risk_amount = self.balance * self.risk_per_trade
        
        # Calculate position size based on confidence
        confidence_multiplier = signal.confidence
        strength_multiplier = signal.strength.value / 5.0  # Normalize to 0-1
        
        # Base position size
        base_size = risk_amount * confidence_multiplier * strength_multiplier
        
        # Apply maximum position size limit
        position_size = min(base_size, self.max_position_size)
        
        # Ensure we have enough balance
        if position_size > self.balance:
            position_size = self.balance * 0.9  # Use 90% of balance
        
        return position_size
    
    async def take_position(self, signal: TradingSignal, position_size: float):
        """Take a trading position based on signal"""
        position_id = f"{signal.symbol}_{int(datetime.now().timestamp())}"
        
        # Determine position type
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            position_type = "LONG"
        else:
            position_type = "SHORT"
        
        # Create position
        position = {
            'id': position_id,
            'symbol': signal.symbol,
            'type': position_type,
            'size': position_size,
            'entry_price': signal.price,
            'entry_time': signal.timestamp,
            'signal_id': signal.id,
            'confidence': signal.confidence,
            'strength': signal.strength.value,
            'status': 'OPEN'
        }
        
        self.positions[signal.symbol] = position
        self.balance -= position_size
        self.stats['trades_taken'] += 1
        
        logger.info(f"Opened {position_type} position in {signal.symbol}: "
                   f"Size: ${position_size:.2f}, Price: {signal.price:.4f}")
        
        # Set up position monitoring
        asyncio.create_task(self.monitor_position(position))
    
    async def monitor_position(self, position: Dict):
        """Monitor a single position"""
        symbol = position['symbol']
        entry_price = position['entry_price']
        position_type = position['type']
        
        # Simulate position monitoring (in real implementation, this would connect to broker API)
        while symbol in self.positions and self.positions[symbol]['status'] == 'OPEN':
            # Get current price (simulated)
            current_price = await self.get_current_price(symbol)
            
            if current_price is None:
                await asyncio.sleep(5)
                continue
            
            # Calculate P&L
            if position_type == "LONG":
                pnl = (current_price - entry_price) / entry_price * position['size']
            else:
                pnl = (entry_price - current_price) / entry_price * position['size']
            
            # Check exit conditions
            should_exit = False
            exit_reason = ""
            
            # Profit target (5%)
            if pnl > position['size'] * 0.05:
                should_exit = True
                exit_reason = "Profit target"
            
            # Stop loss (2%)
            elif pnl < -position['size'] * 0.02:
                should_exit = True
                exit_reason = "Stop loss"
            
            # Time-based exit (30 minutes)
            elif (datetime.now() - position['entry_time']).total_seconds() > 1800:
                should_exit = True
                exit_reason = "Time limit"
            
            if should_exit:
                await self.close_position(symbol, current_price, exit_reason, pnl)
                break
            
            await asyncio.sleep(10)  # Check every 10 seconds
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol (simulated)"""
        # In real implementation, this would connect to broker API
        # For demo purposes, we'll simulate price movement
        import random
        
        # Simulate price movement around entry price
        if symbol in self.positions:
            entry_price = self.positions[symbol]['entry_price']
            # Random walk with slight upward bias
            change = random.uniform(-0.01, 0.02)  # -1% to +2%
            return entry_price * (1 + change)
        
        return None
    
    async def close_position(self, symbol: str, exit_price: float, reason: str, pnl: float):
        """Close a trading position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        position['exit_price'] = exit_price
        position['exit_time'] = datetime.now()
        position['status'] = 'CLOSED'
        position['pnl'] = pnl
        position['exit_reason'] = reason
        
        # Update balance
        self.balance += position['size'] + pnl
        
        # Update statistics
        self.stats['total_pnl'] += pnl
        if pnl > 0:
            self.stats['wins'] += 1
        else:
            self.stats['losses'] += 1
        
        logger.info(f"Closed {position['type']} position in {symbol}: "
                   f"P&L: ${pnl:.2f}, Reason: {reason}")
        
        # Remove from active positions
        del self.positions[symbol]
    
    async def monitor_positions(self):
        """Monitor all open positions"""
        while True:
            if not self.positions:
                await asyncio.sleep(5)
                continue
            
            logger.info(f"Monitoring {len(self.positions)} positions. Balance: ${self.balance:.2f}")
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def print_stats(self):
        """Print trading statistics"""
        total_trades = self.stats['wins'] + self.stats['losses']
        win_rate = (self.stats['wins'] / total_trades * 100) if total_trades > 0 else 0
        
        print("\n" + "="*50)
        print("TRADING BOT STATISTICS")
        print("="*50)
        print(f"Total Trades: {total_trades}")
        print(f"Wins: {self.stats['wins']}")
        print(f"Losses: {self.stats['losses']}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Total P&L: ${self.stats['total_pnl']:.2f}")
        print(f"Final Balance: ${self.balance:.2f}")
        print(f"Return: {((self.balance - 10000) / 10000 * 100):.2f}%")
        print("="*50)

async def main():
    """Main function to run the trading bot"""
    # Configure Signal Bolt client
    config = SignalBoltConfig(
        api_url="http://localhost:8000",
        ws_url="ws://localhost:8765"
    )
    
    # Create and start trading bot
    bot = TradingBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down trading bot...")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())