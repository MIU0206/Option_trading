def put_call_parity(self):
        if time.time() - self.last_time >= 15:
            self.last_time = time.time()
            self.limit_close()
        strategy = [2,3]
        for st in strategy:
            # strike_parity
            if st == 2:
                index = self.ins2index["UBIQ"]
                price = self.md_list[index][-1]
                S_ask = price.AskPrice1
                S_bid = price.BidPrice1
                S_ave = (S_ask + S_bid) / 2
                K = self.options_prices*2

                down_price = S_ave * 0.90
                up_price = S_ave * 1.10
                down_strike = -1
                up_strike = -1
                for i in range(1, 36):
                    if K[i] >= down_price and K[i - 1] < down_price:
                        down_strike = i
                    if K[i] >= up_price and K[i - 1] < up_price:
                        up_strike = i
                for i in range(down_strike, up_strike):
                    strike = K[i]
                    ins_call = self.instruments[i]
                    index_call = self.ins2index[ins_call.InstrumentID]
                    om_call = self.ins2om[ins_call.InstrumentID]
                    ins_put = self.instruments[i + 36]
                    index_put = self.ins2index[ins_put.InstrumentID]
                    om_put = self.ins2om[ins_put.InstrumentID]

                    ask_call = self.md_list[index_call][-1].AskPrice1
                    ask_put = self.md_list[index_put][-1].AskPrice1
                    bid_call = self.md_list[index_call][-1].BidPrice1
                    bid_put = self.md_list[index_put][-1].BidPrice1
                    mid_call = (ask_call + ask_put) / 2
                    mid_put = (ask_put + bid_put) / 2

                    sign_ask = ask_call - ask_put + strike - S_ask
                    sign_put = bid_call - bid_put + strike - S_bid

                    threshold = 0.02
                    varity = 1

                    print(sign_ask, sign_put)
                    if sign_ask > threshold and sign_put > threshold:
                        # and sign_ask < max_threshold and sign_put < max_threshold:
                        print('call unbalance')

                        om = self.ins2om[ins_put.InstrumentID]
                        order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                     max(bid_put + 0.001, 0.001), 30)
                        self.send_input_order(order)
                        self.parity_order_list.append([time.time(), order])
                        om = self.ins2om[ins_call.InstrumentID]
                        order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                     max(ask_call - 0.001, 0.001), 30)
                        self.send_input_order(order)
                        self.parity_order_list.append([time.time(), order])
                        # time.sleep(0.01)

                    elif sign_ask < -threshold and sign_put < -threshold:
                        print('put unbalance')
                        om = self.ins2om[ins_call.InstrumentID]
                        order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                     max(bid_call + 0.001, 0.001), 20)
                        self.send_input_order(order)
                        self.parity_order_list.append([time.time(), order])

                        om = self.ins2om[ins_put.InstrumentID]
                        order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                     max(ask_put - 0.001, 0.001), 20)
                        self.send_input_order(order)
                        self.parity_order_list.append([time.time(), order])
                        # time.sleep(0.01)
                pos_hold = False
                if pos_hold:
                    new_order = []
                    for pos_time, order in self.parity_order_list:
                        ins = order.InstrumentID
                        stop_time = 3
                        if time.time() - pos_time > stop_time:
                            if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                                self.send_cancel_order(order)
                                print('order calceled')
                            elif order.OrderStatus == PHX_FTDC_OST_AllTraded:
                                print('Order Traded...')
                                pass
                            elif order.OrderStatus == PHX_FTDC_OST_Unknown:
                                new_order.append([pos_time, order])
                                print('Order waiting...')
                                continue
                            elif order.OrderStatus == PHX_FTDC_OST_Error or order.OrderStatus == PHX_FTDC_OST_Canceled:
                                continue
                        else:
                            new_order.append([pos_time, order])

                        index = self.ins2index[ins]
                        # if order.OrderStatus == PHX_FTDC_OST_AllTraded:
                        om = self.ins2om[ins]
                        spread = 3
                        if time.time() - pos_time < stop_time and order.VolumeTraded != 0:
                            cur_price = self.get_bid_ask(index).values[0]
                            benefit = 0.05
                            if order.Direction == "0":
                                if order.OffsetFlag == "0":  # buy open
                                    hold = False
                                    if index < 36:
                                        if order.LimitPrice < 10 - spread - self.instruments[index].StrikePrice:

                                            if om.get_long_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True
                                    else:
                                        if order.LimitPrice < self.instruments[index].StrikePrice - 10 - spread:

                                            if om.get_long_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True

                                    if ~hold and order.LimitPrice < cur_price[12] - benefit:
                                        om = self.ins2om[ins]
                                        order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                            PHX_FTDC_OF_Close,
                                                                            min(cur_price[13], order.VolumeTraded))
                                        self.send_input_order(order_close)
                                        self.order_count += 1
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
                                        self.order_count += 1
                                        new_order.append([time.time(), order_close])
                                        # time.sleep(0.01)
                            elif order.Direction == "1":
                                if order.OffsetFlag == "0":  # sell open
                                    hold = False
                                    if index < 36:
                                        if order.LimitPrice > max(10 - spread - self.instruments[index].StrikePrice,
                                                                  0.02):

                                            if om.get_short_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True
                                    else:
                                        if order.LimitPrice > max(self.instruments[index].StrikePrice - 10 - spread,
                                                                  0.02):
                                            print(om.get_long_position_closeable())
                                            if om.get_short_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True

                                    if ~hold and order.LimitPrice > cur_price[2] + benefit:
                                        om = self.ins2om[ins]
                                        order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                            PHX_FTDC_OF_Close,
                                                                            min(cur_price[3], order.VolumeTraded))
                                        self.send_input_order(order_close)
                                        self.order_count += 1
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
                                        self.order_count += 1
                                        new_order.append([time.time(), order_close])
                                        # time.sleep(0.01)
                        elif time.time() - pos_time >= stop_time and order.OrderPriceType == PHX_FTDC_OPT_LimitPrice and order.VolumeTraded != 0:
                            if order.Direction == "0":
                                if order.OffsetFlag == "0":  # buy open
                                    hold = False
                                    if index < 36:
                                        if order.LimitPrice < 10 - spread - self.instruments[index].StrikePrice:
                                            if om.get_long_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True
                                    else:
                                        if order.LimitPrice < self.instruments[index].StrikePrice - 10 - spread:
                                            if om.get_long_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True
                                    position_should_close = order.VolumeTraded

                                    if ~hold and position_should_close != 0:
                                        om = self.ins2om[ins]
                                        order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                            PHX_FTDC_OF_Close,
                                                                            position_should_close)
                                        self.send_input_order(order_close)
                                        self.order_count += 1
                                        new_order.append([time.time(), order_close])
                                        # time.sleep(0.01)

                                elif order.OffsetFlag == "1":  # buy close
                                    position_should_close = order.VolumeTotalOriginal - order.VolumeTraded
                                    if position_should_close != 0:
                                        om = self.ins2om[ins]
                                        order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                            PHX_FTDC_OF_Close,
                                                                            position_should_close)
                                        self.send_input_order(order_close)
                                        self.order_count += 1
                                        new_order.append([time.time(), order_close])
                                        # time.sleep(0.01)

                            elif order.Direction == "1":
                                if order.OffsetFlag == "0":  # sell open
                                    hold = False
                                    if index < 36:
                                        if order.LimitPrice > max(10 - spread - self.instruments[index].StrikePrice,
                                                                  0.02):
                                            if om.get_short_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True
                                    else:
                                        if order.LimitPrice > max(self.instruments[index].StrikePrice - 10 - spread,
                                                                  0.02):
                                            if om.get_short_position_closeable() < 500:
                                                self.position_order_list.append([pos_time, order])
                                                hold = True
                                    position_should_close = order.VolumeTraded
                                    if ~hold and position_should_close != 0:
                                        om = self.ins2om[ins]
                                        order_close = om.place_market_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                            PHX_FTDC_OF_Close,
                                                                            position_should_close)
                                        self.send_input_order(order_close)
                                        self.order_count += 1
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
                                        self.order_count += 1
                                        new_order.append([time.time(), order_close])
                                        # time.sleep(0.01)

                        self.market_data_updated[self.ins2index[ins]] = False  # reset flag
                    self.is_any_updated = False  # reset flag
                    self.parity_order_list = new_order
            # mom
            elif st == 3:
                K = self.options_prices*2
                index = self.ins2index["UBIQ"]
                price = self.md_list[index][-1]
                S_ask = price.AskPrice1
                S_bid = price.BidPrice1
                S_ave = (S_ask + S_bid) / 2
                self.order_count = len(self.monoto_order_list)
                for i in range(self.inst_num - 1):
                    strike = K[i]
                    ins = self.instruments[i]
                    index = self.ins2index[ins.InstrumentID]
                    om = self.ins2om[ins.InstrumentID]
                    five = self.get_bid_ask(index).values[0]

                    sign_vol = five[3] + five[5] - five[13] - five[15]

                    varity1 = 1
                    varity2 = 1
                    if i < 36:
                        if five[12] > max(S_ave - strike, 0) + varity1:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                         max(five[2] - 0.001, 0.001), 20)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            continue
                        elif five[2] < max(S_ave - strike, 0) - varity2:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                         max(five[12] + 0.001, 0.001), 20)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            continue

                    else:
                        if five[12] > max(strike - S_ave, 0) + varity1:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                         max(five[2] - 0.001, 0.001), 20)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.parity_order_list.append([time.time(), order])
                            continue
                        elif five[2] < max(strike - S_ave, 0) - varity2:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                         max(five[12] + 0.001, 0.001), 20)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            continue

                    if five[2] - five[12] < 0.5:

                        thre = 0.3
                        if five[2] < max(S_ave - strike, 0) - thre and sign_vol < 0:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                         max(five[12] + 0.001, 0.001), 15)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])

                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                         max(five[14] / 3 + five[16] * 2 / 3, 0.001), 30)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            time.sleep(0.4)
                            while order.OrderStatus == PHX_FTDC_OST_Unknown:
                                time.sleep(0.01)
                            if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                                self.send_cancel_order(order)

                        elif five[12] > max(S_ave - strike, 0) + thre and sign_vol > 0:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                         max(five[2] - 0.001, 0.001), 15)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])

                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                         max(five[4] / 3 + five[6] * 2 / 3, 0.001), 30)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            time.sleep(0.4)
                            ti = time.time()
                            while order.OrderStatus == PHX_FTDC_OST_Unknown:
                                time.sleep(0.01)

                            if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                                self.send_cancel_order(order)
                    else:
                        if sign_vol < -20:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                         max(five[12] + 0.001, 0.001), 15)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])

                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                         max(five[14] / 3 + five[16] * 2 / 3, 0.001), 30)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            time.sleep(0.4)
                            while order.OrderStatus == PHX_FTDC_OST_Unknown:
                                time.sleep(0.01)
                            if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                                self.send_cancel_order(order)
                        elif sign_vol > 20:
                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                         max(five[2] - 0.001, 0.001), 15)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])

                            order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                         max(five[4] / 3 + five[6] * 2 / 3, 0.001), 30)
                            self.send_input_order(order)
                            self.order_count += 1
                            self.monoto_order_list.append([time.time(), order])
                            time.sleep(0.4)
                            while order.OrderStatus == PHX_FTDC_OST_Unknown:
                                time.sleep(0.005)
                            if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                                self.send_cancel_order(order)
                new_order = []
                for pos_time, order in self.parity_order_list:
                    ins = order.InstrumentID
                    stop_time = 4
                    if time.time() - pos_time > stop_time:
                        if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                            self.send_cancel_order(order)
                            print('order calceled')
                        elif order.OrderStatus == PHX_FTDC_OST_AllTraded:
                            print('Order Traded...')
                            pass
                        elif order.OrderStatus == PHX_FTDC_OST_Unknown:
                            new_order.append([pos_time, order])
                            print('Order waiting...')
                            continue
                        elif order.OrderStatus == PHX_FTDC_OST_Error or order.OrderStatus == PHX_FTDC_OST_Canceled:
                            continue
                    else:
                        new_order.append([pos_time, order])

                    index = self.ins2index[ins]
                    om = self.ins2om[ins]
                    spread = 3
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
                                    self.order_count += 1
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
                                    self.order_count += 1
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
                                    self.order_count += 1
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
                                    self.order_count += 1
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
                                    self.order_count += 1
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
                                    self.order_count += 1
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
                                    self.order_count += 1
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
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)

                    self.market_data_updated[self.ins2index[ins]] = False  # reset flag
                self.is_any_updated = False  # reset flag
                self.parity_order_list = new_order
            # uniq
            elif st == 4:
                ins = self.instruments[72]
                om = self.ins2om[ins.InstrumentID]
                index = self.ins2index[ins.InstrumentID]
                five = self.get_bid_ask(index).values[0]
                try:
                    five_1 = self.get_bid_ask(index, 2).values[0]
                except:
                    five_1 = [0] * len(five)
                mom_up = 0
                mom_down = 0
                if five[2] < five_1[2]:
                    mom_down = five[3]
                elif five[2] == five_1[2]:
                    mom_down = five[3] - five_1[3]
                if five[12] > five_1[12]:
                    mom_up = five[13]
                elif five[12] == five_1[12]:
                    mom_up = five[13] - five_1[13]

                threshold = 5
                if mom_down > threshold and mom_up < -threshold:
                    order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                 five[2], 50)
                    self.send_input_order(order)
                    self.ubiq_order_list.append([time.time(), order])
                elif mom_down < -threshold and mom_up > threshold:
                    order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                 five[12], 50)
                    self.send_input_order(order)
                    self.ubiq_order_list.append([time.time(), order])
                elif mom_up - mom_down > threshold:
                    order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy, PHX_FTDC_OF_Open,
                                                 five[12], 30)
                    self.send_input_order(order)
                    self.ubiq_order_list.append([time.time(), order])
                elif mom_up - mom_down < -threshold:
                    order = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell, PHX_FTDC_OF_Open,
                                                 five[2], 30)
                    self.send_input_order(order)
                    self.ubiq_order_list.append([time.time(), order])

                new_order = []
                for pos_time, order in self.ubiq_order_list:
                    ins = order.InstrumentID
                    stop_time = 2
                    if time.time() - pos_time > stop_time:
                        if order.OrderStatus == PHX_FTDC_OST_PartTradedQueueing or order.OrderStatus == PHX_FTDC_OST_NoTradeQueueing:
                            self.send_cancel_order(order)
                            print('order calceled')
                        elif order.OrderStatus == PHX_FTDC_OST_AllTraded:
                            print('Order Traded...')
                        elif order.OrderStatus == PHX_FTDC_OST_Unknown:
                            new_order.append([pos_time, order])
                            print('Order waiting...')
                            continue
                        elif order.OrderStatus == PHX_FTDC_OST_Error or order.OrderStatus == PHX_FTDC_OST_Canceled:
                            pass
                    else:
                        new_order.append([pos_time, order])

                    index = self.ins2index[ins]
                    om = self.ins2om[ins]
                    spread = 3
                    cur_price = self.get_bid_ask(index).values[0]
                    if time.time() - pos_time < stop_time and order.VolumeTraded != 0:

                        benefit = 0.02
                        if order.Direction == "0":
                            if order.OffsetFlag == "0":  # buy open

                                if order.LimitPrice < cur_price[12] - benefit:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                       PHX_FTDC_OF_Close,
                                                                       cur_price[12], order.VolumeTraded)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)
                            elif order.OffsetFlag == "1":  # buy close
                                if order.LimitPrice > cur_price[2] + benefit:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                       PHX_FTDC_OF_Close,
                                                                       cur_price[2],
                                                                       order.VolumeTotalOriginal - order.VolumeTraded)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)
                        elif order.Direction == "1":
                            if order.OffsetFlag == "0":  # sell open

                                if order.LimitPrice > cur_price[2] + benefit:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                       PHX_FTDC_OF_Close,
                                                                       cur_price[2], order.VolumeTraded)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)
                            elif order.OffsetFlag == "1":  # sell close
                                if order.LimitPrice < cur_price[12] + benefit:
                                    if order.VolumeTotalOriginal - order.VolumeTraded != 0:
                                        om = self.ins2om[ins]
                                        order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                           PHX_FTDC_OF_Close,
                                                                           cur_price[12],
                                                                           order.VolumeTotalOriginal - order.VolumeTraded)
                                        self.send_input_order(order_close)
                                        self.order_count += 1
                                        new_order.append([time.time(), order_close])
                                        # time.sleep(0.01)
                    elif time.time() - pos_time >= stop_time and order.OrderPriceType == PHX_FTDC_OPT_LimitPrice and order.VolumeTraded != 0:
                        if order.Direction == "0":
                            if order.OffsetFlag == "0":  # buy open

                                position_should_close = order.VolumeTraded

                                if position_should_close != 0:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                       PHX_FTDC_OF_Close, cur_price[12],
                                                                       position_should_close)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)

                            elif order.OffsetFlag == "1":  # sell close
                                position_should_close = order.VolumeTotalOriginal - order.VolumeTraded
                                if position_should_close != 0:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                       PHX_FTDC_OF_Close, cur_price[12],
                                                                       position_should_close)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)

                        elif order.Direction == "1":
                            if order.OffsetFlag == "0":  # sell open
                                position_should_close = order.VolumeTraded
                                if position_should_close != 0:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Buy,
                                                                       PHX_FTDC_OF_Close, cur_price[2],
                                                                       position_should_close)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)

                            elif order.OffsetFlag == "1":  # sell close
                                position_should_close = order.VolumeTotalOriginal - order.VolumeTraded
                                if position_should_close != 0:
                                    om = self.ins2om[ins]
                                    order_close = om.place_limit_order(self.next_order_ref(), PHX_FTDC_D_Sell,
                                                                       PHX_FTDC_OF_Close, cur_price[12],
                                                                       position_should_close)
                                    self.send_input_order(order_close)
                                    self.order_count += 1
                                    new_order.append([time.time(), order_close])
                                    # time.sleep(0.01)

                    self.market_data_updated[self.ins2index[ins]] = False  # reset flag
                self.is_any_updated = False  # reset flag
                self.ubiq_order_list = new_order
