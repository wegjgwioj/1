# coding:utf-8
import json
import re
from urllib.parse import quote

import requests
from lxml import html

from util.demo_vehicle_knowledge import get_builtin_vehicle_knowledge


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

SEARCH_PROVIDERS = (
    {"name": "bing", "base_url": "https://cn.bing.com/search?q={query}"},
    {"name": "so", "base_url": "https://www.so.com/s?q={query}"},
)
SEARCH_REWRITE_MAP = {
    "BYD": "比亚迪",
    "NIO": "蔚来",
    "Li Auto": "理想",
    "GAC": "广汽",
    "Aion": "埃安",
    "SAIC": "上汽",
    "Roewe": "荣威",
    "Geely": "吉利",
    "Zeekr": "极氪",
    "Zeek": "极氪",
    "Great Wall": "长城汽车",
}
AUTOMOTIVE_KEYWORDS = {
    "汽车",
    "车型",
    "续航",
    "电池",
    "充电",
    "纯电",
    "新能源",
    "参数",
    "报价",
    "试驾",
    "轿车",
    "suv",
    "cltc",
    "电机",
    "autohome",
    "pcauto",
    "yiche",
    "nio",
    "byd",
    "bmw",
    "roewe",
    "xpeng",
}
AUTOMOTIVE_KEYWORDS.update({value.lower() for value in SEARCH_REWRITE_MAP.values()})
AUTOMOTIVE_KEYWORDS.update({key.lower() for key in SEARCH_REWRITE_MAP.keys()})
BLOCKED_PAGE_SIGNALS = (
    "百度安全验证",
    "访问异常页面",
    "qcaptcha",
    "请输入验证码",
    "安全验证",
    "captcha",
)
TRUSTED_AUTOMOTIVE_DOMAINS = (
    "autohome.com.cn",
    "pcauto.com.cn",
    "yiche.com",
    "cheshi.com",
    "dongchedi.com",
    "bitauto.com",
    "baike.so.com",
)


def build_vehicle_knowledge_url(vehiclemodel):
    return f"https://baike.baidu.com/item/{quote((vehiclemodel or '').strip())}"


def _clean_text(value):
    if value is None:
        return ""
    if hasattr(value, "text_content"):
        value = value.text_content()
    value = str(value)
    value = re.sub(r"\[\d+\]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _extract_summary(tree):
    summary_nodes = tree.xpath(
        "//div[contains(@class,'lemmaSummary')]"
        "|//div[contains(@class,'J-summary')]"
        "|//div[contains(@class,'lemma-summary')]"
    )
    texts = [_clean_text(node) for node in summary_nodes]
    texts = [text for text in texts if text]
    if texts:
        return " ".join(texts)

    description = tree.xpath("//meta[@name='description']/@content")
    return _clean_text(description[0]) if description else ""


def _extract_basic_info(tree):
    info = {}
    containers = tree.xpath("//div[contains(@class,'basic-info') or contains(@class,'basicInfo')]")
    for container in containers:
        names = [_clean_text(item) for item in container.xpath(".//dt")]
        values = [_clean_text(item) for item in container.xpath(".//dd")]
        for name, value in zip(names, values):
            if name and value:
                info[name] = value
    return info


def _pick_value(info, keywords):
    for key, value in info.items():
        for keyword in keywords:
            if keyword in key:
                return value
    return ""


def _build_chargeinfo(info):
    pairs = []
    values = []
    for key, value in info.items():
        if "充电" in key or "快充" in key or "慢充" in key:
            pairs.append(f"{key}:{value}")
            values.append(value)
    if len(values) == 1:
        return values[0]
    return "；".join(pairs)


def _compact_text(text):
    return re.sub(r"\s+", "", _clean_text(text))


def _rewrite_search_query(vehiclemodel):
    rewritten = (vehiclemodel or "").strip()
    for source, target in SEARCH_REWRITE_MAP.items():
        rewritten = rewritten.replace(source, target)
    return rewritten.strip()


def _build_search_queries(vehiclemodel):
    base = (vehiclemodel or "").strip()
    queries = []

    def _add(value):
        value = (value or "").strip()
        if value and value not in queries:
            queries.append(value)

    rewritten = _rewrite_search_query(base)
    candidates = [rewritten, rewritten.replace(" ", ""), base]

    for candidate in list(candidates):
        tokens = candidate.split()
        if len(tokens) > 1 and len(tokens[-1]) <= 2:
            _add(" ".join(tokens[:-1]))
    for candidate in candidates:
        _add(candidate)
        _add("%s 汽车" % candidate)
        _add("%s 续航 电池" % candidate)

    return queries


def _extract_batterytype_from_text(text):
    for keyword in ["磷酸铁锂电池", "三元锂电池", "刀片电池", "锂电池", "电池组"]:
        if keyword in text:
            return keyword
    return ""


def _extract_officialrange_from_text(text):
    matches = re.findall(r"\d{2,4}\s*(?:km|KM|公里)", text)
    ordered_matches = []
    for item in matches:
        clean_item = item.upper().replace("KM", "km").replace(" ", "")
        if clean_item not in ordered_matches:
            ordered_matches.append(clean_item)
    return " / ".join(ordered_matches[:3])


def _extract_chargeinfo_from_text(text):
    matches = re.findall(r"(?:快充|慢充|充电)[^。；，]{0,30}", text)
    for item in matches:
        clean_item = _clean_text(item)
        if clean_item:
            return clean_item
    return ""


def _guess_manufacturer(vehiclemodel, text):
    text = _clean_text(text)
    regex_patterns = [
        r"【[^】]+】\s*([^_]+)_",
        r"([A-Za-z\u4e00-\u9fa5]+)旗下",
        r"所属品牌[:：]?\s*([A-Za-z\u4e00-\u9fa5]+)",
    ]
    for pattern in regex_patterns:
        match = re.search(pattern, text)
        if match:
            manufacturer = _clean_text(match.group(1))
            if manufacturer and manufacturer != vehiclemodel:
                return manufacturer

    tokens = (vehiclemodel or "").split()
    if len(tokens) >= 2 and tokens[1].lower() in {"auto", "aion", "roewe"}:
        return " ".join(tokens[:2])
    if tokens:
        first_token = tokens[0]
        if re.fullmatch(r"[A-Za-z]+", first_token):
            return first_token
    return ""


def _search_match_score(title, snippet, href, vehiclemodel):
    combined = _compact_text("%s %s %s" % (title, snippet, href)).lower()
    score = 0

    for query in _build_search_queries(vehiclemodel):
        compact_query = _compact_text(query).lower()
        if compact_query and compact_query in combined:
            score += 30

    rewritten = _rewrite_search_query(vehiclemodel)
    tokens = [token.lower() for token in re.split(r"[\s\-_]+", rewritten) if len(token) > 1]
    for token in tokens:
        if token in combined:
            score += 8

    if "baike.so.com" in href or "百科" in title:
        score += 20
    if snippet:
        score += min(len(snippet), 120) // 6
    return score


def _has_automotive_signal(text, href):
    combined = ("%s %s" % (text, href)).lower()
    return any(keyword and keyword in combined for keyword in AUTOMOTIVE_KEYWORDS)


def _page_is_blocked(content, url=""):
    text = _clean_text(content).lower()
    url = (url or "").lower()
    return any(signal.lower() in text or signal.lower() in url for signal in BLOCKED_PAGE_SIGNALS)


def _build_search_payload(vehiclemodel, sourceurl, title, snippet, text, href):
    return {
        "vehiclemodel": (vehiclemodel or "").strip(),
        "manufacturer": _guess_manufacturer(vehiclemodel, text),
        "batterytype": _extract_batterytype_from_text(text),
        "officialrange": _extract_officialrange_from_text(text),
        "chargeinfo": _extract_chargeinfo_from_text(text),
        "summary": snippet or title,
        "sourceurl": href or sourceurl,
        "crawlstatus": "成功",
        "rawdata": json.dumps(
            {"title": title, "snippet": snippet, "sourceurl": href or sourceurl},
            ensure_ascii=False,
        ),
    }


def _payload_quality_score(payload):
    fields = ("manufacturer", "batterytype", "officialrange", "chargeinfo", "summary")
    return sum(1 for field in fields if _clean_text((payload or {}).get(field)))


def _prefer_builtin_demo_payload(vehiclemodel, payload, reason):
    builtin_payload = get_builtin_vehicle_knowledge(vehiclemodel, reason=reason)
    if builtin_payload is None:
        return payload
    if payload is None or _payload_quality_score(payload) < 3:
        return builtin_payload
    return payload


def _extract_so_search_result(tree, vehiclemodel, sourceurl):
    best_payload = None
    best_score = -1
    for node in tree.xpath("//li[contains(@class,'res-list')]"):
        title = _clean_text("".join(node.xpath(".//h3//text()")))
        href = _clean_text("".join(node.xpath(".//h3/a/@href")))
        snippet = _clean_text(
            " ".join(node.xpath(".//p//text() | .//div[contains(@class,'res-desc')]//text()"))
        )
        if not title and not snippet:
            continue

        text = _clean_text("%s %s" % (title, snippet))
        if not _has_automotive_signal(text, href):
            continue
        payload = _build_search_payload(vehiclemodel, sourceurl, title, snippet, text, href)
        score = _search_match_score(title, snippet, href, vehiclemodel)
        if score > best_score:
            best_payload = payload
            best_score = score

    if best_payload is not None:
        return best_payload
    raise ValueError("未找到可用的公开搜索结果")


def _extract_bing_search_result(tree, vehiclemodel, sourceurl):
    best_payload = None
    best_score = -1
    for node in tree.xpath("//li[contains(@class,'b_algo')]"):
        title = _clean_text("".join(node.xpath(".//h2//text()")))
        href = _clean_text("".join(node.xpath(".//h2/a/@href")))
        snippet = _clean_text(" ".join(node.xpath(".//div[contains(@class,'b_caption')]//p//text()")))
        if not title and not snippet:
            continue

        text = _clean_text("%s %s" % (title, snippet))
        compact_query = _compact_text(vehiclemodel).lower()
        compact_text = _compact_text(text).lower()
        compact_href = _compact_text(href).lower()

        if compact_query and compact_query not in compact_text and compact_query not in compact_href:
            continue
        if not _has_automotive_signal(text, href):
            continue

        payload = _build_search_payload(vehiclemodel, sourceurl, title, snippet, text, href)
        score = _search_match_score(title, snippet, href, vehiclemodel)
        if any(domain in (href or "").lower() for domain in TRUSTED_AUTOMOTIVE_DOMAINS):
            score += 25
        if payload.get("summary"):
            score += 10
        if score > best_score:
            best_payload = payload
            best_score = score

    if best_payload is not None:
        return best_payload
    raise ValueError("未找到可用的公开搜索结果")


def _extract_search_result(tree, vehiclemodel, sourceurl, provider_name):
    if provider_name == "bing":
        return _extract_bing_search_result(tree, vehiclemodel, sourceurl)
    return _extract_so_search_result(tree, vehiclemodel, sourceurl)


def search_vehicle_knowledge(vehiclemodel, timeout=15):
    last_error = None
    for provider in SEARCH_PROVIDERS:
        for query in _build_search_queries(vehiclemodel):
            search_url = provider["base_url"].format(query=quote(query))
            try:
                response = requests.get(search_url, headers=DEFAULT_HEADERS, timeout=timeout)
                response.raise_for_status()
                if _page_is_blocked(response.text, response.url or search_url):
                    raise ValueError("搜索源触发安全验证")
                payload = _extract_search_result(
                    html.fromstring(response.text),
                    vehiclemodel,
                    response.url or search_url,
                    provider["name"],
                )
                if payload.get("summary"):
                    return payload
            except Exception as exc:
                last_error = exc
                continue

    if last_error is not None:
        raise last_error
    raise ValueError("未找到可用的公开搜索结果")


def extract_vehicle_knowledge(html_string, vehiclemodel, sourceurl):
    tree = html.fromstring(html_string)
    summary = _extract_summary(tree)
    basic_info = _extract_basic_info(tree)
    manufacturer = _pick_value(basic_info, ["所属品牌", "品牌", "生产厂商", "厂商", "生产企业"])
    batterytype = _pick_value(basic_info, ["电池类型", "电池种类", "动力电池"])
    officialrange = _pick_value(basic_info, ["CLTC纯电续航", "NEDC续航", "纯电续航", "续航里程", "综合续航"])
    chargeinfo = _build_chargeinfo(basic_info) or _pick_value(basic_info, ["充电时间"])
    crawlstatus = "成功" if any([summary, manufacturer, batterytype, officialrange, chargeinfo]) else "失败"
    return {
        "vehiclemodel": (vehiclemodel or "").strip(),
        "manufacturer": manufacturer,
        "batterytype": batterytype,
        "officialrange": officialrange,
        "chargeinfo": chargeinfo,
        "summary": summary,
        "sourceurl": sourceurl,
        "crawlstatus": crawlstatus,
        "rawdata": json.dumps(basic_info, ensure_ascii=False),
    }


def fetch_vehicle_knowledge(vehiclemodel, timeout=15):
    vehiclemodel = (vehiclemodel or "").strip()
    if not vehiclemodel:
        raise ValueError("车型名称不能为空")
    sourceurl = build_vehicle_knowledge_url(vehiclemodel)
    last_error = None
    try:
        response = requests.get(sourceurl, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
        if _page_is_blocked(response.text, response.url or sourceurl):
            raise ValueError("百科页面触发安全验证")
        payload = extract_vehicle_knowledge(response.text, vehiclemodel, response.url or sourceurl)
        if payload.get("crawlstatus") == "成功":
            return payload
    except Exception as exc:
        last_error = exc

    try:
        payload = search_vehicle_knowledge(vehiclemodel, timeout=timeout)
        return _prefer_builtin_demo_payload(vehiclemodel, payload, "public_search_payload_fields_insufficient")
    except Exception as exc:
        last_error = exc

    fallback_payload = get_builtin_vehicle_knowledge(vehiclemodel, reason=str(last_error or "external_sources_unavailable"))
    if fallback_payload is not None:
        return fallback_payload
    if last_error is not None:
        raise last_error
    raise ValueError("未找到可用的公开搜索结果")
