# coding:utf-8
import json

from django.db.models import Q
from django.http import JsonResponse

from util.CustomJSONEncoder import CustomJsonEncoder
from util.auth import Auth
from util.codes import *
import util.message as mes

from .models import discussdrivinglog, drivinglog, user, users


def _req_dict(request):
    return dict(request.session.get("req_dict", {}) or {})


def _token_info(request):
    return Auth().getTokenInfo(request) or {}


def _is_admin(request):
    return _token_info(request).get("tablename") == "users"


def _current_user_id(request):
    return _token_info(request).get("params", {}).get("id")


def _error(message):
    return {"code": crud_error_code, "msg": message, "data": {}}


def _current_profile(request):
    token_info = _token_info(request)
    table_name = token_info.get("tablename")
    user_id = token_info.get("params", {}).get("id")
    if table_name == "users":
        profile = users.objects.filter(id=user_id).first()
        return {
            "userid": user_id,
            "nickname": getattr(profile, "username", "管理员"),
            "avatarurl": getattr(profile, "image", "") or "",
        }
    profile = user.objects.filter(id=user_id).first()
    return {
        "userid": user_id,
        "nickname": getattr(profile, "username", "用户"),
        "avatarurl": getattr(profile, "headportrait", "") or "",
    }


def _sync_discussnum(refid):
    if not refid:
        return
    total = discussdrivinglog.objects.filter(refid=refid).count()
    drivinglog.objects.filter(id=refid).update(discussnum=total)


def _reply_flag(reply_value):
    if reply_value in [None, "", "[]", "null", "None"]:
        return 0
    try:
        parsed = json.loads(reply_value)
        return 1 if parsed else 0
    except Exception:
        return 1


def _validate_create_payload(req_dict):
    content = str(req_dict.get("content") or "").strip()
    if not content:
        return None, None, "评论内容不能为空"

    try:
        refid = int(req_dict.get("refid", 0) or 0)
    except (TypeError, ValueError):
        refid = 0
    if refid <= 0 or not drivinglog.objects.filter(id=refid).exists():
        return None, None, "行车日志不存在"

    return refid, content, None


def _comment_scope(request):
    if _is_admin(request):
        return Q()
    return Q(userid=_current_user_id(request) or 0)


def _vehicle_label(item):
    parts = [
        str(item.get("vehiclenumber") or "").strip(),
        str(item.get("vehiclemodel") or "").strip(),
        str(item.get("drivingroute") or "").strip(),
    ]
    label = " / ".join(part for part in parts if part)
    if label:
        return label
    refid = item.get("refid")
    return f"行车日志ID：{refid}（记录不存在）" if refid else "行车日志未关联"


def _reply_display(reply_value):
    if reply_value in [None, "", "[]", "null", "None"]:
        return "未回复"
    try:
        parsed = json.loads(reply_value)
    except Exception:
        return str(reply_value).strip() or "未回复"

    if not parsed:
        return "未回复"
    if isinstance(parsed, list):
        labels = []
        for item in parsed:
            if isinstance(item, dict):
                nickname = str(item.get("nickname") or "管理员").strip()
                content = str(item.get("content") or "").strip()
                if content:
                    labels.append(f"{nickname}：{content}")
            elif str(item).strip():
                labels.append(str(item).strip())
        return "；".join(labels) if labels else "未回复"
    if isinstance(parsed, dict):
        nickname = str(parsed.get("nickname") or "管理员").strip()
        content = str(parsed.get("content") or "").strip()
        return f"{nickname}：{content}" if content else "未回复"
    return str(parsed).strip() or "未回复"


def _enrich_comments(records):
    refids = [item.get("refid") for item in records if item.get("refid")]
    logs = {
        row["id"]: row
        for row in drivinglog.objects.filter(id__in=refids).values("id", "vehiclenumber", "vehiclemodel", "drivingroute")
    }
    for item in records:
        log_item = logs.get(item.get("refid"), {})
        item["vehiclenumber"] = log_item.get("vehiclenumber", "")
        item["vehiclemodel"] = log_item.get("vehiclemodel", "")
        item["drivingroute"] = log_item.get("drivingroute", "")
        item["vehicleinfo"] = _vehicle_label(item)
        item["replydisplay"] = _reply_display(item.get("reply"))
    return records


def discussdrivinglog_default(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        req_dict.update({"isdefault": "是"})
        data = discussdrivinglog.getbyparams(discussdrivinglog, discussdrivinglog, req_dict)
        msg["data"] = data[0] if data else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_page(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {"currPage": 1, "totalPage": 1, "total": 1, "pageSize": 10, "list": []}}
        req_dict = _req_dict(request)
        msg["data"]["list"], msg["data"]["currPage"], msg["data"]["totalPage"], msg["data"]["total"], msg["data"]["pageSize"] = discussdrivinglog.page(
            discussdrivinglog, discussdrivinglog, req_dict, request, _comment_scope(request)
        )
        msg["data"]["list"] = _enrich_comments(msg["data"]["list"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_autoSort(request):
    if request.method in ["POST", "GET"]:
        req_dict = _req_dict(request)
        req_dict["sort"] = "addtime"
        req_dict["order"] = "desc"
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {"currPage": 1, "totalPage": 1, "total": 1, "pageSize": 10, "list": []}}
        msg["data"]["list"], msg["data"]["currPage"], msg["data"]["totalPage"], msg["data"]["total"], msg["data"]["pageSize"] = discussdrivinglog.page(
            discussdrivinglog, discussdrivinglog, req_dict, request, _comment_scope(request)
        )
        msg["data"]["list"] = _enrich_comments(msg["data"]["list"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_lists(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": []}
        msg["data"], _, _, _, _ = discussdrivinglog.page(discussdrivinglog, discussdrivinglog, {}, request, _comment_scope(request))
        msg["data"] = _enrich_comments(msg["data"])
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_query(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        query_result = discussdrivinglog.objects.filter(**_req_dict(request)).values()
        msg["data"] = query_result[0] if query_result else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_list(request):
    if request.method in ["POST", "GET"]:
        return discussdrivinglog_page(request)


def discussdrivinglog_save(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        refid, content, error = _validate_create_payload(req_dict)
        if error:
            return JsonResponse(_error(error), encoder=CustomJsonEncoder)
        profile = _current_profile(request)
        req_dict["refid"] = refid
        req_dict["content"] = content
        req_dict["userid"] = req_dict.get("userid") or profile["userid"]
        req_dict["nickname"] = req_dict.get("nickname") or profile["nickname"]
        req_dict["avatarurl"] = req_dict.get("avatarurl") or profile["avatarurl"]
        req_dict["status"] = req_dict.get("status") or "正常"
        req_dict["reply"] = req_dict.get("reply") or ""
        req_dict["isreply"] = _reply_flag(req_dict["reply"])
        discuss_id = discussdrivinglog.createbyreq(discussdrivinglog, discussdrivinglog, req_dict)
        if discuss_id is Exception or (isinstance(discuss_id, str) and "Exception" in discuss_id):
            msg["code"] = crud_error_code
            msg["msg"] = str(discuss_id)
        else:
            _sync_discussnum(refid)
            msg["data"] = discuss_id
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_add(request):
    return discussdrivinglog_save(request)


def discussdrivinglog_thumbsup(request, id_):
    return JsonResponse({"code": normal_code, "msg": mes.normal_code, "data": {}}, encoder=CustomJsonEncoder)


def discussdrivinglog_info(request, id_):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        data = discussdrivinglog.getbyid(discussdrivinglog, discussdrivinglog, int(id_))
        if data and not _is_admin(request) and data[0].get("userid") != _current_user_id(request):
            return JsonResponse(_error("无权限查看该评论"), encoder=CustomJsonEncoder)
        msg["data"] = _enrich_comments([data[0]])[0] if data else {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_detail(request, id_):
    return discussdrivinglog_info(request, id_)


def discussdrivinglog_update(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = _req_dict(request)
        original = discussdrivinglog.objects.filter(id=req_dict.get("id")).first()
        if not original:
            msg["code"] = crud_error_code
            msg["msg"] = "评论不存在"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        if not _is_admin(request):
            msg["code"] = crud_error_code
            msg["msg"] = "无权限修改评论"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        update_fields = {}
        for key in ["content", "reply", "status", "nickname", "avatarurl"]:
            if key in req_dict:
                update_fields[key] = req_dict.get(key)
        if "reply" in update_fields:
            update_fields["isreply"] = _reply_flag(update_fields["reply"])
        if "refid" in req_dict and req_dict.get("refid") not in [None, ""]:
            update_fields["refid"] = int(req_dict.get("refid"))
        try:
            discussdrivinglog.objects.filter(id=original.id).update(**update_fields)
            _sync_discussnum(original.refid)
            updated = discussdrivinglog.objects.filter(id=original.id).first()
            if updated and updated.refid != original.refid:
                _sync_discussnum(updated.refid)
        except Exception as exc:
            msg["code"] = crud_error_code
            msg["msg"] = str(exc)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_delete(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        if not _is_admin(request):
            msg["code"] = crud_error_code
            msg["msg"] = "无权限删除评论"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        req_dict = _req_dict(request)
        ids = req_dict.get("ids") or []
        refids = list(discussdrivinglog.objects.filter(id__in=ids).values_list("refid", flat=True))
        error = discussdrivinglog.deletes(discussdrivinglog, discussdrivinglog, ids)
        if error is not None:
            msg["code"] = crud_error_code
            msg["msg"] = str(error)
        else:
            for refid in set(refids):
                _sync_discussnum(refid)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def discussdrivinglog_vote(request, id_):
    return JsonResponse({"code": normal_code, "msg": mes.normal_code}, encoder=CustomJsonEncoder)


def discussdrivinglog_importExcel(request):
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


def discussdrivinglog_autoSort2(request):
    return discussdrivinglog_autoSort(request)
