import copy
import json


BUILTIN_SOURCE_LABEL = "答辩演示内置知识库（外部站点触发安全验证时自动兜底）"


DEMO_VEHICLE_KNOWLEDGE = {
    "比亚迪海豹": {
        "manufacturer": "比亚迪",
        "batterytype": "刀片电池 / 磷酸铁锂电池",
        "officialrange": "550km / 650km / 700km",
        "chargeinfo": "支持直流快充，常见快充时间约0.5小时",
        "summary": "比亚迪海豹是基于e平台3.0打造的纯电轿车，主打中型纯电市场，兼顾续航、操控与智能化配置，常用于城市通勤和中长途出行场景演示。",
    },
    "五菱宏光MINIEV": {
        "manufacturer": "上汽通用五菱",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "120km / 170km / 215km / 280km",
        "chargeinfo": "以家用慢充为主，常见充电时间约6.5至9小时",
        "summary": "五菱宏光MINIEV是微型纯电车型代表，车身小巧、使用成本低，适合作为城市短途与共享出行场景的答辩示例车型。",
    },
    "极氪001": {
        "manufacturer": "极氪",
        "batterytype": "三元锂电池",
        "officialrange": "656km / 741km / 1032km",
        "chargeinfo": "支持高压快充与家用慢充",
        "summary": "极氪001定位中大型纯电猎装车，强调性能、空间和高续航能力，适合在系统中展示高端纯电车型的参数与知识库能力。",
    },
    "蔚来ES6": {
        "manufacturer": "蔚来",
        "batterytype": "75kWh / 100kWh / 150kWh 电池包",
        "officialrange": "500km / 625km / 930km",
        "chargeinfo": "支持快充、慢充和换电",
        "summary": "蔚来ES6是蔚来品牌的重要中型SUV，特点包括智能驾驶辅助、多规格电池包和换电体系，适合用于展示多补能方式车型。",
    },
    "比亚迪汉EV": {
        "manufacturer": "比亚迪",
        "batterytype": "刀片电池 / 磷酸铁锂电池",
        "officialrange": "506km / 605km / 715km",
        "chargeinfo": "支持直流快充与交流慢充",
        "summary": "比亚迪汉EV是比亚迪中大型纯电轿车代表车型，兼顾商务和家用定位，常见于续航与电池安全相关分析场景。",
    },
    "荣威D7 EV": {
        "manufacturer": "荣威",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "510km / 610km",
        "chargeinfo": "支持快充与慢充",
        "summary": "荣威D7 EV定位中型纯电轿车，强调舒适性、智能座舱和较长续航，适合用于展示主流家用纯电车型的知识采集效果。",
    },
    "埃安AION S": {
        "manufacturer": "埃安",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "430km / 510km / 610km",
        "chargeinfo": "支持快充与慢充",
        "summary": "埃安AION S是面向家用和网约车市场的紧凑型纯电轿车，保有量较高，适合用作行车日志与车型知识联动展示样本。",
    },
    "理想L9": {
        "manufacturer": "理想汽车",
        "batterytype": "三元锂电池",
        "officialrange": "CLTC纯电续航约215km",
        "chargeinfo": "支持快充，长途可结合增程补能",
        "summary": "理想L9为大型增程式SUV，兼顾纯电短途通勤与长途续航扩展，适合在系统中展示新能源车型的多样化补能路线。",
    },
    "奥迪Q4 e-tron": {
        "manufacturer": "奥迪",
        "batterytype": "三元锂电池",
        "officialrange": "560km / 605km",
        "chargeinfo": "支持快充与家用慢充",
        "summary": "奥迪Q4 e-tron是豪华品牌纯电SUV，强调品牌质感、智能座舱和主流续航水平，可作为合资纯电车型示例。",
    },
    "大众ID.3": {
        "manufacturer": "大众",
        "batterytype": "三元锂电池",
        "officialrange": "450km",
        "chargeinfo": "支持快充与慢充",
        "summary": "大众ID.3是大众MEB平台下的紧凑型纯电两厢车，适合作为合资品牌城市通勤纯电车型的知识样本。",
    },
    "特斯拉Model 3": {
        "manufacturer": "特斯拉",
        "batterytype": "磷酸铁锂电池 / 三元锂电池",
        "officialrange": "606km / 713km",
        "chargeinfo": "支持超级充电与家用充电",
        "summary": "特斯拉Model 3是高关注度纯电轿车，具备智能化程度高、补能体系成熟等特点，适合在答辩时展示热门车型知识采集效果。",
    },
    "欧拉好猫": {
        "manufacturer": "欧拉",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "401km / 501km",
        "chargeinfo": "支持快充与慢充",
        "summary": "欧拉好猫定位时尚小型纯电车型，强调城市代步、外观设计和智能配置，是展示细分市场车型知识的合适样本。",
    },
    "江淮钇为3": {
        "manufacturer": "江淮钇为",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "405km / 505km / 602km",
        "chargeinfo": "支持快充与慢充",
        "summary": "江淮钇为3是面向年轻家用市场的纯电小型车，具备多续航版本和轻量化城市出行定位，适合用于多车型数据展示。",
    },
    "小鹏P7": {
        "manufacturer": "小鹏汽车",
        "batterytype": "三元锂电池",
        "officialrange": "480km / 586km / 702km",
        "chargeinfo": "支持快充与慢充",
        "summary": "小鹏P7是小鹏品牌代表性纯电轿跑，突出智能驾驶与长续航能力，适合在系统中展示智能电动车知识采集能力。",
    },
    "奇瑞小蚂蚁": {
        "manufacturer": "奇瑞新能源",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "251km / 301km / 408km",
        "chargeinfo": "支持慢充，部分版本支持快充",
        "summary": "奇瑞小蚂蚁是典型微型纯电车型，适合展示低速城市代步场景和轻量级车型知识库样本。",
    },
    "长安Lumin": {
        "manufacturer": "长安",
        "batterytype": "磷酸铁锂电池",
        "officialrange": "205km / 301km",
        "chargeinfo": "支持慢充，部分版本支持快充",
        "summary": "长安Lumin是面向城市代步的微型纯电车型，三门四座布局较具辨识度，适合用于系统答辩中的轻量化车型展示。",
    },
    "宝马iX3": {
        "manufacturer": "宝马",
        "batterytype": "三元锂电池",
        "officialrange": "500km / 540km",
        "chargeinfo": "支持快充与慢充",
        "summary": "宝马iX3是宝马品牌中型纯电SUV，适合用于展示豪华品牌纯电车型在知识库中的收录与管理效果。",
    },
}


def get_builtin_vehicle_knowledge(vehiclemodel, reason=""):
    template = DEMO_VEHICLE_KNOWLEDGE.get((vehiclemodel or "").strip())
    if template is None:
        return None

    payload = copy.deepcopy(template)
    payload.update(
        {
            "vehiclemodel": (vehiclemodel or "").strip(),
            "sourceurl": BUILTIN_SOURCE_LABEL,
            "crawlstatus": "成功",
        }
    )
    payload["rawdata"] = json.dumps(
        {
            "source": "builtin_demo_knowledge",
            "reason": reason or "external_sources_unavailable",
            "data": copy.deepcopy(template),
        },
        ensure_ascii=False,
    )
    return payload
