from flask import Flask
from flask import send_file
from flask import request
from flask import Response

import requests
import json

from bs4 import BeautifulSoup, NavigableString, Tag

import re
import datetime
import configparser


config = configparser.ConfigParser()
config.read('/etc/auth.conf')




print("starting up!")

access_token = config['botato_token']['token']
targetURL = 'https://graph.facebook.com/v2.6/me/messages?access_token=' + access_token

all_list_en = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel', '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra', 'Nehemiah', 'Tobit', 'Judith', 'Esther', '1 Maccabees', '2 Maccabees', 'Job', 'Psalm', 'Proverbs', 'Ecclesiastes', 'Song of Solomon', 'Wisdom', 'Sirach', 'Isaiah', 'Jeremiah', 'Lamentations', 'Baruch', 'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation']

all_list_kr = ['창세기', '탈출기', '레위기', '민수기', '신명기', '여호수아기', '판관기', '룻기', '사무엘기 상권', '사무엘기 하권', '열왕기 상권', '열왕기 하권', '역대기 상권', '역대기 하권', '에즈라기', '느헤미야기', '토빗기', '유딧기', '에스테르기', '마카베오기 상권', '마카베오기 하권', '욥기', '시편', '잠언', '코헬렛', '아가', '지혜서', '집회서', '이사야서', '예레미야서', '애가', '바룩서', '에제키엘서', '다니엘서', '호세아서', '요엘서', '아모스서', '오바드야서', '요나서', '미카서', '나훔서', '하바쿡서', '스바니야서', '하까이서', '즈카르야서', '말라키서', '마태오 복음서', '마르코 복음서', '루카 복음서', '요한 복음서', '사도행전', '로마 신자들에게 보낸 서간', '코린토 신자들에게 보낸 첫째 서간', '코린토 신자들에게 보낸 둘째 서간', '갈라티아 신자들에게 보낸 서간', '에페소 신자들에게 보낸 서간', '필리피 신자들에게 보낸 서간', '콜로새 신자들에게 보낸 서간', '테살로니카 신자들에게 보낸 첫째 서간', '테살로니카 신자들에게 보낸 둘째 서간', '티모테오에게 보낸 첫째 서간', '티모테오에게 보낸 둘째 서간', '티토에게 보낸 서간 ', '필레몬에게 보낸 서간', '히브리인들에게 보낸 서간', '야고보 서간', '베드로의 첫째 서간', '베드로의 둘째 서간', '요한의 첫째 서간', '요한의 둘째 서간', '요한의 셋째 서간', '유다 서간', '요한 묵시록']

ko_en_dict = dict(zip(all_list_kr, all_list_en))

app = Flask(__name__)


print("ready!")

@app.route('/fb/webhook', methods=['POST'])
#@app.route('/webook', methods=['POST'])
def webhook_post():
    #field = request.json["field"]
    value = request.get_json()
    print(value)

    try:
        sender_id = value['entry'][0]['messaging'][0]['sender']['id']
        text = value['entry'][0]['messaging'][0]['message']['text']

    except:
        return Response('Not OK')
    
    print(sender_id, text)

    if text == '본문이름':
        send_message(sender_id, '\n'.join(all_list_kr))


    elif '장' in text or ':' in text:	
        if '장' in text:
            re_성경 = re.search(r'(.*)\s(\d+)장', text)

            if re_성경:
                성경 = re_성경.group(1)
                장= re_성경.group(2)
            
        elif ':' in text:
            re_성경 = re.search(r'(.*)\s(\d+):', text)
            if re_성경:
                성경 = re_성경.group(1)
                장= re_성경.group(2)

        try:
            print('\nsearching dictionary for ' + 성경.strip() + '\n')
            mid_url_str = ko_en_dict[성경.strip()] + '+' + 장
            bible_gate_url = 'https://www.biblegateway.com/passage/?search=' \
                + mid_url_str + '&version=NRSVCE'
           
            print('\n Trying ' + bible_gate_url + '\n')
            eng_raw_text = get_english_bible(bible_gate_url)

            if eng_raw_text:
                print('Formatting text...\n')
            eng_text = en_clear_junks(eng_raw_text)

            if len(eng_text) < 2000:
                send_message(sender_id, eng_text)
            else:
                print('Message too long...\n')
                send_message(sender_id, text + ' 영문구절은 여기서 확인가능합니다: ' + bible_gate_url)

        except:
            send_error(sender_id, text)

    elif '복음' in text:
        if '오늘' in text:
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            print('retrieving 복음말씀...')
            ko_gospel_text = '오늘의 복음말씀 입니다.\n'
            ko_gospel_text += get_ko_gospel(today)
            send_message(sender_id, ko_gospel_text)

        elif text == '복음':
            today = datetime.datetime.today()
            next_sunday = next_weekday(today, 6)
            ko_gospel_text = next_sunday.strftime('%d') + '일 주일 복음말씀 입니다.\n'
            ko_gospel_text += get_ko_gospel(next_sunday.strftime('%Y-%m-%d'))
            send_message(sender_id, ko_gospel_text)

        else:
            send_error(sender_id, text)

    else:
        send_error(sender_id, text)
        #sorry_msg = 'Sorry, I did not understand "' + text + '".\n Please try "복음" or "오늘복음".'
        #send_message(sender_id, sorry_msg)

    return Response('OK')

@app.route('/')
def index():
    pikachu = 'pikachu.html'
    return send_file(pikachu, mimetype='text/html')
    #return Response('There is nothing here.')


@app.route('/tos')
def tos():
    tos = 'tos.txt'
    return send_file(tos, mimetype='text/plain')


@app.route('/privacy_policy')
def privacy():
    privacy = 'privacy.txt'
    #return Response('We don’t store your data, period.')
    return send_file(privacy, mimetype='text/plain')

@app.route('/fb/webhook')
def webhook():
    BOT_TOKEN = config['botato_token']['BOT_TOKEN']
    mode = request.args.get('hub.mode', None)
    token = request.args.get('hub.verify_token', None)
    challenge = request.args.get('hub.challenge', None)

    if mode and token:
        if (mode == 'subscribe' and token == BOT_TOKEN):
            print('WEBHOOK_VERIFIED')
            return Response(challenge)

    else:
        abort(400)



@app.route('/ppap')
def ppap():
    ppap_gif = 'ppap.gif'
    return send_file(ppap_gif, mimetype='image/gif')



def send_message(sender_id, msg):
    headers = {'content-type': 'application/json'}
    payload = {"messaging_type": "RESPONSE", "recipient": {"id": sender_id}, "message":{"text":msg}}
    
    r = requests.post(targetURL, data=json.dumps(payload), headers=headers)
    print (r.text)
    

def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
        
    return d + datetime.timedelta(days_ahead)


def get_ko_gospel(date):
    mass_url_ko = 'http://maria.catholic.or.kr/mi_pr/missa/missa.asp?menu=missa&gomonth=' + date

    response_ko = requests.get(mass_url_ko)
    soup_ko = BeautifulSoup(response_ko.content, "html5lib")
    
    gospel_ko = ''

    for header in soup_ko.find_all('h3', text='복음'):
        nextNode = header
        while True:
            nextNode = nextNode.nextSibling
            
            if nextNode is None:
                break

            if isinstance(nextNode, NavigableString):
                gospel_ko += nextNode.strip()
                
            if isinstance(nextNode, Tag):
                if nextNode.name == "h3":
                    break
                
                gospel_ko += nextNode.get_text().strip()
                
    gospel_ko_edited = re.sub('<[^>]+>', '', gospel_ko)
    gospel_ko_edited = re.sub('(\d+,\d+-\d+)', r'\1\n', gospel_ko_edited)
    
    return gospel_ko_edited

'''
@app.errorhandler(403)
def auth_error(e):
    return Response('403 Forbidden')
'''

def get_english_bible(url):
    response_en = requests.get(url)
    soup_en = BeautifulSoup(response_en.content, "html5lib")
    if soup_en:
        print('Got response!!!\n')

    para = soup_en.find_all('p')
    ignore = 1
    end = 0
    eng_bible_raw = ''
    for p in para:
        if p.span:
            ignore = 0
        
        if 'copyright' in p.text:
            end = 1
        
        if ignore == 0 and end == 0:
            for tag in p:
                try:
                    eng_bible_raw += tag.text + '\n'
                except:
                    pass

    return eng_bible_raw


def en_clear_junks(text):
    try:
        text_no_bracket = re.sub(r'\[\w\]', '', text)
    except:
        text_no_bracket = text

    try:
        text_clear_spaces = re.sub(r'\s\s+', ' ', text_no_bracket)
    except:
        text_clear_spaces = text_no_bracket

    try:
        text_newline_added = re.sub(r'(\d+)', r'\n\1', text_clear_spaces)
    except:
        text_newline_added = text_clear_spaces

    text_first_digit_fixed = re.sub(r'\d+', '1', text_newline_added, 1)
    return text_first_digit_fixed


def send_error(sender_id, text):
    sorry_msg = 'Sorry, I did not understand "' + text + '".\n Please try "복음" or "오늘복음".\n\n'
    sorry_msg += '영문 성경이 찾고 싶으셨다면, 본문이름 x장 (예: 루카 복음서 2장)을 사용해주세요.\n'
    sorry_msg += '정확한 본문이름이 알고싶으시다면 "본문이름"을 보내주세요.'

    send_message(sender_id, sorry_msg)



if __name__ == '__main__':
    app.run(threaded = True)

