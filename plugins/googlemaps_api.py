import googlemaps

from cloudbot import api


@api('googlemaps')
class API:
    def __init__(self, bot):
        google_key = bot.config.get_api_key("google_dev_key")
        if google_key:
            self._api = googlemaps.Client(google_key)
        else:
            self._api = None

        self._region = bot.config.get('location_bias_cc')

    def geocode(self, address=None, components=None, bounds=None, region=None,
                language=None):
        if region is None:
            region = self._region

        return self._api.geocode(
            address=address,
            components=components,
            bounds=bounds,
            region=region,
            language=language,
        )

    def geocode_get_coords(self, *args, **kwargs):
        data = self.geocode(*args, **kwargs)
        result = data[0]
        out = result['geometry']['location']
        out['formatted_address'] = result['formatted_address']
        return out

    def timezone(self, location, timestamp=None, language=None):
        return self._api.timezone(
            location, timestamp=timestamp, language=language
        )
