import json
import datetime
import csv
import time
import numpy as np
from fb import facebook
from watson_developer_cloud import ToneAnalyzerV3 

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request


tone_analyzer = ToneAnalyzerV3(
    version='2017-09-26',
    username='e975a6b5-641a-4010-a2c4-ab4b7f7638e0',
    password='zyzj8wO87iM2'
)

app_id = "586581221691013"
app_secret = "80fa08cc96dcdf93a68c1723e629e54b"  # DO NOT SHARE WITH ANYONE!
page_id = "cnn"

graph = facebook.GraphAPI(access_token=(app_id+'|'+app_secret))


access_token = app_id + "|" + app_secret


def request_until_succeed(url):
    req = Request(url)
    success = False
    while success is False:
        try:
            response = urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL {}: {}".format(url, datetime.datetime.now()))
            print("Retrying.")

    return response.read()


# Needed to write tricky unicode correctly to csv
def unicode_decode(text):
    try:
        return text.encode('utf-8').decode()
    except UnicodeDecodeError:
        return text.encode('utf-8')


def getFacebookPageFeedUrl(base_url):

    # Construct the URL string; see http://stackoverflow.com/a/37239851 for
    # Reactions parameters
    fields = "&fields=message,link,created_time,type,name,id," + \
        "comments.limit(0).summary(true),shares,reactions" + \
        ".limit(0).summary(true)"

    return base_url + fields


def getReactionsForStatuses(base_url):

    reaction_types = ['like', 'love', 'wow', 'haha', 'sad', 'angry']
    reactions_dict = {}   # dict of {status_id: tuple<6>}

    for reaction_type in reaction_types:
        fields = "&fields=reactions.type({}).limit(0).summary(total_count)".format(
            reaction_type.upper())

        url = base_url + fields

        data = json.loads(request_until_succeed(url))['data']

        data_processed = set()  # set() removes rare duplicates in statuses
        for status in data:
            id = status['id']
            count = status['reactions']['summary']['total_count']
            data_processed.add((id, count))

        for id, count in data_processed:
            if id in reactions_dict:
                reactions_dict[id] = reactions_dict[id] + (count,)
            else:
                reactions_dict[id] = (count,)

    return reactions_dict


def processFacebookPageFeedStatus(status):

    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.

    # Additionally, some items may not always exist,
    # so must check for existence first

    status_id = status['id']
    status_type = status['type']

    status_message = '' if 'message' not in status else \
        unicode_decode(status['message'])
    link_name = '' if 'name' not in status else \
        unicode_decode(status['name'])
    status_link = '' if 'link' not in status else \
        unicode_decode(status['link'])

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    status_published = datetime.datetime.strptime(
        status['created_time'], '%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published + \
        datetime.timedelta(hours=-5)  # EST
    status_published = status_published.strftime(
        '%Y-%m-%d %H:%M:%S')  # best time format for spreadsheet programs

    # Nested items require chaining dictionary keys.

    num_reactions = 0 if 'reactions' not in status else \
        status['reactions']['summary']['total_count']
    num_comments = 0 if 'comments' not in status else \
        status['comments']['summary']['total_count']
    num_shares = 0 if 'shares' not in status else status['shares']['count']

    return (status_id, status_message, link_name, status_type, status_link,
            status_published, num_reactions, num_comments, num_shares)

def relevant(text):
    keywords = ["guns","violence","gun","shooting","shooter",'NRA',]
    if any(word in text.split(' ') for word in keywords):
        return True
    else:
        return False

def comments(iid):
    post = graph.get_connections(id = iid,connection_name='comments')
    cmnts = ''
    for i in range(0,len(post['data'])):
        cmnts= cmnts + ' ' +post['data'][i]['message']
    return cmnts

def scrapeFacebookPageFeedStatus(page_id, access_token, since_date, until_date):
    find_count = [0,0,0]

    with open('{}_facebook_statuses.csv'.format(page_id), 'a') as file:
        w = csv.writer(file)
        #w.writerow(["Date","Joy", "Anger", "Sadness", "Analytical", "Tenative"])
        #w.writerow(["Joy", "Anger", "Sadness", "Analytical", "Tenative"])

        has_next_page = True
        num_processed = 0
        scrape_starttime = datetime.datetime.now()
        after = ''
        base = "https://graph.facebook.com/v2.9"
        node = "/{}/posts".format(page_id)
        parameters = "/?limit={}&access_token={}".format(100, access_token)
        since = "&since={}".format(since_date) if since_date \
            is not '' else ''
        until = "&until={}".format(until_date) if until_date \
            is not '' else ''

        print("Scraping {} Facebook Page: {}".format(page_id, scrape_starttime))
        tout = [0,0,0]
        while has_next_page:
            after = '' if after is '' else "&after={}".format(after)
            base_url = base + node + parameters + after + since + until

            url = getFacebookPageFeedUrl(base_url)
            statuses = json.loads(request_until_succeed(url))
            reactions = getReactionsForStatuses(base_url)
            for status in statuses['data']:
                # Ensure it is a status with the expected metadata
                #if np.random.binomial(1,0.5)==1:
                    if 'reactions' in status:
                        status_data = processFacebookPageFeedStatus(status)
                        reactions_data = reactions[status_data[0]]

                        # calculate thankful/pride through algebra
                        num_special = status_data[6] - sum(reactions_data)
                        #print(status_data[1])
                        #############################################
                        if relevant(status_data[1]):
                            print(status_data[5])
                            print(status_data[1])
                            #print(status_data[1])
                            tone = (tone_analyzer.tone(comments(status_data[0]), "text/plain")['document_tone']['tones'])
                            #count = len(graph.get_connections(id = status_data[0],connection_name='comments')['data'])
                            #print(count)
                            emotion_list = ["Joy","Anger","Sadness"]#Joy, Anger, Sadness, Analytical, Tenative
                            i = 0
                            #tout = [0,0,0,0,0]
                            for emotion in emotion_list:
                                for res in tone:
                                        if res['tone_name']==emotion:
                                            if emotion=='Joy' and res['score']!=0:
                                                tout[i]+=res['score']
                                                find_count[i] +=1
                                            if emotion=='Anger' and res['score']!=0:
                                                tout[i]+=res['score']
                                                find_count[i] +=1
                                            if emotion=='Sadness' and res['score']!=0:
                                                tout[i]+=res['score']
                                                find_count[i] +=1
                                            i +=1
                            #if tout[0]!=0:
                                #date = status_data[5]
                                #w.writerow([date] + tout + [count])
                            #fbc.scrapeFacebookPageFeedComments(page_id, access_token,status_data[0])



                    num_processed += 1
                    if num_processed % 100 == 0:
                        print("{} Statuses Processed: {}".format
                              (num_processed, datetime.datetime.now()))
            # if there is no next page, we're done.
            if 'paging' in statuses:
                after = statuses['paging']['cursors']['after']
            else:
                has_next_page = False

        print("Done!\n{} Statuses Processed in {}\nRelevant Articles:{}".format(
              num_processed, datetime.datetime.now() - scrape_starttime,find_count[0]))
        for l in range(0,len(tout)):
            if find_count[l]!=0:
                tout[l] /= find_count[l]
            
        if tout[0]!=0:
            w.writerow([since_date] + tout)


if __name__ == '__main__':
    # input date formatted as YYYY-MM-DD
    #year = np.random.random_integers(2015,2017,1000)
    #month = np.random.random_integers(1,12,1000)
    #day = np.random.random_integers(1,27,1000)
    #print(day)
    #print(month)
    #print(year)
    year = range(2018,2019)
    month = range(1,12)
    for y in year:
        for m in month:
            since_date = str(y)
            until_date = str(y)
            if m < 10:
                if m != 9:
                    since_date += '-' + '0' + str(m)
                    until_date += '-' + '0' + str(m+1)
                else:
                    since_date += '-' + '0' + str(m)
                    until_date += '-' + str(m+1)
            else:
                since_date += '-' + str(m)
                until_date += '-' + str(m+1)

            since_date += '-01'
            until_date += '-01'
            print()
            print()
            print(since_date) 
            print(until_date)
            for page_id in ['cnn','nbc','abc','nytimes']:
                scrapeFacebookPageFeedStatus(page_id, access_token, since_date, until_date)