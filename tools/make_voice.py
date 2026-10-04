"""Generate the terminal's spoken clips with ElevenLabs (voice: Solomiya Vitlitska - Podcast Pro).

Usage:  python tools/make_voice.py            # generate missing clips into audio/
        python tools/make_voice.py --list     # print the phrase list and character count only
The API key is read from %USERPROFILE%/.tts/elevenlabs.txt and is never printed.
"""
import json, os, sys, time, urllib.request, concurrent.futures as cf

VOICE = 'yMBZR4SLoc24wOJLWAB2'
MODEL = 'eleven_multilingual_v2'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'audio')

UNITS = ['', 'один', 'два', 'три', 'чотири', 'пʼять', 'шість', 'сім', 'вісім', 'девʼять']
TEENS = ['десять', 'одинадцять', 'дванадцять', 'тринадцять', 'чотирнадцять', 'пʼятнадцять', 'шістнадцять',
         'сімнадцять', 'вісімнадцять', 'девʼятнадцять']
TENS = ['', '', 'двадцять', 'тридцять', 'сорок', 'пʼятдесят', 'шістдесят', 'сімдесят', 'вісімдесят', 'девʼяносто']
HUNDREDS = ['', 'сто', 'двісті', 'триста', 'чотириста', 'пʼятсот', 'шістсот', 'сімсот', 'вісімсот', 'девʼятсот']


def below_thousand(n):
    w = [HUNDREDS[n // 100]]
    r = n % 100
    if 10 <= r < 20:
        w.append(TEENS[r - 10])
    else:
        w += [TENS[r // 10], UNITS[r % 10]]
    return [x for x in w if x]


def words(n, acc=False):
    """Ukrainian number words, 1..9999 (thousands are feminine: одна/дві тисячі). acc: accusative («за тисячу»)."""
    t, r = divmod(n, 1000)
    w = []
    if t:
        w += {1: ['тисячу' if acc else 'тисяча'], 2: ['дві', 'тисячі'], 3: ['три', 'тисячі'], 4: ['чотири', 'тисячі']}.get(t, below_thousand(t) + ['тисяч'])
    w += below_thousand(r)
    return ' '.join(w)


PROPS = ['Києво-Печерська лавра', 'Батьківщина-Мати', 'Пізанська вежа', 'Венеція', 'Колізей', 'Тріумфальна арка',
         'Єлисейські поля', 'Ейфелева вежа', 'Співаючі фонтани', 'Острови Пальм', 'Бурдж-Халіфа', 'Октоберфест',
         'Бундестаг', 'Бранденбурзькі ворота', 'Оксфордський університет', 'Стадіон Уемблі', 'Біг-Бен', 'Шанхай',
         'Великий Китайський мур', 'Гонконг', 'Голлівуд', 'Волл-стріт']
RENTS = [[70, 130, 220, 370, 750], [70, 130, 220, 370, 750], [80, 140, 240, 410, 800], [80, 140, 240, 410, 800],
         [100, 160, 260, 440, 860], [110, 180, 290, 460, 900], [110, 180, 290, 460, 900], [130, 200, 310, 490, 980],
         [140, 210, 330, 520, 1000], [140, 210, 330, 520, 1000], [160, 230, 350, 550, 1100], [170, 250, 380, 580, 1160],
         [170, 250, 380, 580, 1160], [190, 270, 400, 610, 1200], [200, 280, 420, 640, 1300], [200, 280, 420, 640, 1300],
         [220, 300, 440, 670, 1340], [230, 320, 460, 700, 1400], [230, 320, 460, 700, 1400], [250, 340, 480, 730, 1440],
         [270, 360, 510, 740, 1500], [300, 400, 560, 810, 1600]]
EVENTS = ['Добрі справи!', 'Місто зростає!', 'Дом з привидами!', 'Безпечне місто!', 'Метелики у животі!', 'Пакуй валізи!',
          'Паті на хаті!', 'Великий куш!', 'Дорожній збір!', 'Затор на дорозі!', 'Мані на кармані!', 'Поверніть своє!',
          'Сезон застуд!', 'Що смердить?!', 'Біжи, друже... біжи!', 'Будівля знесена!', 'Це хлопчик!', 'Угода тижня!',
          'Помста Бобіка!', 'Несподіваний ураган!', 'Скандали. Інтриги. Розслідування!', 'У нас на районі зірка!',
          'Прокатись з вітерцем!']
NAMES = ['Автомобіль', 'Гелікоптер', 'Яхта', 'Літак']
DATIVE = ['Автомобілю', 'Гелікоптеру', 'Яхті', 'Літаку']


def phrases():
    p = {
        'go': 'Вперед! Плюс двісті.',
        'jailout': 'Вихід з вʼязниці.',
        'ownerjail': 'Власник у вʼязниці. Оренди немає.',
        'debtdone': 'Борг закрито.',
        'swap': 'Власність обміняно. Обміняйтеся картками.',
        'houses': 'Пересуньте будинки.',
        'nochange': 'Нічого не змінилося.',
        'undo': 'Скасовано.',
        'start': 'Гру розпочато! Успіхів!',
        'voiceon': 'Голос увімкнено.',
        'setbonus': 'Групу кольору зібрано! Пересуньте будинки.',
        'both': 'Кожен отримує двісті.',
        'rent': 'Оренда.',
        'sold': 'Продано!',
        'paynothing': 'Платити нічого.',
        'pay': 'Сплатіть.',
    }
    for i, name in enumerate(PROPS):
        p[f'buy-{i + 1}'] = f'Куплено: {name}.'
    for lv in range(1, 6):
        p[f'level-{lv}'] = f'Оренду підвищено. Рівень {words(lv) if lv > 1 else "один"}.'
    for v in sorted({r for rs in RENTS for r in rs}):
        p[f'rent-{v}'] = f'Оренда {words(v)}.'
    for i, t in enumerate(EVENTS):
        p[f'ev-{i + 1}'] = t
    for n in range(1, 23):
        p[f'pay-{50 * n}'] = f'Сплатіть {words(50 * n, acc=True)}.'
    for b in range(20, 1501, 20):
        p[f'sold-{b}'] = f'Продано за {words(b, acc=True)}!'
    for i in range(4):
        p[f'tojail-{i}'] = f'{NAMES[i]} іде до вʼязниці.'
        p[f'nomoney-{i}'] = f'{DATIVE[i]} не вистачає грошей.'
        p[f'third-{i}'] = f'{NAMES[i]}: третя спроба. Сплатіть сто, щоб вийти.'
        p[f'bankrupt-{i}'] = f'{NAMES[i]} — банкрут! Гру завершено.'
        p[f'win-{i}'] = f'Перемагає {NAMES[i]}! Вітаємо!'
    return p


def generate(key, text):
    body = json.dumps({'text': text, 'model_id': MODEL}).encode()
    req = urllib.request.Request(f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_64',
                                 data=body, headers={'xi-api-key': key, 'Content-Type': 'application/json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(3 * (attempt + 1)); continue
            raise RuntimeError(f'{e.code}: {e.read().decode()[:200]}')
    raise RuntimeError('gave up after retries')


def main():
    p = phrases()
    if '--list' in sys.argv:
        for k, v in p.items(): print(f'{k:14} {v}')
        print(len(p), 'clips,', sum(len(v) for v in p.values()), 'characters')
        return
    key = open(os.path.join(os.path.expanduser('~'), '.tts', 'elevenlabs.txt'), encoding='utf-8').read().strip()
    os.makedirs(OUT, exist_ok=True)
    todo = [(k, v) for k, v in p.items() if not os.path.exists(os.path.join(OUT, k + '.mp3'))]
    print(len(todo), 'to generate,', sum(len(v) for _, v in todo), 'characters')

    def one(kv):
        k, v = kv
        data = generate(key, v)
        open(os.path.join(OUT, k + '.mp3'), 'wb').write(data)
        return k
    failed = []
    with cf.ThreadPoolExecutor(3) as ex:
        for kv, fut in [(kv, ex.submit(one, kv)) for kv in todo]:
            try: fut.result()
            except Exception as e: failed.append((kv[0], str(e)))
    json.dump(sorted(k for k in p if os.path.exists(os.path.join(OUT, k + '.mp3'))),
              open(os.path.join(OUT, 'clips.json'), 'w'), ensure_ascii=False)
    print('done;', len(failed), 'failed', failed[:5])


if __name__ == '__main__':
    main()
