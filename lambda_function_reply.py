import os
import sys
import bs4
import requests
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)

CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', None)
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
LINE_USER_ID = os.getenv('LINE_USER_ID', None)
LINE_BOT_API = LineBotApi(CHANNEL_ACCESS_TOKEN)
LINE_HANDLER = WebhookHandler(CHANNEL_SECRET)
LOT_RESULT_URL = "https://takarakuji.rakuten.co.jp/backnumber/loto6/"
SUCCESS_RES = {"statusCode": 200, "body": "Success"}
FAILDED_RES = {"statusCode": 500, "body": "Error"}


def lambda_handler(event, context):

    @LINE_HANDLER.add(MessageEvent, message=TextMessage)
    def message(line_event):
        # 実際の当選番号の取得
        res = requests.get(LOT_RESULT_URL)
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        recent_loto_numbers = [s.text for s in soup.find_all(
            'span', class_='loto-font-large')[:7]]
        recent_loto_numbers_str = " ".join(recent_loto_numbers)

        # ユーザーから受信した当選番号の取得
        user_text = line_event.message.text
        my_numbers = user_text.split(" ")

        # 当選判定
        matched_numbers = set(recent_loto_numbers) & set(my_numbers)
        matched_numbers_length = len(matched_numbers)
        bonus_matched = recent_loto_numbers[-1] in [
            f"({x})" for x in my_numbers]
        if matched_numbers_length == 6:
            send_message = "1等！！！！！"
        elif matched_numbers_length == 5 and bonus_matched:
            send_message = "2等！！！！"
        elif matched_numbers_length == 5:
            send_message = "3等！！！"
        elif matched_numbers_length == 4:
            send_message = "4等！！"
        elif matched_numbers_length == 3:
            send_message = "5等！"
        else:
            send_message = "ハズレ"

        # 返信
        rep = f"{recent_loto_numbers_str}\n{send_message}"
        LINE_BOT_API.reply_message(
            line_event.reply_token, TextSendMessage(text=rep))

    try:
        body = event["body"]
        signature = event["headers"]["x-line-signature"]
        LINE_HANDLER.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        return FAILDED_RES
    except InvalidSignatureError:
        return FAILDED_RES
    return SUCCESS_RES
