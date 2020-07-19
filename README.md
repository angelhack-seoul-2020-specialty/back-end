# back-end
스폐셜티 Backend AI Blockchain 연동 플랫폼 (Flask 및 Web) 


[Python Flask 기반 추가되는 라이브러리 정보]
-


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

2) 뱃지정보
CREATE TABLE `BADGE_INFO` (
  `Idx` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Name` varchar(100) NOT NULL, -- 뱃지명
  `Way` varchar(100) NOT NULL, --뱃지획득 방법
  `Image_src` varchar(100) NOT NULL, --뱃지 이미지경로
  `Rarity` varchar(100) DEFAULT NULL, --뱃지등급
  PRIMARY KEY (`Idx`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

3) 커피박 로그정보
CREATE TABLE `COFFEEPARK_LOG` (
  `Idx` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` varchar(50) NOT NULL, --사용자ID
  `UserType` varchar(30) NOT NULL DEFAULT '', --사용자타입
  `QtyKg` float NOT NULL, --커피박신청 수량(Kg)
  `Status` varchar(30) NOT NULL DEFAULT '', --상태값 (waiting, on_way, completed)
  `Insert_Dt` datetime DEFAULT NULL, --입력일시
  PRIMARY KEY (`Idx`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8;

4) 블록체인 로그정보
CREATE TABLE `BLOCKCHAIN_LOG` (
  `Idx` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `TranQty` int(11) DEFAULT NULL, --트랜잭션 발생수
  `Insert_Dt` datetime DEFAULT NULL, --블록체인 트랜잭션 발생수 수집일시
  PRIMARY KEY (`Idx`)
) ENGINE=InnoDB AUTO_INCREMENT=622 DEFAULT CHARSET=utf8;

5) 뱃지 로그정보
CREATE TABLE `BADGE_LOG` (
  `Idx` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `Userid` varchar(50) NOT NULL, --사용자ID
  `UserType` varchar(30) NOT NULL DEFAULT '', --사용자타입
  `BadgeKey` bigint(20) NOT NULL, --뱃지 key Index
  `Insert_Dt` datetime DEFAULT NULL, --획득일시
  PRIMARY KEY (`Idx`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;

[웹플랫폼 html,css 참조]
- jui 기반 html, css, chart 참조하여 만들었습니다. (MIT 라이센스, 누구나 활용가능)
