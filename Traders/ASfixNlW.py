# Copyright 2021 Optiver Asia Pacific Pty. Ltd.
#
# This file is part of Ready Trader Go.
#
#     Ready Trader Go is free software: you can redistribute it and/or
#     modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     Ready Trader Go is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public
#     License along with Ready Trader Go.  If not, see
#     <https://www.gnu.org/licenses/>.
import asyncio
from base64 import a85decode
import itertools
from statistics import variance

from typing import List

from ready_trader_go import BaseAutoTrader, Instrument, Lifespan, MAXIMUM_ASK, MINIMUM_BID, Side
import numpy as np
import time

LIQ_TIME = 4
LOT_SIZE = 10
POSITION_LIMIT = 100
TICK_SIZE_IN_CENTS = 100
MIN_BID_NEAREST_TICK = (MINIMUM_BID + TICK_SIZE_IN_CENTS) // TICK_SIZE_IN_CENTS * TICK_SIZE_IN_CENTS
MAX_ASK_NEAREST_TICK = MAXIMUM_ASK // TICK_SIZE_IN_CENTS * TICK_SIZE_IN_CENTS


class AutoTrader(BaseAutoTrader):
    """Example Auto-trader.

    When it starts this auto-trader places ten-lot bid and ask orders at the
    current best-bid and best-ask prices respectively. Thereafter, if it has
    a long position (it has bought more lots than it has sold) it reduces its
    bid and ask prices. Conversely, if it has a short position (it has sold
    more lots than it has bought) then it increases its bid and ask prices.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, team_name: str, secret: str):
        """Initialise a new instance of the AutoTrader class."""
        super().__init__(loop, team_name, secret)
        self.order_ids = itertools.count(1)
        self.bids = set()
        self.asks = set()
        self.ask_id = self.ask_price = self.bid_id = self.bid_price = self.position = 0

        self.gamma=0.025
        self.k=1.9875
        self.variance=160


        self.TICK=0
        self.startTime=0
        self.last_position=0
        self.flagnotstart=True
        self.my_ask_prices=[[None]*5]*2
        self.my_ask_volumes=[[None]*5]*2
        self.my_bid_prices=[[None]*5]*2
        self.my_bid_volumes=[[None]*5]*2
    def spreadCal(self, gamma, var, T, k):
        return gamma*var*self.find_time()/T+2/gamma*np.log(1+gamma/k)


    def midpriceCal(self,s,q, gamma, var, T):
        return s-q*gamma*var*self.find_time()/T

    def on_error_message(self, client_order_id: int, error_message: bytes) -> None:
        """Called when the exchange detects an error.

        If the error pertains to a particular order, then the client_order_id
        will identify that order, otherwise the client_order_id will be zero.
        """
        self.logger.warning("error with order %d: %s", client_order_id, error_message.decode())
        if client_order_id != 0 and (client_order_id in self.bids or client_order_id in self.asks):
            self.on_order_status_message(client_order_id, 0, 0, 0)

    def on_hedge_filled_message(self, client_order_id: int, price: int, volume: int) -> None:
        """Called when one of your hedge orders is filled.

        The price is the average price at which the order was (partially) filled,
        which may be better than the order's limit price. The volume is
        the number of lots filled at that price.
        """
        self.logger.info("received hedge filled for order %d with average price %d and volume %d", client_order_id,
                         price, volume)

    def adjust_volume(self, t):
        RESTRICTLOT=10000
        if t>=RESTRICTLOT/2:
            t-=RESTRICTLOT
        return np.abs(t)

    def find_time(self):
        #return time.time()-self.startTime
        return 1

    def find_gamma(self):
        self.gamma=4/self.variance

    def find_k(self):
        self.k=self.gamma/(np.exp(self.gamma/2)-1)

    def on_order_book_update_message(self, instrument: int, sequence_number: int, ask_prices: List[int],
                                     ask_volumes: List[int], bid_prices: List[int], bid_volumes: List[int]) -> None:
        """Called periodically to report the status of an order book.

        The sequence number can be used to detect missed or out-of-order
        messages. The five best available ask (i.e. sell) and bid (i.e. buy)
        prices are reported along with the volume available at each of those
        price levels.
        """
        self.logger.info("received order book for instrument %d with sequence number %d", instrument,
                         sequence_number)
        tmptotallot=0
        tmptotmean=0
        self.TICK+=1
        self.my_ask_prices[instrument]=ask_prices
        self.my_ask_volumes[instrument]=ask_volumes
        self.my_bid_prices[instrument]=bid_prices
        self.my_bid_volumes[instrument]=bid_volumes

        if not ask_prices[0] or not bid_prices[0]:
            return

        if self.flagnotstart:
            self.startTime=time.time()
            self.flagnotstart=False

        if self.last_position!=self.position:
            self.startTime=time.time()
        self.last_position=self.position
        self.logger.info("time in mil sec %d", int((time.time()-self.startTime)*1000))
        if instrument == Instrument.ETF:
            tmptotallot=0
            tmptotmean=0
            #self.variance=0
            """print(ask_prices)
            print(ask_volumes)
            print(bid_prices)
            print(bid_volumes)"""

            """
            for i in range(0,5):
                tmp=self.adjust_volume(ask_volumes[i])
                tmptotallot+=tmp
                tmptotmean+=tmp*(ask_prices[i]/100)
            for i in range(0,5):
                tmp=self.adjust_volume(bid_volumes[i])
                tmptotallot+=tmp
                tmptotmean+=tmp*(bid_prices[i]/100)
            if tmptotallot==0:
                tmptotmean=1500
            tmptotmean/=tmptotallot
            for i in range(0,5):
                tmpvolume=self.adjust_volume(bid_volumes[i])
                self.variance+=(((tmptotmean-bid_prices[i]/100))**2)*tmpvolume
            for i in range(0,5):
                tmpvolume=self.adjust_volume(ask_volumes[i])
                self.variance+=(((tmptotmean-ask_prices[i]/100))**2)*tmpvolume
            if tmptotallot-1<=0 or self.variance<20:
                self.variance=20
            else:
                self.variance/=(tmptotallot-1)
            """
            
            self.find_gamma()
            self.find_k()


            price_adjustment = self.spreadCal(self.gamma,self.variance,LIQ_TIME,self.k)
            
            midprice = self.midpriceCal(((self.my_ask_prices[0][0]+self.my_bid_prices[0][0])/2)/100,self.position/POSITION_LIMIT,self.gamma, self.variance, LIQ_TIME)
            
            new_ask_price=int((midprice+price_adjustment/2+1))
            new_bid_price=int((midprice-price_adjustment/2))

            """print("etf mean ",tmptotmean)
            print("etf total lot ",tmptotallot)
            print("etf variance ",self.variance)
            print("gamma=",self.gamma)
            print("k=",self.k)
            print("price_adjustment=",price_adjustment)
            print("midprice=",midprice)
            print("new_ask_price=",new_ask_price)
            print("new_bid_price=",new_bid_price)"""

            if self.bid_id != 0 and new_bid_price not in (self.bid_price, 0):
                self.send_cancel_order(self.bid_id)
                self.bid_id = 0
            if self.ask_id != 0 and new_ask_price not in (self.ask_price, 0):
                self.send_cancel_order(self.ask_id)
                self.ask_id = 0

            if self.bid_id == 0 and new_bid_price != 0 and self.position < POSITION_LIMIT:
                self.bid_id = next(self.order_ids)
                self.bid_price = new_bid_price
                if (POSITION_LIMIT-self.position)//2!=0:
                    self.send_insert_order(self.bid_id, Side.BUY, new_bid_price*100, (POSITION_LIMIT-self.position)//2, Lifespan.GOOD_FOR_DAY)
                self.bids.add(self.bid_id)

            if self.ask_id == 0 and new_ask_price != 0 and self.position > -POSITION_LIMIT:
                self.ask_id = next(self.order_ids)
                self.ask_price = new_ask_price
                if (POSITION_LIMIT+self.position)//2!=0:
                    self.send_insert_order(self.ask_id, Side.SELL, new_ask_price*100, (POSITION_LIMIT+self.position)//2, Lifespan.GOOD_FOR_DAY)
                self.asks.add(self.ask_id)

    def on_order_filled_message(self, client_order_id: int, price: int, volume: int) -> None:
        """Called when one of your orders is filled, partially or fully.

        The price is the price at which the order was (partially) filled,
        which may be better than the order's limit price. The volume is
        the number of lots filled at that price.
        """
        self.logger.info("received order filled for order %d with price %d and volume %d", client_order_id,
                         price, volume)
        if client_order_id in self.bids:
            self.position += volume
            self.send_hedge_order(next(self.order_ids), Side.ASK, MIN_BID_NEAREST_TICK, volume)
        elif client_order_id in self.asks:
            self.position -= volume
            self.send_hedge_order(next(self.order_ids), Side.BID, MAX_ASK_NEAREST_TICK, volume)

    def on_order_status_message(self, client_order_id: int, fill_volume: int, remaining_volume: int,
                                fees: int) -> None:
        """Called when the status of one of your orders changes.

        The fill_volume is the number of lots already traded, remaining_volume
        is the number of lots yet to be traded and fees is the total fees for
        this order. Remember that you pay fees for being a market taker, but
        you receive fees for being a market maker, so fees can be negative.

        If an order is cancelled its remaining volume will be zero.
        """
        self.logger.info("received order status for order %d with fill volume %d remaining %d and fees %d",
                         client_order_id, fill_volume, remaining_volume, fees)
        if remaining_volume == 0:
            if client_order_id == self.bid_id:
                self.bid_id = 0
            elif client_order_id == self.ask_id:
                self.ask_id = 0

            # It could be either a bid or an ask
            self.bids.discard(client_order_id)
            self.asks.discard(client_order_id)

    def on_trade_ticks_message(self, instrument: int, sequence_number: int, ask_prices: List[int],
                               ask_volumes: List[int], bid_prices: List[int], bid_volumes: List[int]) -> None:
        """Called periodically when there is trading activity on the market.

        The five best ask (i.e. sell) and bid (i.e. buy) prices at which there
        has been trading activity are reported along with the aggregated volume
        traded at each of those price levels.

        If there are less than five prices on a side, then zeros will appear at
        the end of both the prices and volumes arrays.
        """
        self.logger.info("received trade ticks for instrument %d with sequence number %d", instrument,
                         sequence_number)
