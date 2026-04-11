from main.models import drivinglog, vehicleknowledge


MODEL_NORMALIZATION_MAP = {
    "Model-A": "比亚迪海豹",
    "M1": "五菱宏光MINIEV",
    "Geely Zeek": "极氪001",
    "NIO ES6 SU": "蔚来ES6",
    "BYD Han EV": "比亚迪汉EV",
    "SAIC Roewe": "荣威D7 EV",
    "GAC Aion S": "埃安AION S",
    "Li Auto L9": "理想L9",
    "Audi Q4 e-": "奥迪Q4 e-tron",
    "VW ID.3 20": "大众ID.3",
    "Tesla Mode": "特斯拉Model 3",
    "Great Wall": "欧拉好猫",
    "Jianghuai": "江淮钇为3",
    "Jianghuai ": "江淮钇为3",
    "Xpeng P7 P": "小鹏P7",
    "Chery Tigg": "奇瑞小蚂蚁",
    "Changan UN": "长安Lumin",
    "BMW iX3 20": "宝马iX3",
}

VEHICLE_NUMBER_NORMALIZATION_MAP = {
    "C1": "MINI-001",
}


def prepare_demo_data():
    updated_models = 0
    updated_numbers = 0

    for source, target in MODEL_NORMALIZATION_MAP.items():
        updated_models += drivinglog.objects.filter(vehiclemodel=source).update(vehiclemodel=target)

    for source, target in VEHICLE_NUMBER_NORMALIZATION_MAP.items():
        updated_numbers += drivinglog.objects.filter(vehiclenumber=source).update(vehiclenumber=target)

    deleted_knowledge, _ = vehicleknowledge.objects.all().delete()

    return {
        "updated_models": updated_models,
        "updated_numbers": updated_numbers,
        "deleted_knowledge": deleted_knowledge,
    }
