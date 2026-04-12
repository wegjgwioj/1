# coding:utf-8
import datetime

from django.db.models import Q
from django.http import JsonResponse

from util.CustomJSONEncoder import CustomJsonEncoder
from util.auth import Auth
from util.codes import *
import util.message as mes

from .models import drivinglog, storeup

DEFAULT_STOREUP_PICTURE = "upload/image1.jpg"


def _req_dict(request):
    return dict(request.session.get("req_dict", {}) or {})


def _current_user_id(request):
    return Auth().getTokenInfo(request).get("params", {}).get("id")


def _sync_storeupnum(tablename, refid):
    if tablename != "drivinglog" or not refid:
        return
    total = storeup.objects.filter(tablename="drivinglog", refid=refid).count()
    drivinglog.objects.filter(id=refid).update(storeupnum=total)


def _fallback_picture(tablename):
    if tablename == "drivinglog":
        return DEFAULT_STOREUP_PICTURE
    return ""


def _normalize_storeup_record(record):
    if not record:
        return record
    if not record.get("picture"):
        record["picture"] = _fallback_picture(record.get("tablename"))
    return record


def _normalize_storeup_list(records):
    return [_normalize_storeup_record(record) for record in records]


def _enrich_storeup_payload(request_dict, user_id):
    payload = dict(request_dict)
    payload["userid"] = payload.get("userid") or user_id
    payload["tablename"] = payload.get("tablename") or "drivinglog"
    payload["type"] = payload.get("type") or "1"
    payload["picture"] = payload.get("picture") or _fallback_picture(payload["tablename"])
    refid = int(payload.get("refid", 0) or 0)

    if payload["tablename"] == "drivinglog" and refid:
        record = drivinglog.objects.filter(id=refid).first()
        if record:
            payload["name"] = payload.get("name") or record.vehiclenumber or record.vehiclemodel or f"drivinglog-{refid}"
            if not payload.get("inteltype"):
                payload["inteltype"] = "vehiclemodel" if record.vehiclemodel else "drivingroute"
        else:
            payload["name"] = payload.get("name") or f"drivinglog-{refid}"
    else:
        payload["name"] = payload.get("name") or f"{payload['tablename']}-{refid}"

    return payload


def storeup_default(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        req_dict.update({"isdefault": "是"})
        data = storeup.getbyparams(storeup, storeup, req_dict)
        msg["data"] = _normalize_storeup_record(data[0]) if data else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_page(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {"currPage": 1, "totalPage": 1, "total": 1, "pageSize": 10, "list": []}}
        req_dict = _req_dict(request)
        if Auth().getTokenInfo(request).get("tablename") != "users":
            req_dict["userid"] = _current_user_id(request)
        msg["data"]["list"], msg["data"]["currPage"], msg["data"]["totalPage"], msg["data"]["total"], msg["data"]["pageSize"] = storeup.page(storeup, storeup, req_dict, request, Q())
        msg["data"]["list"] = _normalize_storeup_list(msg["data"]["list"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_autoSort(request):
    if request.method in ["POST", "GET"]:
        req_dict = _req_dict(request)
        req_dict["sort"] = "addtime"
        req_dict["order"] = "desc"
        if Auth().getTokenInfo(request).get("tablename") != "users":
            req_dict["userid"] = _current_user_id(request)
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {"currPage": 1, "totalPage": 1, "total": 1, "pageSize": 10, "list": []}}
        msg["data"]["list"], msg["data"]["currPage"], msg["data"]["totalPage"], msg["data"]["total"], msg["data"]["pageSize"] = storeup.page(storeup, storeup, req_dict, request, Q())
        msg["data"]["list"] = _normalize_storeup_list(msg["data"]["list"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_lists(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": []}
        req_dict = {}
        if Auth().getTokenInfo(request).get("tablename") != "users":
            req_dict["userid"] = _current_user_id(request)
        msg["data"], _, _, _, _ = storeup.page(storeup, storeup, req_dict, request, Q())
        msg["data"] = _normalize_storeup_list(msg["data"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_query(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        query_result = storeup.objects.filter(**_req_dict(request)).values()
        msg["data"] = _normalize_storeup_record(query_result[0]) if query_result else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_list(request):
    if request.method in ["POST", "GET"]:
        return storeup_page(request)


def storeup_save(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        user_id = req_dict.get("userid") or _current_user_id(request)
        req_dict = _enrich_storeup_payload(req_dict, user_id)
        existing = storeup.objects.filter(userid=req_dict["userid"], refid=req_dict["refid"], tablename=req_dict["tablename"]).first()
        if existing:
            msg["data"] = existing.id
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        storeup_id = storeup.createbyreq(storeup, storeup, req_dict)
        if storeup_id is Exception or (isinstance(storeup_id, str) and "Exception" in storeup_id):
            msg["code"] = crud_error_code
            msg["msg"] = str(storeup_id)
        else:
            _sync_storeupnum(req_dict["tablename"], int(req_dict["refid"]))
            msg["data"] = storeup_id
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_add(request):
    return storeup_save(request)


def storeup_thumbsup(request, id_):
    return JsonResponse({"code": normal_code, "msg": mes.normal_code, "data": {}}, encoder=CustomJsonEncoder)


def storeup_info(request, id_):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        data = storeup.getbyid(storeup, storeup, int(id_))
        msg["data"] = _normalize_storeup_record(data[0]) if data else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_detail(request, id_):
    return storeup_info(request, id_)


def storeup_update(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        original = storeup.objects.filter(id=req_dict.get("id")).first()
        if req_dict.get("userid") is None and original:
            req_dict["userid"] = original.userid
        error = storeup.updatebyparams(storeup, storeup, req_dict)
        if error is not None:
            msg["code"] = crud_error_code
            msg["msg"] = str(error)
        else:
            if original:
                _sync_storeupnum(original.tablename, original.refid)
            updated = storeup.objects.filter(id=req_dict.get("id")).first()
            if updated:
                _sync_storeupnum(updated.tablename, updated.refid)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_delete(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        ids = req_dict.get("ids") or []
        records = list(storeup.objects.filter(id__in=ids).values("tablename", "refid"))
        error = storeup.deletes(storeup, storeup, ids)
        if error is not None:
            msg["code"] = crud_error_code
            msg["msg"] = str(error)
        else:
            for record in records:
                _sync_storeupnum(record["tablename"], record["refid"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_vote(request, id_):
    return JsonResponse({"code": normal_code, "msg": mes.normal_code}, encoder=CustomJsonEncoder)


def storeup_importExcel(request):
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


def storeup_autoSort2(request):
    return storeup_autoSort(request)


def storeup_toggle(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        user_id = _current_user_id(request)
        refid = int(req_dict.get("refid", 0) or 0)
        tablename = req_dict.get("tablename") or "drivinglog"
        existing = storeup.objects.filter(userid=user_id, refid=refid, tablename=tablename).first()
        if existing:
            existing.delete()
            _sync_storeupnum(tablename, refid)
            msg["data"] = {"storeup": False}
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        payload = _enrich_storeup_payload(req_dict, user_id)
        storeup_id = storeup.createbyreq(storeup, storeup, payload)
        if storeup_id is Exception or (isinstance(storeup_id, str) and "Exception" in storeup_id):
            msg["code"] = crud_error_code
            msg["msg"] = str(storeup_id)
        else:
            _sync_storeupnum(tablename, refid)
            msg["data"] = {"storeup": True, "id": storeup_id}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def storeup_isStoreup(request):
    if request.method in ["POST", "GET"]:
        req_dict = _req_dict(request)
        user_id = _current_user_id(request)
        refid = int(req_dict.get("refid", 0) or 0)
        tablename = req_dict.get("tablename") or "drivinglog"
        exists = storeup.objects.filter(userid=user_id, refid=refid, tablename=tablename).exists()
        return JsonResponse({"code": normal_code, "msg": mes.normal_code, "data": exists}, encoder=CustomJsonEncoder)
