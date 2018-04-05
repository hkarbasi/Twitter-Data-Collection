#! /usr/bin/env python


from __future__ import print_function
import logging
import getopt
import json
import time
import datetime
import sys
import os
import errno

# third-party: `pip install tweepy`
try:
    import tweepy
except ImportError:
    print('Tweepy module is not installed on your system!')
    sys.exit()


def usage():
    print('Usage: get_tweets_by_search.py config_file')
    sys.exit()


def search_tweets(twapi, params):
    """
    `twapi`: Initialized, authorized API object from Tweepy
    `params`: Dictionary of all necessary of the parameters
    """
    query = params['query']
    folder = params['outputFolder'] + params['queryName'] + '/JSONs/'
    interval = eval(params['interval'])
    iteration = eval(params['iteration'])

    count = 0
    count += 1
    last_id = -1
    since_id = 0

    try:
        os.makedirs(folder)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    output = open(folder + params['queryName'] + '-' + str(datetime.datetime.now()) + '.txt', 'w')
    print(params['queryName'] + '\n\nPast 10 days ago Tweets')

    while True:
        try:
            new_tweets = twapi.search(q=query, count=100, max_id=str(last_id - 1), tweet_mode='extended')
            if not new_tweets:
                output.close()
                break
            else:
                print('page ' + str(count) + ': ' + str(len(new_tweets)))
                for t in new_tweets:
                    output.write((json.dumps(t._json).replace('"full_text":', '"text":') + '\n').encode('utf-8'))
                output.flush()
                last_id = new_tweets[-1].id
                since_id = max(new_tweets[0].id, since_id)
                count += 1
        except tweepy.TweepError as e:
            print (e.api_code)
            print (getExceptionMessage(e.reason))
            break

    last_id = -1
    temp_since_id = since_id

    print('\nNew Tweets')
    output = open(folder + params['queryName'] + '-' + str(datetime.datetime.now()) + '.txt', 'w')
    while iteration > 0:
        
        try:
            new_tweets = twapi.search(q=query, count=100, since_id=since_id, max_id=str(last_id - 1),
                                      tweet_mode='extended')
            if not new_tweets:
                output.close()
                if since_id == temp_since_id:
                    os.remove(output.name)

                iteration -= 1
                print(params['queryName'] + ' - iteration #' + str(eval(params['iteration']) - iteration) + ' - waiting  ' +
                      params['interval'] + ' minutes starting from ' + str(datetime.datetime.now()))
                time.sleep(interval * 60)
                output = open(folder + params['queryName'] + '-' + str(datetime.datetime.now()) + '.txt', 'w')
                since_id = temp_since_id
                last_id = -1
            else:
                print('page ' + str(count) + ': ' + str(len(new_tweets)))
                for t in new_tweets:
                    output.write((json.dumps(t._json).replace('"full_text":', '"text":') + '\n').encode('utf-8'))
                output.flush()

                last_id = new_tweets[-1].id
                temp_since_id = max(new_tweets[0].id, temp_since_id)
                count += 1

        except tweepy.TweepError as e:
            print (e.api_code)
            print (getExceptionMessage(e.reason))
            time.sleep(60)


def config_reader(filename):
    params = dict()
    with open(filename, 'rU') as config_file:
        for line in config_file:
            if line.find('=') != -1:
                words = line.split('=')

                if len(words) < 2:
                    print(
                        'Check your config file!\nMake sure your comments start with #! \nMakse sure your params are '
                        'not empty!')
                    sys.exit()
                params[words[0].lstrip().rstrip()] = words[1].lstrip().rstrip()
    if 'consumerKey' not in params or \
            'consumerSecret' not in params or \
            'twitterAccessToken' not in params or \
            'twitterAccessTokenSecret' not in params or \
            'outputFolder' not in params or \
            'queryName' not in params or \
            'query' not in params or \
            'interval' not in params or \
            'iteration' not in params:
        print(
            'Check your config file!\nMake sure your comments start with #! \nMakse sure your params are not empty!')
        sys.exit()
    if params['outputFolder'][-1] != '/':
        params['outputFolder'] += '/'
    return params


def main(args):
    try:

        if len(args) != 1:
            usage()

        for arg in args:
            if not os.path.isfile(arg):
                print('Not found or not a file: %s' % arg)
                usage()

        params = config_reader(args[0])

        # connect to twitter
        auth = tweepy.OAuthHandler(params['consumerKey'], params['consumerSecret'])
        auth.set_access_token(params['twitterAccessToken'], params['twitterAccessTokenSecret'])
        api = tweepy.API(auth,
                         # retry_count = 2,
                         # retry_delay = 1,
                         # retry_errors={401, 404, 500, 503},
                         wait_on_rate_limit=True,
                         wait_on_rate_limit_notify=True
                         )

        search_tweets(api, params)

    except getopt.GetoptError:
        usage()


if __name__ == '__main__':
    try:
        logging.info("Begin")
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\nProgram Interrupted!')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
