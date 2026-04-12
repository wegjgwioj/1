#coding:utf-8
import base64, copy, logging, os, sys, time, xlrd, json, datetime, configparser
from django.http import JsonResponse
from django.apps import apps
import numbers
from collections import defaultdict
from django.db.models.aggregates import Count,Sum
from django.db.models import Case, When, IntegerField, F
from django.forms import model_to_dict
import requests
from util.CustomJSONEncoder import CustomJsonEncoder
from .models import drivinglog
from util.codes import *
from urllib.parse import unquote
from util.auth import Auth
from util.common import Common
import util.message as mes
from django.db import connection
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from django.db.models import Q
from django.core.paginator import Paginator
from util.baidubce_api import BaiDuBce
from .config_model import config
import pandas as pd
from .models import storeup
from .ml.data_cleaning import export_cleanse_artifacts, summarize_drivinglog_quality


def drivinglog_default(request):

    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code,"msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        req_dict.update({"isdefault":"是"})
        data=drivinglog.getbyparams(drivinglog, drivinglog, req_dict)
        if len(data)>0:
            msg['data']  = data[0]
        else:
            msg['data']  = {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_page(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        global drivinglog
        #当前登录用户信息
        tablename = Auth().getTokenInfo(request).get('tablename')

        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  =drivinglog.page(drivinglog, drivinglog,req_dict, request)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_autoSort(request):
    '''
    ．智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
主要信息列表（如商品列表，新闻列表）中使用，显示最近点击的或最新添加的5条记录就行
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        if "clicknum"  in drivinglog.getallcolumn(drivinglog,drivinglog):
            req_dict['sort']='clicknum'
        elif "browseduration"  in drivinglog.getallcolumn(drivinglog,drivinglog):
            req_dict['sort']='browseduration'
        else:
            req_dict['sort']='clicktime'
        req_dict['order']='desc'
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = drivinglog.page(drivinglog,drivinglog, req_dict)

        return JsonResponse(msg, encoder=CustomJsonEncoder)

#分类列表
def drivinglog_lists(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":[]}
        msg['data'],_,_,_,_  = drivinglog.page(drivinglog, drivinglog, {})
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_query(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        try:
            query_result = drivinglog.objects.filter(**request.session.get("req_dict")).values()
            msg['data'] = query_result[0]
        except Exception as e:

            msg['code'] = crud_error_code
            msg['msg'] = f"发生错误：{e}"
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_list(request):
    '''
    前台分页
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        #获取全部列名
        columns=  drivinglog.getallcolumn( drivinglog, drivinglog)
        if "vipread" in req_dict and "vipread" not in columns:
          del req_dict["vipread"]
        #表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
        try:
            __foreEndList__=drivinglog.__foreEndList__
        except:
            __foreEndList__=None
        try:
            __foreEndListAuth__=drivinglog.__foreEndListAuth__
        except:
            __foreEndListAuth__=None

        #authSeparate
        try:
            __authSeparate__=drivinglog.__authSeparate__
        except:
            __authSeparate__=None

        if __foreEndListAuth__ =="是" and __authSeparate__=="是":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users" and Auth().getTokenInfo(request).get('params') is not None:
                req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")

        tablename = Auth().getTokenInfo(request).get('tablename')
        if tablename == "users" and req_dict.get("userid") != None:#判断是否存在userid列名
            del req_dict["userid"]
        else:
            __isAdmin__ = None

            allModels = apps.get_app_config('main').get_models()
            for m in allModels:
                if m.__tablename__==tablename:

                    try:
                        __isAdmin__ = m.__isAdmin__
                    except:
                        __isAdmin__ = None
                    break

            if __isAdmin__ == "是":
                if req_dict.get("userid"):
        # del req_dict["userid"]
                    pass
            else:
    #非管理员权限的表,判断当前表字段名是否有userid
                if "userid" in columns:
                    try:
                        pass
                    except:
                        pass
        #当列属性authTable有值(某个用户表)[该列的列名必须和该用户表的登陆字段名一致]，则对应的表有个隐藏属性authTable为”是”，那么该用户查看该表信息时，只能查看自己的
        try:
            __authTables__=drivinglog.__authTables__
        except:
            __authTables__=None

        if __authTables__!=None and  __authTables__!={} and __foreEndListAuth__=="是":
            for authColumn,authTable in __authTables__.items():
                if authTable==tablename:
                    try:
                        del req_dict['userid']
                    except:
                        pass
                    params = Auth().getTokenInfo(request).get('params')
                    req_dict[authColumn]=params.get(authColumn)
                    username=params.get(authColumn)
                    break
        
        if drivinglog.__tablename__[:7]=="discuss":
            try:
                del req_dict['userid']
            except:
                pass

        q = Q()
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = drivinglog.page(drivinglog, drivinglog, req_dict, request, q)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_save(request):
    '''
    后台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if 'clicktime' in req_dict.keys():
            del req_dict['clicktime']
        tablename=Auth().getTokenInfo(request).get('tablename')
        __isAdmin__ = None
        allModels = apps.get_app_config('main').get_models()
        for m in allModels:
            if m.__tablename__==tablename:

                try:
                    __isAdmin__ = m.__isAdmin__
                except:
                    __isAdmin__ = None
                break

        #获取全部列名
        columns=  drivinglog.getallcolumn( drivinglog, drivinglog)
        if tablename!='users' and req_dict.get("userid")==None and 'userid' in columns  and __isAdmin__!='是':
            params=Auth().getTokenInfo(request).get('params')
            req_dict['userid']=params.get('id')


        if 'addtime' in req_dict.keys():
            del req_dict['addtime']

        idOrErr= drivinglog.createbyreq(drivinglog,drivinglog, req_dict)
        if idOrErr is Exception:
            msg['code'] = crud_error_code
            msg['msg'] = idOrErr
        else:
            msg['data'] = idOrErr

        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_add(request):
    '''
    前台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        tablename=Auth().getTokenInfo(request).get('tablename')

        #获取全部列名
        columns=  drivinglog.getallcolumn( drivinglog, drivinglog)
        try:
            __authSeparate__=drivinglog.__authSeparate__
        except:
            __authSeparate__=None

        if __authSeparate__=="是":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users" and 'userid' in columns:
                try:
                    req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")
                except:
                    pass

        try:
            __foreEndListAuth__=drivinglog.__foreEndListAuth__
        except:
            __foreEndListAuth__=None

        if __foreEndListAuth__ and __foreEndListAuth__!="否":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users":
                req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")


        if 'addtime' in req_dict.keys():
            del req_dict['addtime']
        error= drivinglog.createbyreq(drivinglog,drivinglog, req_dict)
        if error is Exception:
            msg['code'] = crud_error_code
            msg['msg'] = error
        else:
            msg['data'] = error
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_thumbsup(request,id_):
    '''
     点赞：表属性thumbsUp[是/否]，刷表新增thumbsupnum赞和crazilynum踩字段，
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        id_=int(id_)
        type_=int(req_dict.get("type",0))
        rets=drivinglog.getbyid(drivinglog,drivinglog,id_)

        update_dict={
        "id":id_,
        }
        if type_==1:#赞
            update_dict["thumbsupnum"]=int(rets[0].get('thumbsupnum'))+1
        elif type_==2:#踩
            update_dict["crazilynum"]=int(rets[0].get('crazilynum'))+1
        error = drivinglog.updatebyparams(drivinglog,drivinglog, update_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglog_info(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data = drivinglog.getbyid(drivinglog,drivinglog, int(id_))
        if len(data)>0:
            msg['data']=data[0]
            if msg['data'].__contains__("reversetime"):
                if isinstance(msg['data']['reversetime'], datetime.datetime):
                    msg['data']['reversetime'] = msg['data']['reversetime'].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if msg['data']['reversetime'] != None:
                        reversetime = datetime.datetime.strptime(msg['data']['reversetime'], '%Y-%m-%d %H:%M:%S')
                        msg['data']['reversetime'] = reversetime.strftime("%Y-%m-%d %H:%M:%S")

        #浏览点击次数
        try:
            __browseClick__= drivinglog.__browseClick__
        except:
            __browseClick__=None

        if __browseClick__=="是"  and  "clicknum"  in drivinglog.getallcolumn(drivinglog,drivinglog):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum,"clicktime":datetime.datetime.now()}
            ret=drivinglog.updatebyparams(drivinglog,drivinglog,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_detail(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data =drivinglog.getbyid(drivinglog,drivinglog, int(id_))
        if len(data)>0:
            msg['data']=data[0]
            if msg['data'].__contains__("reversetime"):
                if isinstance(msg['data']['reversetime'], datetime.datetime):
                    msg['data']['reversetime'] = msg['data']['reversetime'].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if msg['data']['reversetime'] != None:
                        reversetime = datetime.datetime.strptime(msg['data']['reversetime'], '%Y-%m-%d %H:%M:%S')
                        msg['data']['reversetime'] = reversetime.strftime("%Y-%m-%d %H:%M:%S")

        #浏览点击次数
        try:
            __browseClick__= drivinglog.__browseClick__
        except:
            __browseClick__=None

        if __browseClick__=="是"   and  "clicknum"  in drivinglog.getallcolumn(drivinglog,drivinglog):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum,"clicktime":datetime.datetime.now()}

            ret=drivinglog.updatebyparams(drivinglog,drivinglog,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_update(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if 'clicktime' in req_dict.keys() and req_dict['clicktime']=="None":
            del req_dict['clicktime']
        if req_dict.get("mima") and "mima" not in drivinglog.getallcolumn(drivinglog,drivinglog) :
            del req_dict["mima"]
        if req_dict.get("password") and "password" not in drivinglog.getallcolumn(drivinglog,drivinglog) :
            del req_dict["password"]
        try:
            del req_dict["clicknum"]
        except:
            pass


        error = drivinglog.updatebyparams(drivinglog, drivinglog, req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error

        return JsonResponse(msg)


def drivinglog_delete(request):
    '''
    批量删除
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")

        error=drivinglog.deletes(drivinglog,
            drivinglog,
             req_dict.get("ids")
        )
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)


def drivinglog_vote(request,id_):
    '''
    浏览点击次数（表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1）
统计商品或新闻的点击次数；提供新闻的投票功能
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code}


        data= drivinglog.getbyid(drivinglog, drivinglog, int(id_))
        for i in data:
            votenum=i.get('votenum')
            if votenum!=None:
                params={"id":int(id_),"votenum":votenum+1}
                error=drivinglog.updatebyparams(drivinglog,drivinglog,params)
                if error!=None:
                    msg['code'] = crud_error_code
                    msg['msg'] = error
        return JsonResponse(msg)

def drivinglog_importExcel(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}

        excel_file = request.FILES.get("file", "")
        if excel_file.size > 100 * 1024 * 1024:  # 限制为 100MB
            msg['code'] = 400
            msg["msg"] = '文件大小不能超过100MB'
            return JsonResponse(msg)

        file_type = excel_file.name.split('.')[1]
        
        if file_type in ['xlsx', 'xls']:
            data = xlrd.open_workbook(filename=None, file_contents=excel_file.read())
            table = data.sheets()[0]
            rows = table.nrows
            
            try:
                for row in range(1, rows):
                    row_values = table.row_values(row)
                    req_dict = {}
                    if '.0' in str(row_values[0]):
                        req_dict['vehiclenumber'] = str(row_values[0]).split('.')[0]
                    elif str(row_values[0]) != '':
                        req_dict['vehiclenumber'] = row_values[0]
                    else:
                        req_dict['vehiclenumber'] = None
                    if '.0' in str(row_values[1]):
                        req_dict['vehiclemodel'] = str(row_values[1]).split('.')[0]
                    elif str(row_values[1]) != '':
                        req_dict['vehiclemodel'] = row_values[1]
                    else:
                        req_dict['vehiclemodel'] = None
                    if '.0' in str(row_values[2]):
                        req_dict['batterycapacity'] = str(row_values[2]).split('.')[0]
                    elif str(row_values[2]) != '':
                        req_dict['batterycapacity'] = row_values[2]
                    else:
                        req_dict['batterycapacity'] = None
                    if '.0' in str(row_values[3]):
                        req_dict['batterylife'] = str(row_values[3]).split('.')[0]
                    elif str(row_values[3]) != '':
                        req_dict['batterylife'] = row_values[3]
                    else:
                        req_dict['batterylife'] = None
                    if '.0' in str(row_values[4]):
                        req_dict['accumulatedmileage'] = str(row_values[4]).split('.')[0]
                    elif str(row_values[4]) != '':
                        req_dict['accumulatedmileage'] = row_values[4]
                    else:
                        req_dict['accumulatedmileage'] = None
                    if str(row_values[5]) != '':
                        try:
                            starttime = xlrd.xldate_as_datetime(row_values[5],0)
                            req_dict['starttime'] = starttime.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            req_dict['starttime'] = row_values[5]
                    else:
                        req_dict['starttime'] = None
                    if str(row_values[6]) != '':
                        try:
                            endtime = xlrd.xldate_as_datetime(row_values[6],0)
                            req_dict['endtime'] = endtime.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            req_dict['endtime'] = row_values[6]
                    else:
                        req_dict['endtime'] = None
                    if '.0' in str(row_values[7]):
                        req_dict['averagespeed'] = str(row_values[7]).split('.')[0]
                    elif str(row_values[7]) != '':
                        req_dict['averagespeed'] = row_values[7]
                    else:
                        req_dict['averagespeed'] = None
                    if '.0' in str(row_values[8]):
                        req_dict['batterylevel'] = str(row_values[8]).split('.')[0]
                    elif str(row_values[8]) != '':
                        req_dict['batterylevel'] = row_values[8]
                    else:
                        req_dict['batterylevel'] = None
                    if '.0' in str(row_values[9]):
                        req_dict['powerconsumption'] = str(row_values[9]).split('.')[0]
                    elif str(row_values[9]) != '':
                        req_dict['powerconsumption'] = row_values[9]
                    else:
                        req_dict['powerconsumption'] = None
                    if '.0' in str(row_values[10]):
                        req_dict['drivingroute'] = str(row_values[10]).split('.')[0]
                    elif str(row_values[10]) != '':
                        req_dict['drivingroute'] = row_values[10]
                    else:
                        req_dict['drivingroute'] = None
                    if str(row_values[11]) != '':
                        try:
                            collectiontime = xlrd.xldate_as_datetime(row_values[11],0)
                            req_dict['collectiontime'] = collectiontime.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            req_dict['collectiontime'] = row_values[11]
                    else:
                        req_dict['collectiontime'] = None
                    if '.0' in str(row_values[12]):
                        req_dict['rapidaccelerationtimes'] = str(row_values[12]).split('.')[0]
                    elif str(row_values[12]) != '':
                        req_dict['rapidaccelerationtimes'] = row_values[12]
                    else:
                        req_dict['rapidaccelerationtimes'] = None
                    if '.0' in str(row_values[13]):
                        req_dict['numberofrapiddecelerations'] = str(row_values[13]).split('.')[0]
                    elif str(row_values[13]) != '':
                        req_dict['numberofrapiddecelerations'] = row_values[13]
                    else:
                        req_dict['numberofrapiddecelerations'] = None
                    if '.0' in str(row_values[14]):
                        req_dict['numberofspeedingincidents'] = str(row_values[14]).split('.')[0]
                    elif str(row_values[14]) != '':
                        req_dict['numberofspeedingincidents'] = row_values[14]
                    else:
                        req_dict['numberofspeedingincidents'] = None
                    if '.0' in str(row_values[15]):
                        req_dict['energysavingsuggestions'] = str(row_values[15]).split('.')[0]
                    elif str(row_values[15]) != '':
                        req_dict['energysavingsuggestions'] = row_values[15]
                    else:
                        req_dict['energysavingsuggestions'] = None
                    if '.0' in str(row_values[16]):
                        req_dict['drivingbehaviorrating'] = str(row_values[16]).split('.')[0]
                    elif str(row_values[16]) != '':
                        req_dict['drivingbehaviorrating'] = row_values[16]
                    else:
                        req_dict['drivingbehaviorrating'] = None
                    drivinglog.createbyreq(drivinglog, drivinglog, req_dict)
                    
            except:
                pass
                
        else:
            msg = {
                "msg": "文件类型错误",
                "code": 500
            }
                
        return JsonResponse(msg)

def drivinglog_autoSort2(request):
    if request.method in ["POST", "GET"]:
        req_dict = request.session.get("req_dict", {}) or {}
        token_info = Auth().getTokenInfo(request)
        user_id = token_info.get("params", {}).get("id")
        page = int(req_dict.get("page", 1) or 1)
        limit = int(req_dict.get("limit", 10) or 10)
        favorite_items = list(
            storeup.objects.filter(userid=user_id, tablename="drivinglog").values("refid")
        )
        favorite_refids = [item["refid"] for item in favorite_items]
        favorite_logs = list(
            drivinglog.objects.filter(id__in=favorite_refids).values("vehiclemodel", "drivingroute")
        )
        model_prefs = {item["vehiclemodel"] for item in favorite_logs if item.get("vehiclemodel")}
        route_prefs = {item["drivingroute"] for item in favorite_logs if item.get("drivingroute")}

        queryset = drivinglog.objects.all()
        if favorite_refids:
            queryset = queryset.exclude(id__in=favorite_refids)
        records = list(queryset.values())

        def score(record):
            current = 0
            if record.get("vehiclemodel") in model_prefs:
                current += 3
            if record.get("drivingroute") in route_prefs:
                current += 2
            current += min(int(record.get("storeupnum") or 0), 1)
            current += min(int(record.get("discussnum") or 0), 1)
            return current

        if model_prefs or route_prefs:
            records.sort(
                key=lambda item: (
                    score(item),
                    str(item.get("addtime") or ""),
                    int(item.get("id") or 0),
                ),
                reverse=True,
            )
        else:
            records.sort(
                key=lambda item: (
                    str(item.get("addtime") or ""),
                    int(item.get("id") or 0),
                ),
                reverse=True,
            )

        for record in records:
            for key, value in list(record.items()):
                if isinstance(value, datetime.datetime):
                    record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

        paginator = Paginator(records, limit)
        page_obj = paginator.page(page) if paginator.count else []
        page_list = list(page_obj.object_list) if paginator.count else []
        data = {
            "currPage": page,
            "totalPage": paginator.num_pages if paginator.count else 1,
            "total": paginator.count,
            "pageSize": limit,
            "list": page_list,
        }
        return JsonResponse({"code": 0, "msg": mes.normal_code, "data": data}, encoder=CustomJsonEncoder)



def drivinglog_count(request):
    '''
    总数接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        req_dict = request.session.get("req_dict")
        where = ' where 1 = 1 '
        for key in req_dict:
            if req_dict[key] != None:
                where = where + " and key like '{0}'".format(req_dict[key])
        
        sql = "SELECT count(*) AS count FROM drivinglog {0}".format(where)
        count = 0
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            count = online_dict['count']
        msg['data'] = count

        return JsonResponse(msg, encoder=CustomJsonEncoder)

#对日期进行排序
def order_time(data,type,xColumnName,rev):
    if type=="日":
        result_data = sorted(
            data,
            key=lambda x: (
                int(x[xColumnName].split("-")[0]),
                int(x[xColumnName].split("-")[1]),
                int(x[xColumnName].split("-")[2]),
            ),
            reverse=rev  # 设置排列
        )
    elif type=="月":
        result_data = sorted(
            data,
            key=lambda x: (
                int(x[xColumnName].split("-")[0]),
                int(x[xColumnName].split("-")[1])
            ),
            reverse=rev  # 设置排列
        )
    elif type=="年":
        result_data = sorted(
            data,
            key=lambda x: (
                int(x[xColumnName].split("-")[0]),  # 提取年份并转为整数
            ),
            reverse=rev  # 设置排列
        )
    else:
        result_data = sorted(data, key=lambda x: x[xColumnName], reverse=rev)
    return result_data

# （按值统计）时间统计类型
def drivinglog_value(request, xColumnName, yColumnName, timeStatType):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        #获取hadoop分析后的数据文件
        date_type = ""
        if timeStatType == '日':
            date_type = "date"
        if timeStatType == '月':
            date_type = "month"
        if timeStatType == '季':
            date_type = "quarter"
        if timeStatType == '年':
            date_type = "year"
        json_filename = f'drivinglog_value{xColumnName}{yColumnName}{date_type}.json'

        if os.path.exists(json_filename) == True:
            with open(json_filename, encoding='utf-8') as f:
                msg['data'] = json.load(f)
        else:
            where = ' where 1 = 1 '
            raw_query_string = request.META.get('QUERY_STRING', '')
            raw_query_string = unquote(raw_query_string)
            conditionColumn = ""
            conditionValue = ""
            if "conditionColumn=" in raw_query_string:
                conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
            if "conditionValue=" in raw_query_string:
                conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
            if conditionColumn != "":
                for index, value in enumerate(conditionColumn.split(";")):
                    if ',' in value:
                        where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                        where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                    else:
                        where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''
            req_dict = request.session.get("req_dict")
            statistics_func = "SUM"
            func_params = req_dict.get("func")
            if func_params == "平均":
                statistics_func = "AVG"
            elif func_params == "最大":
                statistics_func = "MAX"
            elif func_params == "最小":
                statistics_func = "MIN"
            elif func_params == "总和":
                statistics_func = "COUNT"
            try:
                del req_dict["func"]
            except:
                pass
            #定义查询统计语句
            for key, value in req_dict.items():
                if key!="limit" and key!="order" and key!="orderType" and key!="conditionColumn"and key!="conditionValue":
                    where = where + " and {0} ='{1}' ".format(key,value)
            sql = ''
            if timeStatType == '日':
                sql = "SELECT DATE_FORMAT({0}, '%Y-%m-%d') {0}, ROUND({1}({2}),2) total FROM drivinglog {3} GROUP BY DATE_FORMAT({0}, '%Y-%m-%d')".format(xColumnName, statistics_func,yColumnName, where, '%Y-%m-%d')

            if timeStatType == '月':
                sql = "SELECT DATE_FORMAT({0}, '%Y-%m') {0}, ROUND({1}({2}),2) total FROM drivinglog {3} GROUP BY DATE_FORMAT({0}, '%Y-%m')".format(xColumnName, statistics_func,yColumnName, where, '%Y-%m')

            if timeStatType == '季':
                sql = "SELECT CONCAT(YEAR(MIN({0})), '-Q', QUARTER(MIN({0}))) AS {0}, {1}({2}) AS total FROM orders {3} GROUP BY YEAR({0}), QUARTER({0})".format(xColumnName,statistics_func, yColumnName, where)

            if timeStatType == '年':
                sql = "SELECT DATE_FORMAT({0}, '%Y') {0}, ROUND({1}({2}),2) total FROM drivinglog {3} GROUP BY DATE_FORMAT({0}, '%Y')".format(xColumnName,statistics_func, yColumnName, where, '%Y')
            L = []
            cursor = connection.cursor()
            cursor.execute(sql)
            desc = cursor.description
            data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
            for online_dict in data_dict:
                for key in online_dict:
                    if 'datetime.datetime' in str(type(online_dict[key])):
                        online_dict[key] = online_dict[key].strftime(
                            "%Y-%m-%d %H:%M:%S")
                    else:
                        pass
                L.append(online_dict)
            msg['data'] = L
        req_dict = request.session.get("req_dict")
        #对结果进行排序
        order = req_dict.get('order')
        orderType = req_dict.get('orderType')
        if orderType=='x' :
            if order == "desc":
                msg['data'] = order_time(msg['data'], timeStatType, xColumnName, True)
            else:
                msg['data'] = order_time(msg['data'], timeStatType, xColumnName, False)
        else:
            if order == "desc":
                msg['data'] = sorted((x for x in msg['data'] if x['total'] is not None), key=lambda x: x['total'],
                                     reverse=True)
            else:
                msg['data'] = sorted((x for x in msg['data'] if x['total'] is not None), key=lambda x: x['total'])

        if "limit" in req_dict and int(req_dict["limit"]) < len(L):
            msg['data'] = msg['data'][:int(req_dict["limit"])]
        return JsonResponse(msg, encoder=CustomJsonEncoder)

# 按值统计
def drivinglog_o_value(request, xColumnName, yColumnName):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        #获取hadoop分析后的数据文件
        json_filename = f'drivinglog_value{xColumnName}{yColumnName}.json'

        if os.path.exists(json_filename) == True:
            with open(json_filename, encoding='utf-8') as f:
                msg['data'] = json.load(f)
        else:
            where = ' where 1 = 1 '
            raw_query_string = request.META.get('QUERY_STRING', '')
            raw_query_string = unquote(raw_query_string)
            conditionColumn = ""
            conditionValue = ""
            if "conditionColumn=" in raw_query_string:
                conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
            if "conditionValue=" in raw_query_string:
                conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
            if conditionColumn != "":
                for index, value in enumerate(conditionColumn.split(";")):
                    if "," in value:
                        where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                        where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                    else:
                        where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''
            req_dict = request.session.get("req_dict")
            statistics_func = "SUM"
            func_params = req_dict.get("func")
            if func_params == "平均":
                statistics_func = "AVG"
            elif func_params == "最大":
                statistics_func = "MAX"
            elif func_params == "最小":
                statistics_func = "MIN"
            elif func_params == "总和":
                statistics_func = "COUNT"
            try:
                del req_dict["func"]
            except:
                pass
            sql = "SELECT {0}, ROUND({1}({2}),2) AS total FROM drivinglog {3} GROUP BY {0}".format(xColumnName,statistics_func, yColumnName, where)
            L = []
            cursor = connection.cursor()
            cursor.execute(sql)
            desc = cursor.description
            data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
            for online_dict in data_dict:
                for key in online_dict:
                    if 'datetime.datetime' in str(type(online_dict[key])):
                        online_dict[key] = online_dict[key].strftime(
                            "%Y-%m-%d %H:%M:%S")
                    else:
                        pass
                L.append(online_dict)
            msg['data'] = L
        req_dict = request.session.get("req_dict")
        if "order" in req_dict:
            order = req_dict["order"]
            if order == "desc":
                msg['data'] = sorted((x for x in msg['data'] if x['total'] is not None),key=lambda x: x['total'],reverse=True)
            else:
                msg['data'] = sorted((x for x in msg['data'] if x['total'] is not None),key=lambda x: x['total'])

        if "limit" in req_dict and int(req_dict["limit"]) < len(L):
            msg['data'] = msg['data'][:int(req_dict["limit"])]
        return JsonResponse(msg, encoder=CustomJsonEncoder)

# （按值统计）时间统计类型(多)
def drivinglog_valueMul(request, xColumnName, timeStatType):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": []}
        req_dict = request.session.get("req_dict")
        #获取hadoop分析后的数据文件
        date_type = ""
        if timeStatType == '日':
            date_type = "date"
        if timeStatType == '月':
            date_type = "month"
        if timeStatType == '季':
            date_type = "quarter"
        if timeStatType == '年':
            date_type = "year"
        #获取hadoop分析后的数据文件
        json_filename = f'''drivinglog_value{xColumnName}｛req_dict['yColumnNameMul'].replace(",","")｝{date_type}.json'''

        if os.path.exists(json_filename) == True:
            with open(json_filename, encoding='utf-8') as f:
                msg['data'] = json.load(f)
        else:
            where = ' where 1 = 1 '
            raw_query_string = request.META.get('QUERY_STRING', '')
            raw_query_string = unquote(raw_query_string)
            conditionColumn = ""
            conditionValue = ""
            if "conditionColumn=" in raw_query_string:
                conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
            if "conditionValue=" in raw_query_string:
                conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
            if conditionColumn != "":
                for index, value in enumerate(conditionColumn.split(";")):
                    if "," in value:
                        where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                        where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                    else:
                        where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''

            statistics_func = "SUM"
            func_params = req_dict.get("func")
            if func_params == "平均":
                statistics_func = "AVG"
            elif func_params == "最大":
                statistics_func = "MAX"
            elif func_params == "最小":
                statistics_func = "MIN"
            elif func_params == "总和":
                statistics_func = "COUNT"
            try:
                del req_dict["func"]
            except:
                pass
              # 定义查询统计语句
            for key, value in req_dict.items():
                if key != "limit" and key != "order" and key != "orderType" and key != "yColumnNameMul" and key != "conditionColumn" and key != "conditionValue":
                    where = where + " and {0} ='{1}' ".format(key, value)

            for item in req_dict['yColumnNameMul'].split(','):
                sql = ''
                if timeStatType == '日':
                    sql = "SELECT DATE_FORMAT({0}, '%Y-%m-%d') {0}, ROUND({1}({2}),2) total FROM drivinglog {3} GROUP BY DATE_FORMAT({0}, '%Y-%m-%d')".format(xColumnName, statistics_func,item, where, '%Y-%m-%d')

                if timeStatType == '月':
                    sql = "SELECT DATE_FORMAT({0}, '%Y-%m') {0}, ROUND({1}({2}),2) total FROM drivinglog {3} GROUP BY DATE_FORMAT({0}, '%Y-%m')".format(xColumnName,statistics_func, item, where, '%Y-%m')

                if timeStatType == '季':
                    sql = "SELECT CONCAT(YEAR(MIN({0})), '-Q', QUARTER(MIN({0}))) {0}, {1}({2}) total FROM drivinglog {3} GROUP BY YEAR({0}), QUARTER({0})".format(xColumnName, statistics_func,item, where)

                if timeStatType == '年':
                    sql = "SELECT DATE_FORMAT({0}, '%Y') {0}, ROUND({1}({2}),2) total FROM drivinglog {3} GROUP BY DATE_FORMAT({0}, '%Y')".format(xColumnName, statistics_func,item, where, '%Y')

                L = []
                cursor = connection.cursor()
                cursor.execute(sql)
                desc = cursor.description
                data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
                for online_dict in data_dict:
                    for key in online_dict:
                        if 'datetime.datetime' in str(type(online_dict[key])):
                            online_dict[key] = online_dict[key].strftime(
                                "%Y-%m-%d %H:%M:%S")
                        else:
                            pass
                    L.append(online_dict)
                    # 结果进行排序
                    order = req_dict.get('order')
                    orderType = req_dict.get('orderType')
                    if orderType == 'x':
                        if order == "desc":
                            L = order_time(L, timeStatType, xColumnName, True)
                        else:
                            L = order_time(L, timeStatType, xColumnName, False)
                    else:
                        if order == "desc":
                            L = sorted((x for x in L if x['total'] is not None),
                                       key=lambda x: x['total'],
                                       reverse=True)
                        else:
                            L = sorted((x for x in L if x['total'] is not None),
                                       key=lambda x: x['total'])
                    # 截取列表个数
                    if "limit" in req_dict and int(req_dict["limit"]) < len(msg['data']):
                        L = L[:int(req_dict["limit"])]
                msg['data'].append(L)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

# （按值统计(多)）
def drivinglog_o_valueMul(request, xColumnName):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": []}

        req_dict = request.session.get("req_dict")
        #获取hadoop分析后的数据文件
        json_filename = f'''drivinglog_value{xColumnName}｛req_dict['yColumnNameMul'].replace(",","")｝.json'''

        if os.path.exists(json_filename) == True:
            with open(json_filename, encoding='utf-8') as f:
                msg['data'] = json.load(f)
        else:
            where = ' where 1 = 1 '
            raw_query_string = request.META.get('QUERY_STRING', '')
            raw_query_string = unquote(raw_query_string)
            conditionColumn = ""
            conditionValue = ""
            if "conditionColumn=" in raw_query_string:
                conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
            if "conditionValue=" in raw_query_string:
                conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
            if conditionColumn != "":
                for index, value in enumerate(conditionColumn.split(";")):
                    if "," in value:
                        where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                        where = where + f''' and {value.split(',')[0]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                    else:
                        where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''
            statistics_func = "SUM"
            func_params = req_dict.get("func")
            if func_params == "平均":
                statistics_func = "AVG"
            elif func_params == "最大":
                statistics_func = "MAX"
            elif func_params == "最小":
                statistics_func = "MIN"
            elif func_params == "总和":
                statistics_func = "COUNT"
            try:
                del req_dict["func"]
            except:
                pass
            for item in req_dict['yColumnNameMul'].split(','):
                sql = "SELECT {0}, ROUND({1}({2}),2) AS total FROM drivinglog {3} GROUP BY {0}".format(xColumnName, statistics_func,item, where)
                L = []
                cursor = connection.cursor()
                cursor.execute(sql)
                desc = cursor.description
                data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
                for online_dict in data_dict:
                    for key in online_dict:
                        if 'datetime.datetime' in str(type(online_dict[key])):
                            online_dict[key] = online_dict[key].strftime(
                                "%Y-%m-%d %H:%M:%S")
                        else:
                            pass
                    L.append(online_dict)
                msg['data'].append(L)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_group(request, columnName):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}

        #获取hadoop分析后的数据文件
        json_filename = f'drivinglog_group{columnName}.json'

        if os.path.exists(json_filename) == True:
            with open(json_filename, encoding='utf-8') as f:
                msg['data'] = json.load(f)
        else:
            where = ' where 1 = 1 '
            raw_query_string = request.META.get('QUERY_STRING', '')
            raw_query_string = unquote(raw_query_string)
            conditionColumn = ""
            conditionValue = ""
            if "conditionColumn=" in raw_query_string:
                conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
            if "conditionValue=" in raw_query_string:
                conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
            if conditionColumn != "":
                for index, value in enumerate(conditionColumn.split(";")):
                    if ',' in value:
                        where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                        where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                    else:
                        where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''

            sql = "SELECT COUNT(*) AS total, " + columnName + " FROM drivinglog " + where + " GROUP BY " + columnName
            L = []
            cursor = connection.cursor()
            cursor.execute(sql)
            desc = cursor.description
            data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
            for online_dict in data_dict:
                for key in online_dict:
                    if 'datetime.datetime' in str(type(online_dict[key])):
                        online_dict[key] = online_dict[key].strftime("%Y-%m-%d")
                    else:
                        pass
                L.append(online_dict)
            msg['data'] = L
        req_dict = request.session.get("req_dict")
        if "order" in req_dict:
            order = req_dict["order"]
            if order == "desc":
                msg['data'] = sorted((x for x in msg['data'] if x['total'] is not None),key=lambda x: x['total'],reverse=True)
            else:
                msg['data'] = sorted((x for x in msg['data'] if x['total'] is not None),key=lambda x: x['total'])

        if "limit" in req_dict and int(req_dict["limit"]) < len(L):
            msg['data'] = msg['data'][:int(req_dict["limit"])]
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglog_sectionStat_batterycapacity(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))
        raw_query_string = request.META.get('QUERY_STRING', '')
        raw_query_string = unquote(raw_query_string)
        conditionColumn = ""
        conditionValue = ""
        if "conditionColumn=" in raw_query_string:
            conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
        if "conditionValue=" in raw_query_string:
            conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
        if conditionColumn != "":
            for index, value in enumerate(conditionColumn.split(";")):
                if ',' in value:
                    where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                    where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                else:
                    where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''
        sql = """
            SELECT '40以下' as batterycapacity,case when t.40以下 is null then 0 else t.40以下 end total
            from 
            (select
            sum(case when batterycapacity <= 20 then 1 else 0 end) as 40以下,            sum(case when batterycapacity >= 41 and batterycapacity <= 60 then 1 else 0 end) as 41到60,            sum(case when batterycapacity >= 61 and batterycapacity <= 100 then 1 else 0 end) as 60到100,            sum(case when batterycapacity >= 101 then 1 else 0 end) as 100以上            from drivinglog
            {where}
            ) t
            union all
            SELECT '41到60' as batterycapacity,case when t.41到60 is null then 0 else t.41到60 end total
            from 
            (select
            sum(case when batterycapacity <= 20 then 1 else 0 end) as 40以下,            sum(case when batterycapacity >= 41 and batterycapacity <= 60 then 1 else 0 end) as 41到60,            sum(case when batterycapacity >= 61 and batterycapacity <= 100 then 1 else 0 end) as 60到100,            sum(case when batterycapacity >= 101 then 1 else 0 end) as 100以上            from drivinglog
            {where}
            ) t
            union all
            SELECT '60到100' as batterycapacity,case when t.60到100 is null then 0 else t.60到100 end total
            from 
            (select
            sum(case when batterycapacity <= 20 then 1 else 0 end) as 40以下,            sum(case when batterycapacity >= 41 and batterycapacity <= 60 then 1 else 0 end) as 41到60,            sum(case when batterycapacity >= 61 and batterycapacity <= 100 then 1 else 0 end) as 60到100,            sum(case when batterycapacity >= 101 then 1 else 0 end) as 100以上            from drivinglog
            {where}
            ) t
            union all
            SELECT '100以上' as batterycapacity,case when t.100以上 is null then 0 else t.100以上 end total
            from 
            (select
            sum(case when batterycapacity <= 20 then 1 else 0 end) as 40以下,            sum(case when batterycapacity >= 41 and batterycapacity <= 60 then 1 else 0 end) as 41到60,            sum(case when batterycapacity >= 61 and batterycapacity <= 100 then 1 else 0 end) as 60到100,            sum(case when batterycapacity >= 101 then 1 else 0 end) as 100以上            from drivinglog
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg, encoder=CustomJsonEncoder)
def drivinglog_sectionStat_batterylife(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))
        raw_query_string = request.META.get('QUERY_STRING', '')
        raw_query_string = unquote(raw_query_string)
        conditionColumn = ""
        conditionValue = ""
        if "conditionColumn=" in raw_query_string:
            conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
        if "conditionValue=" in raw_query_string:
            conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
        if conditionColumn != "":
            for index, value in enumerate(conditionColumn.split(";")):
                if ',' in value:
                    where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                    where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                else:
                    where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''
        sql = """
            SELECT '50以下' as batterylife,case when t.50以下 is null then 0 else t.50以下 end total
            from 
            (select
            sum(case when batterylife <= 50 then 1 else 0 end) as 50以下,            sum(case when batterylife >= 51 and batterylife <= 100 then 1 else 0 end) as 51到100,            sum(case when batterylife >= 101 and batterylife <= 150 then 1 else 0 end) as 101至150,            sum(case when batterylife >= 151 then 1 else 0 end) as 151以上            from drivinglog
            {where}
            ) t
            union all
            SELECT '51到100' as batterylife,case when t.51到100 is null then 0 else t.51到100 end total
            from 
            (select
            sum(case when batterylife <= 50 then 1 else 0 end) as 50以下,            sum(case when batterylife >= 51 and batterylife <= 100 then 1 else 0 end) as 51到100,            sum(case when batterylife >= 101 and batterylife <= 150 then 1 else 0 end) as 101至150,            sum(case when batterylife >= 151 then 1 else 0 end) as 151以上            from drivinglog
            {where}
            ) t
            union all
            SELECT '101至150' as batterylife,case when t.101至150 is null then 0 else t.101至150 end total
            from 
            (select
            sum(case when batterylife <= 50 then 1 else 0 end) as 50以下,            sum(case when batterylife >= 51 and batterylife <= 100 then 1 else 0 end) as 51到100,            sum(case when batterylife >= 101 and batterylife <= 150 then 1 else 0 end) as 101至150,            sum(case when batterylife >= 151 then 1 else 0 end) as 151以上            from drivinglog
            {where}
            ) t
            union all
            SELECT '151以上' as batterylife,case when t.151以上 is null then 0 else t.151以上 end total
            from 
            (select
            sum(case when batterylife <= 50 then 1 else 0 end) as 50以下,            sum(case when batterylife >= 51 and batterylife <= 100 then 1 else 0 end) as 51到100,            sum(case when batterylife >= 101 and batterylife <= 150 then 1 else 0 end) as 101至150,            sum(case when batterylife >= 151 then 1 else 0 end) as 151以上            from drivinglog
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg, encoder=CustomJsonEncoder)
def drivinglog_sectionStat_drivingbehaviorrating(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))
        raw_query_string = request.META.get('QUERY_STRING', '')
        raw_query_string = unquote(raw_query_string)
        conditionColumn = ""
        conditionValue = ""
        if "conditionColumn=" in raw_query_string:
            conditionColumn = raw_query_string.split("conditionColumn=")[1].split("&")[0]
        if "conditionValue=" in raw_query_string:
            conditionValue = raw_query_string.split("conditionValue=")[1].split("&")[0]
        if conditionColumn != "":
            for index, value in enumerate(conditionColumn.split(";")):
                if ',' in value:
                    where = where + f''' and {value.split(',')[0]} >= \'{conditionValue.split(";")[index].split(",")[0]}\''''
                    where = where + f''' and {value.split(',')[1]} <= \'{conditionValue.split(";")[index].split(",")[1]}\''''
                else:
                    where = where + f''' and {value} = \'{conditionValue.split(";")[index]}\''''
        sql = """
            SELECT '20以下' as drivingbehaviorrating,case when t.20以下 is null then 0 else t.20以下 end total
            from 
            (select
            sum(case when drivingbehaviorrating <= 20 then 1 else 0 end) as 20以下,            sum(case when drivingbehaviorrating >= 21 and drivingbehaviorrating <= 60 then 1 else 0 end) as 31到60,            sum(case when drivingbehaviorrating >= 61 and drivingbehaviorrating <= 100 then 1 else 0 end) as 60到100            from drivinglog
            {where}
            ) t
            union all
            SELECT '31到60' as drivingbehaviorrating,case when t.31到60 is null then 0 else t.31到60 end total
            from 
            (select
            sum(case when drivingbehaviorrating <= 20 then 1 else 0 end) as 20以下,            sum(case when drivingbehaviorrating >= 21 and drivingbehaviorrating <= 60 then 1 else 0 end) as 31到60,            sum(case when drivingbehaviorrating >= 61 and drivingbehaviorrating <= 100 then 1 else 0 end) as 60到100            from drivinglog
            {where}
            ) t
            union all
            SELECT '60到100' as drivingbehaviorrating,case when t.60到100 is null then 0 else t.60到100 end total
            from 
            (select
            sum(case when drivingbehaviorrating <= 20 then 1 else 0 end) as 20以下,            sum(case when drivingbehaviorrating >= 21 and drivingbehaviorrating <= 60 then 1 else 0 end) as 31到60,            sum(case when drivingbehaviorrating >= 61 and drivingbehaviorrating <= 100 then 1 else 0 end) as 60到100            from drivinglog
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg, encoder=CustomJsonEncoder)



import math

def drivinglog_cleanse_preview(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        try:
            summary = summarize_drivinglog_quality(drivinglog.objects.all())
            msg["data"] = {
                "total_count": summary["total_count"],
                "valid_count": summary["valid_count"],
                "invalid_count": summary["invalid_count"],
                "issues": summary["issues"],
                "invalid_rows": summary["invalid_rows"],
            }
        except Exception as e:
            msg["code"] = other_code
            msg["msg"] = str(e)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglog_cleanse_apply(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        try:
            summary = summarize_drivinglog_quality(drivinglog.objects.all())
            artifact_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "artifacts", "reports")
            paths = export_cleanse_artifacts(summary, artifact_dir)
            msg["data"] = {
                "total_count": summary["total_count"],
                "valid_count": summary["valid_count"],
                "invalid_count": summary["invalid_count"],
                "issues": summary["issues"],
                "report_path": paths["report_path"],
                "training_path": paths["training_path"],
            }
        except Exception as e:
            msg["code"] = other_code
            msg["msg"] = str(e)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglog_cleanse(request):
    return drivinglog_cleanse_apply(request)




