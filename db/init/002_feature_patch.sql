USE `diandong5k56la1f`;

ALTER TABLE `drivinglog`
  ADD COLUMN `clicknum` int(11) DEFAULT 0 COMMENT '点击次数';

ALTER TABLE `drivinglog`
  ADD COLUMN `clicktime` datetime DEFAULT NULL COMMENT '最近点击时间';

ALTER TABLE `drivinglog`
  ADD COLUMN `storeupnum` int(11) DEFAULT 0 COMMENT '收藏数';

ALTER TABLE `drivinglog`
  ADD COLUMN `discussnum` int(11) DEFAULT 0 COMMENT '评论数';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='行车日志评论';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='车型知识';
