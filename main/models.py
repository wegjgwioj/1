#coding:utf-8
from django.db import models

from .model import BaseModel

from datetime import datetime



class user(BaseModel):
    __doc__ = u'''user'''
    __tablename__ = 'user'

    __loginUser__='useraccount'


    __authTables__={}
    __authPeople__='是'#用户表，表属性loginUserColumn对应的值就是用户名字段，mima就是密码字段
    __loginUserColumn__='useraccount'#用户表，表属性loginUserColumn对应的值就是用户名字段，mima就是密码字段
    __sfsh__='否'#表sfsh(是否审核，”是”或”否”)字段和sfhf(审核回复)字段，后台列表(page)的操作中要多一个”审核”按钮，点击”审核”弹出一个页面，包含”是否审核”和”审核回复”，点击确定调用update接口，修改sfsh和sfhf两个字段。
    __authSeparate__='否'#后台列表权限
    __thumbsUp__='否'#表属性thumbsUp[是/否]，新增thumbsupnum赞和crazilynum踩字段
    __intelRecom__='否'#智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
    __browseClick__='否'#表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1
    __foreEndListAuth__='否'#前台列表权限foreEndListAuth[是/否]；当foreEndListAuth=是，刷的表新增用户字段userid，前台list列表接口仅能查看自己的记录和add接口后台赋值userid的值
    __foreEndList__='否'#表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
    __isAdmin__='否'#表属性isAdmin=”是”,刷出来的用户表也是管理员，即page和list可以查看所有人的考试记录(同时应用于其他表)
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    useraccount=models.CharField ( max_length=255,null=False,unique=True, verbose_name='用户账号' )
    password=models.CharField ( max_length=255,null=False, unique=False, verbose_name='密码' )
    username=models.CharField ( max_length=255,null=False, unique=False, verbose_name='用户姓名' )
    gender=models.CharField ( max_length=255, null=True, unique=False, verbose_name='性别' )
    headportrait=models.TextField   (  null=True, unique=False, verbose_name='头像' )
    mobilephone=models.CharField ( max_length=255, null=True, unique=False, verbose_name='手机' )
    '''
    useraccount=VARCHAR
    password=VARCHAR
    username=VARCHAR
    gender=VARCHAR
    headportrait=Text
    mobilephone=VARCHAR
    '''
    class Meta:
        db_table = 'user'
        verbose_name = verbose_name_plural = '用户'
class drivinglog(BaseModel):
    __doc__ = u'''drivinglog'''
    __tablename__ = 'drivinglog'



    __authTables__={}
    __authPeople__='否'#用户表，表属性loginUserColumn对应的值就是用户名字段，mima就是密码字段
    __sfsh__='否'#表sfsh(是否审核，”是”或”否”)字段和sfhf(审核回复)字段，后台列表(page)的操作中要多一个”审核”按钮，点击”审核”弹出一个页面，包含”是否审核”和”审核回复”，点击确定调用update接口，修改sfsh和sfhf两个字段。
    __authSeparate__='否'#后台列表权限
    __thumbsUp__='否'#表属性thumbsUp[是/否]，新增thumbsupnum赞和crazilynum踩字段
    __intelRecom__='是'#智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
    __browseClick__='是'#表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1
    __foreEndListAuth__='否'#前台列表权限foreEndListAuth[是/否]；当foreEndListAuth=是，刷的表新增用户字段userid，前台list列表接口仅能查看自己的记录和add接口后台赋值userid的值
    __foreEndList__='否'#表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
    __isAdmin__='否'#表属性isAdmin=”是”,刷出来的用户表也是管理员，即page和list可以查看所有人的考试记录(同时应用于其他表)
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    vehiclenumber=models.CharField ( max_length=255, null=True, unique=False, verbose_name='车辆编号' )
    vehiclemodel=models.CharField ( max_length=255, null=True, unique=False, verbose_name='车辆型号' )
    batterycapacity=models.IntegerField  (  null=True, unique=False, verbose_name='电池容量' )
    batterylife=models.IntegerField  (  null=True, unique=False, verbose_name='电池寿命/月' )
    accumulatedmileage=models.IntegerField  (  null=True, unique=False, verbose_name='行驶里程' )
    starttime=models.DateTimeField  (  null=True, unique=False, verbose_name='开始时间' )
    endtime=models.DateTimeField  (  null=True, unique=False, verbose_name='结束时间' )
    averagespeed=models.IntegerField  (  null=True, unique=False, verbose_name='平均车速' )
    batterylevel=models.IntegerField  (  null=True, unique=False, verbose_name='电池余量' )
    powerconsumption=models.IntegerField  (  null=True, unique=False, verbose_name='耗电量' )
    drivingroute=models.CharField ( max_length=255, null=True, unique=False, verbose_name='行驶路线' )
    collectiontime=models.DateTimeField  (  null=True, unique=False, verbose_name='采集时间' )
    rapidaccelerationtimes=models.IntegerField  (  null=True, unique=False, verbose_name='急加速次数' )
    numberofrapiddecelerations=models.IntegerField  (  null=True, unique=False, verbose_name='急减速次数' )
    numberofspeedingincidents=models.IntegerField  (  null=True, unique=False, verbose_name='超速次数' )
    energysavingsuggestions=models.CharField ( max_length=255, null=True, unique=False, verbose_name='节能建议' )
    drivingbehaviorrating=models.IntegerField  (  null=True, unique=False, verbose_name='驾驶行为评分' )
    clicknum=models.IntegerField  (  null=True, default=0, unique=False, verbose_name='点击次数' )
    clicktime=models.DateTimeField  (  null=True, unique=False, verbose_name='最近点击时间' )
    storeupnum=models.IntegerField  (  null=True, default=0, unique=False, verbose_name='收藏数' )
    discussnum=models.IntegerField  (  null=True, default=0, unique=False, verbose_name='评论数' )
    '''
    vehiclenumber=VARCHAR
    vehiclemodel=VARCHAR
    batterycapacity=Integer
    batterylife=Integer
    accumulatedmileage=Integer
    starttime=DateTime
    endtime=DateTime
    averagespeed=Integer
    batterylevel=Integer
    powerconsumption=Integer
    drivingroute=VARCHAR
    collectiontime=DateTime
    rapidaccelerationtimes=Integer
    numberofrapiddecelerations=Integer
    numberofspeedingincidents=Integer
    energysavingsuggestions=VARCHAR
    drivingbehaviorrating=Integer
    '''
    class Meta:
        db_table = 'drivinglog'
        verbose_name = verbose_name_plural = '行车日志'
class vehicleknowledge(BaseModel):
    __doc__ = u'''vehicleknowledge'''
    __tablename__ = 'vehicleknowledge'

    __authTables__={}
    __authPeople__='否'
    __sfsh__='否'
    __authSeparate__='否'
    __thumbsUp__='否'
    __intelRecom__='否'
    __browseClick__='否'
    __foreEndListAuth__='否'
    __foreEndList__='否'
    __isAdmin__='否'
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    vehiclemodel=models.CharField ( max_length=255, null=False, unique=False, verbose_name='车型名称' )
    manufacturer=models.CharField ( max_length=255, null=True, unique=False, verbose_name='厂商/品牌' )
    batterytype=models.CharField ( max_length=255, null=True, unique=False, verbose_name='电池类型' )
    officialrange=models.CharField ( max_length=255, null=True, unique=False, verbose_name='官方续航' )
    chargeinfo=models.CharField ( max_length=255, null=True, unique=False, verbose_name='充电信息' )
    summary=models.TextField   (  null=True, unique=False, verbose_name='车型简介' )
    sourceurl=models.TextField   (  null=True, unique=False, verbose_name='来源地址' )
    crawlstatus=models.CharField ( max_length=50, null=True, default='未采集', unique=False, verbose_name='采集状态' )
    crawltime=models.DateTimeField  (  null=True, unique=False, verbose_name='采集时间' )
    rawdata=models.TextField   (  null=True, unique=False, verbose_name='原始数据' )
    '''
    vehiclemodel=VARCHAR
    manufacturer=VARCHAR
    batterytype=VARCHAR
    officialrange=VARCHAR
    chargeinfo=VARCHAR
    summary=Text
    sourceurl=Text
    crawlstatus=VARCHAR
    crawltime=DateTime
    rawdata=Text
    '''
    class Meta:
        db_table = 'vehicleknowledge'
        verbose_name = verbose_name_plural = '车型知识'
class storeup(BaseModel):
    __doc__ = u'''storeup'''
    __tablename__ = 'storeup'

    __authTables__={}
    __authPeople__='否'
    __sfsh__='否'
    __authSeparate__='是'
    __thumbsUp__='否'
    __intelRecom__='否'
    __browseClick__='否'
    __foreEndListAuth__='是'
    __foreEndList__='是'
    __isAdmin__='否'
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    userid=models.BigIntegerField  (  null=False, unique=False, verbose_name='用户id' )
    refid=models.BigIntegerField  (  null=False, unique=False, verbose_name='关联主表id' )
    tablename=models.CharField ( max_length=100, null=False, unique=False, verbose_name='关联表名' )
    name=models.CharField ( max_length=255, null=True, unique=False, verbose_name='收藏名称' )
    picture=models.TextField   (  null=True, unique=False, verbose_name='封面' )
    type=models.CharField ( max_length=50, null=True, default='1', unique=False, verbose_name='收藏类型' )
    inteltype=models.CharField ( max_length=100, null=True, unique=False, verbose_name='偏好类型' )
    '''
    userid=BigInteger
    refid=BigInteger
    tablename=VARCHAR
    name=VARCHAR
    picture=Text
    type=VARCHAR
    inteltype=VARCHAR
    '''
    class Meta:
        db_table = 'storeup'
        verbose_name = verbose_name_plural = '收藏'
        unique_together = ('userid', 'refid', 'tablename')
class discussdrivinglog(BaseModel):
    __doc__ = u'''discussdrivinglog'''
    __tablename__ = 'discussdrivinglog'

    __authTables__={}
    __authPeople__='否'
    __sfsh__='否'
    __authSeparate__='否'
    __thumbsUp__='否'
    __intelRecom__='否'
    __browseClick__='否'
    __foreEndListAuth__='否'
    __foreEndList__='是'
    __isAdmin__='否'
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    refid=models.BigIntegerField  (  null=False, unique=False, verbose_name='行车日志id' )
    userid=models.BigIntegerField  (  null=False, unique=False, verbose_name='评论用户id' )
    avatarurl=models.TextField   (  null=True, unique=False, verbose_name='头像' )
    nickname=models.CharField ( max_length=255, null=True, unique=False, verbose_name='昵称' )
    content=models.TextField   (  null=True, unique=False, verbose_name='评论内容' )
    reply=models.TextField   (  null=True, unique=False, verbose_name='回复JSON' )
    isreply=models.IntegerField  (  null=True, default=0, unique=False, verbose_name='是否回复' )
    status=models.CharField ( max_length=50, null=True, default='正常', unique=False, verbose_name='状态' )
    '''
    refid=BigInteger
    userid=BigInteger
    avatarurl=Text
    nickname=VARCHAR
    content=Text
    reply=Text
    isreply=Integer
    status=VARCHAR
    '''
    class Meta:
        db_table = 'discussdrivinglog'
        verbose_name = verbose_name_plural = '行车日志评论'
class drivinglogforecast(BaseModel):
    __doc__ = u'''drivinglogforecast'''
    __tablename__ = 'drivinglogforecast'



    __authTables__={}
    __authPeople__='否'#用户表，表属性loginUserColumn对应的值就是用户名字段，mima就是密码字段
    __sfsh__='否'#表sfsh(是否审核，”是”或”否”)字段和sfhf(审核回复)字段，后台列表(page)的操作中要多一个”审核”按钮，点击”审核”弹出一个页面，包含”是否审核”和”审核回复”，点击确定调用update接口，修改sfsh和sfhf两个字段。
    __authSeparate__='否'#后台列表权限
    __thumbsUp__='否'#表属性thumbsUp[是/否]，新增thumbsupnum赞和crazilynum踩字段
    __intelRecom__='否'#智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
    __browseClick__='否'#表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1
    __foreEndListAuth__='否'#前台列表权限foreEndListAuth[是/否]；当foreEndListAuth=是，刷的表新增用户字段userid，前台list列表接口仅能查看自己的记录和add接口后台赋值userid的值
    __foreEndList__='否'#表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
    __isAdmin__='否'#表属性isAdmin=”是”,刷出来的用户表也是管理员，即page和list可以查看所有人的考试记录(同时应用于其他表)
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    vehiclemodel=models.CharField ( max_length=255, null=True, unique=False, verbose_name='车辆型号' )
    batterycapacity=models.IntegerField  (  null=True, unique=False, verbose_name='电池容量' )
    accumulatedmileage=models.IntegerField  (  null=True, unique=False, verbose_name='累计行驶里程' )
    drivingbehaviorrating=models.IntegerField  (  null=True, unique=False, verbose_name='驾驶行为评分' )
    batterylife=models.IntegerField  (  null=True, unique=False, verbose_name='电池寿命' )
    predictedpowerconsumption=models.FloatField  (  null=True, unique=False, verbose_name='预测耗电量' )
    risklevel=models.CharField ( max_length=20, null=True, unique=False, verbose_name='风险等级' )
    modelname=models.CharField ( max_length=100, null=True, unique=False, verbose_name='模型名称' )
    modelversion=models.CharField ( max_length=100, null=True, unique=False, verbose_name='模型版本' )
    majorfactors=models.TextField   (  null=True, unique=False, verbose_name='主要影响因素' )
    '''
    vehiclemodel=VARCHAR
    batterycapacity=Integer
    accumulatedmileage=Integer
    drivingbehaviorrating=Integer
    batterylife=Integer
    predictedpowerconsumption=Float
    risklevel=VARCHAR
    modelname=VARCHAR
    modelversion=VARCHAR
    majorfactors=Text
    '''
    class Meta:
        db_table = 'drivinglogforecast'
        verbose_name = verbose_name_plural = '电池寿命预测'
class users(BaseModel):
    __doc__ = u'''users'''
    __tablename__ = 'users'



    __authTables__={}
    __authPeople__ = '是'
    __isAdmin__ = '是'
    addtime = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    username=models.CharField ( max_length=255,null=False, unique=False, verbose_name='用户名' )
    password=models.CharField ( max_length=255,null=False, unique=False, verbose_name='密码' )
    role=models.CharField ( max_length=255, null=True, unique=False,default='管理员', verbose_name='角色' )
    image=models.TextField   (  null=True, unique=False, verbose_name='头像' )
    '''
    username=VARCHAR
    password=VARCHAR
    role=VARCHAR
    image=Text
    '''
    class Meta:
        db_table = 'users'
        verbose_name = verbose_name_plural = '管理员'
