import datetime
import re
import time

from cloudbot import hook


@hook.command("time")
def time_command(text, reply, bot):
    """<location> - Gets the current time in <location>."""
    googlemaps_api = bot.apis.googlemaps
    if not googlemaps_api:
        return "This command requires a Google Developers Console API key."

    if text.lower().startswith("utc") or text.lower().startswith("gmt"):
        timezone = text.strip()
        pattern = re.compile(r"utc|gmt|[:+]")
        utcoffset = [x for x in pattern.split(text.lower()) if x]
        if len(utcoffset) > 2:
            return "Please specify a valid UTC/GMT format Example: UTC-4, UTC+7 GMT7"
        if len(utcoffset) == 1:
            utcoffset.append('0')
        if len(utcoffset) == 2:
            try:
                offset = datetime.timedelta(hours=int(utcoffset[0]), minutes=int(utcoffset[1]))
            except Exception:
                reply("Sorry I could not parse the UTC format you entered. Example UTC7 or UTC-4")
                raise
            curtime = datetime.datetime.utcnow()
            tztime = curtime + offset
            formatted_time = datetime.datetime.strftime(tztime, '%I:%M %p, %A, %B %d, %Y')
            return "\x02{}\x02 ({})".format(formatted_time, timezone)

    location = googlemaps_api.geocode_get_coords(text)
    location_name = location['formatted_address']

    epoch = time.time()

    json = googlemaps_api.timezone(location, timestamp=epoch)

    # Work out the current time
    offset = json['rawOffset'] + json['dstOffset']

    # I'm telling the time module to parse the data as GMT, but whatever, it doesn't matter
    # what the time module thinks the timezone is. I just need dumb time formatting here.
    raw_time = time.gmtime(epoch + offset)
    formatted_time = time.strftime('%I:%M %p, %A, %B %d, %Y', raw_time)

    timezone = json['timeZoneName']

    return "\x02{}\x02 - {} ({})".format(formatted_time, location_name, timezone)


@hook.command(autohelp=False)
def beats(text):
    """- Gets the current time in .beats (Swatch Internet Time)."""

    if text.lower() == "wut":
        return "Instead of hours and minutes, the mean solar day is divided " \
               "up into 1000 parts called \".beats\". Each .beat lasts 1 minute and" \
               " 26.4 seconds. Times are notated as a 3-digit number out of 1000 af" \
               "ter midnight. So, @248 would indicate a time 248 .beats after midni" \
               "ght representing 248/1000 of a day, just over 5 hours and 57 minute" \
               "s. There are no timezones."

    if text.lower() == "guide":
        return "1 day = 1000 .beats, 1 hour = 41.666 .beats, 1 min = 0.6944 .beats, 1 second = 0.01157 .beats"

    t = time.gmtime()
    h, m, s = t.tm_hour, t.tm_min, t.tm_sec

    utc = 3600 * h + 60 * m + s
    bmt = utc + 3600  # Biel Mean Time (BMT)

    beat = bmt / 86.4

    if beat > 1000:
        beat -= 1000

    return "Swatch Internet Time: @%06.2f" % beat
