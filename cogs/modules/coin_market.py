from coinmarketcap import Market

fiat_currencies = {
    'AUD': '$', 'BRL': 'R$', 'CAD': '$', 'CHF': 'Fr.',
    'CLP': '$', 'CNY': '¥', 'CZK': 'Kc', 'DKK': 'kr',
    'EUR': '€', 'GBP': '£', 'HKD': 'HK$', 'HUF': 'Ft',
    'IDR': 'Rp ', 'ILS': '₪', 'INR': '₹', 'JPY': '¥‎',
    'KRW': '₩', 'MXN': '$', 'MYR': 'RM', 'NOK': 'kr',
    'NZD': '$', 'PHP': '₱', 'PKR': 'Rupees', 'PLN': 'zł',
    'RUB': '₽', 'SEK': 'kr', 'SGD': 'S$', 'THB': '฿',
    'TRY': '₺', 'TWD': 'NT$', 'ZAR': 'R ', 'USD': '$'
}

fiat_suffix = [
    'CZK', 'DKK', 'HUF',
    'NOK', 'PKR', 'RUB',
    'SEK'
]


class CurrencyException(Exception):
    """Exception class for invalid currencies"""


class FiatException(Exception):
    """Exception class for invalid fiat"""


class MarketStatsException(Exception):
    """Exception class for invalid retrieval of market stats"""


class CoinMarketException(Exception):
    """Exception class for CoinMarket"""


class CoinMarket:
    """
    Handles CoinMarketCap API features
    """
    def __init__(self):
        """
        Initiates CoinMarket

        @param bot - discord bot object
        """
        self.market = Market()

    def _fiat_check(self, fiat):
        """
        Checks if fiat is valid. If invalid, raise FiatException error.

        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        """
        if fiat is not fiat.upper():
            fiat = fiat.upper()
        if fiat not in fiat_currencies:
            error_msg = "This currency is not supported: {}.".format(fiat)
            raise FiatException(error_msg)
        return fiat

    def _fetch_currency_data(self, currency, fiat):
        """
        Fetches the currency data based on the desired currency

        @param currency - the cryptocurrency to search for (i.e. 'bitcoin', 'ethereum')
        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        @return - currency data
        """
        try:
            return self.market.ticker(currency, convert=fiat)
        except Exception:
            raise CurrencyException("Failed to find currency: {}. Check if "
                                    "this currency is valid and also check for "
                                    "spelling errors.".format(currency))

    def _format_currency_data(self, data, fiat):
        """
        Formats the data fetched

        @param currency - the cryptocurrency to search for (i.e. 'bitcoin', 'ethereum')
        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        @return - formatted currency data
        """
        try:
            isPositivePercent = True
            formatted_data = ''
            hour_trend = ''
            if float(data['percent_change_1h']) >= 0:
                hour_trend = ':arrow_upper_right:'
            else:
                hour_trend = ':arrow_lower_right:'
                isPositivePercent = False

            formatted_data += '__**#{}. {} ({})**__ {}\n'.format(data['rank'], data['name'], data['symbol'], hour_trend)
            if fiat in fiat_suffix:
                formatted_data += 'Price ({}): **{:,} {}**\n'.format(fiat, float(data['price_{}'.format(fiat.lower())]), fiat_currencies[fiat])
            else:
                formatted_data += 'Price ({}): **{}{:,}**\n'.format(fiat, fiat_currencies[fiat], float(data['price_{}'.format(fiat.lower())]))
            formatted_data += 'Price (BTC): **{:,}**\n'.format(float(data['price_btc']))
            if (data['market_cap_usd'] is None):
                formatted_data += 'Market Cap (USD): Unknown\n'
            else:
                formatted_data += 'Market Cap (USD): **${:,}**\n'.format(float(data['market_cap_usd']))
            if (data['available_supply'] is None):
                formatted_data += 'Available Supply: Unknown\n'
            else:
                formatted_data += 'Available Supply: **{:,}**\n'.format(float(data['available_supply']))
            formatted_data += 'Percent Change (1H): **{}%**\n'.format(data['percent_change_1h'])
            formatted_data += 'Percent Change (24H): **{}%**\n'.format(data['percent_change_24h'])
            formatted_data += 'Percent Change (7D): **{}%**\n'.format(data['percent_change_7d'])

            return formatted_data, isPositivePercent
        except Exception as e:
            print("Failed to format data: {}".format(e))

    async def get_currency(self, currency, fiat):
        """
        Obtains the data of the specified currency and returns them.

        @param currency - the cryptocurrency to search for (i.e. 'bitcoin', 'ethereum')
        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        """
        try:
            isPositivePercent = False
            fiat = self._fiat_check(fiat)
            data = self._fetch_currency_data(currency, fiat)[0]
            formatted_data, isPositivePercent = self._format_currency_data(data, fiat)
            return formatted_data, isPositivePercent
        except CurrencyException as e:
            raise
        except FiatException as e:
            raise
        except Exception as e:
            raise CoinMarketException(e)

    def _fetch_coinmarket_stats(self, fiat):
        """
        Fetches the coinmarket stats

        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        @return - market stats
        """
        try:
            return self.market.stats(convert=fiat)
        except Exception as e:
            raise MarketStatsException("Unable to retrieve crypto market stats "
                                       "at this time.")

    def _format_coinmarket_stats(self, stats, fiat):
        """
        Receives and formats coinmarket stats

        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        @return - formatted stats
        """
        try:
            formatted_stats = ''
            if (stats['total_market_cap_usd'] is None):
                formatted_stats += "Total Market Cap (USD): Unknown"
            else:
                if fiat in fiat_suffix:
                    formatted_stats += "Total Market Cap ({}): **{:,} {}**\n".format(fiat, float(stats['total_market_cap_{}'.format(fiat.lower())]), fiat_currencies[fiat])
                else:
                    formatted_stats += "Total Market Cap ({}): **{}{:,}**\n".format(fiat, fiat_currencies[fiat], float(stats['total_market_cap_{}'.format(fiat.lower())]))
            formatted_stats += "Bitcoin Percentage of Market: **{:,}%**\n".format(stats['bitcoin_percentage_of_market_cap'])
            formatted_stats += "Active Markets: **{:,}**\n".format(stats['active_markets'])
            formatted_stats += "Active Currencies: **{:,}**\n".format(stats['active_currencies'])
            formatted_stats += "Active Assets: **{:,}**\n".format(stats['active_assets'])

            return formatted_stats
        except Exception as e:
            print("Failed to format data: {}".format(e))

    async def get_stats(self, fiat):
        """
        Returns the market stats

        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        """
        try:
            fiat = self._fiat_check(fiat)
            stats = self._fetch_coinmarket_stats(fiat)
            formatted_stats = self._format_coinmarket_stats(stats, fiat)
            return formatted_stats
        except FiatException as e:
            raise
        except MarketStatsException as e:
            raise
        except Exception as e:
            raise CoinMarketException(e)

    async def get_multiple_currency(self, currency_list, fiat):
        """
        Returns updated info of multiple coin stats

        @param currency_list - list of cryptocurrencies
        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        """
        try:
            fiat = self._fiat_check(fiat)
            formatted_data = ''
            data_list = []
            for currency in currency_list:
                data_list.append(self._fetch_currency_data(currency, fiat)[0])
            data_list.sort(key=lambda x: int(x['rank']))
            for data in data_list:
                formatted_data += self._format_currency_data(data, fiat)[0] + '\n'
            return formatted_data
        except CurrencyException as e:
            raise
        except FiatException as e:
            raise
        except Exception as e:
            raise CoinMarketException(e)
