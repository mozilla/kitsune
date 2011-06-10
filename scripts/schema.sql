-- MySQL dump 10.13  Distrib 5.1.48, for redhat-linux-gnu (x86_64)
--
-- Host: localhost    Database: sumo
-- ------------------------------------------------------
-- Server version	5.1.48

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add permission',1,'add_permission'),(2,'Can change permission',1,'change_permission'),(3,'Can delete permission',1,'delete_permission'),(4,'Can add group',2,'add_group'),(5,'Can change group',2,'change_group'),(6,'Can delete group',2,'delete_group'),(7,'Can add user',3,'add_user'),(8,'Can change user',3,'change_user'),(9,'Can delete user',3,'delete_user'),(10,'Can add message',4,'add_message'),(11,'Can change message',4,'change_message'),(12,'Can delete message',4,'delete_message'),(13,'Can add content type',5,'add_contenttype'),(14,'Can change content type',5,'change_contenttype'),(15,'Can delete content type',5,'delete_contenttype'),(16,'Can add session',6,'add_session'),(17,'Can change session',6,'change_session'),(18,'Can delete session',6,'delete_session'),(19,'Can add site',7,'add_site'),(20,'Can change site',7,'change_site'),(21,'Can delete site',7,'delete_site'),(28,'Can add wiki page',10,'add_wikipage'),(29,'Can change wiki page',10,'change_wikipage'),(30,'Can delete wiki page',10,'delete_wikipage'),(31,'Can add category',11,'add_category'),(32,'Can change category',11,'change_category'),(33,'Can delete category',11,'delete_category'),(34,'Can add session',12,'add_session'),(35,'Can change session',12,'change_session'),(36,'Can delete session',12,'delete_session'),(37,'Can add tiki user',13,'add_tikiuser'),(38,'Can change tiki user',13,'change_tikiuser'),(39,'Can delete tiki user',13,'delete_tikiuser'),(40,'Can add forum',14,'add_forum'),(41,'Can change forum',14,'change_forum'),(42,'Can delete forum',14,'delete_forum'),(43,'Can add thread',15,'add_thread'),(44,'Can change thread',15,'change_thread'),(45,'Can delete thread',15,'delete_thread'),(46,'Can add post',16,'add_post'),(47,'Can change post',16,'change_post'),(48,'Can delete post',16,'delete_post'),(49,'Can add event watch',18,'add_eventwatch'),(50,'Can change event watch',18,'change_eventwatch'),(51,'Can delete event watch',18,'delete_eventwatch'),(52,'Can add question',19,'add_question'),(53,'Can change question',19,'change_question'),(54,'Can delete question',19,'delete_question'),(55,'Can add question meta data',20,'add_questionmetadata'),(56,'Can change question meta data',20,'change_questionmetadata'),(57,'Can delete question meta data',20,'delete_questionmetadata'),(58,'Can add answer',21,'add_answer'),(59,'Can change answer',21,'change_answer'),(60,'Can delete answer',21,'delete_answer'),(61,'Can add question vote',22,'add_questionvote'),(62,'Can change question vote',22,'change_questionvote'),(63,'Can delete question vote',22,'delete_questionvote'),(64,'Can add answer vote',23,'add_answervote'),(65,'Can change answer vote',23,'change_answervote'),(66,'Can delete answer vote',23,'delete_answervote'),(67,'Can add tags to and remove tags from questions',19,'tag_question'),(68,'Can add tag',24,'add_tag'),(69,'Can change tag',24,'change_tag'),(70,'Can delete tag',24,'delete_tag'),(71,'Can add tagged item',25,'add_taggeditem'),(72,'Can change tagged item',25,'change_taggeditem'),(73,'Can delete tagged item',25,'delete_taggeditem'),(74,'Can lock question',19,'lock_question'),(75,'Can moderate flagged objects',26,'can_moderate'),(76,'Can view restricted forums',14,'view_in_forum'),(77,'Can post in restricted forums',14,'post_in_forum'),(78,'Can add tweet',27,'add_tweet'),(79,'Can change tweet',27,'change_tweet'),(80,'Can delete tweet',27,'delete_tweet'),(81,'Can add canned category',28,'add_cannedcategory'),(82,'Can change canned category',28,'change_cannedcategory'),(83,'Can delete canned category',28,'delete_cannedcategory'),(84,'Can add canned response',29,'add_cannedresponse'),(85,'Can change canned response',29,'change_cannedresponse'),(86,'Can delete canned response',29,'delete_cannedresponse'),(87,'Can add category membership',30,'add_categorymembership'),(88,'Can change category membership',30,'change_categorymembership'),(89,'Can delete category membership',30,'delete_categorymembership'),(90,'Can add document',31,'add_document'),(91,'Can change document',31,'change_document'),(92,'Can delete document',31,'delete_document'),(93,'Can add revision',32,'add_revision'),(94,'Can change revision',32,'change_revision'),(95,'Can delete revision',32,'delete_revision'),(96,'Can review a revision',32,'review_revision'),(97,'Can add KB threads',33,'add_thread'),(98,'Can lock KB threads',33,'lock_thread'),(99,'Can sticky KB threads',33,'sticky_thread'),(100,'Can change KB threads',33,'change_thread'),(101,'Can delete KB threads',33,'delete_thread'),(102,'Can add KB posts',34,'add_post'),(103,'Can change KB posts',34,'change_post'),(104,'Can delete KB posts',34,'delete_post'),(105,'Can add image',36,'add_image'),(106,'Can change image',36,'change_image'),(107,'Can delete image',36,'delete_image'),(108,'Can add video',35,'add_video'),(109,'Can change video',35,'change_video'),(110,'Can delete video',35,'delete_video');
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
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `customercare_cannedcategory`
--

DROP TABLE IF EXISTS `customercare_cannedcategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customercare_cannedcategory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `weight` int(11) NOT NULL,
  `locale` varchar(7) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'en-US',
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`,`locale`),
  KEY `customercare_cannedcategory_f8f0a775` (`weight`),
  KEY `customercare_cannedcategory_928541cb` (`locale`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customercare_cannedresponse`
--

DROP TABLE IF EXISTS `customercare_cannedresponse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customercare_cannedresponse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `response` varchar(140) COLLATE utf8_unicode_ci DEFAULT NULL,
  `locale` varchar(7) COLLATE utf8_unicode_ci NOT NULL DEFAULT 'en-US',
  PRIMARY KEY (`id`),
  UNIQUE KEY `title` (`title`,`locale`),
  KEY `customercare_cannedresponse_928541cb` (`locale`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customercare_categorymembership`
--

DROP TABLE IF EXISTS `customercare_categorymembership`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customercare_categorymembership` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `category_id` int(11) NOT NULL,
  `response_id` int(11) NOT NULL,
  `weight` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `customercare_categorymembership_42dc49bc` (`category_id`),
  KEY `customercare_categorymembership_d5ea739f` (`response_id`),
  KEY `customercare_categorymembership_f8f0a775` (`weight`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customercare_tweet`
--

DROP TABLE IF EXISTS `customercare_tweet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customercare_tweet` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tweet_id` bigint(20) NOT NULL,
  `raw_json` longtext COLLATE utf8_unicode_ci,
  `locale` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `created` datetime NOT NULL,
  `reply_to` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tweet_id` (`tweet_id`),
  KEY `customercare_tweet_3216ff68` (`created`),
  KEY `customercare_tweet_928541cb` (`locale`),
  KEY `reply_to` (`reply_to`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'permission','auth','permission'),(2,'group','auth','group'),(3,'user','auth','user'),(4,'message','auth','message'),(5,'content type','contenttypes','contenttype'),(6,'session','sessions','session'),(7,'site','sites','site'),(10,'wiki page','sumo','wikipage'),(11,'category','sumo','category'),(12,'session','sumo','session'),(13,'tiki user','sumo','tikiuser'),(14,'forum','forums','forum'),(15,'thread','forums','thread'),(16,'post','forums','post'),(17,'permission','authority','permission'),(18,'event watch','notifications','eventwatch'),(19,'question','questions','question'),(20,'question meta data','questions','questionmetadata'),(21,'answer','questions','answer'),(22,'question vote','questions','questionvote'),(23,'answer vote','questions','answervote'),(24,'Tag','taggit','tag'),(25,'Tagged Item','taggit','taggeditem'),(26,'Flagged Object','flagit','flaggedobject'),(27,'tweet','customercare','tweet'),(28,'canned category','customercare','cannedcategory'),(29,'canned response','customercare','cannedresponse'),(30,'category membership','customercare','categorymembership'),(31,'document','wiki','document'),(32,'revision','wiki','revision'),(33,'KB Forum Thread','kbforums','thread'),(34,'KB Forum Post','kbforums','post'),(35,'Gallery Video','gallery','video'),(36,'Gallery Image','gallery','image'),(37,'periodic task','djcelery','periodictask'),(38,'interval','djcelery','intervalschedule'),(39,'task','djcelery','taskstate'),(40,'crontab','djcelery','crontabschedule'),(41,'worker','djcelery','workerstate'),(42,'watch','notifications','watch'),(43,'watch filter','notifications','watchfilter');
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

INSERT INTO `django_site` VALUES (1,'support-local.allizom.org','support-local.allizom.org');


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
  PRIMARY KEY (`id`),
  UNIQUE KEY `gallery_image_locale_title` (`locale`,`title`),
  KEY `gallery_image_title` (`title`),
  KEY `gallery_image_created` (`created`),
  KEY `gallery_image_updated` (`updated`),
  KEY `gallery_image_updated_by_id` (`updated_by_id`),
  KEY `gallery_image_locale` (`locale`),
  KEY `gallery_image_creator_id` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_9add8201` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_9add8201` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  PRIMARY KEY (`id`),
  UNIQUE KEY `gallery_video_locale_title` (`locale`,`title`),
  KEY `gallery_video_title` (`title`),
  KEY `gallery_video_created` (`created`),
  KEY `gallery_video_updated` (`updated`),
  KEY `gallery_video_updated_by_id` (`updated_by_id`),
  KEY `gallery_video_locale` (`locale`),
  KEY `gallery_video_creator_id` (`creator_id`),
  CONSTRAINT `creator_id_refs_id_7d7f5ce1` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `updated_by_id_refs_id_7d7f5ce1` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `metrics_assigned`
--

DROP TABLE IF EXISTS `metrics_assigned`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `metrics_assigned` (
  `assigned_id` int(11) NOT NULL AUTO_INCREMENT,
  `metric_id` int(11) NOT NULL,
  `tab_id` int(11) NOT NULL,
  PRIMARY KEY (`assigned_id`),
  KEY `metric_id` (`metric_id`),
  KEY `tab_id` (`tab_id`),
  CONSTRAINT `metrics_assigned_ibfk_1` FOREIGN KEY (`metric_id`) REFERENCES `metrics_metric` (`metric_id`) ON DELETE CASCADE,
  CONSTRAINT `metrics_assigned_ibfk_2` FOREIGN KEY (`tab_id`) REFERENCES `metrics_tab` (`tab_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metrics_metric`
--

DROP TABLE IF EXISTS `metrics_metric`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `metrics_metric` (
  `metric_id` int(11) NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(255) NOT NULL,
  `metric_range` varchar(1) NOT NULL DEFAULT '+' COMMENT 'values: + (daily), @ (monthly&weekly), - (weekly)',
  `metric_datatype` varchar(1) NOT NULL DEFAULT 'i' COMMENT 'values: i(nteger), %(percentage), f(loat), L(ist)',
  `metric_lastupdate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `metric_query` text,
  PRIMARY KEY (`metric_id`),
  UNIQUE KEY `metric_name` (`metric_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `metrics_tab`
--

DROP TABLE IF EXISTS `metrics_tab`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `metrics_tab` (
  `tab_id` int(11) NOT NULL AUTO_INCREMENT,
  `tab_name` varchar(255) NOT NULL,
  `tab_order` int(11) NOT NULL DEFAULT '0',
  `tab_content` longtext NOT NULL,
  PRIMARY KEY (`tab_id`),
  UNIQUE KEY `tab_name` (`tab_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications_eventwatch`
--

DROP TABLE IF EXISTS `notifications_eventwatch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_eventwatch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `content_type_id` int(11) NOT NULL,
  `watch_id` int(11) DEFAULT NULL,
  `email` varchar(75) NOT NULL,
  `hash` varchar(40) DEFAULT NULL,
  `event_type` varchar(20) DEFAULT NULL,
  `locale` varchar(7) DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `content_type_id` (`content_type_id`,`watch_id`,`email`,`event_type`,`locale`),
  KEY `notifications_eventwatch_content_type_id` (`content_type_id`),
  KEY `notifications_eventwatch_watch_id` (`watch_id`),
  KEY `notifications_eventwatch_email` (`email`),
  KEY `hash` (`hash`),
  KEY `notifications_eventwatch_event_type_idx` (`event_type`),
  KEY `notifications_eventwatch_928541cb` (`locale`),
  CONSTRAINT `content_type_id_refs_id_1b6122ce` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications_watch`
--

DROP TABLE IF EXISTS `notifications_watch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_watch` (
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
-- Table structure for table `notifications_watchfilter`
--

DROP TABLE IF EXISTS `notifications_watchfilter`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notifications_watchfilter` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `watch_id` int(11) NOT NULL,
  `name` varchar(20) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  `value` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`,`watch_id`),
  KEY `notifications_watchfilter_6e1bd094` (`watch_id`),
  CONSTRAINT `watch_id_refs_id_444d6e79` FOREIGN KEY (`watch_id`) REFERENCES `notifications_watch` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
  `status` int(11) NOT NULL,
  `is_locked` tinyint(1) NOT NULL,
  `solution_id` int(11) DEFAULT NULL,
  `num_votes_past_week` int(10) unsigned DEFAULT '0',
  `confirmation_id` varchar(40) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `questions_question_creator_id` (`creator_id`),
  KEY `questions_question_created` (`created`),
  KEY `questions_question_updated` (`updated`),
  KEY `questions_question_updated_by_id` (`updated_by_id`),
  KEY `questions_question_last_answer_id` (`last_answer_id`),
  KEY `questions_question_num_answers` (`num_answers`),
  KEY `questions_question_status` (`status`),
  KEY `solution_id_refs_id_95fb9a4d` (`solution_id`),
  KEY `questions_question_num_votes_past_week_idx` (`num_votes_past_week`),
  KEY `questions_question_confirmation_id` (`confirmation_id`),
  CONSTRAINT `creator_id_refs_id_723e3a28` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `last_answer_id_refs_id_6a0465b3` FOREIGN KEY (`last_answer_id`) REFERENCES `questions_answer` (`id`),
  CONSTRAINT `solution_id_refs_id_95fb9a4d` FOREIGN KEY (`solution_id`) REFERENCES `questions_answer` (`id`),
  CONSTRAINT `updated_by_id_refs_id_723e3a28` FOREIGN KEY (`updated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
INSERT INTO `schema_version` VALUES (83);
/*!40000 ALTER TABLE `schema_version` ENABLE KEYS */;
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
  `livechat_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_id_refs_id_21617f27` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;


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
  `parent_id` int(11) DEFAULT NULL,
  `html` longtext NOT NULL,
  `category` int(11) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `is_template` tinyint(1) NOT NULL DEFAULT '0',
  `is_localizable` tinyint(1) NOT NULL DEFAULT '1',
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
  CONSTRAINT `current_revision_id_refs_id_79f9a479` FOREIGN KEY (`current_revision_id`) REFERENCES `wiki_revision` (`id`),
  CONSTRAINT `parent_id_refs_id_6c4b5a5` FOREIGN KEY (`parent_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_firefoxversion`
--

DROP TABLE IF EXISTS `wiki_firefoxversion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_firefoxversion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `document_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id` (`item_id`,`document_id`),
  KEY `wiki_firefoxversion_f4226d13` (`document_id`),
  CONSTRAINT `document_id_refs_id_5d21595b` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_helpfulvote`
--

DROP TABLE IF EXISTS `wiki_helpfulvote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_helpfulvote` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `document_id` int(11) NOT NULL,
  `helpful` tinyint(1) NOT NULL,
  `created` datetime NOT NULL,
  `creator_id` int(11) DEFAULT NULL,
  `anonymous_id` varchar(40) COLLATE utf8_unicode_ci NOT NULL,
  `user_agent` varchar(1000) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `wiki_helpfulvote_f4226d13` (`document_id`),
  KEY `wiki_helpfulvote_3216ff68` (`created`),
  KEY `wiki_helpfulvote_f97a5119` (`creator_id`),
  KEY `wiki_helpfulvote_2291b592` (`anonymous_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiki_operatingsystem`
--

DROP TABLE IF EXISTS `wiki_operatingsystem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `wiki_operatingsystem` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `document_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_id` (`item_id`,`document_id`),
  KEY `wiki_operatingsystem_f4226d13` (`document_id`),
  CONSTRAINT `document_id_refs_id_e92dd159` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-02-24 12:38:43
