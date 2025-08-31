import re
HASHTAG_REGEX = re.compile(r"(^|\s)#(\w{1,64})\b", re.UNICODE)
def extract_hashtags(text: str) -> list[str]:
    tags = {m.group(2).lower() for m in HASHTAG_REGEX.finditer(text)}
    return list(tags)
