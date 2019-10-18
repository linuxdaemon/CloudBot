import re
import socket
from ipaddress import IPv4Network, IPv6Network, ip_address, IPv4Address, IPv6Address
from typing import Union

import requests
from yarl import URL

from cloudbot import hook
from cloudbot.hook import Action, Priority
from cloudbot.util import exc_util
from cloudbot.util.http import parse_soup, UrlOrStr

MAX_TITLE = 100

ALLOWED_PORTS = [80, 443]
IP_BLACKLIST = [
    IPv4Network('127.0.0.0/8'),
    IPv6Network('::1/128'),
]

ENCODED_CHAR = r"%[A-F0-9]{2}"
PATH_SEG_CHARS = r"[A-Za-z0-9!$&'*-.:;=@_~\u00A0-\U0010FFFD]|" + ENCODED_CHAR
QUERY_CHARS = PATH_SEG_CHARS + r"|/"
FRAG_CHARS = QUERY_CHARS


def no_parens(pattern):
    return r"{0}|\(({0}|[\(\)])*\)".format(pattern)


# This will match any URL, blacklist removed and abstracted to a priority/halting system
url_re = re.compile(
    r"""
    https? # Scheme
    ://
    
    # Username and Password
    (?:
        (?:[^\[\]?/<~#`!@$%^&*()=+}|:";',>{\s]|%[0-9A-F]{2})*
        (?::(?:[^\[\]?/<~#`!@$%^&*()=+}|:";',>{\s]|%[0-9A-F]{2})*)?
        @
    )?
    
    # Domain
    (?:
        # TODO Add support for IDNA hostnames as specified by RFC5891
        (?:[\-.0-9A-Za-z]+)
        (?<![.,?!\]])  # Invalid end chars
    )
    
    (?::\d*)?  # port
    
    (?:/(?:""" + no_parens(PATH_SEG_CHARS) + r""")*(?<![.,?!\]]))*  # Path segment
    
    (?:\?(?:""" + no_parens(QUERY_CHARS) + r""")*(?<![.,!\]]))?  # Query
    
    (?:\#(?:""" + no_parens(FRAG_CHARS) + r""")*(?<![.,?!\]]))?  # Fragment
    """,
    re.IGNORECASE | re.VERBOSE
)

HEADERS = {
    'Accept-Language': 'en-US,en;q=0.5',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/53.0.2785.116 Safari/537.36'
}

MAX_RECV = 1000000


def get_encoding(soup):
    meta_charset = soup.find('meta', charset=True)

    if meta_charset:
        return meta_charset['charset']

    meta_content_type = soup.find(
        'meta', {'http-equiv': lambda t: t and t.lower() == 'content-type', 'content': True}
    )
    if meta_content_type:
        return requests.utils.get_encoding_from_headers({'content-type': meta_content_type['content']})

    return None


def parse_content(content, encoding=None):
    html = parse_soup(content, from_encoding=encoding)
    old_encoding = encoding

    encoding = get_encoding(html)

    if encoding is not None and encoding != old_encoding:
        html = parse_soup(content, from_encoding=encoding)

    return html


ip_strip_re = re.compile(r'^\[?(.*)\]?$')

IPAddress = Union[IPv4Address, IPv6Address]


def is_ip_url(url: UrlOrStr) -> bool:
    """
    Returns whether a URL points to an IP address or a normal DNS name

    >>> is_ip_url('https://127.0.0.1/test')
    True
    >>> is_ip_url('https://127.0.0.1:80/test')
    True
    >>> is_ip_url('https://8.8.8.8/test')
    True
    >>> is_ip_url('https://google.com/test')
    False

    :param url: URL object to check
    :return: True if the URL's host is an IP address, False otherwise
    """

    url = URL(url)
    stripped_host = ip_strip_re.match(url.host).group(1)
    try:
        ip_address(stripped_host)
    except ValueError:
        return False

    return True


def is_ip_in_blacklist(ip: IPAddress) -> bool:
    return any(ip in net for net in IP_BLACKLIST)


def get_ips_for_hostname(hostname):
    try:
        ais = socket.getaddrinfo(hostname, 0)
    except socket.gaierror:
        return []

    return [ip_address(ai[4][0]) for ai in ais]


def is_url_allowed(url):
    url = URL(url)
    if url.port and url.port not in ALLOWED_PORTS:
        return False

    if is_ip_url(url):
        return False

    for ip in get_ips_for_hostname(url.host):
        if is_ip_in_blacklist(ip):
            return False

    return True


class InsecureRequestException(Exception):
    pass


def checker(session: requests.Session):
    def check_redirect(resp: requests.Response, **kwargs):
        next_req = next(session.resolve_redirects(
            resp, resp.request, yield_requests=True, **kwargs
        ), None)
        if next_req and not is_url_allowed(next_req.url):
            raise InsecureRequestException()

    return check_redirect


def get_soup(url):
    if not is_url_allowed(url):
        return None

    with requests.Session() as sesssion:
        response = sesssion.get(
            url, headers=HEADERS, stream=True, timeout=3,
            hooks={'response': [checker(sesssion)]},
        )
        with response:
            if not response.encoding or not response.ok:
                return None

            content = response.raw.read(MAX_RECV, decode_content=True)
            encoding = response.encoding

    html = parse_content(content, encoding)
    return html


@hook.regex(url_re, priority=Priority.LOW, action=Action.HALTTYPE, only_no_match=True)
def print_url_title(message, match, logger):
    try:
        html = get_soup(match.group())
    except InsecureRequestException:
        return
    except requests.exceptions.SSLError:
        logger.debug("SSL Error during link announce", exc_info=1)
        return
    except requests.ConnectTimeout:
        logger.debug("Connect timeout reached for %r", match.group())
        return
    except requests.ReadTimeout:
        logger.debug("Read timeout reached for %r", match.group())
        return
    except requests.ConnectionError as e:
        if exc_util.match_any_in_chain(e, ConnectionError):
            logger.debug("Connection error during link announce", exc_info=1)
            return

        raise

    if html and html.title and html.title.text:
        title = html.title.text.strip()

        if len(title) > MAX_TITLE:
            title = title[:MAX_TITLE] + " ... [trunc]"

        out = "Title: \x02{}\x02".format(title)
        message(out)
