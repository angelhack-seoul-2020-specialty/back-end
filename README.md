# back-end
스폐셜티 Backend AI Blockchain 연동 플랫폼 (Flask 및 Web) 

[DB 테이블 정보]
1) 유저정보
CREATE TABLE `USER_INFO` (
  `Idx` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` varchar(50) NOT NULL, -- 사용자ID
  `UserType` varchar(20) NOT NULL, -- 사용자타입
  `UserName` varchar(50) DEFAULT NULL, --사용자이름
  `province` varchar(50) DEFAULT NULL, --사용자지역
  PRIMARY KEY (`Idx`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;

2)
