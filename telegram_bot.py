import logging
import telegram
import time
from time import sleep
import requests
import datetime
import re

try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError  

def main():
    bot = telegram.Bot('HERE IS A TOKEN')
    try:
        update_id = bot.getUpdates()[0].update_id
    except IndexError:
        update_id = None
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    while True:
        try:
            update_id = telegram_queries_processing(bot, update_id)
        except telegram.TelegramError as e:
            if e.message in ("Bad Gateway", "Timed out"):
                sleep(1)
            elif e.message == "Unauthorized":
                update_id += 1
            else:
                raise e
        except URLError as e:
            sleep(1)

def contestant_in_place(response, place):
    return response.json()['result']['rows'][place]['party']['members'][0]['handle']
            
def telegram_queries_processing(bot, update_id):
    for update in bot.getUpdates(offset=update_id, timeout=10):
        chat_id = update.message.chat_id
        update_id = update.update_id + 1
        message = update.message.text
        if (message == '/upcoming'):
            current_time = int(round(time.time()))
            response = requests.get("http://codeforces.com/api/contest.list?gym=false")
            if (response.status_code != 200):
                return update_id
            list_of_contests = response.json()["result"]
            result = []
            for contest in list_of_contests:
                if (contest['startTimeSeconds'] >= current_time):
                    announce = contest['name'] + " will start at Codeforces in " + \
                    str(datetime.timedelta(seconds=contest['startTimeSeconds'] - current_time))
                    result.append(announce)
            reply = ""
            if (len(result) > 0):
                reply = "\n".join(result)
            else:
                reply = "No upcoming contests"
            bot.sendMessage(chat_id=chat_id, text=reply)
        elif (message[:8] == '/results'):
            numbers = re.findall('[0-9]+', message)
            if (len(numbers) < 2):
                continue
            needed_round_number = int(numbers[0])
            top_number = int(numbers[1])
            response = requests.get("http://codeforces.com/api/contest.list?gym=false")
            if (response.status_code != 200):
                return update_id
            list_of_contests = response.json()["result"]
            reply = ""
            for contest in list_of_contests:
                if (contest['type'] == 'CF'):
                    name = contest['name']
                    round_number = int(re.findall('[0-9]+', name)[0])
                    if (round_number == needed_round_number):
                        if (len(reply) > 0):
                            reply += '\n'
                        reply += name + "\n"
                        contest_id = contest['id']
                        url = 'http://codeforces.com/api/contest.standings?contestId='
                        url += str(contest_id)
                        url += '&from=1&count='
                        url += str(top_number)
                        url += '&showUnofficial=false'
                        response = requests.get(url)
                        status_code = response.status_code
                        if (response.status_code != 200):
                            return update_id
                        if (top_number > 100):
                            reply += 'Only first participants will be showed\n'
                            top_number = 100
                        for place in range(top_number):
                            if (place < len(response.json()['result']['rows'])):
                                reply += str(place + 1) + '. ' + contestant_in_place(response, place) + '\n'
                            else:
                                break
            if (len(reply) == 0):
                reply = "Such contest has not been found"
            bot.sendMessage(chat_id=chat_id, text=reply)

    return update_id

if __name__ == '__main__':
    main()
