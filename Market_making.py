def get_price_list(self):
        for op in self.instruments[:36]:
            self.options_prices.append(op.StrikePrice)

        for op in self.instruments:
            self.options_names.append(op.InstrumentID)

    def close_all(self):
        # for pos in [72]:
        for pos in range(len(self.instruments)):
            ins = self.instruments[pos]
            om = self.ins2om[ins.InstrumentID]

            bids, asks = om.get_live_orders()
            for order in bids:
                self.send_cancel_order(order)
                # time.sleep(0.01)
            for order in asks:
                self.send_cancel_order(order)
                # time.sleep(0.01)

            long_pos_number = om.get_long_position_closeable()
            short_pos_number=om.get_short_position_closeable()

            self_trade=min(long_pos_number,short_pos_number)

            if long_pos_number>short_pos_number:
                long_pos_number-=self_trade
            else:
                short_pos_number-=self_trade

            while self_trade>0:
                if self_trade>=100:
                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Sell,
                                                  PHX_FTDC_OF_Close, 100)
                    self.send_input_order(order)

                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Buy,
                                                  PHX_FTDC_OF_Close, 100)
                    self.send_input_order(order)
                    self_trade-=100
                else:
                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Sell,
                                                  PHX_FTDC_OF_Close, self_trade)
                    self.send_input_order(order)

                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Buy,
                                                  PHX_FTDC_OF_Close, self_trade)

                    self.send_input_order(order)
                    self_trade =0



            while long_pos_number > 0:
                if long_pos_number >= 100:
                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Sell,
                                                  PHX_FTDC_OF_Close, 100)
                    self.send_input_order(order)
                else:
                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Sell,
                                                  PHX_FTDC_OF_Close,
                                                  long_pos_number)
                    self.send_input_order(order)
                self.market_data_updated[pos] = False
                long_pos_number-=100
                # time.sleep(0.01)

            while short_pos_number > 0:
                if short_pos_number >= 100:
                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Buy,
                                                  PHX_FTDC_OF_Close, 100)
                    self.send_input_order(order)
                else:
                    order = om.place_market_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Buy,
                                                  PHX_FTDC_OF_Close,
                                                  short_pos_number)
                    self.send_input_order(order)
                self.market_data_updated[pos] = False
                short_pos_number-=100
                # time.sleep(0.01)

            self.market_data_updated[pos] = False

        self.is_any_updated = False

        print("Try to close all")
        pass

    def close_market(self):
        # sell_close_pos=[0]*72
        # buy_close_pos=[0]*72
        #
        # while len(self.market_sell_close_order) > 0:
        #     tmp = self.market_sell_close_order.popleft()
        #     vol_remain = tmp.VolumeTotalOriginal - tmp.VolumeTraded
        #     if vol_remain > 0:
        #         sell_close_pos[self.ins2index[tmp.InstrumentID]] += vol_remain
        #
        # while len(self.market_buy_close_order) > 0:
        #     tmp = self.market_buy_close_order.popleft()
        #     vol_remain = tmp.VolumeTotalOriginal - tmp.VolumeTraded
        #     if vol_remain > 0:
        #         buy_close_pos[self.ins2index[tmp.InstrumentID]] += vol_remain
        #
        # # print(buy_close_pos)
        # # print(sell_close_pos)
        #
        # for pos in range(72):
        #     om = self.ins2om[self.options_names[pos]]
        #     while sell_close_pos[pos] > 0:
        #         if sell_close_pos[pos] >= 100:
        #             order = om.place_market_order(self.next_order_ref(),
        #                                           PHX_FTDC_D_Sell,
        #                                           PHX_FTDC_OF_Close, 100)
        #             self.send_input_order(order)
        #         else:
        #             order = om.place_market_order(self.next_order_ref(),
        #                                           PHX_FTDC_D_Sell,
        #                                           PHX_FTDC_OF_Close,
        #                                           sell_close_pos[pos])
        #             self.send_input_order(order)
        #         self.market_sell_close_order.append(order)
        #         self.market_data_updated[pos] = False
        #         sell_close_pos[pos] -= 100
        #         # time.sleep(0.01)
        #
        # for pos in range(72):
        #     om = self.ins2om[self.options_names[pos]]
        #     while buy_close_pos[pos] > 0:
        #         if buy_close_pos[pos] >= 100:
        #             order = om.place_market_order(self.next_order_ref(),
        #                                           PHX_FTDC_D_Buy,
        #                                           PHX_FTDC_OF_Close,
        #                                           100)
        #             self.send_input_order(order)
        #         else:
        #             order = om.place_market_order(self.next_order_ref(),
        #                                           PHX_FTDC_D_Buy,
        #                                           PHX_FTDC_OF_Close,
        #                                           buy_close_pos[pos])
        #             self.send_input_order(order)
        #         self.market_buy_close_order.append(order)
        #         self.market_data_updated[pos] = False
        #         buy_close_pos[pos] -= 100
                # time.sleep(0.01)

        while len(self.market_bid_offer) != 0:
            bid_offer = self.market_bid_offer.pop()
            vol_traded = bid_offer.VolumeTraded
            om = self.ins2om[bid_offer.InstrumentID]
            if vol_traded > 0:
                order = om.place_market_order(self.next_order_ref(),
                                              PHX_FTDC_D_Sell,
                                              PHX_FTDC_OF_Close,
                                              vol_traded )
                self.send_input_order(order)
                self.market_sell_close_order.append(order)
            try:
                self.send_cancel_order(bid_offer)
            except:
                pass
            self.market_data_updated[self.options_names.index(bid_offer.InstrumentID)] = False

        while len(self.market_ask_offer) != 0:
            ask_offer = self.market_ask_offer.pop()
            vol_traded = ask_offer.VolumeTraded
            om = self.ins2om[ask_offer.InstrumentID]
            if vol_traded > 0:
                order = om.place_market_order(self.next_order_ref(),
                                              PHX_FTDC_D_Buy, PHX_FTDC_OF_Close,
                                              vol_traded )
                self.send_input_order(order)
                self.market_buy_close_order.append(order)
            try:
                self.send_cancel_order(ask_offer)
            except:
                pass
            self.market_data_updated[self.options_names.index(ask_offer.InstrumentID)] = False

        self.is_any_updated = False

    def get_intrinsic_price(self,S,ins):
        K=ins.StrikePrice
        In_id=ins.InstrumentID
        if In_id[0]=="C":
            return max(S-K,0.001)
        elif In_id[0]=="P":
            return min(K-S,0.001)

    def market_maker_strategy(self):
        print("Market Maker")
        self.close_market()
        # K = self.options_prices * 2
        index = self.ins2index["UBIQ"]
        ubi_price = self.md_list[index][-1].LastPrice

        price = self.md_list[index][-1]
        S_ask = price.AskPrice1
        S_bid = price.BidPrice1
        S_ave = (S_ask + S_bid) / 2
        tau = self.game_status.CurrGameCycleLeftTime
        r = 0
        price = np.array(self.ubiq_price)[:, 0]
        returns = np.diff(price) / price[:-1]
        sigma = np.std(returns)
        returns = 2 * returns
        sigma = sigma * np.sqrt(2)
        if len(returns) < 10:
            sigma = 0.0001
        K = self.options_prices*2
        op_price = [0.001] * 72
        for i in range(18):
            op_price[i] = bs_call(S_ave, K[i], tau, r, sigma)
        for i in range(36, 54):
            op_price[i] = bs_put(S_ave, K[i], tau, r, sigma)


        down_price = ubi_price * 0.90
        up_price = ubi_price * 1.10
        l_pos = r_pos = -1
        for pos in range(len(self.options_prices)):
            if self.options_prices[pos] >= down_price and l_pos == -1:
                l_pos = pos
            if self.options_prices[pos] <= up_price:
                r_pos = pos

        for yi_wu_option_pos in list(range(l_pos, r_pos + 1)) + list(
                range(l_pos + 36, r_pos + 1 + 36)):

            ins = self.instruments[yi_wu_option_pos]
            om = self.ins2om[ins.InstrumentID]

            current_op_price =self.get_intrinsic_price(ubi_price,ins)

            l=[current_op_price]

            last_op_price = self.md_list[yi_wu_option_pos][-1].LastPrice
            # if abs(last_op_price-current_op_price)<1:
            l.append(last_op_price)
            if last_op_price<=0.001:
                continue

            bid_ask_price = (self.md_list[yi_wu_option_pos][-1].AskPrice1 + self.md_list[yi_wu_option_pos][
                -1].BidPrice1) / 2

            # if abs(bid_ask_price-current_op_price)<1:
            if bid_ask_price>0.001:
                l.append(bid_ask_price)


            bs_price=op_price[yi_wu_option_pos]

            # if abs(bs_price-current_op_price)<0.3:

            if bs_price>0.001:
                l.append(bs_price)

            for current_op_price in l:
                biggest_spread = 0
                if current_op_price < 0.1:
                    biggest_spread = 0.005
                elif current_op_price >= 0.1 and current_op_price < 0.2:
                    biggest_spread = 0.01
                elif current_op_price >= 0.2 and current_op_price < 0.5:
                    biggest_spread = 0.025
                elif current_op_price >= 0.5 and current_op_price <= 1.0:
                    biggest_spread = 0.05
                elif current_op_price > 1.0:
                    biggest_spread = 0.08

                bid_price = current_op_price - (
                        biggest_spread * 1000 *3// 7) / 1000.0
                ask_price = current_op_price + (
                        biggest_spread * 1000 *3 // 7) / 1000.0

                if ask_price <= 0.001 or bid_price <= 0.001:
                    continue

                bid_order = om.place_limit_order(self.next_order_ref(),
                                                 PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                 bid_price, 40)
                self.send_input_order(bid_order)
                self.market_bid_offer.append(bid_order)

                ask_order = om.place_limit_order(self.next_order_ref(),
                                                 PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                 ask_price, 40)
                self.send_input_order(ask_order)
                self.market_ask_offer.append(ask_order)

                self.market_ops.append(yi_wu_option_pos)

                self.market_data_updated[yi_wu_option_pos] = False

            self.is_any_updated = False


    ## Spread_market

    def limit_close(self):
        print("Self traded")
        for pos in range(len(self.instruments)-1):
            ins = self.instruments[pos]
            om = self.ins2om[ins.InstrumentID]

            long_pos_number = om.get_long_position_closeable()
            short_pos_number=om.get_short_position_closeable()

            index = self.ins2index["UBIQ"]
            ubi_price = self.md_list[index][-1].LastPrice

            current_op_price = self.get_intrinsic_price(ubi_price, ins)

            # bid_ask_price = (self.md_list[pos][-1].AskPrice1 + self.md_list[pos][
            #     -1].BidPrice1) / 2

            bid_ask_price=current_op_price

            self_trade=min(long_pos_number,short_pos_number)

            if long_pos_number>short_pos_number:
                long_pos_number-=self_trade
            else:
                short_pos_number-=self_trade

            while self_trade>0:
                if self_trade>100:
                    order = om.place_limit_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Sell,
                                                  PHX_FTDC_OF_Close, bid_ask_price,100)
                    self.send_input_order(order)

                    order = om.place_limit_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Buy,
                                                  PHX_FTDC_OF_Close, bid_ask_price,100)
                    self.send_input_order(order)
                    self_trade-=100
                    self.market_data_updated[pos] = False
                else:
                    order = om.place_limit_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Sell,
                                                  PHX_FTDC_OF_Close, bid_ask_price,int(self_trade))
                    self.send_input_order(order)

                    order = om.place_limit_order(self.next_order_ref(),
                                                  PHX_FTDC_D_Buy,
                                                  PHX_FTDC_OF_Close,bid_ask_price ,int(self_trade))

                    self.send_input_order(order)
                    self_trade =0
                    self.market_data_updated[pos] = False
            self.market_data_updated[pos] = False
        self.is_any_updated = False

    def spread_strategy(self):
        print("Spread")
        if time.time()-self.last_time>=15:
            self.last_time = time.time()
            self.limit_close()
        index = self.ins2index["UBIQ"]
        ubi_price = self.md_list[index][-1].LastPrice

        down_price = ubi_price * 0.91
        up_price = ubi_price * 1.09
        l_pos = r_pos = -1
        for pos in range(len(self.options_prices)):
            if self.options_prices[pos] >= down_price and l_pos == -1:
                l_pos = pos
            if self.options_prices[pos] <= up_price:
                r_pos = pos

        for yi_wu_option_pos in list(range(l_pos, r_pos + 1)) + list(
                range(l_pos + 36, r_pos + 1 + 36)):

            ins = self.instruments[yi_wu_option_pos]
            om = self.ins2om[ins.InstrumentID]

            ask1_price = self.md_list[yi_wu_option_pos][-1].AskPrice1-0.001
            ask1_volume= self.md_list[yi_wu_option_pos][-1].AskVolume1//2
            if ask1_volume>50:
                ask1_volume=50

            bid1_price=self.md_list[yi_wu_option_pos][-1].BidPrice1+0.001
            bid1_volume = self.md_list[yi_wu_option_pos][-1].BidVolume1//2
            if bid1_volume>50:
                bid1_volume=50

            ask1_volume=bid1_volume=min(ask1_volume,bid1_volume)

            if ask1_price-bid1_price>0.0002 and ask1_volume>=1 and bid1_volume>=1:
                bid_order = om.place_limit_order(self.next_order_ref(),
                                                 PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                 bid1_price, bid1_volume)

                self.send_input_order(bid_order)
                self.spread_bid_offer.append([time.time(),bid_order])

                ask_order = om.place_limit_order(self.next_order_ref(),
                                                 PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                 ask1_price, ask1_volume)
                self.send_input_order(ask_order)
                self.spread_ask_offer.append([time.time(),ask_order])

                self.market_data_updated[yi_wu_option_pos] = False

            self.is_any_updated = False

        # 撤单
        new_order = []
        for pos_time, order in self.spread_bid_offer+self.spread_ask_offer:
            ins = order.InstrumentID
            stop_time = 3
            if time.time() - pos_time > stop_time:
                if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                    self.send_cancel_order(order)
                    # print('order calceled')
                elif order.OrderStatus == PHX_FTDC_OST_Error or order.OrderStatus == PHX_FTDC_OST_Canceled or order.OrderStatus == PHX_FTDC_OST_AllTraded:
                    # new_order.append([pos_time,order])
                    # print('Order waiting...')
                    # print(order.OrderStatus)
                    continue
            else:
                new_order.append([pos_time, order])
            om = self.ins2om[ins]

            index = self.ins2index[ins]
            if time.time() - pos_time < stop_time and order.OrderPriceType == PHX_FTDC_OPT_LimitPrice and order.VolumeTraded != 0:
                cur_price = self.get_bid_ask(index).values[0]
                benefit = 0.05
                if order.Direction == "0":
                    if order.OffsetFlag == "0":  # buy open

                        if order.LimitPrice < cur_price[12] - benefit:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                PHX_FTDC_OF_Close,
                                                                min(cur_price[13], order.VolumeTraded))
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)
                    elif order.OffsetFlag == "1":  # buy close
                        if order.LimitPrice > cur_price[2] + benefit:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                PHX_FTDC_OF_Close,
                                                                min(cur_price[3],
                                                                    order.VolumeTotalOriginal - order.VolumeTraded))
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)
                elif order.Direction == "1":
                    if order.OffsetFlag == "0":  # sell open
                        if order.LimitPrice > cur_price[2] + benefit:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                PHX_FTDC_OF_Close,
                                                                min(cur_price[3], order.VolumeTraded))
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)
                    elif order.OffsetFlag == "1":  # sell close
                        if order.LimitPrice < cur_price[12] + benefit:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                PHX_FTDC_OF_Close,
                                                                min([13],
                                                                    order.VolumeTotalOriginal - order.VolumeTraded))
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)
            elif time.time() - pos_time >= stop_time and order.OrderPriceType == PHX_FTDC_OPT_LimitPrice and order.VolumeTraded != 0:
                if order.Direction == "0":
                    if order.OffsetFlag == "0":  # buy open
                        position_should_close = order.VolumeTraded
                        if position_should_close != 0:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                PHX_FTDC_OF_Close,
                                                                position_should_close)
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)

                    elif order.OffsetFlag == "1":  # sell close
                        position_should_close = order.VolumeTotalOriginal - order.VolumeTraded
                        if position_should_close != 0:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                PHX_FTDC_OF_Close,
                                                                position_should_close)
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)

                elif order.Direction == "1":
                    if order.OffsetFlag == "0":  # sell open
                        position_should_close = order.VolumeTraded
                        if position_should_close != 0:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                PHX_FTDC_OF_Close,
                                                                position_should_close)
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)

                    elif order.OffsetFlag == "1":  # buy close
                        position_should_close = order.VolumeTotalOriginal - order.VolumeTraded
                        if position_should_close != 0:
                            om = self.ins2om[ins]
                            order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                PHX_FTDC_OF_Close,
                                                                position_should_close)
                            self.send_input_order(order_close)
                            new_order.append([time.time(), order_close])
                            # time.sleep(0.01)

                self.market_data_updated[self.ins2index[ins]] = False  # reset flag
        self.is_any_updated = False  # reset flag
