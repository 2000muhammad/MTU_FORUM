"""Fast local translations for directory labels shown in the UI and Telegram bot."""

import re


POSITION_TRANSLATIONS = {
    "Начальник станции": {"uz": "Stansiya boshlig‘i", "uz-cyrl": "Станция бошлиғи", "en": "Station chief"},
    "Зам. Начальник станции": {"uz": "Stansiya boshlig‘i o‘rinbosari", "uz-cyrl": "Станция бошлиғи ўринбосари", "en": "Deputy station chief"},
    "Товар. кассир": {"uz": "Tovar kassiri", "uz-cyrl": "Товар кассири", "en": "Freight cashier"},
    "Приёмо сдатчик": {"uz": "Qabul-topshirish xodimi", "uz-cyrl": "Қабул-топшириш ходими", "en": "Cargo acceptance clerk"},
    "Техническая контора": {"uz": "Texnik idora", "uz-cyrl": "Техник идора", "en": "Technical office"},
    "ДСП": {"uz": "DSP", "uz-cyrl": "ДСП", "en": "Station duty officer"},
    "МГСП оператор": {"uz": "MGSP operatori", "uz-cyrl": "МГСП оператори", "en": "MGSP operator"},
    "Пунктах коммерческого осмотра (ПКО)": {"uz": "Tijorat ko‘rik punkti (PKO)", "uz-cyrl": "Тижорат кўрик пункти (ПКО)", "en": "Commercial inspection point (PKO)"},
    "Э - АСУ": {"uz": "E-ASU", "uz-cyrl": "Э-АСУ", "en": "E-ASU"},
    "ДНЦО": {"uz": "DNCO", "uz-cyrl": "ДНЦО", "en": "DNCO"},
}

PLATFORM_TRANSLATIONS = {
    '"Единое окно" АО «Ўзбекистон темир йўллари»': {
        "uz": '“Yagona darcha” “O‘zbekiston temir yo‘llari” AJ',
        "uz-cyrl": '“Ягона дарча” “Ўзбекистон темир йўллари” АЖ',
        "en": 'Single Window — Uzbekistan Railways JSC',
    },
    "Komission oylik ko'rigi onlayn platformasi “Oʻzbekiston temir yoʻllari” AJ": {
        "uz": "Komission oylik ko‘rik onlayn platformasi — O‘zbekiston temir yo‘llari AJ",
        "uz-cyrl": "Комиссион ойлик кўрик онлайн платформаси — Ўзбекистон темир йўллари АЖ",
        "en": "Online monthly commission inspection platform — Uzbekistan Railways JSC",
    },
}

_CYRILLIC_TO_LATIN = str.maketrans({
    "А":"A","Б":"B","В":"V","Г":"G","Д":"D","Е":"E","Ё":"Yo","Ж":"J","З":"Z","И":"I","Й":"Y","К":"K","Л":"L","М":"M","Н":"N","О":"O","П":"P","Р":"R","С":"S","Т":"T","У":"U","Ф":"F","Х":"X","Ц":"S","Ч":"Ch","Ш":"Sh","Щ":"Sh","Ъ":"","Ы":"I","Ь":"","Э":"E","Ю":"Yu","Я":"Ya",
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"yo","ж":"j","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"x","ц":"s","ч":"ch","ш":"sh","щ":"sh","ъ":"","ы":"i","ь":"","э":"e","ю":"yu","я":"ya",
})


def _latinize(value):
    return re.sub(r"\s+", " ", str(value or "").translate(_CYRILLIC_TO_LATIN)).strip()


def localize_directory_name(value, language):
    """Return a display-only translation while preserving the stored source value."""
    value = str(value or "").strip()
    language = language if language in {"ru", "uz", "uz-cyrl", "en"} else "ru"
    if not value or language == "ru":
        return value
    exact = POSITION_TRANSLATIONS.get(value) or PLATFORM_TRANSLATIONS.get(value)
    if exact:
        return exact.get(language, value)
    station = re.match(r"^[СC]танция\s+(.+)$", value, flags=re.IGNORECASE)
    if station:
        place = _latinize(station.group(1))
        if language == "uz":
            return f"{place} stansiyasi"
        if language == "uz-cyrl":
            return f"{station.group(1)} станцияси"
        return f"{place} Station"
    return _latinize(value) if language in {"uz", "en"} else value
