#coding:utf-8
import os
from configparser import ConfigParser

def config_read(filePath:str):
    cfg=ConfigParser()
    cfg.read(filePath, encoding="utf-8-sig")
    if "sql" in cfg.sections():
        dbType=os.getenv("DB_TYPE", cfg.get('sql','type'))
        host=os.getenv("DB_HOST", cfg.get('sql','host'))
        port=int(os.getenv("DB_PORT", cfg.getint('sql','port')))
        user=os.getenv("DB_USER", cfg.get('sql','user'))
        passwd=os.getenv("DB_PASSWORD", cfg.get('sql','passwd'))
        dbName=os.getenv("DB_NAME", cfg.get('sql','db'))
        charset=os.getenv("DB_CHARSET", cfg.get('sql','charset'))
        hasHadoop=os.getenv("HAS_HADOOP", cfg.get('sql','hasHadoop'))
        return dbType,host,port,user,passwd,dbName,charset,hasHadoop
    else:
        return None,None,None,None,None,None,None,None
