# coding:utf-8
import datetime
import json

from django.db.models import Q
from django.http import JsonResponse

from util.CustomJSONEncoder import CustomJsonEncoder
from util.codes import *
import util.message as mes
from util.vehicle_knowledge_crawler import build_vehicle_knowledge_url, fetch_vehicle_knowledge

from .models import drivinglog, vehicleknowledge


def _req_dict(request):
    return dict(request.session.get("req_dict", {}) or {})


def _model_fields():
    return {field.name for field in vehicleknowledge._meta.fields}


def _serialize_record(record):
    data = vehicleknowledge.getbyid(vehicleknowledge, vehicleknowledge, record.id)
    return data[0] if data else {}


def _upsert_vehicleknowledge(payload):
    payload = dict(payload or {})
    payload["vehiclemodel"] = (payload.get("vehiclemodel") or "").strip()
    payload["crawltime"] = datetime.datetime.now()
    allowed_fields = _model_fields() - {"id", "addtime"}
    filtered_payload = {key: value for key, value in payload.items() if key in allowed_fields}
    record = vehicleknowledge.objects.filter(vehiclemodel=payload["vehiclemodel"]).first()
    if record:
        for key, value in filtered_payload.items():
            setattr(record, key, value)
        record.save(update_fields=list(filtered_payload.keys()))
        return record, False
    record = vehicleknowledge.objects.create(**filtered_payload)
    return record, True


def _crawl_one(vehiclemodel):
    vehiclemodel = (vehiclemodel or "").strip()
    if not vehiclemodel:
        raise ValueError("车型名称不能为空")
    try:
        payload = fetch_vehicle_knowledge(vehiclemodel)
        error_message = ""
    except Exception as exc:
        payload = {
            "vehiclemodel": vehiclemodel,
            "manufacturer": "",
            "batterytype": "",
            "officialrange": "",
            "chargeinfo": "",
            "summary": "",
            "sourceurl": build_vehicle_knowledge_url(vehiclemodel),
            "crawlstatus": "失败",
            "rawdata": json.dumps({"error": str(exc)}, ensure_ascii=False),
        }
        error_message = str(exc)
    record, created = _upsert_vehicleknowledge(payload)
    return record, created, error_message


def vehicleknowledge_default(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        req_dict.update({"isdefault": "是"})
        data = vehicleknowledge.getbyparams(vehicleknowledge, vehicleknowledge, req_dict)
        msg["data"] = data[0] if data else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_page(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {"currPage": 1, "totalPage": 1, "total": 1, "pageSize": 10, "list": []}}
        req_dict = _req_dict(request)
        msg["data"]["list"], msg["data"]["currPage"], msg["data"]["totalPage"], msg["data"]["total"], msg["data"]["pageSize"] = vehicleknowledge.page(vehicleknowledge, vehicleknowledge, req_dict, request, Q())
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_autoSort(request):
    if request.method in ["POST", "GET"]:
        req_dict = _req_dict(request)
        req_dict["sort"] = req_dict.get("sort") or "crawltime"
        req_dict["order"] = req_dict.get("order") or "desc"
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {"currPage": 1, "totalPage": 1, "total": 1, "pageSize": 10, "list": []}}
        msg["data"]["list"], msg["data"]["currPage"], msg["data"]["totalPage"], msg["data"]["total"], msg["data"]["pageSize"] = vehicleknowledge.page(vehicleknowledge, vehicleknowledge, req_dict, request, Q())
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_lists(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": []}
        msg["data"], _, _, _, _ = vehicleknowledge.page(vehicleknowledge, vehicleknowledge, {}, request, Q())
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_query(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        query_result = vehicleknowledge.objects.filter(**_req_dict(request)).values()
        msg["data"] = query_result[0] if query_result else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_list(request):
    if request.method in ["POST", "GET"]:
        return vehicleknowledge_page(request)


def vehicleknowledge_save(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        saved_id = vehicleknowledge.createbyreq(vehicleknowledge, vehicleknowledge, req_dict)
        if saved_id is Exception or (isinstance(saved_id, str) and "Exception" in saved_id):
            msg["code"] = crud_error_code
            msg["msg"] = str(saved_id)
        else:
            msg["data"] = saved_id
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_add(request):
    return vehicleknowledge_save(request)


def vehicleknowledge_thumbsup(request, id_):
    return JsonResponse({"code": normal_code, "msg": mes.normal_code, "data": {}}, encoder=CustomJsonEncoder)


def vehicleknowledge_info(request, id_):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        data = vehicleknowledge.getbyid(vehicleknowledge, vehicleknowledge, int(id_))
        msg["data"] = data[0] if data else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_detail(request, id_):
    return vehicleknowledge_info(request, id_)


def vehicleknowledge_update(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        error = vehicleknowledge.updatebyparams(vehicleknowledge, vehicleknowledge, req_dict)
        if error is not None:
            msg["code"] = crud_error_code
            msg["msg"] = str(error)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_delete(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        error = vehicleknowledge.deletes(vehicleknowledge, vehicleknowledge, req_dict.get("ids") or [])
        if error is not None:
            msg["code"] = crud_error_code
            msg["msg"] = str(error)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_vote(request, id_):
    return JsonResponse({"code": normal_code, "msg": mes.normal_code}, encoder=CustomJsonEncoder)


def vehicleknowledge_importExcel(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        excel_file = request.FILES.get("file")
        if excel_file is None:
            msg["code"] = 400
            msg["msg"] = "请选择Excel文件"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        suffix = excel_file.name.rsplit(".", 1)[-1].lower() if "." in excel_file.name else ""
        if suffix not in ["xlsx", "xls"]:
            msg["code"] = 500
            msg["msg"] = "文件类型错误"
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_autoSort2(request):
    return vehicleknowledge_autoSort(request)


def vehicleknowledge_queryByModel(request):
    if request.method in ["POST", "GET"]:
        req_dict = _req_dict(request)
        vehiclemodel = (req_dict.get("vehiclemodel") or "").strip()
        record = vehicleknowledge.objects.filter(vehiclemodel=vehiclemodel).first()
        return JsonResponse({"code": normal_code, "msg": mes.normal_code, "data": _serialize_record(record) if record else {}}, encoder=CustomJsonEncoder)


def vehicleknowledge_crawlByModel(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        vehiclemodel = (req_dict.get("vehiclemodel") or "").strip()
        if not vehiclemodel:
            msg["code"] = other_code
            msg["msg"] = "车型名称不能为空"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        record, created, error_message = _crawl_one(vehiclemodel)
        if error_message:
            msg["code"] = other_code
            msg["msg"] = error_message
        msg["data"] = {
            "id": record.id,
            "vehiclemodel": record.vehiclemodel,
            "crawlstatus": record.crawlstatus,
            "created": created,
        }
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def vehicleknowledge_crawlBatch(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        distinct_models = []
        seen = set()
        for model_name in drivinglog.objects.exclude(vehiclemodel__isnull=True).exclude(vehiclemodel="").values_list("vehiclemodel", flat=True):
            value = (model_name or "").strip()
            if value and value not in seen:
                seen.add(value)
                distinct_models.append(value)
        items = []
        success_count = 0
        failed_count = 0
        for model_name in distinct_models:
            record, created, error_message = _crawl_one(model_name)
            if record.crawlstatus == "成功":
                success_count += 1
            else:
                failed_count += 1
            items.append(
                {
                    "id": record.id,
                    "vehiclemodel": record.vehiclemodel,
                    "crawlstatus": record.crawlstatus,
                    "created": created,
                    "error": error_message,
                }
            )
        msg["data"] = {
            "total": len(distinct_models),
            "success": success_count,
            "failed": failed_count,
            "items": items,
        }
        return JsonResponse(msg, encoder=CustomJsonEncoder)
