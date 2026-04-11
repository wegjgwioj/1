USE `diandong5k56la1f`;

UPDATE `drivinglog`
SET `vehiclemodel` = CASE `vehiclemodel`
  WHEN 'Model-A' THEN '比亚迪海豹'
  WHEN 'M1' THEN '五菱宏光MINIEV'
  WHEN 'Geely Zeek' THEN '极氪001'
  WHEN 'NIO ES6 SU' THEN '蔚来ES6'
  WHEN 'BYD Han EV' THEN '比亚迪汉EV'
  WHEN 'SAIC Roewe' THEN '荣威D7 EV'
  WHEN 'GAC Aion S' THEN '埃安AION S'
  WHEN 'Li Auto L9' THEN '理想L9'
  WHEN 'Audi Q4 e-' THEN '奥迪Q4 e-tron'
  WHEN 'VW ID.3 20' THEN '大众ID.3'
  WHEN 'Tesla Mode' THEN '特斯拉Model 3'
  WHEN 'Great Wall' THEN '欧拉好猫'
  WHEN 'Jianghuai' THEN '江淮钇为3'
  WHEN 'Jianghuai ' THEN '江淮钇为3'
  WHEN 'Xpeng P7 P' THEN '小鹏P7'
  WHEN 'Chery Tigg' THEN '奇瑞小蚂蚁'
  WHEN 'Changan UN' THEN '长安Lumin'
  WHEN 'BMW iX3 20' THEN '宝马iX3'
  ELSE `vehiclemodel`
END;

UPDATE `drivinglog`
SET `vehiclenumber` = 'MINI-001'
WHERE `vehiclenumber` = 'C1';
