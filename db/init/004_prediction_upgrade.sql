ALTER TABLE `drivinglogforecast`
  ADD COLUMN `predictedpowerconsumption` double DEFAULT NULL COMMENT '预测耗电量',
  ADD COLUMN `risklevel` varchar(20) DEFAULT NULL COMMENT '风险等级',
  ADD COLUMN `modelname` varchar(100) DEFAULT NULL COMMENT '模型名称',
  ADD COLUMN `modelversion` varchar(100) DEFAULT NULL COMMENT '模型版本',
  ADD COLUMN `majorfactors` longtext COMMENT '主要影响因素';
