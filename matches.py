import ssl
import aiohttp
import certifi
import logging
from datetime import datetime
import pytz

from config import FOOTBALL_API_KEY, WORLD_CUP_CODE, TIMEZONE

logger = logging.getLogger(__name__)
API_BASE = "https://api.football-data.org/v4"

COUNTRY_FLAGS = {
    "Argentina": "🇦🇷", "Australia": "🇦🇺", "Belgium": "🇧🇪", "Bolivia": "🇧🇴",
    "Brazil": "🇧🇷", "Cameroon": "🇨🇲", "Canada": "🇨🇦", "Chile": "🇨🇱",
    "China PR": "🇨🇳", "China": "🇨🇳", "Colombia": "🇨🇴", "Congo DR": "🇨🇩",
    "Costa Rica": "🇨🇷", "Croatia": "🇭🇷", "Czech Republic": "🇨🇿", "Czechia": "🇨🇿",
    "Denmark": "🇩🇰", "Ecuador": "🇪🇨", "Egypt": "🇪🇬", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France": "🇫🇷", "Georgia": "🇬🇪", "Germany": "🇩🇪", "Ghana": "🇬🇭",
    "Haiti": "🇭🇹", "Honduras": "🇭🇳", "Hungary": "🇭🇺", "Indonesia": "🇮🇩",
    "Iran": "🇮🇷", "Ivory Coast": "🇨🇮", "Jamaica": "🇯🇲", "Japan": "🇯🇵",
    "Jordan": "🇯🇴", "Mali": "🇲🇱", "Mexico": "🇲🇽", "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱", "Nigeria": "🇳🇬", "Norway": "🇳🇴", "Panama": "🇵🇦",
    "Paraguay": "🇵🇾", "Peru": "🇵🇪", "Poland": "🇵🇱", "Portugal": "🇵🇹",
    "Qatar": "🇶🇦", "Romania": "🇷🇴", "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Senegal": "🇸🇳", "Serbia": "🇷🇸", "Slovakia": "🇸🇰", "Slovenia": "🇸🇮",
    "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Spain": "🇪🇸", "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭", "Thailand": "🇹🇭", "Tunisia": "🇹🇳", "Turkey": "🇹🇷",
    "Türkiye": "🇹🇷", "Ukraine": "🇺🇦", "United States": "🇺🇸", "Uruguay": "🇺🇾",
    "Uzbekistan": "🇺🇿", "Venezuela": "🇻🇪", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Angola": "🇦🇴",
    "Albania": "🇦🇱", "Austria": "🇦🇹", "New Zealand": "🇳🇿",
}

TEAM_UA = {
    "Argentina": "Аргентина", "Australia": "Австралія", "Belgium": "Бельгія",
    "Bolivia": "Болівія", "Brazil": "Бразилія", "Cameroon": "Камерун",
    "Canada": "Канада", "Chile": "Чилі", "China PR": "Китай", "China": "Китай",
    "Colombia": "Колумбія", "Congo DR": "ДР Конго", "Costa Rica": "Коста-Ріка",
    "Croatia": "Хорватія", "Czech Republic": "Чехія", "Czechia": "Чехія",
    "Denmark": "Данія", "Ecuador": "Еквадор", "Egypt": "Єгипет", "England": "Англія",
    "France": "Франція", "Georgia": "Грузія", "Germany": "Німеччина", "Ghana": "Гана",
    "Haiti": "Гаїті", "Honduras": "Гондурас", "Hungary": "Угорщина",
    "Indonesia": "Індонезія", "Iran": "Іран", "Ivory Coast": "Кот-д'Івуар",
    "Jamaica": "Ямайка", "Japan": "Японія", "Jordan": "Йорданія", "Mali": "Малі",
    "Mexico": "Мексика", "Morocco": "Марокко", "Netherlands": "Нідерланди",
    "Nigeria": "Нігерія", "Norway": "Норвегія", "Panama": "Панама",
    "Paraguay": "Парагвай", "Peru": "Перу", "Poland": "Польща", "Portugal": "Португалія",
    "Qatar": "Катар", "Romania": "Румунія", "Saudi Arabia": "Саудівська Аравія",
    "Scotland": "Шотландія", "Senegal": "Сенегал", "Serbia": "Сербія",
    "Slovakia": "Словаччина", "Slovenia": "Словенія", "South Africa": "Південна Африка",
    "South Korea": "Південна Корея", "Spain": "Іспанія", "Sweden": "Швеція",
    "Switzerland": "Швейцарія", "Thailand": "Таїланд", "Tunisia": "Туніс",
    "Turkey": "Туреччина", "Türkiye": "Туреччина", "Ukraine": "Україна",
    "United States": "США", "Uruguay": "Уругвай", "Uzbekistan": "Узбекистан",
    "Venezuela": "Венесуела", "Wales": "Уельс", "Angola": "Ангола",
    "Albania": "Албанія", "Austria": "Австрія", "New Zealand": "Нова Зеландія",
}

STAGE_LABELS = {
    "GROUP_STAGE": "Груповий етап",
    "LAST_16": "1/8 фіналу",
    "QUARTER_FINALS": "Чвертьфінал",
    "SEMI_FINALS": "Півфінал",
    "THIRD_PLACE": "Матч за 3-є місце",
    "FINAL": "Фінал",
}

UA_MONTHS = ["", "січня", "лютого", "березня", "квітня", "травня", "червня",
             "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"]


def get_flag(team_name):
    return COUNTRY_FLAGS.get(team_name, "🏳️")


def get_ua_name(team_name):
    return TEAM_UA.get(team_name, team_name)


def stage_label(stage):
    return STAGE_LABELS.get(stage, stage.replace("_", " ").title())


async def fetch_wc_matches(date_str):
    url = f"{API_BASE}/competitions/{WORLD_CUP_CODE}/matches"
    params = {"dateFrom": date_str, "dateTo": date_str}
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)

    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            async with session.get(url, params=params, headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("matches", [])
                else:
                    logger.error(f"API error {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return []


async def get_todays_matches(hide_finished_scores=False):
    tz = pytz.timezone(TIMEZONE)
    today = datetime.now(tz)
    date_str = today.strftime("%Y-%m-%d")
    date_pretty = f"{today.day} {UA_MONTHS[today.month]} {today.year}"

    matches = await fetch_wc_matches(date_str)

    header = f"🌍 <b>ЧС-2026 — матчі на {date_pretty}</b>\n"

    if not matches:
        return f"{header}\nСьогодні матчів не заплановано 😴"

    matches.sort(key=lambda m: m.get("utcDate", ""))
    groups = {}
    for m in matches:
        stage = m.get("stage", "GROUP_STAGE")
        groups.setdefault(stage, []).append(m)

    lines = [header]

    for stage, stage_matches in groups.items():
        lines.append(f"\n<b>📌 {stage_label(stage)}</b>")

        for m in stage_matches:
            utc_date = m.get("utcDate", "")
            try:
                utc_dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                local_dt = utc_dt.astimezone(tz)
                time_str = local_dt.strftime("%H:%M")
            except Exception:
                time_str = "??:??"

            home_name = m.get("homeTeam", {}).get("name", "?")
            away_name = m.get("awayTeam", {}).get("name", "?")
            hf = get_flag(home_name)
            af = get_flag(away_name)
            home_ua = get_ua_name(home_name)
            away_ua = get_ua_name(away_name)

            status = m.get("status", "")
            score_data = m.get("score", {})

            if status == "FINISHED":
                if hide_finished_scores:
                    # Рахунок захований — показуємо що матч вже зіграно
                    score_str = "  ✅ зіграно"
                else:
                    ft = score_data.get("fullTime", {})
                    h, a = ft.get("home", "?"), ft.get("away", "?")
                    duration = score_data.get("duration", "REGULAR")
                    extra = " (д.ч.)" if duration == "EXTRA_TIME" else ""
                    if duration == "PENALTY_SHOOTOUT":
                        pen = score_data.get("penalties", {})
                        extra = f" (пен. {pen.get('home','?')}:{pen.get('away','?')})"
                    score_str = f"  ✅ {h}:{a}{extra}"
            elif status in ("IN_PLAY", "PAUSED", "LIVE"):
                ft = score_data.get("fullTime", {})
                h, a = ft.get("home", "?"), ft.get("away", "?")
                score_str = f"  🔴 LIVE {h}:{a}"
            elif status == "POSTPONED":
                score_str = "  ⚠️ Перенесено"
            else:
                score_str = ""

            group = m.get("group", "")
            group_str = f" <i>({group.replace('GROUP_', 'Група ')})</i>" if group else ""

            lines.append(f"🕐 {time_str}  {hf} {home_ua} — {af} {away_ua}{group_str}{score_str}")

    return "\n".join(lines)
