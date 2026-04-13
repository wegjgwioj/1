#coding:utf-8
import base64, copy, logging, os, sys, time, xlrd, json, datetime, configparser
import mimetypes
from django.http import HttpResponse, JsonResponse
from django.apps import apps
import numbers
from collections import defaultdict
from django.db.models.aggregates import Count,Sum
from django.db.models import Case, When, IntegerField, F
from django.forms import model_to_dict
import requests
from util.CustomJSONEncoder import CustomJsonEncoder
from .models import drivinglog, drivinglogforecast
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
from util.baidubce_api import BaiDuBce
from .config_model import config
import pandas as pd

import joblib
import pymysql
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 在导入pyplot之前设置
from matplotlib import pyplot as plt
import matplotlib.font_manager as fm
from util.configread import config_read
import os
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error,accuracy_score
from sklearn.feature_extraction import DictVectorizer
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import classification_report, confusion_matrix,confusion_matrix, mean_squared_error, mean_absolute_error, r2_score
from sklearn.tree import DecisionTreeClassifier, export_graphviz
import seaborn as sns
pd.options.mode.chained_assignment = None  # default='warn'

from .ml.predictors import load_ml_bundle, predict_drivinglog, predict_scenarios
from .dl import predict_drivinglog_dl
from .battery_life.nasa_dataset import get_battery_life_artifact_paths

#获取当前文件路径的根目录
parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dbtype, host, port, user, passwd, dbName, charset,hasHadoop = config_read(os.path.join(parent_directory,"config.ini"))
#MySQL连接配置
mysql_config = {
    'host': host,
    'user':user,
    'password': passwd,
    'database': dbName,
    'port':port
}

NASA_EXPERIMENT_FIGURES = [
    {
        "key": "capacity_curve",
        "path_key": "capacity_curve",
        "title": "容量衰减曲线",
        "description": "展示不同电池在循环过程中的容量衰减趋势，以及 1.4Ah 退化阈值。",
    },
    {
        "key": "soh_prediction_plot",
        "path_key": "soh_prediction_plot",
        "title": "SOH 预测散点图",
        "description": "对比真实 SOH 与模型预测 SOH，越贴近对角线说明拟合越稳定。",
    },
    {
        "key": "rul_prediction_plot",
        "path_key": "rul_prediction_plot",
        "title": "RUL 预测散点图",
        "description": "对比真实 RUL 与模型预测 RUL，用于说明剩余寿命估计误差分布。",
    },
]


def _load_json_file(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def _figure_url(file_name):
    return f"/{dbName}/drivinglogforecast/nasaFigure/{file_name}"


def _nasa_experiment_payload(paths):
    dataset_manifest = _load_json_file(paths.get("manifest"))
    training_manifest = _load_json_file(paths.get("training_manifest"))
    metrics = _load_json_file(paths.get("metrics"))
    available = bool(dataset_manifest and training_manifest and metrics)

    train_batteries = training_manifest.get("train_batteries") or []
    test_batteries = training_manifest.get("test_batteries") or []
    figures = []
    for figure in NASA_EXPERIMENT_FIGURES:
        file_path = paths.get(figure["path_key"])
        if file_path and os.path.exists(file_path):
            figures.append(
                {
                    "key": figure["key"],
                    "title": figure["title"],
                    "description": figure["description"],
                    "url": _figure_url(os.path.basename(file_path)),
                }
            )

    return {
        "available": available,
        "dataset": dataset_manifest,
        "experiment": {
            "dataset": training_manifest.get("dataset") or dataset_manifest.get("dataset"),
            "model_family": training_manifest.get("model_family"),
            "split_strategy": training_manifest.get("split_strategy"),
            "feature_columns": training_manifest.get("feature_columns") or {},
            "sample_count": training_manifest.get("sample_count") or dataset_manifest.get("sample_count"),
            "battery_count": training_manifest.get("battery_count") or dataset_manifest.get("battery_count"),
            "train_battery_count": len(train_batteries),
            "test_battery_count": len(test_batteries),
            "updated_at": training_manifest.get("updated_at") or dataset_manifest.get("generated_at"),
        },
        "metrics": metrics,
        "figures": figures,
        "notes": [
            "NASA PCoE 电池老化数据用于验证系统已经具备接入公开真实寿命实验、训练模型并输出可解释结果的能力。",
            "SOH 用来表示当前健康度，RUL 用来表示距离退化终点还剩多少循环，两者可以支撑答辩中的寿命分析说明。",
            "当前结果适合用作“真实寿命实验”展示，不应直接表述为对任意真实车辆剩余寿命的精准承诺。",
        ],
        "limitations": [
            "实验对象是标准化电池循环数据，不是整车 BMS 长周期时序，所以和实际车辆工况仍有域差异。",
            "若要进一步逼近真实车辆寿命预测，需要补充车辆级时序、电流倍率、温度环境、充电习惯等长期标签数据。",
        ],
    }


def drivinglogforecast_nasaExperiment(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, "msg": mes.normal_code, "data": {}}
        try:
            paths = get_battery_life_artifact_paths()
            payload = _nasa_experiment_payload(paths)
            if not payload["available"]:
                msg["msg"] = "NASA 实验产物尚未生成，请先运行数据准备与训练命令。"
            msg["data"] = payload
        except Exception as e:
            msg["code"] = other_code
            msg["msg"] = str(e)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglogforecast_nasaFigure(request, file_name):
    if request.method in ["POST", "GET"]:
        paths = get_battery_life_artifact_paths()
        allowed_files = {
            os.path.basename(paths[item["path_key"]]): paths[item["path_key"]]
            for item in NASA_EXPERIMENT_FIGURES
            if paths.get(item["path_key"])
        }
        file_path = allowed_files.get(file_name)
        if not file_path or not os.path.exists(file_path):
            return JsonResponse({"code": other_code, "msg": "实验图片不存在"}, status=404)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as image_file:
            return HttpResponse(image_file.read(), content_type=content_type)

def auto_figsize(x_data, base_width=8, base_height=6, width_per_point=0.2):
    """根据数据点数量自动调整画布宽度"""
    num_points = len(x_data)
    dynamic_width = base_width + width_per_point * num_points
    return (dynamic_width, base_height)

#获取预测可视化图表接口
def drivinglogforecast_forecastimgs(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, 'message': 'success'}
        # 指定目录
        directory = os.path.join(parent_directory, "templates", "upload", "drivinglogforecast")
        # 获取目录下的所有文件和文件夹名称
        all_items = os.listdir(directory)
        # 过滤出文件（排除文件夹）
        files = [f'upload/drivinglogforecast/{item}' for item in all_items if os.path.isfile(os.path.join(directory, item))]
        msg["data"] = files
        fontlist=[]
        for font in fm.fontManager.ttflist:
            fontlist.append(font.name)
        msg["message"]=fontlist
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_forecast(request):
    if request.method in ["POST", "GET"]:
        try:
            req_dict = (request.session.get("req_dict") or {}).copy()
            persist = str(req_dict.pop("persist", "true")).lower() not in ("0", "false", "no", "否")
            force_retrain = str(req_dict.pop("forceRetrain", "false")).lower() in ("1", "true", "yes", "是")
            prediction = predict_drivinglog(req_dict, persist=persist, force_retrain=force_retrain)
            msg = {'code': normal_code, "msg": mes.normal_code, "data": prediction}
        except Exception as e:
            msg = {'code': other_code, "msg": str(e)}
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglogforecast_predict(request):
    return drivinglogforecast_forecast(request)


def drivinglogforecast_metrics(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, "msg": mes.normal_code, "data": {}}
        try:
            req_dict = (request.session.get("req_dict") or {}).copy()
            force_retrain = str(req_dict.pop("forceRetrain", "false")).lower() in ("1", "true", "yes", "是")
            bundle = load_ml_bundle(force_retrain=force_retrain)
            msg["data"] = {
                "metrics": bundle["metrics"],
                "comparison_metrics": bundle.get("comparison_metrics", {}),
                "updated_at": bundle["updated_at"],
                "modelversion": bundle["version"],
                "available_models": list(bundle["models"].keys()),
            }
        except Exception as e:
            msg["code"] = other_code
            msg["msg"] = str(e)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglogforecast_scenarios(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, "msg": mes.normal_code, "data": {}}
        try:
            req_dict = (request.session.get("req_dict") or {}).copy()
            force_retrain = str(req_dict.pop("forceRetrain", "false")).lower() in ("1", "true", "yes", "是")
            msg["data"] = predict_scenarios(req_dict, force_retrain=force_retrain)
        except Exception as e:
            msg["code"] = other_code
            msg["msg"] = str(e)
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglogforecast_compare(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, "msg": mes.normal_code, "data": {}}
        try:
            req_dict = (request.session.get("req_dict") or {}).copy()
            force_retrain = str(req_dict.pop("forceRetrain", "false")).lower() in ("1", "true", "yes", "是")
            ml_result = predict_drivinglog(req_dict, persist=False, force_retrain=force_retrain)
            dl_result = predict_drivinglog_dl(
                req_dict,
                force_retrain=force_retrain,
                queryset_or_records=drivinglog.objects.all(),
            )
            ml_score = float(ml_result.get("metrics", {}).get("power", {}).get("MAE", 999)) + float(
                ml_result.get("metrics", {}).get("life", {}).get("MAE", 999)
            )
            dl_score = float(dl_result.get("metrics", {}).get("power_dl", {}).get("MAE", 999)) + float(
                dl_result.get("metrics", {}).get("life_dl", {}).get("MAE", 999)
            )
            msg["data"] = {
                "ml": ml_result,
                "dl": dl_result,
                "comparison": {
                    "power_delta": round(
                        float(dl_result["predictedpowerconsumption"]) - float(ml_result["predictedpowerconsumption"]),
                        2,
                    ),
                    "life_delta": int(dl_result["batterylife"]) - int(ml_result["batterylife"]),
                    "preferred_model": "ml" if ml_score <= dl_score else "dl",
                },
                "updated_at": dl_result.get("updated_at") or ml_result.get("updated_at"),
            }
        except Exception as e:
            msg["code"] = other_code
            msg["msg"] = str(e)
        return JsonResponse(msg, encoder=CustomJsonEncoder)
def to_forecast(data,req_dict,value):
    if len(data) < 5:
        print(f"的样本数量不足: {len(data)}")
        return pd.DataFrame()
    #3.处理特征值和目标值
    labels={}
    for key in data.keys():
        if pd.api.types.is_string_dtype(data[key]):
            label_encoder = LabelEncoder()
            labels[key] = label_encoder
            data[key] = label_encoder.fit_transform(data[key])
    #4.数据集划分
    X = data[[
        'vehiclemodel',
        'batterycapacity',
        'accumulatedmileage',
        'drivingbehaviorrating',
    ]]
    y = data[[
        'batterylife',
    ]]
    x_train, x_test, y_train, y_test = train_test_split(X, y,test_size=0.2, random_state=22)
    #5.构建预测特征值
    #根据输入的特征值去预测
    if req_dict:
        req_dict.pop('addtime',None)
        future_df = pd.DataFrame([req_dict])
        for key in future_df.keys():
           if key in labels:
               encoder = labels[key]
               values = future_df[key][0]
               try:
                   values = encoder.transform([values])[0]
               except ValueError as e: #处理未见过的标签
                   values = np.array([encoder.transform([v])[0] if v in encoder.classes_ else -1 for v in values]).sum()
               future_df[key][0] = values
    else:
        future_df = x_test
    #特征工程-标准化
    estimator_file = os.path.join(parent_directory, "drivinglogforecast.pkl")
    estimator = RandomForestRegressor(n_estimators=100, random_state=42)
    _, num_columns = y_train.shape
    if num_columns>=2:
        estimator.fit(x_train, y_train)
    else:
        estimator.fit(x_train, y_train.values.ravel())
    y_pred = estimator.predict(x_test)
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体 SimHei
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题
    # 绘制预测值与实际值的散点图
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], color='red', lw=2)
    plt.xlabel("实际值")
    plt.ylabel("预测值")
    plt.title("实际值与预测值(随机森林回归)")
    directory =os.path.join(parent_directory, "templates","upload","drivinglogforecast","figure.png")
    os.makedirs(os.path.dirname(directory), exist_ok=True)
    plt.savefig(directory)
    plt.clf()
    plt.close()
    # 绘制特征重要性
    feature_importances = estimator.feature_importances_
    features = [
        'vehiclemodel',
        'batterycapacity',
        'accumulatedmileage',
        'drivingbehaviorrating',
    ]
    sns.barplot(x=feature_importances, y=features)
    plt.xlabel("重要性得分")
    plt.ylabel("特征")
    plt.title("特征重要性")
    if value!=None:
        directory =os.path.join(parent_directory, "templates","upload","drivinglogforecast","{value}_figure.png")
        os.makedirs(os.path.dirname(directory), exist_ok=True)
        plt.savefig(directory)
    else:
        directory =os.path.join(parent_directory, "templates","upload","drivinglogforecast","figure_other.png")
        os.makedirs(os.path.dirname(directory), exist_ok=True)
        plt.savefig(directory)
    plt.clf()
    plt.close()
    #保存模型
    joblib.dump(estimator, estimator_file)

    #7.进行预测
    y_predict = estimator.predict(future_df)
    if isinstance(y_predict[0], numbers.Number) or len(y_predict[0])<2:
        y_predict = np.mean(y_predict, axis=0)
        if not isinstance(y_predict, np.ndarray):
            y_predict = np.expand_dims(y_predict, axis=0)
    df = pd.DataFrame(y_predict, columns=[
        'batterylife',
    ])
    df['batterylife']=df['batterylife'].astype(int)
    return df

def drivinglogforecast_default(request):

    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code,"msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        req_dict.update({"isdefault":"是"})
        data=drivinglogforecast.getbyparams(drivinglogforecast, drivinglogforecast, req_dict)
        if len(data)>0:
            msg['data']  = data[0]
        else:
            msg['data']  = {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_page(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        global drivinglogforecast
        #当前登录用户信息
        tablename = Auth().getTokenInfo(request).get('tablename')

        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  =drivinglogforecast.page(drivinglogforecast, drivinglogforecast,req_dict, request)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_autoSort(request):
    '''
    ．智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
主要信息列表（如商品列表，新闻列表）中使用，显示最近点击的或最新添加的5条记录就行
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        if "clicknum"  in drivinglogforecast.getallcolumn(drivinglogforecast,drivinglogforecast):
            req_dict['sort']='clicknum'
        elif "browseduration"  in drivinglogforecast.getallcolumn(drivinglogforecast,drivinglogforecast):
            req_dict['sort']='browseduration'
        else:
            req_dict['sort']='clicktime'
        req_dict['order']='desc'
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = drivinglogforecast.page(drivinglogforecast,drivinglogforecast, req_dict)

        return JsonResponse(msg, encoder=CustomJsonEncoder)

#分类列表
def drivinglogforecast_lists(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":[]}
        msg['data'],_,_,_,_  = drivinglogforecast.page(drivinglogforecast, drivinglogforecast, {})
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_query(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        try:
            query_result = drivinglogforecast.objects.filter(**request.session.get("req_dict")).values()
            msg['data'] = query_result[0]
        except Exception as e:

            msg['code'] = crud_error_code
            msg['msg'] = f"发生错误：{e}"
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_list(request):
    '''
    前台分页
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        #获取全部列名
        columns=  drivinglogforecast.getallcolumn( drivinglogforecast, drivinglogforecast)
        if "vipread" in req_dict and "vipread" not in columns:
          del req_dict["vipread"]
        #表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
        try:
            __foreEndList__=drivinglogforecast.__foreEndList__
        except:
            __foreEndList__=None
        try:
            __foreEndListAuth__=drivinglogforecast.__foreEndListAuth__
        except:
            __foreEndListAuth__=None

        #authSeparate
        try:
            __authSeparate__=drivinglogforecast.__authSeparate__
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
            __authTables__=drivinglogforecast.__authTables__
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
        
        if drivinglogforecast.__tablename__[:7]=="discuss":
            try:
                del req_dict['userid']
            except:
                pass

        q = Q()
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = drivinglogforecast.page(drivinglogforecast, drivinglogforecast, req_dict, request, q)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_save(request):
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
        columns=  drivinglogforecast.getallcolumn( drivinglogforecast, drivinglogforecast)
        if tablename!='users' and req_dict.get("userid")==None and 'userid' in columns  and __isAdmin__!='是':
            params=Auth().getTokenInfo(request).get('params')
            req_dict['userid']=params.get('id')


        if 'addtime' in req_dict.keys():
            del req_dict['addtime']

        idOrErr= drivinglogforecast.createbyreq(drivinglogforecast,drivinglogforecast, req_dict)
        if idOrErr is Exception:
            msg['code'] = crud_error_code
            msg['msg'] = idOrErr
        else:
            msg['data'] = idOrErr

        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_add(request):
    '''
    前台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        tablename=Auth().getTokenInfo(request).get('tablename')

        #获取全部列名
        columns=  drivinglogforecast.getallcolumn( drivinglogforecast, drivinglogforecast)
        try:
            __authSeparate__=drivinglogforecast.__authSeparate__
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
            __foreEndListAuth__=drivinglogforecast.__foreEndListAuth__
        except:
            __foreEndListAuth__=None

        if __foreEndListAuth__ and __foreEndListAuth__!="否":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users":
                req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")


        if 'addtime' in req_dict.keys():
            del req_dict['addtime']
        error= drivinglogforecast.createbyreq(drivinglogforecast,drivinglogforecast, req_dict)
        if error is Exception:
            msg['code'] = crud_error_code
            msg['msg'] = error
        else:
            msg['data'] = error
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_thumbsup(request,id_):
    '''
     点赞：表属性thumbsUp[是/否]，刷表新增thumbsupnum赞和crazilynum踩字段，
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        id_=int(id_)
        type_=int(req_dict.get("type",0))
        rets=drivinglogforecast.getbyid(drivinglogforecast,drivinglogforecast,id_)

        update_dict={
        "id":id_,
        }
        if type_==1:#赞
            update_dict["thumbsupnum"]=int(rets[0].get('thumbsupnum'))+1
        elif type_==2:#踩
            update_dict["crazilynum"]=int(rets[0].get('crazilynum'))+1
        error = drivinglogforecast.updatebyparams(drivinglogforecast,drivinglogforecast, update_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def drivinglogforecast_info(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data = drivinglogforecast.getbyid(drivinglogforecast,drivinglogforecast, int(id_))
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
            __browseClick__= drivinglogforecast.__browseClick__
        except:
            __browseClick__=None

        if __browseClick__=="是"  and  "clicknum"  in drivinglogforecast.getallcolumn(drivinglogforecast,drivinglogforecast):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum,"clicktime":datetime.datetime.now()}
            ret=drivinglogforecast.updatebyparams(drivinglogforecast,drivinglogforecast,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_detail(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data =drivinglogforecast.getbyid(drivinglogforecast,drivinglogforecast, int(id_))
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
            __browseClick__= drivinglogforecast.__browseClick__
        except:
            __browseClick__=None

        if __browseClick__=="是"   and  "clicknum"  in drivinglogforecast.getallcolumn(drivinglogforecast,drivinglogforecast):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum,"clicktime":datetime.datetime.now()}

            ret=drivinglogforecast.updatebyparams(drivinglogforecast,drivinglogforecast,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def drivinglogforecast_update(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if 'clicktime' in req_dict.keys() and req_dict['clicktime']=="None":
            del req_dict['clicktime']
        if req_dict.get("mima") and "mima" not in drivinglogforecast.getallcolumn(drivinglogforecast,drivinglogforecast) :
            del req_dict["mima"]
        if req_dict.get("password") and "password" not in drivinglogforecast.getallcolumn(drivinglogforecast,drivinglogforecast) :
            del req_dict["password"]
        try:
            del req_dict["clicknum"]
        except:
            pass


        error = drivinglogforecast.updatebyparams(drivinglogforecast, drivinglogforecast, req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error

        return JsonResponse(msg)


def drivinglogforecast_delete(request):
    '''
    批量删除
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")

        error=drivinglogforecast.deletes(drivinglogforecast,
            drivinglogforecast,
             req_dict.get("ids")
        )
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)


def drivinglogforecast_vote(request,id_):
    '''
    浏览点击次数（表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1）
统计商品或新闻的点击次数；提供新闻的投票功能
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code}


        data= drivinglogforecast.getbyid(drivinglogforecast, drivinglogforecast, int(id_))
        for i in data:
            votenum=i.get('votenum')
            if votenum!=None:
                params={"id":int(id_),"votenum":votenum+1}
                error=drivinglogforecast.updatebyparams(drivinglogforecast,drivinglogforecast,params)
                if error!=None:
                    msg['code'] = crud_error_code
                    msg['msg'] = error
        return JsonResponse(msg)

def drivinglogforecast_importExcel(request):
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
                    drivinglogforecast.createbyreq(drivinglogforecast, drivinglogforecast, req_dict)
                    
            except:
                pass
                
        else:
            msg = {
                "msg": "文件类型错误",
                "code": 500
            }
                
        return JsonResponse(msg)

def drivinglogforecast_autoSort2(request):
    return JsonResponse({"code": 0, "msg": '',  "data":{}})












