from urllib import parse


def quote(url: str):
    quoted: str = parse.quote(url)
    print(quoted)
    return parse.quote(url).replace("%20", "+")
