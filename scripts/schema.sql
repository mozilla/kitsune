-- MySQL dump 10.13  Distrib 5.1.46, for apple-darwin10.3.1 (i386)
--
-- Host: localhost    Database: kitsune
-- ------------------------------------------------------
-- Server version	5.1.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `activity_action`
--

DROP TABLE IF EXISTS `activity_action`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `activity_action` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `creator_id` int(11) DEFAULT NULL,
  `created` datetime NOT NULL,
  `data` varchar(400) NOT NULL,
  `url` varchar(200) DEFAULT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` int(10) unsigned DEFAULT NULL,
  `formatter_cls` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `activity_action_f97a5119` (`creator_id`),
  KEY `activity_action_3216ff68` (`created`),
  KEY `activity_action_e4470c6e` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_95f5c947` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `creator_id_refs_id_4475b305` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_action`
--

LOCK TABLES `activity_action` WRITE;
/*!40000 ALTER TABLE `activity_action` DISABLE KEYS */;
/*!40000 ALTER TABLE `activity_action` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `activity_action_users`
--

DROP TABLE IF EXISTS `activity_action_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `activity_action_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `action_id` (`action_id`,`user_id`),
  KEY `user_id_refs_id_514426b8` (`user_id`),
  CONSTRAINT `action_id_refs_id_52ad1f42` FOREIGN KEY (`action_id`) REFERENCES `activity_action` (`id`),
  CONSTRAINT `user_id_refs_id_514426b8` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_action_users`
--

LOCK TABLES `activity_action_users` WRITE;
/*!40000 ALTER TABLE `activity_action_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `activity_action_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `announcements_announcement`
--

DROP TABLE IF EXISTS `announcements_announcement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `announcements_announcement` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `created` datetime NOT NULL,
  `creator_id` int(11) NOT NULL,
  `show_after` datetime NOT NULL,
  `show_until` datetime DEFAULT NULL,
  `content` longtext NOT NULL,
  `group_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `announcements_announcement_f97a5119` (`creator_id`),
  KEY `announcements_announcement_3c9f0fe7` (`show_after`),
  KEY `announcements_announcement_d63a60f1` (`show_until`),
  KEY `announcements_announcement_bda51c3c` (`group_id`),
  CONSTRAINT `creator_id_refs_id_1b56d8` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `group_id_refs_id_685bd3c7` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `announcements_announcement`
--

LOCK TABLES `announcements_announcement` WRITE;
/*!40000 ALTER TABLE `announcements_announcement` DISABLE KEYS */;
/*!40000 ALTER TABLE `announcements_announcement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
INSERT INTO `auth_group` VALUES (1,'Contributors');
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`,`permission_id`),
  KEY `auth_group_permissions_group_id` (`group_id`),
  KEY `auth_group_permissions_permission_id` (`permission_id`),
  CONSTRAINT `group_id_refs_id_3cea63fe` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `permission_id_refs_id_5886d21f` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_message`
--

DROP TABLE IF EXISTS `auth_message`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `message` longtext COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auth_message_user_id` (`user_id`),
  CONSTRAINT `user_id_refs_id_650f49a6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_message`
--

LOCK TABLES `auth_message` WRITE;
/*!40000 ALTER TABLE `auth_message` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_message` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`codename`),
  KEY `auth_permission_content_type_id` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_728de91f` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=222 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can add group',2,'add_group'),(5,'Can change group',2,'change_group'),(6,'Can delete group',2,'delete_group'),(7,'Can add user',3,'add_user'),(8,'Can change user',3,'change_user'),(9,'Can delete user',3,'delete_user'),(10,'Can add message',4,'add_message'),(11,'Can change message',4,'change_message'),(12,'Can delete message',4,'delete_message'),(13,'Can add content type',5,'add_contenttype'),(14,'Can change content type',5,'change_contenttype'),(15,'Can delete content type',5,'delete_contenttype'),(16,'Can add session',6,'add_session'),(17,'Can change session',6,'change_session'),(18,'Can delete session',6,'delete_session'),(19,'Can add site',7,'add_site'),(20,'Can change site',7,'change_site'),(21,'Can delete site',7,'delete_site'),(28,'Can add wiki page',10,'add_wikipage'),(29,'Can change wiki page',10,'change_wikipage'),(30,'Can delete wiki page',10,'delete_wikipage'),(31,'Can add category',11,'add_category'),(32,'Can change category',11,'change_category'),(33,'Can delete category',11,'delete_category'),(34,'Can add session',12,'add_session'),(35,'Can change session',12,'change_session'),(36,'Can delete session',12,'delete_session'),(37,'Can add tiki user',13,'add_tikiuser'),(38,'Can change tiki user',13,'change_tikiuser'),(39,'Can delete tiki user',13,'delete_tikiuser'),(40,'Can add forum',14,'add_forum'),(41,'Can change forum',14,'change_forum'),(42,'Can delete forum',14,'delete_forum'),(43,'Can add thread',15,'add_thread'),(44,'Can change thread',15,'change_thread'),(45,'Can delete thread',15,'delete_thread'),(46,'Can add post',16,'add_post'),(47,'Can change post',16,'change_post'),(48,'Can delete post',16,'delete_post'),(49,'Can add event watch',18,'add_eventwatch'),(50,'Can change event watch',18,'change_eventwatch'),(51,'Can delete event watch',18,'delete_eventwatch'),(52,'Can add question',19,'add_question'),(53,'Can change question',19,'change_question'),(54,'Can delete question',19,'delete_question'),(55,'Can add question meta data',20,'add_questionmetadata'),(56,'Can change question meta data',20,'change_questionmetadata'),(57,'Can delete question meta data',20,'delete_questionmetadata'),(58,'Can add answer',21,'add_answer'),(59,'Can change answer',21,'change_answer'),(60,'Can delete answer',21,'delete_answer'),(61,'Can add question vote',22,'add_questionvote'),(62,'Can change question vote',22,'change_questionvote'),(63,'Can delete question vote',22,'delete_questionvote'),(64,'Can add answer vote',23,'add_answervote'),(65,'Can change answer vote',23,'change_answervote'),(66,'Can delete answer vote',23,'delete_answervote'),(67,'Can add tags to and remove tags from questions',19,'tag_question'),(68,'Can add tag',24,'add_tag'),(69,'Can change tag',24,'change_tag'),(70,'Can delete tag',24,'delete_tag'),(71,'Can add tagged item',25,'add_taggeditem'),(72,'Can change tagged item',25,'change_taggeditem'),(73,'Can delete tagged item',25,'delete_taggeditem'),(74,'Can lock question',19,'lock_question'),(75,'Can moderate flagged objects',26,'can_moderate'),(76,'Can view restricted forums',14,'view_in_forum'),(77,'Can post in restricted forums',14,'post_in_forum'),(78,'Can add tweet',27,'add_tweet'),(79,'Can change tweet',27,'change_tweet'),(80,'Can delete tweet',27,'delete_tweet'),(81,'Can add canned category',28,'add_cannedcategory'),(82,'Can change canned category',28,'change_cannedcategory'),(83,'Can delete canned category',28,'delete_cannedcategory'),(84,'Can add canned response',29,'add_cannedresponse'),(85,'Can change canned response',29,'change_cannedresponse'),(86,'Can delete canned response',29,'delete_cannedresponse'),(87,'Can add category membership',30,'add_categorymembership'),(88,'Can change category membership',30,'change_categorymembership'),(89,'Can delete category membership',30,'delete_categorymembership'),(90,'Can add document',31,'add_document'),(91,'Can change document',31,'change_document'),(92,'Can delete document',31,'delete_document'),(93,'Can add revision',32,'add_revision'),(94,'Can change revision',32,'change_revision'),(95,'Can delete revision',32,'delete_revision'),(96,'Can review a revision',32,'review_revision'),(97,'Can add KB threads',33,'add_thread'),(98,'Can lock KB threads',33,'lock_thread'),(99,'Can sticky KB threads',33,'sticky_thread'),(100,'Can change KB threads',33,'change_thread'),(101,'Can delete KB threads',33,'delete_thread'),(102,'Can add KB posts',34,'add_post'),(103,'Can change KB posts',34,'change_post'),(104,'Can delete KB posts',34,'delete_post'),(105,'Can add image',36,'add_image'),(106,'Can change image',36,'change_image'),(107,'Can delete image',36,'delete_image'),(108,'Can add video',35,'add_video'),(109,'Can change video',35,'change_video'),(110,'Can delete video',35,'delete_video'),(111,'Can add image attachments',44,'add_imageattachment'),(112,'Can change image attachments',44,'change_imageattachment'),(113,'Can delete image attachments',44,'delete_imageattachment'),(114,'Can add announcement',45,'add_announcement'),(115,'Can change announcement',45,'change_announcement'),(116,'Can delete announcement',45,'delete_announcement'),(117,'Can add group dashboard',46,'add_groupdashboard'),(118,'Can change group dashboard',46,'change_groupdashboard'),(119,'Can delete group dashboard',46,'delete_groupdashboard'),(120,'Can delete ak locale documents',31,'delete_document_ak'),(121,'Can delete ar locale documents',31,'delete_document_ar'),(122,'Can delete as locale documents',31,'delete_document_as'),(123,'Can delete ast locale documents',31,'delete_document_ast'),(124,'Can delete bg locale documents',31,'delete_document_bg'),(125,'Can delete bn-BD locale documents',31,'delete_document_bn-BD'),(126,'Can delete bn-IN locale documents',31,'delete_document_bn-IN'),(127,'Can delete bs locale documents',31,'delete_document_bs'),(128,'Can delete ca locale documents',31,'delete_document_ca'),(129,'Can delete cs locale documents',31,'delete_document_cs'),(130,'Can delete da locale documents',31,'delete_document_da'),(131,'Can delete de locale documents',31,'delete_document_de'),(132,'Can delete el locale documents',31,'delete_document_el'),(133,'Can delete en-US locale documents',31,'delete_document_en-US'),(134,'Can delete eo locale documents',31,'delete_document_eo'),(135,'Can delete es locale documents',31,'delete_document_es'),(136,'Can delete et locale documents',31,'delete_document_et'),(137,'Can delete eu locale documents',31,'delete_document_eu'),(138,'Can delete fa locale documents',31,'delete_document_fa'),(139,'Can delete fi locale documents',31,'delete_document_fi'),(140,'Can delete fr locale documents',31,'delete_document_fr'),(141,'Can delete fur locale documents',31,'delete_document_fur'),(142,'Can delete fy-NL locale documents',31,'delete_document_fy-NL'),(143,'Can delete ga-IE locale documents',31,'delete_document_ga-IE'),(144,'Can delete gd locale documents',31,'delete_document_gd'),(145,'Can delete gl locale documents',31,'delete_document_gl'),(146,'Can delete gu-IN locale documents',31,'delete_document_gu-IN'),(147,'Can delete he locale documents',31,'delete_document_he'),(148,'Can delete hi-IN locale documents',31,'delete_document_hi-IN'),(149,'Can delete hr locale documents',31,'delete_document_hr'),(150,'Can delete hu locale documents',31,'delete_document_hu'),(151,'Can delete hy-AM locale documents',31,'delete_document_hy-AM'),(152,'Can delete id locale documents',31,'delete_document_id'),(153,'Can delete ilo locale documents',31,'delete_document_ilo'),(154,'Can delete is locale documents',31,'delete_document_is'),(155,'Can delete it locale documents',31,'delete_document_it'),(156,'Can delete ja locale documents',31,'delete_document_ja'),(157,'Can delete kk locale documents',31,'delete_document_kk'),(158,'Can delete kn locale documents',31,'delete_document_kn'),(159,'Can delete ko locale documents',31,'delete_document_ko'),(160,'Can delete lt locale documents',31,'delete_document_lt'),(161,'Can delete mai locale documents',31,'delete_document_mai'),(162,'Can delete mk locale documents',31,'delete_document_mk'),(163,'Can delete mn locale documents',31,'delete_document_mn'),(164,'Can delete mr locale documents',31,'delete_document_mr'),(165,'Can delete ms locale documents',31,'delete_document_ms'),(166,'Can delete my locale documents',31,'delete_document_my'),(167,'Can delete nb-NO locale documents',31,'delete_document_nb-NO'),(168,'Can delete nl locale documents',31,'delete_document_nl'),(169,'Can delete no locale documents',31,'delete_document_no'),(170,'Can delete oc locale documents',31,'delete_document_oc'),(171,'Can delete pa-IN locale documents',31,'delete_document_pa-IN'),(172,'Can delete pl locale documents',31,'delete_document_pl'),(173,'Can delete pt-BR locale documents',31,'delete_document_pt-BR'),(174,'Can delete pt-PT locale documents',31,'delete_document_pt-PT'),(175,'Can delete rm locale documents',31,'delete_document_rm'),(176,'Can delete ro locale documents',31,'delete_document_ro'),(177,'Can delete ru locale documents',31,'delete_document_ru'),(178,'Can delete rw locale documents',31,'delete_document_rw'),(179,'Can delete si locale documents',31,'delete_document_si'),(180,'Can delete sk locale documents',31,'delete_document_sk'),(181,'Can delete sl locale documents',31,'delete_document_sl'),(182,'Can delete sq locale documents',31,'delete_document_sq'),(183,'Can delete sr-CYRL locale documents',31,'delete_document_sr-CYRL'),(184,'Can delete sr-LATN locale documents',31,'delete_document_sr-LATN'),(185,'Can delete sv-SE locale documents',31,'delete_document_sv-SE'),(186,'Can delete ta-LK locale documents',31,'delete_document_ta-LK'),(187,'Can delete te locale documents',31,'delete_document_te'),(188,'Can delete th locale documents',31,'delete_document_th'),(189,'Can delete tr locale documents',31,'delete_document_tr'),(190,'Can delete uk locale documents',31,'delete_document_uk'),(191,'Can delete vi locale documents',31,'delete_document_vi'),(192,'Can delete zh-CN locale documents',31,'delete_document_zh-CN'),(193,'Can delete zh-TW locale documents',31,'delete_document_zh-TW'),(194,'Can archive document',31,'archive_document'),(195,'Can change/remove the solution to a question',19,'change_solution'),(199,'Can add user profiles',47,'add_profile'),(200,'Can change user profiles',47,'change_profile'),(201,'Can delete user profiles',47,'delete_profile'),(202,'Can mark revision as ready for localization',32,'mark_ready_for_l10n'),(203,'Can add group profile',48,'add_groupprofile'),(204,'Can change group profile',48,'change_groupprofile'),(205,'Can delete group profile',48,'delete_groupprofile'),(206,'Can view karma points',47,'view_karma_points'),(207,'Can add important dates',49,'add_importantdate'),(208,'Can change important dates',49,'change_importantdate'),(209,'Can delete important dates',49,'delete_importantdate'),(210,'Can add title',50,'add_title'),(211,'Can change title',50,'change_title'),(212,'Can delete title',50,'delete_title'),(213,'Can access karma dashboard',50,'view_dashboard'),(214,'Can add metric value',51,'add_metric'),(215,'Can add record',52,'add_record'),(216,'Can change record',52,'change_record'),(217,'Can delete record',52,'delete_record'),(218,'Can run a full reindexing',52,'reindex'),(219,'Can add reply',53,'add_reply'),(220,'Can change reply',53,'change_reply'),(221,'Can delete reply',53,'delete_reply');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `first_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `last_name` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `email` varchar(75) COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(128) COLLATE utf8_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `last_login` datetime NOT NULL,
  `date_joined` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `auth_user_e01be369` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`group_id`),
  KEY `auth_user_groups_user_id` (`user_id`),
  KEY `auth_user_groups_group_id` (`group_id`),
  CONSTRAINT `group_id_refs_id_f116770` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_id_refs_id_7ceef80f` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`permission_id`),
  KEY `auth_user_user_permissions_user_id` (`user_id`),
  KEY `auth_user_user_permissions_permission_id` (`permission_id`),
  CONSTRAINT `permission_id_refs_id_67e79cb` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `user_id_refs_id_dfbab7d` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `authority_permission`
--

DROP TABLE IF EXISTS `authority_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `authority_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codename` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `group_id` int(11) DEFAULT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `approved` tinyint(1) NOT NULL,
  `date_requested` datetime NOT NULL,
  `date_approved` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codename` (`codename`,`object_id`,`content_type_id`,`user_id`,`group_id`),
  KEY `authority_permission_content_type_id` (`content_type_id`),
  KEY `authority_permission_user_id` (`user_id`),
  KEY `authority_permission_group_id` (`group_id`),
  KEY `authority_permission_creator_id` (`creator_id`),
  CONSTRAINT `content_type_id_refs_id_3a7e97c5` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `creator_id_refs_id_112fc87` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `group_id_refs_id_d3ca3118` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `user_id_refs_id_112fc87` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `authority_permission`
--

LOCK TABLES `authority_permission` WRITE;
/*!40000 ALTER TABLE `authority_permission` DISABLE KEYS */;
/*!40000 ALTER TABLE `authority_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customercare_reply`
--

DROP TABLE IF EXISTS `customercare_reply`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customercare_reply` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `twitter_username` varchar(20) NOT NULL,
  `tweet_id` bigint(20) NOT NULL,
  `raw_json` longtext NOT NULL,
  `locale` varchar(20) NOT NULL,
  `created` datetime NOT NULL,
  `reply_to_tweet_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `customercare_reply_fbfc09f1` (`user_id`),
  KEY `customercare_reply_3216ff68` (`created`),
  CONSTRAINT `user_id_refs_id_e32e21e0` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customercare_reply`
--

LOCK TABLES `customercare_reply` WRITE;
/*!40000 ALTER TABLE `customercare_reply` DISABLE KEYS */;
/*!40000 ALTER TABLE `customercare_reply` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customercare_tweet`
--

DROP TABLE IF EXISTS `customercare_tweet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customercare_tweet` (
  `tweet_id` bigint(20) NOT NULL,
  `raw_json` longtext COLLATE utf8_unicode_ci,
  `locale` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `created` datetime NOT NULL,
  `reply_to_id` bigint(20) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`tweet_id`),
  KEY `customercare_tweet_3216ff68` (`created`),
  KEY `customercare_tweet_928541cb` (`locale`),
  KEY `reply_to` (`reply_to_id`),
  KEY `hidden` (`hidden`),
  CONSTRAINT `reply_to_id_refs_tweet_id_47b7f44d` FOREIGN KEY (`reply_to_id`) REFERENCES `customercare_tweet` (`tweet_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customercare_tweet`
--

LOCK TABLES `customercare_tweet` WRITE;
/*!40000 ALTER TABLE `customercare_tweet` DISABLE KEYS */;
/*!40000 ALTER TABLE `customercare_tweet` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dashboards_groupdashboard`
--

DROP TABLE IF EXISTS `dashboards_groupdashboard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dashboards_groupdashboard` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `dashboard` varchar(10) NOT NULL,
  `parameters` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `group_id` (`group_id`),
  KEY `dashboards_groupdashboard_bda51c3c` (`group_id`),
  CONSTRAINT `group_id_refs_id_142d6845` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dashboards_groupdashboard`
--

LOCK TABLES `dashboards_groupdashboard` WRITE;
/*!40000 ALTER TABLE `dashboards_groupdashboard` DISABLE KEYS */;
/*!40000 ALTER TABLE `dashboards_groupdashboard` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dashboards_wikidocumentvisits`
--

DROP TABLE IF EXISTS `dashboards_wikidocumentvisits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dashboards_wikidocumentvisits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `visits` int(11) NOT NULL,
  `period` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `period` (`period`,`document_id`),
  KEY `dashboards_wikidocumentvisits_f4226d13` (`document_id`),
  KEY `dashboards_wikidocumentvisits_5bfc8463` (`visits`),
  CONSTRAINT `document_id_refs_id_814b8dd0` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dashboards_wikidocumentvisits`
--

LOCK TABLES `dashboards_wikidocumentvisits` WRITE;
/*!40000 ALTER TABLE `dashboards_wikidocumentvisits` DISABLE KEYS */;
/*!40000 ALTER TABLE `dashboards_wikidocumentvisits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime NOT NULL,
  `user_id` int(11) NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_user_id` (`user_id`),
  KEY `django_admin_log_content_type_id` (`content_type_id`),
  CONSTRAINT `content_type_id_refs_id_288599e6` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_c8665aa` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `app_label` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `app_label` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'permission','auth','permission'),(2,'group','auth','group'),(3,'user','auth','user'),(4,'message','auth','message'),(5,'content type','contenttypes','contenttype'),(6,'session','sessions','session'),(7,'site','sites','site'),(10,'wiki page','sumo','wikipage'),(11,'category','sumo','category'),(12,'session','sumo','session'),(13,'tiki user','sumo','tikiuser'),(14,'forum','forums','forum'),(15,'thread','forums','thread'),(16,'post','forums','post'),(17,'permission','authority','permission'),(18,'event watch','notifications','eventwatch'),(19,'question','questions','question'),(20,'question meta data','questions','questionmetadata'),(21,'answer','questions','answer'),(22,'question vote','questions','questionvote'),(23,'answer vote','questions','answervote'),(24,'Tag','taggit','tag'),(25,'Tagged Item','taggit','taggeditem'),(26,'Flagged Object','flagit','flaggedobject'),(27,'tweet','customercare','tweet'),(28,'canned category','customercare','cannedcategory'),(29,'canned response','customercare','cannedresponse'),(30,'category membership','customercare','categorymembership'),(31,'document','wiki','document'),(32,'revision','wiki','revision'),(33,'KB Forum Thread','kbforums','thread'),(34,'KB Forum Post','kbforums','post'),(35,'Gallery Video','gallery','video'),(36,'Gallery Image','gallery','image'),(37,'periodic task','djcelery','periodictask'),(38,'interval','djcelery','intervalschedule'),(39,'task','djcelery','taskstate'),(40,'crontab','djcelery','crontabschedule'),(41,'worker','djcelery','workerstate'),(42,'watch','notifications','watch'),(43,'watch filter','notifications','watchfilter'),(44,'image attachment','upload','imageattachment'),(45,'announcement','announcements','announcement'),(46,'group dashboard','dashboards','groupdashboard'),(47,'profile','users','profile'),(48,'group profile','groups','groupprofile'),(49,'important date','wiki','importantdate'),(50,'title','karma','title'),(51,'metric','kpi','metric'),(52,'record','search','record'),(53,'reply','customercare','reply');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8_unicode_ci NOT NULL,
  `expire_date` datetime NOT NULL,
  PRIMARY KEY (`session_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_site`
--

DROP TABLE IF EXISTS `django_site`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_site` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_site`
--

LOCK TABLES `django_site` WRITE;
/*!40000 ALTER TABLE `django_site` DISABLE KEYS */;
INSERT INTO `django_site` VALUES (1,'support-local.allizom.org','support-local.allizom.org');
/*!40000 ALTER TABLE `django_site` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_crontabschedule`
--

DROP TABLE IF EXISTS `djcelery_crontabschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_crontabschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `minute` varchar(64) NOT NULL,
  `hour` varchar(64) NOT NULL,
  `day_of_week` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `djcelery_crontabschedule`
--

LOCK TABLES `djcelery_crontabschedule` WRITE;
/*!40000 ALTER TABLE `djcelery_crontabschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `djcelery_crontabschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_intervalschedule`
--

DROP TABLE IF EXISTS `djcelery_intervalschedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_intervalschedule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `every` int(11) NOT NULL,
  `period` varchar(24) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `djcelery_intervalschedule`
--

LOCK TABLES `djcelery_intervalschedule` WRITE;
/*!40000 ALTER TABLE `djcelery_intervalschedule` DISABLE KEYS */;
/*!40000 ALTER TABLE `djcelery_intervalschedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_periodictask`
--

DROP TABLE IF EXISTS `djcelery_periodictask`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `task` varchar(200) NOT NULL,
  `interval_id` int(11) DEFAULT NULL,
  `crontab_id` int(11) DEFAULT NULL,
  `args` longtext NOT NULL,
  `kwargs` longtext NOT NULL,
  `queue` varchar(200) DEFAULT NULL,
  `exchange` varchar(200) DEFAULT NULL,
  `routing_key` varchar(200) DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `total_run_count` int(10) unsigned NOT NULL,
  `date_changed` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `djcelery_periodictask_17d2d99d` (`interval_id`),
  KEY `djcelery_periodictask_7aa5fda` (`crontab_id`),
  CONSTRAINT `crontab_id_refs_id_1400a18c` FOREIGN KEY (`crontab_id`) REFERENCES `djcelery_crontabschedule` (`id`),
  CONSTRAINT `interval_id_refs_id_dfabcb7` FOREIGN KEY (`interval_id`) REFERENCES `djcelery_intervalschedule` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `djcelery_periodictask`
--

LOCK TABLES `djcelery_periodictask` WRITE;
/*!40000 ALTER TABLE `djcelery_periodictask` DISABLE KEYS */;
/*!40000 ALTER TABLE `djcelery_periodictask` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_periodictasks`
--

DROP TABLE IF EXISTS `djcelery_periodictasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_periodictasks` (
  `ident` smallint(6) NOT NULL,
  `last_update` datetime NOT NULL,
  PRIMARY KEY (`ident`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `djcelery_periodictasks`
--

LOCK TABLES `djcelery_periodictasks` WRITE;
/*!40000 ALTER TABLE `djcelery_periodictasks` DISABLE KEYS */;
/*!40000 ALTER TABLE `djcelery_periodictasks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_taskstate`
--

DROP TABLE IF EXISTS `djcelery_taskstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_taskstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `state` varchar(64) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `tstamp` datetime NOT NULL,
  `args` longtext,
  `kwargs` longtext,
  `eta` datetime DEFAULT NULL,
  `expires` datetime DEFAULT NULL,
  `result` longtext,
  `traceback` longtext,
  `runtime` double DEFAULT NULL,
  `worker_id` int(11) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `djcelery_taskstate_355bfc27` (`state`),
  KEY `djcelery_taskstate_52094d6e` (`name`),
  KEY `djcelery_taskstate_f459b00` (`tstamp`),
  KEY `djcelery_taskstate_20fc5b84` (`worker_id`),
  KEY `djcelery_taskstate_c91f1bf` (`hidden`),
  CONSTRAINT `worker_id_refs_id_4e3453a` FOREIGN KEY (`worker_id`) REFERENCES `djcelery_workerstate` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `djcelery_taskstate`
--

LOCK TABLES `djcelery_taskstate` WRITE;
/*!40000 ALTER TABLE `djcelery_taskstate` DISABLE KEYS */;
/*!40000 ALTER TABLE `djcelery_taskstate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `djcelery_workerstate`
--

DROP TABLE IF EXISTS `djcelery_workerstate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `djcelery_workerstate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `last_heartbeat` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  KEY `djcelery_workerstate_1475381c` (`last_heartbeat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `djcelery_workerstate`
--

LOCK TABLES `djcelery_workerstate` WRITE;
/*!40000 ALTER TABLE `djcelery_workerstate` DISABLE KEYS */;
/*!40000 ALTER TABLE `djcelery_workerstate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flagit_flaggedobject`
--

DROP TABLE IF EXISTS `flagit_flaggedobject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `flagit_flaggedobject` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  `status` int(11) NOT NULL,
  `reason` varchar(64) COLLATE utf8_unicode_ci DEFAULT NULL,
  `notes` longtext COLLATE utf8_unicode_ci,
  `creator_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `handled` datetime NOT NULL,
  `handled_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`object_id`,`creator_id`),
  KEY `flagit_flaggedobject_e4470c6e` (`content_type_id`),
  KEY `flagit_flaggedobject_c9ad71dd` (`status`),
  KEY `flagit_flaggedobject_f97a5119` (`creator_id`),
  KEY `flagit_flaggedobject_3216ff68` (`created`),
  KEY `flagit_flaggedobject_a8d7f3ae` (`handled`),
  KEY `flagit_flaggedobject_c77d7f80` (`handled_by_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flagit_flaggedobject`
--

LOCK TABLES `flagit_flaggedobject` WRITE;
/*!40000 ALTER TABLE `flagit_flaggedobject` DISABLE KEYS */;
/*!40000 ALTER TABLE `flagit_flaggedobject` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forums_forum`
--

DROP TABLE IF EXISTS `forums_forum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `forums_forum` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `slug` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `description` longtext COLLATE utf8_unicode_ci,
  `last_post_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `slug` (`slug`),
  KEY `forums_forum_last_post_id_idx` (`last_post_id`),
  CONSTRAINT `last_post_id_refs_id_e3773179` FOREIGN KEY (`last_post_id`) REFERENCES `forums_post` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forums_forum`
--

LOCK TABLES `forums_forum` WRITE;
/*!40000 ALTER TABLE `forums_forum` DISABLE KEYS */;
/*!40000 ALTER TABLE `forums_forum` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forums_post`
--

DROP TABLE IF EXISTS `forums_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `forums_post` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `thread_id` int(11) NOT NULL,
  `content` longtext COLLATE utf8_unicode_ci NOT NULL,
  `author_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `forums_post_thread_id` (`thread_id`),
  KEY `forums_post_author_id` (`author_id`),
  KEY `forums_post_created` (`created`),
  KEY `forums_post_updated` (`updated`),
  KEY `post_updated_by_id_refs_id_5c0b8875` (`updated_by_id`),
  CONSTRAINT `author_id_refs_id_59fe2704` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `post_updated_by_id_refs_id_5c0b8875` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`) ON DELETE SET NULL,
  CONSTRAINT `thread_id_refs_id_5646bc53` FOREIGN KEY (`thread_id`) REFERENCES `forums_thread` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forums_post`
--

LOCK TABLES `forums_post` WRITE;
/*!40000 ALTER TABLE `forums_post` DISABLE KEYS */;
/*!40000 ALTER TABLE `forums_post` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forums_thread`
--

DROP TABLE IF EXISTS `forums_thread`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `forums_thread` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `forum_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) NOT NULL,
  `last_post_id` int(11) DEFAULT NULL,
  `replies` int(11) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `is_sticky` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `forums_thread_forum_id` (`forum_id`),
  KEY `forums_thread_created` (`created`),
  KEY `forums_thread_creator_id` (`creator_id`),
  KEY `forums_thread_last_post_id` (`last_post_id`),
  KEY `forums_thread_is_sticky` (`is_sticky`),
  CONSTRAINT `creator_id_refs_id_4938e584` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `forum_id_refs_id_7f5fd759` FOREIGN KEY (`forum_id`) REFERENCES `forums_forum` (`id`),
  CONSTRAINT `last_post_id_refs_id_3fa89f33` FOREIGN KEY (`last_post_id`) REFERENCES `forums_post` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forums_thread`
--

LOCK TABLES `forums_thread` WRITE;
/*!40000 ALTER TABLE `forums_thread` DISABLE KEYS */;
/*!40000 ALTER TABLE `forums_thread` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gallery_image`
--

DROP TABLE IF EXISTS `gallery_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gallery_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `description` longtext NOT NULL,
  `locale` varchar(7) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `file` varchar(250) DEFAULT NULL,
  `thumbnail` varchar(250) DEFAULT NULL,
  `is_draft` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gallery_image_locale_title` (`locale`,`title`),
  UNIQUE KEY `gallery_image_is_draft_creator_id` (`is_draft`,`creator_id`),
  KEY `gallery_image_title` (`title`),
  KEY `gallery_image_created` (`created`),
  KEY `gallery_image_updated` (`updated`),
  KEY `gallery_image_updated_by_id` (`updated_by_id`),
  KEY `gallery_image_creator_id` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_9add8201` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_9add8201` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gallery_image`
--

LOCK TABLES `gallery_image` WRITE;
/*!40000 ALTER TABLE `gallery_image` DISABLE KEYS */;
/*!40000 ALTER TABLE `gallery_image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gallery_video`
--

DROP TABLE IF EXISTS `gallery_video`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gallery_video` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `description` longtext NOT NULL,
  `locale` varchar(7) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `thumbnail` varchar(250) DEFAULT NULL,
  `webm` varchar(250) DEFAULT NULL,
  `ogv` varchar(250) DEFAULT NULL,
  `flv` varchar(250) DEFAULT NULL,
  `poster` varchar(250) DEFAULT NULL,
  `is_draft` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `gallery_video_locale_title` (`locale`,`title`),
  UNIQUE KEY `gallery_video_is_draft_creator_id` (`is_draft`,`creator_id`),
  KEY `gallery_video_title` (`title`),
  KEY `gallery_video_created` (`created`),
  KEY `gallery_video_updated` (`updated`),
  KEY `gallery_video_updated_by_id` (`updated_by_id`),
  KEY `gallery_video_creator_id` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_7d7f5ce1` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_7d7f5ce1` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gallery_video`
--

LOCK TABLES `gallery_video` WRITE;
/*!40000 ALTER TABLE `gallery_video` DISABLE KEYS */;
/*!40000 ALTER TABLE `gallery_video` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `groups_groupprofile`
--

DROP TABLE IF EXISTS `groups_groupprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups_groupprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `slug` varchar(80) NOT NULL,
  `group_id` int(11) NOT NULL,
  `information` longtext NOT NULL,
  `information_html` longtext NOT NULL,
  `avatar` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `slug` (`slug`),
  KEY `groups_groupprofile_bda51c3c` (`group_id`),
  CONSTRAINT `group_id_refs_id_acfd2c6f` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `groups_groupprofile`
--

LOCK TABLES `groups_groupprofile` WRITE;
/*!40000 ALTER TABLE `groups_groupprofile` DISABLE KEYS */;
/*!40000 ALTER TABLE `groups_groupprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `groups_groupprofile_leaders`
--

DROP TABLE IF EXISTS `groups_groupprofile_leaders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `groups_groupprofile_leaders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `groupprofile_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `groupprofile_id` (`groupprofile_id`,`user_id`),
  KEY `user_id_refs_id_82107ee1` (`user_id`),
  CONSTRAINT `groupprofile_id_refs_id_607797bc` FOREIGN KEY (`groupprofile_id`) REFERENCES `groups_groupprofile` (`id`),
  CONSTRAINT `user_id_refs_id_82107ee1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `groups_groupprofile_leaders`
--

LOCK TABLES `groups_groupprofile_leaders` WRITE;
/*!40000 ALTER TABLE `groups_groupprofile_leaders` DISABLE KEYS */;
/*!40000 ALTER TABLE `groups_groupprofile_leaders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inproduct_redirect`
--

DROP TABLE IF EXISTS `inproduct_redirect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inproduct_redirect` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `version` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `platform` varchar(30) COLLATE utf8_unicode_ci NOT NULL,
  `locale` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  `topic` varchar(50) COLLATE utf8_unicode_ci NOT NULL,
  `target` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `product` (`product`,`version`,`platform`,`locale`,`topic`),
  KEY `inproduct_redirect_81e0dea9` (`product`),
  KEY `inproduct_redirect_659105e4` (`version`),
  KEY `inproduct_redirect_eab31616` (`platform`),
  KEY `inproduct_redirect_928541cb` (`locale`),
  KEY `inproduct_redirect_277e394d` (`topic`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inproduct_redirect`
--

LOCK TABLES `inproduct_redirect` WRITE;
/*!40000 ALTER TABLE `inproduct_redirect` DISABLE KEYS */;
/*!40000 ALTER TABLE `inproduct_redirect` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `karma_points`
--

DROP TABLE IF EXISTS `karma_points`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `karma_points` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action` varchar(100) NOT NULL,
  `points` int(11) NOT NULL,
  `updated` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `karma_points`
--

LOCK TABLES `karma_points` WRITE;
/*!40000 ALTER TABLE `karma_points` DISABLE KEYS */;
/*!40000 ALTER TABLE `karma_points` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `karma_title`
--

DROP TABLE IF EXISTS `karma_title`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `karma_title` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `is_auto` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `karma_title`
--

LOCK TABLES `karma_title` WRITE;
/*!40000 ALTER TABLE `karma_title` DISABLE KEYS */;
/*!40000 ALTER TABLE `karma_title` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `karma_title_groups`
--

DROP TABLE IF EXISTS `karma_title_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `karma_title_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title_id` (`title_id`,`group_id`),
  KEY `group_id_refs_id_b8eda48d` (`group_id`),
  CONSTRAINT `title_id_refs_id_2468f187` FOREIGN KEY (`title_id`) REFERENCES `karma_title` (`id`),
  CONSTRAINT `group_id_refs_id_b8eda48d` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `karma_title_groups`
--

LOCK TABLES `karma_title_groups` WRITE;
/*!40000 ALTER TABLE `karma_title_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `karma_title_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `karma_title_users`
--

DROP TABLE IF EXISTS `karma_title_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `karma_title_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title_id` (`title_id`,`user_id`),
  KEY `user_id_refs_id_83fda647` (`user_id`),
  CONSTRAINT `title_id_refs_id_898b376c` FOREIGN KEY (`title_id`) REFERENCES `karma_title` (`id`),
  CONSTRAINT `user_id_refs_id_83fda647` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `karma_title_users`
--

LOCK TABLES `karma_title_users` WRITE;
/*!40000 ALTER TABLE `karma_title_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `karma_title_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kbforums_post`
--

DROP TABLE IF EXISTS `kbforums_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kbforums_post` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `thread_id` int(11) NOT NULL,
  `content` longtext COLLATE utf8_unicode_ci NOT NULL,
  `creator_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime NOT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `kbforums_post_65912a8a` (`thread_id`),
  KEY `kbforums_post_685aee7` (`creator_id`),
  KEY `kbforums_post_3216ff68` (`created`),
  KEY `kbforums_post_8aac229` (`updated`),
  KEY `kbforums_post_6f403c1` (`updated_by_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kbforums_post`
--

LOCK TABLES `kbforums_post` WRITE;
/*!40000 ALTER TABLE `kbforums_post` DISABLE KEYS */;
/*!40000 ALTER TABLE `kbforums_post` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kbforums_thread`
--

DROP TABLE IF EXISTS `kbforums_thread`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kbforums_thread` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `document_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) NOT NULL,
  `last_post_id` int(11) DEFAULT NULL,
  `replies` int(11) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `is_sticky` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `kbforums_thread_bdd92ed` (`document_id`),
  KEY `kbforums_thread_3216ff68` (`created`),
  KEY `kbforums_thread_685aee7` (`creator_id`),
  KEY `kbforums_thread_11738784` (`last_post_id`),
  KEY `kbforums_thread_714cf0d8` (`is_sticky`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kbforums_thread`
--

LOCK TABLES `kbforums_thread` WRITE;
/*!40000 ALTER TABLE `kbforums_thread` DISABLE KEYS */;
/*!40000 ALTER TABLE `kbforums_thread` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kpi_metric`
--

DROP TABLE IF EXISTS `kpi_metric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kpi_metric` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `kind_id` int(11) NOT NULL,
  `start` date NOT NULL,
  `end` date NOT NULL,
  `value` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `kind_id` (`kind_id`,`start`,`end`),
  CONSTRAINT `kind_id_refs_id_8a165d49` FOREIGN KEY (`kind_id`) REFERENCES `kpi_metrickind` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kpi_metric`
--

LOCK TABLES `kpi_metric` WRITE;
/*!40000 ALTER TABLE `kpi_metric` DISABLE KEYS */;
/*!40000 ALTER TABLE `kpi_metric` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `kpi_metrickind`
--

DROP TABLE IF EXISTS `kpi_metrickind`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kpi_metrickind` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `kpi_metrickind`
--

LOCK TABLES `kpi_metrickind` WRITE;
/*!40000 ALTER TABLE `kpi_metrickind` DISABLE KEYS */;
INSERT INTO `kpi_metrickind` VALUES (5,'general keymetrics:visitors'),(6,'general l10n:coverage'),(4,'search clickthroughs:elastic:clicks'),(3,'search clickthroughs:elastic:searches'),(1,'search clickthroughs:sphinx:clicks'),(2,'search clickthroughs:sphinx:searches');
/*!40000 ALTER TABLE `kpi_metrickind` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages_inboxmessage`
--

DROP TABLE IF EXISTS `messages_inboxmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messages_inboxmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `to_id` int(11) NOT NULL,
  `sender_id` int(11) DEFAULT NULL,
  `message` longtext NOT NULL,
  `created` datetime NOT NULL,
  `read` tinyint(1) NOT NULL,
  `replied` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `messages_inboxmessage_80e39a0d` (`to_id`),
  KEY `messages_inboxmessage_901f59e9` (`sender_id`),
  KEY `messages_inboxmessage_3216ff68` (`created`),
  KEY `messages_inboxmessage_df3d2e75` (`read`),
  CONSTRAINT `sender_id_refs_id_2d90390f` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `to_id_refs_id_2d90390f` FOREIGN KEY (`to_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages_inboxmessage`
--

LOCK TABLES `messages_inboxmessage` WRITE;
/*!40000 ALTER TABLE `messages_inboxmessage` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages_inboxmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages_outboxmessage`
--

DROP TABLE IF EXISTS `messages_outboxmessage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messages_outboxmessage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) NOT NULL,
  `message` longtext NOT NULL,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `messages_outboxmessage_901f59e9` (`sender_id`),
  KEY `messages_outboxmessage_3216ff68` (`created`),
  CONSTRAINT `sender_id_refs_id_4fcca07f` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages_outboxmessage`
--

LOCK TABLES `messages_outboxmessage` WRITE;
/*!40000 ALTER TABLE `messages_outboxmessage` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages_outboxmessage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages_outboxmessage_to`
--

DROP TABLE IF EXISTS `messages_outboxmessage_to`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messages_outboxmessage_to` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `outboxmessage_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `outboxmessage_id` (`outboxmessage_id`,`user_id`),
  KEY `user_id_refs_id_de0b949e` (`user_id`),
  CONSTRAINT `outboxmessage_id_refs_id_f8c08fc4` FOREIGN KEY (`outboxmessage_id`) REFERENCES `messages_outboxmessage` (`id`),
  CONSTRAINT `user_id_refs_id_de0b949e` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages_outboxmessage_to`
--

LOCK TABLES `messages_outboxmessage_to` WRITE;
/*!40000 ALTER TABLE `messages_outboxmessage_to` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages_outboxmessage_to` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `postcrash_signature`
--

DROP TABLE IF EXISTS `postcrash_signature`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `postcrash_signature` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `signature` varchar(255) NOT NULL,
  `document_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `signature` (`signature`),
  KEY `postcrash_signature_f4226d13` (`document_id`),
  CONSTRAINT `document_id_refs_id_4d433fd5` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `postcrash_signature`
--

LOCK TABLES `postcrash_signature` WRITE;
/*!40000 ALTER TABLE `postcrash_signature` DISABLE KEYS */;
/*!40000 ALTER TABLE `postcrash_signature` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions_answer`
--

DROP TABLE IF EXISTS `questions_answer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `questions_answer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `content` longtext NOT NULL,
  `updated` datetime DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `upvotes` int(11) NOT NULL,
  `page` int(11) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `questions_answer_question_id` (`question_id`),
  KEY `questions_answer_creator_id` (`creator_id`),
  KEY `questions_answer_created` (`created`),
  KEY `questions_answer_updated` (`updated`),
  KEY `questions_answer_updated_by_id` (`updated_by_id`),
  KEY `questions_answer_upvotes` (`upvotes`),
  CONSTRAINT `creator_id_refs_id_30a2e948` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `question_id_refs_id_5dadc1b3` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`),
  CONSTRAINT `updated_by_id_refs_id_30a2e948` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions_answer`
--

LOCK TABLES `questions_answer` WRITE;
/*!40000 ALTER TABLE `questions_answer` DISABLE KEYS */;
/*!40000 ALTER TABLE `questions_answer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions_answervote`
--

DROP TABLE IF EXISTS `questions_answervote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `questions_answervote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `answer_id` int(11) NOT NULL,
  `helpful` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `anonymous_id` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `questions_answervote_answer_id` (`answer_id`),
  KEY `questions_answervote_created` (`created`),
  KEY `questions_answervote_creator_id` (`creator_id`),
  KEY `questions_answervote_anonymous_id` (`anonymous_id`),
  CONSTRAINT `answer_id_refs_id_112ad03b` FOREIGN KEY (`answer_id`) REFERENCES `questions_answer` (`id`),
  CONSTRAINT `creator_id_refs_id_73284cb0` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions_answervote`
--

LOCK TABLES `questions_answervote` WRITE;
/*!40000 ALTER TABLE `questions_answervote` DISABLE KEYS */;
/*!40000 ALTER TABLE `questions_answervote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions_question`
--

DROP TABLE IF EXISTS `questions_question`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `questions_question` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `content` longtext NOT NULL,
  `created` datetime NOT NULL,
  `updated` datetime DEFAULT NULL,
  `updated_by_id` int(11) DEFAULT NULL,
  `last_answer_id` int(11) DEFAULT NULL,
  `num_answers` int(11) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `solution_id` int(11) DEFAULT NULL,
  `num_votes_past_week` int(10) unsigned DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `questions_question_creator_id` (`creator_id`),
  KEY `questions_question_created` (`created`),
  KEY `questions_question_updated` (`updated`),
  KEY `questions_question_updated_by_id` (`updated_by_id`),
  KEY `questions_question_last_answer_id` (`last_answer_id`),
  KEY `questions_question_num_answers` (`num_answers`),
  KEY `solution_id_refs_id_95fb9a4d` (`solution_id`),
  KEY `questions_question_num_votes_past_week_idx` (`num_votes_past_week`),
  CONSTRAINT `creator_id_refs_id_723e3a28` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `last_answer_id_refs_id_6a0465b3` FOREIGN KEY (`last_answer_id`) REFERENCES `questions_answer` (`id`),
  CONSTRAINT `solution_id_refs_id_95fb9a4d` FOREIGN KEY (`solution_id`) REFERENCES `questions_answer` (`id`),
  CONSTRAINT `updated_by_id_refs_id_723e3a28` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions_question`
--

LOCK TABLES `questions_question` WRITE;
/*!40000 ALTER TABLE `questions_question` DISABLE KEYS */;
/*!40000 ALTER TABLE `questions_question` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions_questionmetadata`
--

DROP TABLE IF EXISTS `questions_questionmetadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `questions_questionmetadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `value` longtext NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `questions_questionmetadata_question_and_name_idx` (`question_id`,`name`),
  KEY `questions_questionmetadata_question_id` (`question_id`),
  KEY `questions_questionmetadata_name` (`name`),
  CONSTRAINT `question_id_refs_id_199b1870` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions_questionmetadata`
--

LOCK TABLES `questions_questionmetadata` WRITE;
/*!40000 ALTER TABLE `questions_questionmetadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `questions_questionmetadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions_questionvote`
--

DROP TABLE IF EXISTS `questions_questionvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `questions_questionvote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `question_id` int(11) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `anonymous_id` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `questions_questionvote_question_id` (`question_id`),
  KEY `questions_questionvote_created` (`created`),
  KEY `questions_questionvote_creator_id` (`creator_id`),
  KEY `questions_questionvote_anonymous_id` (`anonymous_id`),
  CONSTRAINT `creator_id_refs_id_699edd80` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `question_id_refs_id_9dde00db` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions_questionvote`
--

LOCK TABLES `questions_questionvote` WRITE;
/*!40000 ALTER TABLE `questions_questionvote` DISABLE KEYS */;
/*!40000 ALTER TABLE `questions_questionvote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions_votemetadata`
--

DROP TABLE IF EXISTS `questions_votemetadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `questions_votemetadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` int(10) unsigned DEFAULT NULL,
  `key` varchar(40) NOT NULL,
  `value` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `questions_votemetadata_e4470c6e` (`content_type_id`),
  KEY `questions_votemetadata_45544485` (`key`),
  CONSTRAINT `content_type_id_refs_id_f18225bf` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions_votemetadata`
--

LOCK TABLES `questions_votemetadata` WRITE;
/*!40000 ALTER TABLE `questions_votemetadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `questions_votemetadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_version`
--

DROP TABLE IF EXISTS `schema_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_version` (
  `version` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_version`
--

LOCK TABLES `schema_version` WRITE;
/*!40000 ALTER TABLE `schema_version` DISABLE KEYS */;
INSERT INTO `schema_version` VALUES (147);
/*!40000 ALTER TABLE `schema_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `search_record`
--

DROP TABLE IF EXISTS `search_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `search_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `starttime` datetime DEFAULT NULL,
  `endtime` datetime DEFAULT NULL,
  `text` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `search_record`
--

LOCK TABLES `search_record` WRITE;
/*!40000 ALTER TABLE `search_record` DISABLE KEYS */;
/*!40000 ALTER TABLE `search_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taggit_tag`
--

DROP TABLE IF EXISTS `taggit_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_tag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `slug` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_tag`
--

LOCK TABLES `taggit_tag` WRITE;
/*!40000 ALTER TABLE `taggit_tag` DISABLE KEYS */;
/*!40000 ALTER TABLE `taggit_tag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taggit_taggeditem`
--

DROP TABLE IF EXISTS `taggit_taggeditem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `taggit_taggeditem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tag_id` int(11) NOT NULL,
  `object_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `taggit_taggeditem_3747b463` (`tag_id`),
  KEY `taggit_taggeditem_e4470c6e` (`content_type_id`),
  KEY `taggit_taggeditem_c32a93c2` (`object_id`),
  CONSTRAINT `content_type_id_refs_id_5a2b7711` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `tag_id_refs_id_c87e3f85` FOREIGN KEY (`tag_id`) REFERENCES `taggit_tag` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taggit_taggeditem`
--

LOCK TABLES `taggit_taggeditem` WRITE;
/*!40000 ALTER TABLE `taggit_taggeditem` DISABLE KEYS */;
/*!40000 ALTER TABLE `taggit_taggeditem` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tidings_watch`
--

DROP TABLE IF EXISTS `tidings_watch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tidings_watch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_type` varchar(30) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `object_id` int(10) unsigned DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `email` varchar(75) DEFAULT NULL,
  `secret` char(10) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `notifications_watch_2be07fce` (`event_type`),
  KEY `notifications_watch_e4470c6e` (`content_type_id`),
  KEY `notifications_watch_829e37fd` (`object_id`),
  KEY `notifications_watch_fbfc09f1` (`user_id`),
  KEY `notifications_watch_3904588a` (`email`),
  KEY `notifications_watch_2d27166b` (`is_active`),
  CONSTRAINT `content_type_id_refs_id_23da5933` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `user_id_refs_id_2dc6eef1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tidings_watch`
--

LOCK TABLES `tidings_watch` WRITE;
/*!40000 ALTER TABLE `tidings_watch` DISABLE KEYS */;
/*!40000 ALTER TABLE `tidings_watch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tidings_watchfilter`
--

DROP TABLE IF EXISTS `tidings_watchfilter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tidings_watchfilter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `watch_id` int(11) NOT NULL,
  `name` varchar(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `value` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`,`watch_id`),
  KEY `notifications_watchfilter_6e1bd094` (`watch_id`),
  CONSTRAINT `watch_id_refs_id_444d6e79` FOREIGN KEY (`watch_id`) REFERENCES `tidings_watch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tidings_watchfilter`
--

LOCK TABLES `tidings_watchfilter` WRITE;
/*!40000 ALTER TABLE `tidings_watchfilter` DISABLE KEYS */;
/*!40000 ALTER TABLE `tidings_watchfilter` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `upload_imageattachment`
--

DROP TABLE IF EXISTS `upload_imageattachment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `upload_imageattachment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `file` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `thumbnail` varchar(250) COLLATE utf8_unicode_ci DEFAULT NULL,
  `creator_id` int(11) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `object_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `upload_imageattachment_f97a5119` (`creator_id`),
  KEY `upload_imageattachment_e4470c6e` (`content_type_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `upload_imageattachment`
--

LOCK TABLES `upload_imageattachment` WRITE;
/*!40000 ALTER TABLE `upload_imageattachment` DISABLE KEYS */;
/*!40000 ALTER TABLE `upload_imageattachment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_emailchange`
--

DROP TABLE IF EXISTS `users_emailchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_emailchange` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(40) NOT NULL,
  `email` varchar(75) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `users_emailchange_email` (`email`),
  CONSTRAINT `user_id_refs_id_7c0fddb0` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_emailchange`
--

LOCK TABLES `users_emailchange` WRITE;
/*!40000 ALTER TABLE `users_emailchange` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_emailchange` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_profile`
--

DROP TABLE IF EXISTS `users_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_profile` (
  `user_id` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `public_email` tinyint(1) NOT NULL,
  `avatar` varchar(250) DEFAULT NULL,
  `bio` longtext,
  `website` varchar(255) DEFAULT NULL,
  `twitter` varchar(255) DEFAULT NULL,
  `facebook` varchar(255) DEFAULT NULL,
  `irc_handle` varchar(255) DEFAULT NULL,
  `timezone` varchar(100) DEFAULT NULL,
  `country` varchar(2) DEFAULT NULL,
  `city` varchar(255) DEFAULT NULL,
  `locale` varchar(7) NOT NULL DEFAULT 'en-US',
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_id_refs_id_21617f27` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_profile`
--

LOCK TABLES `users_profile` WRITE;
/*!40000 ALTER TABLE `users_profile` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_profile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_registrationprofile`
--

DROP TABLE IF EXISTS `users_registrationprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_registrationprofile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `activation_key` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_registrationprofile`
--

LOCK TABLES `users_registrationprofile` WRITE;
/*!40000 ALTER TABLE `users_registrationprofile` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_registrationprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users_setting`
--

DROP TABLE IF EXISTS `users_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_setting` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` varchar(60) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`name`),
  KEY `users_setting_403f60f` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users_setting`
--

LOCK TABLES `users_setting` WRITE;
/*!40000 ALTER TABLE `users_setting` DISABLE KEYS */;
/*!40000 ALTER TABLE `users_setting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waffle_flag`
--

DROP TABLE IF EXISTS `waffle_flag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_flag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `everyone` tinyint(1) DEFAULT NULL,
  `percent` decimal(3,1) DEFAULT NULL,
  `superusers` tinyint(1) NOT NULL,
  `staff` tinyint(1) NOT NULL,
  `authenticated` tinyint(1) NOT NULL,
  `rollout` tinyint(1) NOT NULL,
  `note` longtext NOT NULL,
  `testing` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `waffle_flag_3216ff68` (`created`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waffle_flag`
--

LOCK TABLES `waffle_flag` WRITE;
/*!40000 ALTER TABLE `waffle_flag` DISABLE KEYS */;
INSERT INTO `waffle_flag` VALUES (1,'elasticsearch',NULL,NULL,0,0,0,0,'',0,'2012-06-07 15:20:20','2012-06-07 15:20:20'),(2,'esunified',NULL,NULL,0,0,0,0,'',0,'2012-06-07 15:20:25','2012-06-07 15:20:25');
/*!40000 ALTER TABLE `waffle_flag` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waffle_flag_groups`
--

DROP TABLE IF EXISTS `waffle_flag_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_flag_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flag_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `flag_id` (`flag_id`,`group_id`),
  KEY `group_id_refs_id_4ea49f34` (`group_id`),
  CONSTRAINT `flag_id_refs_id_8e6a807d` FOREIGN KEY (`flag_id`) REFERENCES `waffle_flag` (`id`),
  CONSTRAINT `group_id_refs_id_4ea49f34` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waffle_flag_groups`
--

LOCK TABLES `waffle_flag_groups` WRITE;
/*!40000 ALTER TABLE `waffle_flag_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `waffle_flag_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waffle_flag_users`
--

DROP TABLE IF EXISTS `waffle_flag_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_flag_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flag_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `flag_id` (`flag_id`,`user_id`),
  KEY `user_id_refs_id_bae2dfc2` (`user_id`),
  CONSTRAINT `flag_id_refs_id_8fef0c12` FOREIGN KEY (`flag_id`) REFERENCES `waffle_flag` (`id`),
  CONSTRAINT `user_id_refs_id_bae2dfc2` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waffle_flag_users`
--

LOCK TABLES `waffle_flag_users` WRITE;
/*!40000 ALTER TABLE `waffle_flag_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `waffle_flag_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waffle_sample`
--

DROP TABLE IF EXISTS `waffle_sample`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_sample` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `percent` decimal(4,1) NOT NULL,
  `note` longtext NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `waffle_sample_3216ff68` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waffle_sample`
--

LOCK TABLES `waffle_sample` WRITE;
/*!40000 ALTER TABLE `waffle_sample` DISABLE KEYS */;
/*!40000 ALTER TABLE `waffle_sample` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waffle_switch`
--

DROP TABLE IF EXISTS `waffle_switch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `waffle_switch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `note` longtext NOT NULL,
  `created` datetime NOT NULL,
  `modified` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `waffle_switch_3216ff68` (`created`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waffle_switch`
--

LOCK TABLES `waffle_switch` WRITE;
/*!40000 ALTER TABLE `waffle_switch` DISABLE KEYS */;
INSERT INTO `waffle_switch` VALUES (1,'wiki-rebuild-on-demand',0,'','2012-06-07 15:20:20','2012-06-07 15:20:20');
/*!40000 ALTER TABLE `waffle_switch` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_document`
--

DROP TABLE IF EXISTS `wiki_document`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_document` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `locale` varchar(7) NOT NULL,
  `current_revision_id` int(11) DEFAULT NULL,
  `latest_localizable_revision_id` int(11) DEFAULT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `html` longtext NOT NULL,
  `category` int(11) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `is_template` tinyint(1) NOT NULL DEFAULT '0',
  `is_localizable` tinyint(1) NOT NULL DEFAULT '1',
  `is_archived` tinyint(1) NOT NULL,
  `allow_discussion` tinyint(1) NOT NULL DEFAULT '1',
  `needs_change` tinyint(1) NOT NULL,
  `needs_change_comment` varchar(500) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`,`locale`),
  UNIQUE KEY `slug` (`slug`,`locale`),
  UNIQUE KEY `parent_id` (`parent_id`,`locale`),
  KEY `wiki_document_841a7e28` (`title`),
  KEY `wiki_document_928541cb` (`locale`),
  KEY `wiki_document_a253e251` (`current_revision_id`),
  KEY `wiki_document_63f17a16` (`parent_id`),
  KEY `wiki_document_slug` (`slug`),
  KEY `wiki_document_is_template` (`is_template`),
  KEY `wiki_document_is_localizable` (`is_localizable`),
  KEY `wiki_document_34876983` (`category`),
  KEY `wiki_document_42e00a51` (`is_archived`),
  KEY `latest_localizable_revision_id_refs_id_79f9a479` (`latest_localizable_revision_id`),
  KEY `wiki_document_c764d599` (`needs_change`),
  CONSTRAINT `current_revision_id_refs_id_79f9a479` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_revision` (`id`),
  CONSTRAINT `latest_localizable_revision_id_refs_id_79f9a479` FOREIGN KEY (`latest_localizable_revision_id`) REFERENCES `wiki_revision` (`id`),
  CONSTRAINT `parent_id_refs_id_6c4b5a5` FOREIGN KEY (`parent_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_document`
--

LOCK TABLES `wiki_document` WRITE;
/*!40000 ALTER TABLE `wiki_document` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_document` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_document_contributors`
--

DROP TABLE IF EXISTS `wiki_document_contributors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_document_contributors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `document_id` (`document_id`,`user_id`),
  KEY `user_id_refs_id_12d875b` (`user_id`),
  CONSTRAINT `document_id_refs_id_a223b3cf` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`),
  CONSTRAINT `user_id_refs_id_12d875b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_document_contributors`
--

LOCK TABLES `wiki_document_contributors` WRITE;
/*!40000 ALTER TABLE `wiki_document_contributors` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_document_contributors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_helpfulvote`
--

DROP TABLE IF EXISTS `wiki_helpfulvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_helpfulvote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `revision_id` int(11) NOT NULL,
  `helpful` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `anonymous_id` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `user_agent` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_helpfulvote_202bdc7f` (`revision_id`),
  KEY `wiki_helpfulvote_3216ff68` (`created`),
  KEY `wiki_helpfulvote_685aee7` (`creator_id`),
  KEY `wiki_helpfulvote_2291b592` (`anonymous_id`),
  CONSTRAINT `creator_id_refs_id_4ec8a21b` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `revision_id_refs_id_a55647b` FOREIGN KEY (`revision_id`) REFERENCES `wiki_revision` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_helpfulvote`
--

LOCK TABLES `wiki_helpfulvote` WRITE;
/*!40000 ALTER TABLE `wiki_helpfulvote` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_helpfulvote` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_helpfulvotemetadata`
--

DROP TABLE IF EXISTS `wiki_helpfulvotemetadata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_helpfulvotemetadata` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `vote_id` int(11) NOT NULL,
  `key` varchar(40) NOT NULL,
  `value` varchar(1000) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_helpfulvotemetadata_f65ecc44` (`vote_id`),
  KEY `wiki_helpfulvotemetadata_45544485` (`key`),
  CONSTRAINT `vote_id_refs_id_3a2685f2` FOREIGN KEY (`vote_id`) REFERENCES `wiki_helpfulvote` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_helpfulvotemetadata`
--

LOCK TABLES `wiki_helpfulvotemetadata` WRITE;
/*!40000 ALTER TABLE `wiki_helpfulvotemetadata` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_helpfulvotemetadata` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_importantdate`
--

DROP TABLE IF EXISTS `wiki_importantdate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_importantdate` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `text` varchar(100) COLLATE utf8_unicode_ci NOT NULL,
  `date` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_importantdate_679343db` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_importantdate`
--

LOCK TABLES `wiki_importantdate` WRITE;
/*!40000 ALTER TABLE `wiki_importantdate` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_importantdate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_relateddocument`
--

DROP TABLE IF EXISTS `wiki_relateddocument`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_relateddocument` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `related_id` int(11) NOT NULL,
  `in_common` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `document_id_refs_id_5206177f` (`document_id`),
  KEY `related_id_refs_id_5206177f` (`related_id`),
  CONSTRAINT `related_id_refs_id_5206177f` FOREIGN KEY (`related_id`) REFERENCES `wiki_document` (`id`),
  CONSTRAINT `document_id_refs_id_5206177f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_relateddocument`
--

LOCK TABLES `wiki_relateddocument` WRITE;
/*!40000 ALTER TABLE `wiki_relateddocument` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_relateddocument` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `wiki_revision`
--

DROP TABLE IF EXISTS `wiki_revision`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_revision` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `summary` longtext NOT NULL,
  `content` longtext NOT NULL,
  `keywords` varchar(255) NOT NULL,
  `created` datetime NOT NULL,
  `reviewed` datetime DEFAULT NULL,
  `significance` int(11) DEFAULT NULL,
  `comment` varchar(255) NOT NULL,
  `reviewer_id` int(11) DEFAULT NULL,
  `creator_id` int(11) NOT NULL,
  `is_approved` tinyint(1) NOT NULL,
  `based_on_id` int(11) DEFAULT NULL,
  `is_ready_for_localization` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `wiki_revision_f4226d13` (`document_id`),
  KEY `wiki_revision_d0f17e2b` (`reviewer_id`),
  KEY `wiki_revision_f97a5119` (`creator_id`),
  KEY `wiki_revision_ec4f2057` (`based_on_id`),
  KEY `wiki_revision_is_approved_idx` (`is_approved`),
  CONSTRAINT `based_on_id_refs_id_cf0bcfb3` FOREIGN KEY (`based_on_id`) REFERENCES `wiki_revision` (`id`),
  CONSTRAINT `creator_id_refs_id_4298f2ad` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `document_id_refs_id_226de0df` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`),
  CONSTRAINT `reviewer_id_refs_id_4298f2ad` FOREIGN KEY (`reviewer_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `wiki_revision`
--

LOCK TABLES `wiki_revision` WRITE;
/*!40000 ALTER TABLE `wiki_revision` DISABLE KEYS */;
/*!40000 ALTER TABLE `wiki_revision` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-06-07 15:22:11
