import threading
import json
import time

from urllib3 import PoolManager
from urllib.parse import urlencode
from argparse import ArgumentParser, RawDescriptionHelpFormatter

HOST = "https://www.simplicialsoftware.com"
GET_PLAYER_PROFILE_URI = "/api/account/GetPlayerProfile"
LOGIN_TICKET = ""

pdata_get_player_profile = {
    'Game': 'Nebulous',
    'Version': 1065,
    'Ticket': LOGIN_TICKET,
    'accountID': 0
}
headers = {
    'Accept-Encoding': 'gzip',
    'Content-Type': 'application/x-www-form-urlencoded'
}

manager = PoolManager(headers = headers)
parser = ArgumentParser(description = "Become a celebrity on Nebulous.", epilog = "https://www.github.com/Anthy1x")

work = True
lock = threading.Lock()
total_views = 0

def do_work(quota):
    global total_views

    _quota = quota

    method = 'POST'
    body = urlencode(pdata_get_player_profile)
    url = HOST + GET_PLAYER_PROFILE_URI

    while work and quota > 0:
        manager.urlopen(method, url, body = body)

        quota -= 1

    with lock:
        total_views += _quota - quota

def main():
    global work

    parser.add_argument('-t', '--threads', help = "Number of threads(workers) to use.", default = 8, dest = 'threads', type = int)
    parser.add_argument('account_id', help = "Nebulous account ID to give the views to.", type = int)
    parser.add_argument('-v', '--views', help = "The number of views to work towards.", default = 2000, type = int)

    args = parser.parse_args()
    threshold = args.views

    print("[ + ] Running %d bots for user '%d'..." % (args.threads, args.account_id))

    pdata_get_player_profile['accountID'] = args.account_id
    work_quota, rem = divmod(args.views, args.threads)
    workers = []

    try:
        for i in range(args.threads):
            worker = threading.Thread(target = do_work, args = [work_quota])

            worker.daemon = True

            worker.start()
            workers.append(worker)

        while (total_views + rem) != args.views:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        work = False

        for worker in workers:
            worker.join()

        print("[ + ] Total views gained: %d." % total_views)

        return

    print("[ + ] Done.")

main()
