#! /usr/bin/env python


from __future__ import print_function
import logging
import getopt
import json
import os
import sys
import datetime
# third-party: `pip install tweepy`
import errno

try:
    import tweepy
except ImportError:
    print('Tweepy module is not installed on your system!')
    sys.exit()


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
                params[words[0].strip()] = words[1].strip()
    if 'consumerKey' not in params or \
            'consumerSecret' not in params or \
            'twitterAccessToken' not in params or \
            'twitterAccessTokenSecret' not in params or \
            'outputFolder' not in params or \
            'queryName' not in params:
        print('Check your config file!\nMake sure your comments start with #! \nMakse sure your params are not empty!')
        sys.exit()
    if params['outputFolder'][-1] == '/' or params['outputFolder'][-1] == '\\':
        params['outputFolder'] = params['outputFolder'][:-1]
    return params


def get_tweets_by_tweetID(twapi, params, tweetids_file):
    """
    Fetches content for tweet IDs in a file one at a time,
    which means a ton of HTTPS requests, so NOT recommended.

    `twapi`: Initialized, authorized API object from Tweepy
    `params`: Dictionary of all necessary of the parameters
    `tweetids_file`: File of all tweet IDs to be recollected
    """
    # process IDs from the file

    # output_folder = os.path.join(params['outputFolder'], params['queryName'])
    # folders = [os.path.join(output_folder, 'JSONs'), os.path.join(output_folder, 'Tweets')]
    output_folder = '/'.join([params['outputFolder'], params['queryName']])
    folders = ['/'.join([output_folder, 'JSONs']), '/'.join([output_folder, 'Tweets'])]

    for folder in folders:
        now = str(datetime.datetime.now()).replace(':', '-')
        if os.path.exists(folder):
            os.rename(folder, folder + '-' + now)

    try:
        os.makedirs(folders[0])
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open(tweetids_file, 'rU') as idfile:
        now = str(datetime.datetime.now()).replace(':', '-')
        # directory = os.path.join(output_folder, 'JSONs', params['queryName'] + '-recollection-')
        directory = '/'.join([output_folder, 'JSONs', params['queryName'] + '-recollection-'])
        write_to = open(directory + 'JSONs-' + now + '.txt', 'wb')
        exception = open(directory + 'exception-' + now + '.txt', 'wb')
        count = 0

        for tweet_id in idfile:
            count += 1
            if count % 100 == 0:
                print(count)
            try:
                tweet = twapi.get_status(tweet_id, tweet_mode='extended')
                write_to.write(json.dumps(tweet._json).replace('"full_text":', '"text":').encode('utf-8') + '\n')

            except tweepy.TweepError as te:
                print('Failed to recollect tweet ID ', tweet_id.replace('\n', ''), '\t', str(te.args[0][0]['message']),
                      te.api_code)
                exception.write(str(tweet_id.replace('\n', '') + '\t' + str(te.args[0][0]['message']) + '\t' + str(
                    te.api_code) + '\n').encode('utf-8'))
                write_to.flush()
        print(str(count) + ' tweets have been recollected!')
        write_to.close()
        exception.close()


def usage():
    print('Usage: get_tweet_by_tweetID.py config_file tweetIDs_file')
    sys.exit()


def main(args):
    try:

        if len(args) != 2:
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
        get_tweets_by_tweetID(api, params, args[1])
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
