from cloudbot import hook


@hook.command("locate", "maps")
def locate(text, bot):
    """<location> - Finds <location> on Google Maps."""
    googlemaps_api = bot.apis.googlemaps

    # Use the Geocoding API to get co-ordinates from the input
    results = googlemaps_api.geocode(text)
    if not results:
        return "Unable to find location"

    result = results[0]

    location_name = result['formatted_address']
    location = result['geometry']['location']
    formatted_location = "{lat},{lng},16z".format(**location)

    url = "https://google.com/maps/@" + formatted_location + "/data=!3m1!1e3"
    tags = result['types']

    # if 'political' is not the only tag, remove it.
    if tags != ['political']:
        tags = [x for x in result['types'] if x != 'political']

    tags = ", ".join(tags).replace("_", " ")

    return "\x02{}\x02 - {} ({})".format(location_name, url, tags)
