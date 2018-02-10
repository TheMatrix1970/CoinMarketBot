from bot_logger import logger
from cogs.modules.coin_market import CurrencyException, FiatException
from collections import defaultdict
from discord.errors import Forbidden
import discord
import json


class AlertFunctionality:
    """Handles Alert Command functionality"""

    def __init__(self, bot, coin_market, alert_capacity):
        self.bot = bot
        self.coin_market = coin_market
        self.alert_capacity = alert_capacity
        self.market_list = ""
        self.acronym_list = ""
        self.supported_operators = ["<", ">", "<=", ">="]
        self.alert_data = self._check_alert_file()
        self._save_alert_file(self.alert_data, backup=True)

    def update(self, market_list, acronym_list):
        """
        Updates utilities with new coin market data
        """
        self.market_list = market_list
        self.acronym_list = acronym_list

    def _check_alert_file(self):
        """
        Checks to see if there's a valid alerts.json file
        """
        try:
            with open('alerts.json') as alerts:
                return json.load(alerts)
        except FileNotFoundError:
            self._save_alert_file()
            return json.loads('{}')
        except Exception as e:
            print("An error has occured. See error.log.")
            logger.error("Exception: {}".format(str(e)))

    def _translate_operation(self, operator):
        """
        Translates the supported operations for alerts
        into english

        @param operator - operator condition to notify the channel
        """
        if operator in self.supported_operators:
            if operator == "<":
                operator_translation = "less than"
            elif operator == "<=":
                operator_translation = "less than or equal to"
            elif operator == ">":
                operator_translation = "greater than"
            elif operator == ">=":
                operator_translation = "greater than or equal to"
            return operator_translation
        else:
            raise Exception("Unable to translate operation.")

    def _check_alert(self, currency, operator, user_value, fiat, kwargs=None):
        """
        Checks if the alert condition isn't true

        @param currency - cryptocurrency to set an alert of
        @param operator - operator condition to notify the channel
        @param user_value - price or percent for condition to compare
        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        @return - True if condition doesn't exist, False if it does
        """
        if self.market_list is None:
            return True
        if currency in self.market_list:
            if kwargs:
                if "hour" in kwargs:
                    market_value = float(self.market_list[currency]["percent_change_1h"])
                elif "day" in kwargs:
                    market_value = float(self.market_list[currency]["percent_change_24h"])
                elif "week" in kwargs:
                    market_value = float(self.market_list[currency]["percent_change_7d"])
                else:
                    raise Exception("Unsupported percent change format.")
            else:
                market_value = float(self.market_list[currency]["price_usd"])
                market_value = float(self.coin_market.format_price(market_value,
                                                                   fiat,
                                                                   False))
            if operator in self.supported_operators:
                if operator == "<":
                    if market_value < float(user_value):
                        return False
                elif operator == "<=":
                    if market_value <= float(user_value):
                        return False
                elif operator == ">":
                    if market_value > float(user_value):
                        return False
                elif operator == ">=":
                    if market_value >= float(user_value):
                        return False
                return True
            else:
                raise Exception("Operator not supported: {}".format(operator))
        else:
            return False

    async def _say_msg(self, msg=None, channel=None, emb=None):
        """
        Bot will say msg if given correct permissions

        @param msg - msg to say
        @param channel - channel to send msg to
        @param emb - embedded msg to say
        """
        try:
            if channel:
                if emb:
                    await self.bot.send_message(channel, embed=emb)
                else:
                    await self.bot.send_message(channel, msg)
            else:
                if emb:
                    await self.bot.say(embed=emb)
                else:
                    await self.bot.say(msg)
        except:
            pass

    async def add_alert(self, ctx, currency, operator, user_value, fiat, **kwargs):
        """
        Adds an alert to alerts.json

        @param currency - cryptocurrency to set an alert of
        @param operator - operator condition to notify the channel
        @param user_value - price or percent for condition to compare
        @param fiat - desired fiat currency (i.e. 'EUR', 'USD')
        """
        try:
            alert_num = None
            ucase_fiat = self.coin_market.fiat_check(fiat)
            if currency.upper() in self.acronym_list:
                currency = self.acronym_list[currency.upper()]
                if "Duplicate" in currency:
                    await self._say_msg(currency)
                    return
            if currency not in self.market_list:
                raise CurrencyException("Currency is invalid: ``{}``".format(currency))
            try:
                if not self._check_alert(currency, operator, user_value, ucase_fiat, kwargs):
                    await self._say_msg("Failed to create alert. Current price "
                                        "of **{}** already meets the condition."
                                        "".format(currency.title()))
                    return
            except Exception:
                await self._say_msg("Invalid operator: **{}**".format(operator))
                return
            user_id = ctx.message.author.id
            if user_id not in self.alert_data:
                self.alert_data[user_id] = {}
            for i in range(1, len(self.alert_data[user_id]) + 2):
                if str(i) not in self.alert_data[user_id]:
                    alert_num = str(i)
            if alert_num is None:
                raise Exception("Something went wrong with adding alert.")
            alert_cap = int(self.alert_capacity)
            if int(alert_num) > alert_cap:
                await self.bot.say("Unable to add alert, user alert capacity of"
                                   " **{}** has been reached.".format(alert_cap))
                return
            alert_list = self.alert_data[user_id]
            alert_list[alert_num] = {}
            channel_alert = alert_list[alert_num]
            channel_alert["currency"] = currency
            if operator in self.supported_operators:
                channel_alert["operation"] = operator
            else:
                await self._say_msg("Invalid operator: {}. Your choices are **<*"
                                    "*, **<=**, **>**, or **>=**"
                                    "".format(operator))
                return
            if kwargs:
                channel_alert["percent"] = ("{}".format(user_value)).rstrip('0')
                for arg in kwargs:
                    channel_alert["percent_change"] = arg
            else:
                channel_alert["price"] = ("{:.6f}".format(user_value)).rstrip('0')
                if channel_alert["price"].endswith('.'):
                    channel_alert["price"] = channel_alert["price"].replace('.', '')
            channel_alert["fiat"] = ucase_fiat
            self._save_alert_file(self.alert_data)
            await self._say_msg("Alert has been set.")
        except CurrencyException as e:
            logger.error("CurrencyException: {}".format(str(e)))
            await self._say_msg(str(e))
        except FiatException as e:
            logger.error("FiatException: {}".format(str(e)))
            await self._say_msg(str(e))
        except Exception as e:
            print("An error has occured. See error.log.")
            logger.error("Exception: {}".format(str(e)))

    def _save_alert_file(self, alert_data={}, backup=False):
        """
        Saves alerts.json file
        """
        if backup:
            alert_filename = "alerts_backup.json"
        else:
            alert_filename = "alerts.json"
        with open(alert_filename, 'w') as outfile:
            json.dump(alert_data,
                      outfile,
                      indent=4)

    async def remove_alert(self, ctx, alert_num):
        """
        Removes an alert from the user's list of alerts

        @param ctx - context of the command sent
        @param alert_num - number of the specific alert to remove
        """
        try:
            user_id = ctx.message.author.id
            user_list = self.alert_data
            alert_list = user_list[user_id]
            if alert_num in alert_list:
                removed_alert = alert_num
                alert_setting = alert_list[alert_num]
                alert_currency = alert_setting["currency"]
                alert_operation = self._translate_operation(alert_setting["operation"])
                if "percent" in alert_setting:
                    alert_percent = alert_setting["percent"]
                    if alert_percent.endswith('.'):
                        alert_percent = alert_percent.replace('.', '')
                    alert_value = "{}%".format(alert_percent)
                else:
                    alert_value = alert_setting["price"]
                alert_fiat = alert_setting["fiat"]
                alert_list.pop(str(alert_num))
                self._save_alert_file(self.alert_data)
                await self._say_msg("Alert **{}** where **{}** is **{}** **{}** "
                                    "in **{}** was successfully "
                                    "removed.".format(removed_alert,
                                                      alert_currency,
                                                      alert_operation,
                                                      alert_value,
                                                      alert_fiat))
            else:
                await self._say_msg("The number you've entered does not exist "
                                    "in the alert list. Use `$geta` to receive "
                                    "a list of ongoing alerts.")
        except Forbidden:
            pass
        except CurrencyException as e:
            logger.error("CurrencyException: {}".format(str(e)))
            await self._say_msg(str(e))
        except Exception as e:
            print("An error has occured. See error.log.")
            logger.error("Exception: {}".format(str(e)))

    async def get_alert_list(self, ctx):
        """
        Gets the list of alerts and displays them

        @param ctx - context of the command sent
        """
        try:
            user_id = ctx.message.author.id
            user_list = self.alert_data
            msg = {}
            result_msg = ""
            if user_id in user_list:
                alert_list = user_list[user_id]
                if len(alert_list) != 0:
                    for alert in alert_list:
                        currency = alert_list[alert]["currency"].title()
                        operation = self._translate_operation(alert_list[alert]["operation"])
                        if "percent" in alert_list[alert]:
                            alert_percent = alert_list[alert]["percent"]
                            if alert_percent.endswith('.'):
                                alert_percent = alert_percent.replace('.', '')
                            alert_value = "{}%".format(alert_percent)
                        else:
                            alert_value = alert_list[alert]["price"]
                        msg[int(alert)] = ("[**{}**] Alert when **{}** is "
                                           "**{}** **{}** "
                                           "".format(alert,
                                                     currency,
                                                     operation,
                                                     alert_value))
                        if "percent_change" in alert_list[alert]:
                            if "hour" == alert_list[alert]["percent_change"]:
                                msg[int(alert)] += "(**1h**)\n"
                            elif "day" == alert_list[alert]["percent_change"]:
                                msg[int(alert)] += "(**24h**)\n"
                            elif "week" == alert_list[alert]["percent_change"]:
                                msg[int(alert)] += "(**7d**)\n"
                        else:
                            msg[int(alert)] += ("in **{}**\n"
                                                "".format(alert_list[alert]["fiat"]))
                    for line in sorted(msg):
                        result_msg += msg[line]
                    color = 0x00FF00
                else:
                    result_msg = "Channel does not have any alerts to display."
                    color = 0xD14836
            else:
                result_msg = "User never created any alerts."
                color = 0xD14836
            em = discord.Embed(title="Alerts",
                               description=result_msg,
                               colour=color)
            await self.bot.say(embed=em)
        except Forbidden:
            pass
        except CurrencyException as e:
            logger.error("CurrencyException: {}".format(str(e)))
            await self._say_msg(str(e))
        except Exception as e:
            print("An error has occured. See error.log.")
            logger.error("Exception: {}".format(str(e)))

    async def alert_user(self):
        """
        Checks and displays alerts that have met the condition of the
        cryptocurrency price
        """
        try:
            percent_change = {}
            raised_alerts = defaultdict(list)
            for user in self.alert_data:
                alert_list = self.alert_data[str(user)]
                for alert in alert_list:
                    alert_currency = alert_list[alert]["currency"]
                    operator_symbol = alert_list[alert]["operation"]
                    if "percent" in alert_list[alert]:
                        alert_value = alert_list[alert]["percent"]
                        if alert_value.endswith('.'):
                            alert_value = alert_value.replace('.', '')
                    else:
                        alert_value = alert_list[alert]["price"]
                    alert_fiat = alert_list[alert]["fiat"]
                    if "percent_change" in alert_list[alert]:
                        percent_change[alert_list[alert]["percent_change"]] = True
                    if not self._check_alert(alert_currency, operator_symbol,
                                             alert_value, alert_fiat,
                                             percent_change):
                        alert_operator = self._translate_operation(operator_symbol)
                        raised_alerts[user].append(alert)
                        user_obj = await self.bot.get_user_info(user)
                        if alert_currency in self.market_list:
                            msg = ("**{}** is **{}** **{}%** "
                                   "".format(alert_currency.title(),
                                             alert_operator,
                                             alert_value))
                            if "percent_change" in alert_list[alert]:
                                if "hour" == alert_list[alert]["percent_change"]:
                                    msg += "(**1h**)\n"
                                elif "day" == alert_list[alert]["percent_change"]:
                                    msg += "(**24h**)\n"
                                elif "week" == alert_list[alert]["percent_change"]:
                                    msg += "(**7d**)\n"
                            else:
                                msg += "**{}**".format(alert_fiat)
                        else:
                            msg = ("**{}** is no longer a valid currency "
                                   "according to the coinmarketapi api. Alerts "
                                   "related to this currency will be removed."
                                   "".format(alert_currency.title()))
                        em = discord.Embed(title="Alert **{}**".format(alert),
                                           description=msg,
                                           colour=0xFF9900)
                        await self._say_msg(channel=user_obj, emb=em)
            if raised_alerts:
                for user in raised_alerts:
                    for alert_num in raised_alerts[user]:
                        self.alert_data[user].pop(str(alert_num))
                self._save_alert_file(self.alert_data)
        except Exception as e:
            print("An error has occured. See error.log.")
            logger.error("Exception: {}".format(str(e)))
