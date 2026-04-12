from django.db import connection


DRIVINGLOG_COLUMN_SQL = {
    "clicknum": "ALTER TABLE `drivinglog` ADD COLUMN `clicknum` int(11) DEFAULT 0 COMMENT '点击次数'",
    "clicktime": "ALTER TABLE `drivinglog` ADD COLUMN `clicktime` datetime DEFAULT NULL COMMENT '最近点击时间'",
    "storeupnum": "ALTER TABLE `drivinglog` ADD COLUMN `storeupnum` int(11) DEFAULT 0 COMMENT '收藏数'",
    "discussnum": "ALTER TABLE `drivinglog` ADD COLUMN `discussnum` int(11) DEFAULT 0 COMMENT '评论数'",
}

DRIVINGLOGFORECAST_COLUMN_SQL = {
    "predictedpowerconsumption": "ALTER TABLE `drivinglogforecast` ADD COLUMN `predictedpowerconsumption` double DEFAULT NULL COMMENT '预测耗电量'",
    "risklevel": "ALTER TABLE `drivinglogforecast` ADD COLUMN `risklevel` varchar(20) DEFAULT NULL COMMENT '风险等级'",
    "modelname": "ALTER TABLE `drivinglogforecast` ADD COLUMN `modelname` varchar(100) DEFAULT NULL COMMENT '模型名称'",
    "modelversion": "ALTER TABLE `drivinglogforecast` ADD COLUMN `modelversion` varchar(100) DEFAULT NULL COMMENT '模型版本'",
    "majorfactors": "ALTER TABLE `drivinglogforecast` ADD COLUMN `majorfactors` longtext COMMENT '主要影响因素'",
}

FEATURE_TABLE_SQL = {
    "storeup": """
        CREATE TABLE IF NOT EXISTS `storeup` (
          `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
          `addtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `userid` bigint(20) NOT NULL COMMENT '用户id',
          `refid` bigint(20) NOT NULL COMMENT '关联主表id',
          `tablename` varchar(100) NOT NULL COMMENT '关联表名',
          `name` varchar(255) DEFAULT NULL COMMENT '收藏名称',
          `picture` longtext COMMENT '封面',
          `type` varchar(50) DEFAULT '1' COMMENT '收藏类型',
          `inteltype` varchar(100) DEFAULT NULL COMMENT '偏好类型',
          PRIMARY KEY (`id`),
          UNIQUE KEY `uniq_storeup_user_ref` (`userid`, `refid`, `tablename`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏'
    """,
    "discussdrivinglog": """
        CREATE TABLE IF NOT EXISTS `discussdrivinglog` (
          `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
          `addtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `refid` bigint(20) NOT NULL COMMENT '行车日志id',
          `userid` bigint(20) NOT NULL COMMENT '评论用户id',
          `avatarurl` longtext COMMENT '头像',
          `nickname` varchar(255) DEFAULT NULL COMMENT '昵称',
          `content` longtext COMMENT '评论内容',
          `reply` longtext COMMENT '回复JSON',
          `isreply` int(11) DEFAULT 0 COMMENT '是否回复',
          `status` varchar(50) DEFAULT '正常' COMMENT '状态',
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行车日志评论'
    """,
    "vehicleknowledge": """
        CREATE TABLE IF NOT EXISTS `vehicleknowledge` (
          `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键',
          `addtime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
          `vehiclemodel` varchar(255) NOT NULL COMMENT '车型名称',
          `manufacturer` varchar(255) DEFAULT NULL COMMENT '厂商/品牌',
          `batterytype` varchar(255) DEFAULT NULL COMMENT '电池类型',
          `officialrange` varchar(255) DEFAULT NULL COMMENT '官方续航',
          `chargeinfo` varchar(255) DEFAULT NULL COMMENT '充电信息',
          `summary` longtext COMMENT '车型简介',
          `sourceurl` longtext COMMENT '来源地址',
          `crawlstatus` varchar(50) DEFAULT '未采集' COMMENT '采集状态',
          `crawltime` datetime DEFAULT NULL COMMENT '采集时间',
          `rawdata` longtext COMMENT '原始数据',
          PRIMARY KEY (`id`),
          KEY `idx_vehicleknowledge_model` (`vehiclemodel`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='车型知识'
    """,
}


def table_exists(table_name):
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", [table_name])
        return cursor.fetchone() is not None


def column_exists(table_name, column_name):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
              AND column_name = %s
            """,
            [table_name, column_name],
        )
        return cursor.fetchone() is not None


def sync_feature_schema():
    actions = []
    with connection.cursor() as cursor:
        for column_name, sql in DRIVINGLOG_COLUMN_SQL.items():
            if column_exists("drivinglog", column_name):
                continue
            cursor.execute(sql)
            actions.append("新增 drivinglog.%s" % column_name)

        for column_name, sql in DRIVINGLOGFORECAST_COLUMN_SQL.items():
            if column_exists("drivinglogforecast", column_name):
                continue
            cursor.execute(sql)
            actions.append("新增 drivinglogforecast.%s" % column_name)

        for table_name, sql in FEATURE_TABLE_SQL.items():
            if table_exists(table_name):
                continue
            cursor.execute(sql)
            actions.append("创建表 %s" % table_name)

    return actions
