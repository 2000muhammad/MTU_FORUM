from django.db import migrations


QUOTES = [
    ('ru', 'Сила — в справедливости.', 'Амир Темур'),
    ('ru', 'Если ты человек, не называй человеком того, кого не заботит горе народа.', 'Алишер Навои'),
    ('ru', 'Кто не владеет своим языком, тот не заслуживает внимания народа.', 'Алишер Навои'),
    ('ru', 'Воспитание для нас — вопрос жизни или смерти, спасения или гибели, счастья или бедствия.', 'Абдулла Авлони'),
    ('ru', 'Знание — плод повторения и возвращения к изученному.', 'Абу Райхан Беруни'),
    ('ru', 'Доброе слово — пища душе.', 'Узбекская народная мудрость'),
    ('ru', 'Знание открывает путь, труд доводит до цели.', 'Узбекская народная мудрость'),
    ('ru', 'Совет мудрого сокращает долгую дорогу.', 'Узбекская народная мудрость'),
    ('ru', 'Терпение приносит плод, поспешность — сожаление.', 'Узбекская народная мудрость'),
    ('ru', 'Человек ценен не словами, а полезными делами.', 'Узбекская народная мудрость'),
    ('ru', 'Где есть согласие, там есть сила.', 'Узбекская народная мудрость'),
    ('ru', 'Время — самый справедливый наставник.', 'Узбекская народная мудрость'),
    ('ru', 'Учись у прошлого, трудись сегодня, думай о будущем.', 'Узбекская народная мудрость'),
    ('ru', 'Малое добро открывает большие двери.', 'Узбекская народная мудрость'),
    ('ru', 'Ум растёт от вопросов, мастерство — от практики.', 'Узбекская народная мудрость'),
    ('ru', 'Честный труд украшает человека.', 'Узбекская народная мудрость'),
    ('ru', 'Порядок в деле начинается с порядка в мыслях.', 'Узбекская народная мудрость'),
    ('ru', 'Дорогу осилит тот, кто продолжает идти.', 'Узбекская народная мудрость'),
    ('uz', 'Kuch — adolatda.', 'Amir Temur'),
    ('uz', 'Odami ersang, demagil odami, onikim yo‘q xalq g‘amidin g‘ami.', 'Alisher Navoiy'),
    ('uz', 'Tilga ixtiyorsiz — elga e’tiborsiz.', 'Alisher Navoiy'),
    ('uz', 'Tarbiya biz uchun yo hayot — yo mamot, yo najot — yo halokat, yo saodat — yo falokat masalasidir.', 'Abdulla Avloniy'),
    ('uz', 'Bilim — qaytarish va takrorlash mevasidir.', 'Abu Rayhon Beruniy'),
    ('uz', 'Yaxshi so‘z — jon ozig‘i.', 'O‘zbek xalq maqoli'),
    ('uz', 'Bilim yo‘l ochar, mehnat manzilga yetkazar.', 'O‘zbek xalq hikmati'),
    ('uz', 'Dononing maslahati uzoq yo‘lni qisqartirar.', 'O‘zbek xalq hikmati'),
    ('uz', 'Sabr meva keltirar, shoshqaloqlik — pushaymon.', 'O‘zbek xalq hikmati'),
    ('uz', 'Inson so‘zi bilan emas, foydali ishi bilan qadrlanadi.', 'O‘zbek xalq hikmati'),
    ('uz', 'Hamjihatlik bor joyda kuch bor.', 'O‘zbek xalq hikmati'),
    ('uz', 'Vaqt — eng adolatli ustoz.', 'O‘zbek xalq hikmati'),
    ('uz', 'O‘tmishdan o‘rgan, bugun mehnat qil, kelajakni o‘yla.', 'O‘zbek xalq hikmati'),
    ('uz', 'Kichik yaxshilik katta eshiklarni ochar.', 'O‘zbek xalq hikmati'),
    ('uz', 'Aql savoldan, mahorat mashqdan o‘sadi.', 'O‘zbek xalq hikmati'),
    ('uz', 'Halol mehnat insonni bezaydi.', 'O‘zbek xalq hikmati'),
    ('uz', 'Ishdagi tartib fikrdagi tartibdan boshlanadi.', 'O‘zbek xalq hikmati'),
    ('uz', 'Yo‘lni davom etgan odam bosib o‘tadi.', 'O‘zbek xalq hikmati'),
    ('uz-cyrl', 'Куч — адолатда.', 'Амир Темур'),
    ('uz-cyrl', 'Одами эрсанг, демагил одами, ониким йўқ халқ ғамидин ғами.', 'Алишер Навоий'),
    ('uz-cyrl', 'Тилга ихтиёрсиз — элга эътиборсиз.', 'Алишер Навоий'),
    ('uz-cyrl', 'Тарбия биз учун ё ҳаёт — ё мамот, ё нажот — ё ҳалокат, ё саодат — ё фалокат масаласидир.', 'Абдулла Авлоний'),
    ('uz-cyrl', 'Билим — қайтариш ва такрорлаш мевасидир.', 'Абу Райҳон Беруний'),
    ('uz-cyrl', 'Яхши сўз — жон озиғи.', 'Ўзбек халқ мақоли'),
    ('uz-cyrl', 'Билим йўл очар, меҳнат манзилга етказар.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Дононинг маслаҳати узоқ йўлни қисқартирар.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Сабр мева келтирар, шошқалоқлик — пушаймон.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Инсон сўзи билан эмас, фойдали иши билан қадрланади.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Ҳамжиҳатлик бор жойда куч бор.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Вақт — энг адолатли устоз.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Ўтмишдан ўрган, бугун меҳнат қил, келажакни ўйла.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Кичик яхшилик катта эшикларни очар.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Ақл саволдан, маҳорат машқдан ўсади.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Ҳалол меҳнат инсонни безайди.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Ишдаги тартиб фикрдаги тартибдан бошланади.', 'Ўзбек халқ ҳикмати'),
    ('uz-cyrl', 'Йўлни давом этган одам босиб ўтади.', 'Ўзбек халқ ҳикмати'),
    ('en', 'Strength lies in justice.', 'Amir Temur'),
    ('en', 'Call no one human who feels no concern for the people’s sorrow.', 'Alisher Navoi'),
    ('en', 'One who cannot govern their tongue shows no regard for the people.', 'Alisher Navoi'),
    ('en', 'Education is for us a matter of life or death, salvation or ruin, happiness or disaster.', 'Abdulla Avloni'),
    ('en', 'Knowledge is the fruit of returning to and repeating what has been learned.', 'Abu Rayhan Beruni'),
    ('en', 'A kind word is nourishment for the soul.', 'Uzbek proverb'),
    ('en', 'Knowledge opens the road; work carries you to the destination.', 'Uzbek wisdom'),
    ('en', 'Wise advice shortens a long road.', 'Uzbek wisdom'),
    ('en', 'Patience bears fruit; haste brings regret.', 'Uzbek wisdom'),
    ('en', 'A person is valued by useful deeds, not words.', 'Uzbek wisdom'),
    ('en', 'Where there is unity, there is strength.', 'Uzbek wisdom'),
    ('en', 'Time is the fairest teacher.', 'Uzbek wisdom'),
    ('en', 'Learn from the past, work today, and think of the future.', 'Uzbek wisdom'),
    ('en', 'A small kindness opens great doors.', 'Uzbek wisdom'),
    ('en', 'The mind grows through questions; skill grows through practice.', 'Uzbek wisdom'),
    ('en', 'Honest work adorns a person.', 'Uzbek wisdom'),
    ('en', 'Order in work begins with order in thought.', 'Uzbek wisdom'),
    ('en', 'The road is completed by the one who keeps moving.', 'Uzbek wisdom')
]


def seed_dashboard_quotes(apps, schema_editor):
    DashboardQuote = apps.get_model("core", "DashboardQuote")
    language_order = {}
    for language, text, author in QUOTES:
        language_order[language] = language_order.get(language, 0) + 1
        DashboardQuote.objects.get_or_create(
            language=language,
            text=text,
            defaults={"author": author, "sort_order": language_order[language], "is_active": True},
        )


def remove_seeded_dashboard_quotes(apps, schema_editor):
    DashboardQuote = apps.get_model("core", "DashboardQuote")
    for language, text, _author in QUOTES:
        DashboardQuote.objects.filter(language=language, text=text).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0054_remove_position_unique_position_name_per_branch_and_more")]
    operations = [migrations.RunPython(seed_dashboard_quotes, remove_seeded_dashboard_quotes)]
