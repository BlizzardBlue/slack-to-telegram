# -*- coding: utf-8 -*-
import re
import json
import urllib
import urllib2
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_text(body):
    return re.findall('text=.*', body)[0][5:]


def plus_to_whitespace(text):
    return re.sub('[+]', ' ', text)


def unquote_text(text):
    return urllib.unquote(text)


def uid_to_username(text):
    slack_api_url = 'https://slack.com/api/'
    token = ''  # 여기에 Slack API 토큰을 넣으세요

    if bool(re.search('<@U\w{8}>', text)):
        method = 'users.info'
        uids = re.findall('<@U\w{8}>', text)
        for uid in uids:
            user_info = urllib2.urlopen(slack_api_url + method, urllib.urlencode({
                'token': token,
                'user': uid[2:-1]
            }))
            username = json.load(user_info)['user']['name']
            text = re.sub(uid, '@' + username, text)

    elif bool(re.search('<#C\w{8}>', text)):
        method = 'channels.info'
        uids = re.findall('<#C\w{8}>', text)
        for uid in uids:
            channel_info = urllib2.urlopen(slack_api_url + method, urllib.urlencode({
                'token': token,
                'channel': uid[2:-1]
            }))
            channelname = json.load(channel_info)['channel']['name']
            text = re.sub(uid, '#' + channelname, text)

    return text


def sub_markdown(text):
    # text = re.sub(r"\*(.*)\*$", r"<b>\1</b>", text)
    text = re.sub(r"\*([^\*\s]*)\*", r"<b>\1</b>", text)

    # text = re.sub(r"^_([^_\s]*)_$", r"<i>\1</i>", text)
    text = re.sub(r"_([^_\s]*)_", r"<i>\1</i>", text)

    pre_compile = re.compile(r"`{3}([^`{3}\s].*)`{3}", re.S)
    text = pre_compile.sub(r"<pre>\1</pre>", text)
    # text = re.sub(r"`{3}([^`{3}\s]*)`{3}", r"<pre>\1</pre>", text)

    text = re.sub(r"`{1}([^`{1}\s]*)`{1}", r"<code>\1</code>", text)

    text = re.sub(r"<!([\w]*)>", r"@\1", text)

    # @here
    text = re.sub("<!here\|@here>", "@here", text)

    return text


def lambda_handler(event, context):
    token = re.findall('token=\w*[&]', event['body'])[0][6:-1]
    if token != '':  # 여기에 Slack Outgoing WebHook 토큰을 넣으세요
        return
    # 텔레그램 메시지가 슬랙 채널로 전달된 후, 해당 메시지가 다시 텔레그램으로 전달되는 것을 막음
    if event['body'][-12:] == 'bot_name=ADA':
        return

    logger.info('\nEvent: ' + str(event))
    username = re.findall('user_name=\w*', event['body'])[0][10:]

    body = event['body']
    parsed_text = parse_text(body)
    whitespaced_text = plus_to_whitespace(parsed_text)
    unquoted_text = unquote_text(whitespaced_text.encode('utf-8'))
    uid_replaced_text = uid_to_username(unquoted_text)
    markdown_replaced_text = sub_markdown(uid_replaced_text)
    text = urllib.unquote(markdown_replaced_text).encode('utf-8')

    telegram_bot_token = ''  # 여기에 텔레그램 Bot 토큰을 넣으세요
    chat_id = ''  # 여기에 텔레그램 채널 ID를 넣으세요
    method = '/sendMessage'

    # for logging
    request_url = str(
        "https://api.telegram.org/bot" + telegram_bot_token + method +
        urllib.urlencode({
            'chat_id': chat_id,
            'text': "<code>[슬랙]</code> <b>{}</b>: {}".format(username, text),
            'parse_mode': 'HTML'
        })
    )
    logger.info('\nRequest URL: ' + request_url)

    try:
        urllib2.urlopen(
            "https://api.telegram.org/bot" + telegram_bot_token + method,
            urllib.urlencode({
                'chat_id': chat_id,
                'text': "<code>[슬랙]</code> <b>{}</b>: {}".format(username, text),
                'parse_mode': 'HTML'
            })
        ).read()
    except:
        urllib2.urlopen(
            "https://api.telegram.org/bot" + telegram_bot_token + method,
            urllib.urlencode({
                'chat_id': chat_id,
                'text': "[에러] {}: {}\n----------\n메시지를 전달하는 도중 문제가 발생하였습니다. 메시지가 정상적으로 보이지 않을 수 있습니다.\n\"블블, 여기 에러났어. @blizzardblue\"".format(username, text)
            })
        ).read()
