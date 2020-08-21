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
    'accountID': 100
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

# not really the best way to validate but it should get the job done
def invalid_ticket():
    resp = manager.urlopen('POST', HOST + GET_PLAYER_PROFILE_URI, body = urlencode(pdata_get_player_profile))
    data = json.loads(resp.data.decode('utf-8'))

    return 'Message' in data and data['Message'] == "An error has occurred."

def do_work(quota):
    global total_views

    method = 'POST'
    body = urlencode(pdata_get_player_profile)
    url = HOST + GET_PLAYER_PROFILE_URI

    while work and quota > 0:
        manager.urlopen(method, url, body = body)

        with lock:
            total_views += 1

        quota -= 1

def print_stats(quota):
    global total_views

    old_views = 0

    while work and total_views != quota:
        with lock:
            print("[ + ] Gained: %d(%d/s)" % (total_views, max(total_views - old_views, 0)), end = '\r')

            old_views = total_views

        time.sleep(1)

def main():
    global work

    parser.add_argument('-t', '--threads', help = "Number of threads(workers) to use.", default = 8, dest = 'threads', type = int)
    parser.add_argument('account_id', help = "Nebulous account ID to give the views to.", type = int)
    parser.add_argument('-v', '--views', help = "The number of views to work towards.", default = 2000, type = int)

    args = parser.parse_args()
    threshold = args.views

    if not LOGIN_TICKET:
        print("[ ! ] LOGIN_TICKET is empty. Please add a login ticket!")

        return

    if invalid_ticket():
        print("[ ! ] Invalid login ticket! Make sure there are no extra/missing characters in the login ticket.")

        return

    if args.account_id == int(LOGIN_TICKET.split(',')[0]):
        print("[ ! ] You can't give yourself views. Please use a different login ticket if you wish to give yourself views.")

        return

    print("[ + ] Running %d bots for user '%d'..." % (args.threads, args.account_id))

    pdata_get_player_profile['accountID'] = args.account_id
    work_quota, rem = divmod(args.views, args.threads)
    stat_thread = threading.Thread(target = print_stats, args = [args.views - rem])
    workers = []

    try:
        for i in range(args.threads):
            worker = threading.Thread(target = do_work, args = [work_quota])

            worker.daemon = True

            worker.start()
            workers.append(worker)

        stat_thread.daemon = True
        stat_thread.start()

        while (total_views + rem) != args.views:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        work = False

        for worker in workers:
            worker.join()

        stat_thread.join()

        print("\n[ + ] Total views gained: %d." % total_views)

        return

    print("\n[ + ] Done.")

main()
