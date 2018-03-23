#! /usr/bin/env python


from __future__ import print_function
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
    raise ImportError('tweepy module is not installed on your system!')


def config_reader(filename):
    params = dict()
    with open(filename, 'rU') as config_file:
        for line in config_file:
            if line.find('=') != -1:
                words = line.split('=')

                if len(words) < 2:
                    print(
                        'Check your config file!\nMake sure your comments start with #! \nMakse sure your params are not empty!')
                    sys.exit()
                params[words[0].lstrip().rstrip()] = words[1].lstrip().rstrip()
    if 'consumerKey' not in params or \
            'consumerSecret' not in params or \
            'twitterAccessToken' not in params or \
            'twitterAccessTokenSecret' not in params or \
            'outputFolder' not in params or \
            'queryName' not in params:
        print('Check your config file!\nMake sure your comments start with #! \nMakse sure your params are not empty!')
        sys.exit()
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

    output_folder = params['outputFolder'] + '/' + params['queryName'] + '/'
    folders = [output_folder + 'JSONs', output_folder + 'Tweets']

    for folder in folders:
        now = datetime.datetime.now()
        if os.path.exists(folder):
            os.rename(folder, folder + '-' + str(now))

    try:
        os.makedirs(output_folder + 'JSONs')
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open(tweetids_file, 'rU') as idfile:
        now = datetime.datetime.now()
        directory = output_folder + 'JSONs/' + params['queryName'] + '-recollection-'
        write_to = open(directory + 'JSONs-' + str(now) + '.txt', 'w')
        exception = open(directory + 'exception-' + str(now) + '.txt', 'w')
        count = 0

        for tweet_id in idfile:
            count += 1
            if count % 100 == 0:
                print(count)
            try:
                tweet = twapi.get_status(tweet_id, tweet_mode='extended')
                write_to.write(json.dumps(tweet._json).replace('"full_text":', '"text":') + '\n')

            except tweepy.TweepError as te:
                if 'message' in te.message[0]:
                    print('Failed to get tweet ID ', tweet_id.replace('\n', ''), '\t', str(te.message[0]['message']),
                          te.api_code)
                    exception.write(tweet_id.replace('\n', '') + '\t' + str(te.message[0]['message']) + '\t' + str(
                        te.api_code) + '\n')
                    write_to.flush()
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
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\nProgram Interrupted!')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
