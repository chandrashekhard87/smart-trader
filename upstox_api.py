import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote
import pandas as pd
try:
    from mock_data import get_mock_market_data
except ImportError:
    get_mock_market_data = None

logger = logging.getLogger(__name__)


class UpstoxAPI:
    """Handle Upstox API interactions"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str = None,
        use_sandbox: bool = True,
        base_url: str = None,
        sandbox_url: str = "https://api-sandbox.upstox.com/v2",
        production_url: str = "https://api.upstox.com/v3",
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.use_sandbox = use_sandbox
        self.sandbox_url = sandbox_url
        self.production_url = production_url
        self.base_url = base_url or (self.sandbox_url if use_sandbox else self.production_url)
        if base_url:
            logger.info(f"Using custom Upstox API URL: {self.base_url}")
        else:
            logger.info(f"Using Upstox {'sandbox' if use_sandbox else 'production'} endpoint: {self.base_url}")
        self.session = requests.Session()
        
    def set_access_token(self, access_token: str):
        """Set the access token for API calls"""
        self.access_token = access_token
        
    def _get_headers(self) -> Dict:
        """Get headers for API requests"""
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
    
    def _build_historical_candle_endpoint(
        self,
        encoded_instrument_key: str,
        interval: str,
        from_date_str: str,
        to_date_str: str,
    ) -> str:
        """Build the historical candle endpoint path for sandbox and production."""
        # Sandbox v2 uses /historical-candle/{instrument}/{interval}/{fromDate}/{toDate}
        if self.use_sandbox or "api-sandbox.upstox.com" in self.base_url:
            return f"{self.base_url}/historical-candle/{encoded_instrument_key}/{interval}/{from_date_str}/{to_date_str}"

        # Production v3: split interval into unit and length, and use the correct order
        # Two production routes:
        # 1) Historical (past dates): /historical-candle/{instrument}/{unit}/{interval}/{to_date}/{from_date}
        # 2) Intraday (current day): /historical-candle/intraday/{instrument}/{unit}/{interval}
        # Determine unit/interval from passed `interval` string (e.g. '5minute', 'day', '30minute')
        low = interval.lower()
        # Map common representations
        if 'minute' in low:
            unit = 'minutes'
            number = ''.join(filter(str.isdigit, low)) or '1'
        elif 'hour' in low or 'hr' in low:
            unit = 'hours'
            number = ''.join(filter(str.isdigit, low)) or '1'
        elif 'day' in low:
            unit = 'days'
            number = ''.join(filter(str.isdigit, low)) or '1'
        elif 'week' in low:
            unit = 'weeks'
            number = ''.join(filter(str.isdigit, low)) or '1'
        elif 'month' in low:
            unit = 'months'
            number = ''.join(filter(str.isdigit, low)) or '1'
        else:
            # Fallback to minutes/1
            unit = 'minutes'
            number = '1'

        # If requesting intraday (from_date == to_date or caller intends live data), prefer intraday route.
        # Caller may pass identical dates for a single-day intraday request; choose intraday when from_date == to_date
        try:
            if from_date_str == to_date_str:
                return f"{self.base_url}/historical-candle/intraday/{encoded_instrument_key}/{unit}/{number}"
        except Exception:
            pass

        # Historical (past data) uses to_date before from_date in v3
        return f"{self.base_url}/historical-candle/{encoded_instrument_key}/{unit}/{number}/{to_date_str}/{from_date_str}"

    def test_connection(self) -> bool:
        """Test if API connection is working with a simple endpoint"""
        try:
            logger.info("Testing Upstox API connection...")
            logger.info(f"Using {'SANDBOX' if self.use_sandbox else 'PRODUCTION'} API")
            
            headers = self._get_headers()
            
            # Test with market data endpoint (works for both sandbox and production)
            from datetime import datetime, timedelta
            
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Use Nifty 50 index
            instrument_key = "NSE_INDEX|Nifty 50"
            encoded_key = quote(instrument_key, safe='')
            
            test_endpoint = self._build_historical_candle_endpoint(encoded_key, "day", from_date, to_date)
            logger.info(f"Testing endpoint: {test_endpoint}")
            
            test_response = self.session.get(test_endpoint, headers=headers, timeout=10)
            logger.info(f"Market data test - Status: {test_response.status_code}")
            
            if test_response.status_code == 200:
                logger.info("OK API connection working with market data!")
                return True
            else:
                logger.error(f"ERROR API connection failed: {test_response.status_code}")
                logger.error(f"Response: {test_response.text[:300]}")
                if test_response.status_code == 404:
                    logger.warning("Market data endpoint returned 404")
                    logger.warning("  - Your account may not have market data access enabled")
                    logger.warning("  - Contact Upstox support to enable market data")
                return False
                
        except Exception as e:
            logger.error(f"Exception in test_connection: {str(e)}")
            return False
    
    def get_market_data(self, instrument_key: str, interval: str = "30minute") -> Optional[Dict]:
        """
        Get historical OHLC data for an instrument
        
        Args:
            instrument_key: NSE instrument key (e.g., "NSE_INDEX|Nifty 50")
            interval: Time interval (1minute, 30minute, day for sandbox; 5minute, 15minute, etc. for production)
        
        Returns:
            Dictionary with OHLC data arrays or None on error
        """
        try:
            from datetime import datetime, timedelta
            
            # Supported intervals by sandbox v2 and production v3
            sandbox_v2_intervals = ["1minute", "30minute", "day", "week", "month"]
            
            # Validate interval
            if self.use_sandbox and interval not in sandbox_v2_intervals:
                logger.error(f"Interval '{interval}' not supported in sandbox v2. Supported: {sandbox_v2_intervals}")
                return None
            
            # Get data for the last 2 days
            to_date = datetime.now().date()
            from_date = to_date - timedelta(days=2)
            
            # Format dates as YYYY-MM-DD
            from_date_str = from_date.strftime("%Y-%m-%d")
            to_date_str = to_date.strftime("%Y-%m-%d")
            
            encoded_instrument_key = quote(instrument_key, safe='')
            endpoint = self._build_historical_candle_endpoint(
                encoded_instrument_key,
                interval,
                from_date_str,
                to_date_str,
            )
            headers = self._get_headers()
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Auth token (first 30 chars): {headers['Authorization'][:30]}...")
            
            response = self.session.get(endpoint, headers=headers, timeout=15)
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Body: {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                # Transform candles array to OHLC dict format
                candles = None
                if data.get("data") and data["data"].get("candles") is not None:
                    candles = data["data"]["candles"]

                if candles:
                    logger.info(f"OK Successfully got {len(candles)} candles")
                    ohlc_data = {
                        "open": [candle[1] for candle in candles],
                        "high": [candle[2] for candle in candles],
                        "low": [candle[3] for candle in candles],
                        "close": [candle[4] for candle in candles],
                        "volume": [candle[5] for candle in candles],
                        "timestamps": [candle[0] for candle in candles]
                    }
                    return ohlc_data

                # Empty candles list — attempt fallbacks for recent/intraday data
                logger.warning(f"No candle data in response for endpoint: {endpoint}")

                # 1) If production v3, try intraday endpoint (no dates)
                if not self.use_sandbox and "api.upstox.com/v3" in self.base_url:
                    try:
                        # derive unit/number from interval string
                        low = interval.lower()
                        if 'minute' in low:
                            unit = 'minutes'
                            number = ''.join(filter(str.isdigit, low)) or '1'
                        elif 'hour' in low or 'hr' in low:
                            unit = 'hours'
                            number = ''.join(filter(str.isdigit, low)) or '1'
                        elif 'day' in low:
                            unit = 'days'
                            number = ''.join(filter(str.isdigit, low)) or '1'
                        else:
                            unit = 'minutes'
                            number = '1'

                        intraday_endpoint = f"{self.base_url}/historical-candle/intraday/{encoded_instrument_key}/{unit}/{number}"
                        logger.info(f"Fallback: trying intraday endpoint: {intraday_endpoint}")
                        intraday_resp = self.session.get(intraday_endpoint, headers=headers, timeout=10)
                        logger.info(f"Intraday resp status: {intraday_resp.status_code}")
                        if intraday_resp.status_code == 200:
                            intraday_data = intraday_resp.json()
                            if intraday_data.get('data') and intraday_data['data'].get('candles'):
                                candles = intraday_data['data']['candles']
                                logger.info(f"OK Intraday fallback returned {len(candles)} candles")
                                ohlc_data = {
                                    "open": [candle[1] for candle in candles],
                                    "high": [candle[2] for candle in candles],
                                    "low": [candle[3] for candle in candles],
                                    "close": [candle[4] for candle in candles],
                                    "volume": [candle[5] for candle in candles],
                                    "timestamps": [candle[0] for candle in candles]
                                }
                                return ohlc_data
                    except Exception as e:
                        logger.warning(f"Intraday fallback failed: {e}")

                # 2) Try NSE_EQ fallback if instrument_key is an index and sandbox/production may not support it
                if 'NSE_INDEX' in instrument_key:
                    try:
                        # Try a mapped NSE_EQ instrument as a fallback (a NIFTY component)
                        fallback_mapping = {
                            'NSE_INDEX|Nifty 50': 'NSE_EQ|INE002A01018',
                            'NSE_INDEX|Nifty Bank': 'NSE_EQ|INE090A01021'
                        }
                        fallback = fallback_mapping.get(instrument_key)
                        if fallback:
                            encoded_fb = quote(fallback, safe='')
                            fb_endpoint = self._build_historical_candle_endpoint(encoded_fb, interval, from_date_str, to_date_str)
                            logger.info(f"Fallback: trying NSE_EQ endpoint: {fb_endpoint}")
                            fb_resp = self.session.get(fb_endpoint, headers=headers, timeout=10)
                            if fb_resp.status_code == 200:
                                fb_data = fb_resp.json()
                                if fb_data.get('data') and fb_data['data'].get('candles'):
                                    candles = fb_data['data']['candles']
                                    logger.info(f"OK NSE_EQ fallback returned {len(candles)} candles")
                                    ohlc_data = {
                                        "open": [candle[1] for candle in candles],
                                        "high": [candle[2] for candle in candles],
                                        "low": [candle[3] for candle in candles],
                                        "close": [candle[4] for candle in candles],
                                        "volume": [candle[5] for candle in candles],
                                        "timestamps": [candle[0] for candle in candles]
                                    }
                                    return ohlc_data
                    except Exception as e:
                        logger.warning(f"NSE_EQ fallback failed: {e}")

                return None
            elif response.status_code == 404:
                logger.error(f"404 - Resource not found. Using mock data for testing...")
                if get_mock_market_data:
                    logger.warning("API returned 404 - Using mock data (demo mode)")
                    logger.warning("Please contact Upstox support to enable market data API access")
                    mock_data = get_mock_market_data(instrument_key, interval, days=2)
                    logger.info(f"OK Generated mock data: {len(mock_data['close'])} candles")
                    return mock_data
                else:
                    if "NSE_INDEX" in instrument_key:
                        logger.error(f"  WARNING NSE_INDEX instruments may not be supported in sandbox")
                        logger.error(f"    Try these alternatives:")
                        logger.error(f"    1. Use NSE_EQ instruments (specific stocks) instead")
                        logger.error(f"    2. Check if your sandbox has market data enabled")
                        logger.error(f"    3. Contact Upstox support for sandbox index data")
                    else:
                        logger.error(f"  - Invalid instrument key: {instrument_key}")
                        logger.error(f"  - Unsupported interval for this instrument: {interval}")
                    logger.error(f"  - Full endpoint: {endpoint}")
                    return None
            else:
                logger.error(f"Error fetching market data: {response.status_code} - {response.text}")
                if response.status_code == 400 and get_mock_market_data:
                    logger.warning("API returned error - Using mock data (demo mode)")
                    logger.warning("Please contact Upstox support to enable market data API access")
                    mock_data = get_mock_market_data(instrument_key, interval, days=2)
                    logger.info(f"OK Generated mock data: {len(mock_data['close'])} candles")
                    return mock_data
                return None
                
        except Exception as e:
            logger.error(f"Exception in get_market_data: {str(e)}", exc_info=True)
            return None
    
    def get_option_chain(self, index: str, expiry_date: str = None) -> Optional[List[Dict]]:
        """
        Get option chain data for an index
        
        Args:
            index: Index name (NIFTY, BANKNIFTY, etc.)
            expiry_date: Expiry date in DDMMMYY format (e.g., "05MAY23")
        
        Returns:
            List of option chain data or None on error
        """
        try:
            # Map index names to NSE symbols
            index_mapping = {
                "NIFTY": "NSE_INDEX|Nifty 50",
                "BANKNIFTY": "NSE_INDEX|Nifty Bank",
                "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
                "MIDCPNIFTY": "NSE_INDEX|Nifty Midcap 50"
            }
            
            symbol = index_mapping.get(index)
            if not symbol:
                logger.error(f"Unknown index: {index}")
                return None
            
            # Get current market data
            market_data = self.get_market_data(symbol)
            
            if not market_data:
                return None
            
            return market_data
            
        except Exception as e:
            logger.error(f"Exception in get_option_chain: {str(e)}")
            return None
    
    def place_order(self, symbol: str, quantity: int, side: str, order_type: str = "MARKET",
                   price: float = None, product: str = "MIS") -> Optional[Dict]:
        """
        Place an order
        
        Args:
            symbol: Option symbol (e.g., "NIFTY05MAY2411000CE")
            quantity: Quantity to trade
            side: BUY or SELL
            order_type: MARKET or LIMIT
            price: Price for limit orders
            product: MIS or CNC
        
        Returns:
            Order response or None on error
        """
        try:
            endpoint = f"{self.base_url}/order/place"
            
            payload = {
                "quantity": quantity,
                "product": product,
                "validity": "DAY",
                "order_type": order_type,
                "instrument_token": symbol,
                "order_side": side,
            }
            
            if order_type == "LIMIT" and price:
                payload["price"] = price
            
            logger.debug(f"Placing order to endpoint: {endpoint}")
            logger.debug(f"Order payload: {json.dumps(payload)}")
            response = self.session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload
            )
            logger.debug(f"Order response status: {response.status_code}, body: {response.text}")
            
            if response.status_code in [200, 201]:
                logger.info(f"Order placed successfully: {response.json()}")
                return response.json()
            else:
                logger.error(f"Error placing order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in place_order: {str(e)}")
            return None
    
    def place_bracket_order(self, symbol: str, quantity: int, side: str, 
                           price: float, sl_price: float, target_price: float,
                           product: str = "MIS") -> Optional[Dict]:
        """
        Place a bracket order with stop loss and target
        
        Args:
            symbol: Option symbol
            quantity: Quantity to trade
            side: BUY or SELL
            price: Entry price
            sl_price: Stop loss price
            target_price: Target price
            product: MIS or CNC
        
        Returns:
            Order response or None on error
        """
        try:
            endpoint = f"{self.base_url}/order/place/bracket"
            
            payload = {
                "quantity": quantity,
                "product": product,
                "validity": "DAY",
                "order_type": "LIMIT",
                "instrument_token": symbol,
                "order_side": side,
                "price": price,
                "stop_loss": sl_price,
                "trailing_stop_loss": None,
                "stoploss_order_type": "LIMIT",
                "stoploss_price": sl_price,
                "target_order_type": "LIMIT",
                "target_price": target_price,
            }
            
            logger.debug(f"Placing bracket order to endpoint: {endpoint}")
            logger.debug(f"Bracket order payload: {json.dumps(payload)}")
            response = self.session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload
            )
            logger.debug(f"Bracket order response status: {response.status_code}, body: {response.text}")
            
            if response.status_code in [200, 201]:
                logger.info(f"Bracket order placed successfully: {response.json()}")
                return response.json()
            else:
                logger.error(f"Error placing bracket order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in place_bracket_order: {str(e)}")
            return None
    
    def get_positions(self) -> Optional[List[Dict]]:
        """Get current positions"""
        try:
            endpoint = f"{self.base_url}/portfolio/long-term-positions"
            
            response = self.session.get(
                endpoint,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json().get("data", {}).get("positions", [])
            else:
                logger.error(f"Error fetching positions: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in get_positions: {str(e)}")
            return None
    
    def get_orders(self) -> Optional[List[Dict]]:
        """Get order history"""
        try:
            endpoint = f"{self.base_url}/order/retrieve-all"
            
            response = self.session.get(
                endpoint,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                logger.error(f"Error fetching orders: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Exception in get_orders: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            endpoint = f"{self.base_url}/order/cancel"
            
            payload = {"order_id": order_id}
            
            response = self.session.post(
                endpoint,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Order cancelled: {order_id}")
                return True
            else:
                logger.error(f"Error cancelling order: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception in cancel_order: {str(e)}")
            return False
