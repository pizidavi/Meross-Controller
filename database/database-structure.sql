--
-- Database: meross-controller
--

--
-- Table structure for table `devices`
--
CREATE TABLE `devices` (
  `intIdDevice` int(11) NOT NULL AUTO_INCREMENT,
  `strName` varchar(50) NOT NULL,
  `intUsage` int(11) NOT NULL,
  `boolSolarPowerOn` tinyint(1) NOT NULL DEFAULT 1,
  `boolDisable` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`intIdDevice`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `logs`
--
CREATE TABLE `logs` (
  `intIdDevice` int(11) NOT NULL,
  `dtaDate` datetime NOT NULL DEFAULT current_timestamp(),
  `boolState` tinyint(1) NOT NULL,
  PRIMARY KEY (`intIdDevice`,`dtaDate`,`boolState`),
  FOREIGN KEY (`intIdDevice`) REFERENCES `devices` (`intIdDevice`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `timesalwayspoweron`
--
CREATE TABLE `timesalwayspoweron` (
  `intIdDevice` int(11) NOT NULL,
  `timePowerOn` time NOT NULL,
  `timePowerOff` time NOT NULL,
  `boolDisable` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`intIdDevice`,`timePowerOn`,`timePowerOff`),
  FOREIGN KEY (`intIdDevice`) REFERENCES `devices` (`intIdDevice`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Table structure for table `users`
--
CREATE TABLE `users` (
  `strIdTelegram` varchar(15) NOT NULL,
  `strName` varchar(50) NOT NULL,
  PRIMARY KEY (`strIdTelegram`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

---
