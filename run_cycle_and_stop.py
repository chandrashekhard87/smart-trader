from trading_bot import OptionChainTradingBot
from config import UPSTOX_API_KEY, UPSTOX_API_SECRET, ACCESS_TOKEN, USE_SANDBOX, UPSTOX_API_BASE_URL

bot = OptionChainTradingBot(UPSTOX_API_KEY, UPSTOX_API_SECRET, ACCESS_TOKEN, use_sandbox=USE_SANDBOX, base_url=UPSTOX_API_BASE_URL)
print('Running one analysis cycle...')
bot.run_analysis_cycle()
print('Stopping bot to export CSVs...')
bot.stop()
print('Done')
