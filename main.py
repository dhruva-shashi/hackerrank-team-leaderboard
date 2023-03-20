from bottle import get, route, static_file, request, run, template
from threading import Thread
from datetime import datetime
import leaderboard as lb
import urllib.parse
import requests
import time
import math
import os

# Header for the HTTP request to HackerRank API
header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "cookie": "hackerrank_mixpanel_token=70dd0cf4-9390-4d57-8790-715d6a32af23; hrc_l_i=F; _hrank_session=0bac1ce625277e046a097cab8e2749463821cbeef10909229c2e0b73cb90082e0fc2201f66ffd6b387c8239038aacf061cfc923f7813c8e87b7e4ada35529339; session_id=4aie7vvx-1647281358997; _biz_uid=d7df9451f96d4cb0cd3e0b682fdaa414; _biz_sid=48da70; __utma=74197771.584894418.1647281361.1647281361.1647281361.1; __utmc=74197771; __utmz=74197771.1647281361.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _biz_flagsA=%7B%22Version%22%3A1%2C%22ViewThrough%22%3A%221%22%2C%22XDomain%22%3A%221%22%7D; _biz_nA=2; _biz_pendingA=%5B%5D; __utmt=1; __utmb=74197771.6.10.1647281361",
    "if-none-match": "W/\"467d7dec7a3db6d84f3f884165375826\"",
    "sec-ch-ua": "\",\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"99\", \"Google Chrome\";v=\"99\"\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
}


@route('/')
def index():
    return template('index.html', root='.')


@route('/form')
def form():
    return template('form.html', root='.')


@route('/styles/<filename>.css')
def style(filename):
    return static_file(filename+'.css', root='.')


# p contains a dictionary of all the users and the points they score in each problem
p = {}

# last_time contains the timestamp of the latest retrieval of data of a contest from HackerRank API
last_time = {}

# last_val contains the latest data of the leaderboard of a contest in HackerRank
last_val = {}

# invalid_probolem_slugs is set to True if there is any invalid problem slug
invalid_problem_slugs = False

# contest_names contains a mapping of each contest_slug to the contest_name
contest_names = {}


def read_points(contest_slug, problem_slug):
    '''Takes contest slug and problem slug as parameters and returns a dictionary with score of each user'''

    url = 'https://www.hackerrank.com/rest/contests/'+contest_slug+'/challenges/'+problem_slug+'/leaderboard?limit=1000'
    points = requests.get(url, headers=header).json()['models']

    user_points = {}

    for point in points:
        user_points[point['hacker']] = [math.ceil(point['score']), point['time_taken']]

    p[problem_slug] = user_points


def verify_problem_slug(contest_slug, problem_slug):
    '''Takes contest slug and problem slug as parameters and verifies whether the problem exists'''

    url = 'https://www.hackerrank.com/rest/contests/'+contest_slug+'/challenges/'+problem_slug
    problem_response = requests.get(url, headers=header).json()

    if 'error' in problem_response:
        global invalid_problem_slugs
        invalid_problem_slugs = True


def timestamp_to_hour(ts):
    '''Returns a string which consists of the time in H:MM:SS format'''
    res = '%d:'%(ts//3600)

    if (ts%3600)//60 < 9:
        res += '0'
    res += '%d:'%((ts%3600)//60)

    if (ts%3600)%60 < 9:
        res += '0'
    res += '%d'%((ts%3600)%60)

    return res


@get('/generate-link')
def generate_link():
    try:
        contest_slug = request.query['contest_slug']
        problem_slugs = request.query['problem_slugs'].split('\n')
        teams_url = request.query['teams_url']

        # Remove empty lines
        while '' in problem_slugs:
            problem_slugs.remove('')

        contest_response = requests.get('https://hackerrank.com/rest/contests/'+contest_slug, headers=header).json()

        # If there is an error in the response, then the contest slug is not valid
        if 'error' in contest_response:
            return {'ok': False, 'error': 'Bad contest slug'}

        threads = []

        global invalid_problem_slugs
        invalid_problem_slugs = False

        # For each problem slug, verify whether it exists
        for problem_slug in problem_slugs:
            thread = Thread(target=verify_problem_slug, args=(contest_slug, problem_slug))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # If invalid_problem_slugs is True, then one of the problem slugs is not valid
        if invalid_problem_slugs:
            return {'ok': False, 'error': 'Bad problem slug'}

        # Return the URL of the leaderboard
        return_url = '?contest_slug='+urllib.parse.quote(contest_slug)
        return_url += '&problem_slugs='+urllib.parse.quote(str(problem_slugs))
        return_url += '&teams_url='+urllib.parse.quote(str(teams_url))

        if os.environ.get('APP_LOCATION') == 'heroku':
            return {'ok': True, 'leaderboard-link': 'https://hackerrank-team-leaderboard.herokuapp.com/leaderboard'+return_url}
        else:
            return {'ok': True, 'leaderboard-link': 'http://localhost:8080/leaderboard'+return_url}

    except Exception as e:
        return {'ok': False, 'error': str(e)}


@route('/leaderboard')
def leaderboard():
    try:
        contest_slug = request.query['contest_slug']
        problem_slugs = eval(request.query['problem_slugs'])
        teams = requests.get(request.query['teams_url']).json()

        if contest_slug in contest_names:
            contest_name = contest_names[contest_slug]
        else:
            url = 'https://www.hackerrank.com/rest/contests/'+contest_slug
            contest_name = requests.get(url, headers=header).json()['model']['name']

        if contest_slug in last_time and int(time.time())-last_time[contest_slug] < 120:
            data = {
                'ok': True,
                'teams': teams,
                'leaderboard': last_val[contest_slug],
                'contest_slug': contest_slug,
                'contest_name': contest_name,
                'problem_slugs': problem_slugs,
                'last_updated': datetime.fromtimestamp(last_time[contest_slug])
            }

            return lb.htmlize_leaderboard(data)

        p.clear()

        threads = []

        # Find the list of points obtained by all the users for each problem
        for problem_slug in problem_slugs:
            thread = Thread(target=read_points, args=(contest_slug, problem_slug))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # List to store the unsorted leaderboard
        leaderboard = list()

        for team in teams:
            a = {}
            t = {}

            for problem in problem_slugs:
                a[problem] = 0
                t[problem] = -1

            # The list a contains the maximum number of points obtained by a user in the team
            for member in teams[team]:
                for problem in problem_slugs:
                    if member in p[problem]:
                        if p[problem][member][0] > a[problem]:
                            a[problem] = p[problem][member][0]
                            t[problem] = p[problem][member][1]

                        elif p[problem][member][0] == a[problem]:
                            t[problem] = min(t[problem], p[problem][member][1])

            # Find the sum of scores of all team
            ss = 0
            for problem in problem_slugs:
                ss += a[problem]

            # Find the sum of minimum time taken for submission of each problem
            ts = 0
            for problem in problem_slugs:
                if t[problem] > -1:
                    ts += t[problem]

            leaderboard.append([ss, -ts, team, a])

        leaderboard.sort()
        leaderboard.reverse()

        # Stores the points scored by each team
        team_points = {}

        for entry in leaderboard:
            team_points[entry[2]] = [entry[3], entry[0], timestamp_to_hour(int(-entry[1]))]

        # Store the time of retrieval and the leaderboard
        last_time[contest_slug] = int(time.time())
        last_val[contest_slug] = team_points

        data = {
            'ok': True,
            'teams': teams,
            'leaderboard': last_val[contest_slug],
            'contest_slug': contest_slug,
            'contest_name': contest_name,
            'problem_slugs': problem_slugs,
            'last_updated': '%s %s' % (datetime.fromtimestamp(last_time[contest_slug]), time.tzname[0])
        }

        return lb.htmlize_leaderboard(data)

    except Exception as e:
        return {'error': str(e)}


if os.environ.get('APP_LOCATION') == 'vercel':
    run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
else:
    run(host='localhost', port=8080, debug=True)

app()

