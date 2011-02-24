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
-- Table structure for table `events_event`
--

DROP TABLE IF EXISTS `events_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `events_event` (
  `event_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_name` varchar(255) NOT NULL,
  `event_date` timestamp NULL DEFAULT NULL,
  `event_signuptext` blob NOT NULL,
  `event_canceltext` blob NOT NULL,
  `event_validfrom` timestamp NULL DEFAULT NULL,
  `event_validto` timestamp NULL DEFAULT NULL,
  `event_signupbefore` blob,
  PRIMARY KEY (`event_id`),
  UNIQUE KEY `event_name` (`event_name`),
  KEY `event_validfrom` (`event_validfrom`),
  KEY `event_validto` (`event_validto`),
  KEY `event_date` (`event_date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `events_signup`
--

DROP TABLE IF EXISTS `events_signup`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `events_signup` (
  `signup_id` int(11) NOT NULL AUTO_INCREMENT,
  `event_id` int(11) NOT NULL,
  `signup_user` varchar(255) NOT NULL,
  `signup_email` varchar(255) NOT NULL,
  `signup_date` datetime NOT NULL,
  `signup_hash` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`signup_id`),
  UNIQUE KEY `signup_hash` (`signup_hash`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `galaxia_activities`
--

DROP TABLE IF EXISTS `galaxia_activities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_activities` (
  `activityId` int(14) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `normalized_name` varchar(80) DEFAULT NULL,
  `pId` int(14) NOT NULL DEFAULT '0',
  `type` enum('start','end','split','switch','join','activity','standalone') DEFAULT NULL,
  `isAutoRouted` char(1) DEFAULT NULL,
  `flowNum` int(10) DEFAULT NULL,
  `isInteractive` char(1) DEFAULT NULL,
  `lastModif` int(14) DEFAULT NULL,
  `description` text,
  `expirationTime` int(6) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`activityId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_activity_roles`
--

DROP TABLE IF EXISTS `galaxia_activity_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_activity_roles` (
  `activityId` int(14) NOT NULL DEFAULT '0',
  `roleId` int(14) NOT NULL DEFAULT '0',
  PRIMARY KEY (`activityId`,`roleId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_instance_activities`
--

DROP TABLE IF EXISTS `galaxia_instance_activities`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_instance_activities` (
  `instanceId` int(14) NOT NULL DEFAULT '0',
  `activityId` int(14) NOT NULL DEFAULT '0',
  `started` int(14) NOT NULL DEFAULT '0',
  `ended` int(14) NOT NULL DEFAULT '0',
  `user` varchar(200) DEFAULT NULL,
  `status` enum('running','completed') DEFAULT NULL,
  PRIMARY KEY (`instanceId`,`activityId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_instance_comments`
--

DROP TABLE IF EXISTS `galaxia_instance_comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_instance_comments` (
  `cId` int(14) NOT NULL AUTO_INCREMENT,
  `instanceId` int(14) NOT NULL DEFAULT '0',
  `user` varchar(200) DEFAULT NULL,
  `activityId` int(14) DEFAULT NULL,
  `hash` varchar(32) DEFAULT NULL,
  `title` varchar(250) DEFAULT NULL,
  `comment` text,
  `activity` varchar(80) DEFAULT NULL,
  `timestamp` int(14) DEFAULT NULL,
  PRIMARY KEY (`cId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_instances`
--

DROP TABLE IF EXISTS `galaxia_instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_instances` (
  `instanceId` int(14) NOT NULL AUTO_INCREMENT,
  `pId` int(14) NOT NULL DEFAULT '0',
  `started` int(14) DEFAULT NULL,
  `name` varchar(200) NOT NULL DEFAULT 'No Name',
  `owner` varchar(200) DEFAULT NULL,
  `nextActivity` int(14) DEFAULT NULL,
  `nextUser` varchar(200) DEFAULT NULL,
  `ended` int(14) DEFAULT NULL,
  `status` enum('active','exception','aborted','completed') DEFAULT NULL,
  `properties` longblob,
  PRIMARY KEY (`instanceId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_processes`
--

DROP TABLE IF EXISTS `galaxia_processes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_processes` (
  `pId` int(14) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) DEFAULT NULL,
  `isValid` char(1) DEFAULT NULL,
  `isActive` char(1) DEFAULT NULL,
  `version` varchar(12) DEFAULT NULL,
  `description` text,
  `lastModif` int(14) DEFAULT NULL,
  `normalized_name` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`pId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_roles`
--

DROP TABLE IF EXISTS `galaxia_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_roles` (
  `roleId` int(14) NOT NULL AUTO_INCREMENT,
  `pId` int(14) NOT NULL DEFAULT '0',
  `lastModif` int(14) DEFAULT NULL,
  `name` varchar(80) DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`roleId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_transitions`
--

DROP TABLE IF EXISTS `galaxia_transitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_transitions` (
  `pId` int(14) NOT NULL DEFAULT '0',
  `actFromId` int(14) NOT NULL DEFAULT '0',
  `actToId` int(14) NOT NULL DEFAULT '0',
  PRIMARY KEY (`actFromId`,`actToId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_user_roles`
--

DROP TABLE IF EXISTS `galaxia_user_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_user_roles` (
  `pId` int(14) NOT NULL DEFAULT '0',
  `roleId` int(14) NOT NULL AUTO_INCREMENT,
  `user` varchar(200) NOT NULL,
  PRIMARY KEY (`roleId`,`user`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `galaxia_workitems`
--

DROP TABLE IF EXISTS `galaxia_workitems`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `galaxia_workitems` (
  `itemId` int(14) NOT NULL AUTO_INCREMENT,
  `instanceId` int(14) NOT NULL DEFAULT '0',
  `orderId` int(14) NOT NULL DEFAULT '0',
  `activityId` int(14) NOT NULL DEFAULT '0',
  `properties` longblob,
  `started` int(14) DEFAULT NULL,
  `ended` int(14) DEFAULT NULL,
  `user` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`itemId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
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
-- Table structure for table `messu_archive`
--

DROP TABLE IF EXISTS `messu_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messu_archive` (
  `msgId` int(14) NOT NULL AUTO_INCREMENT,
  `user` varchar(40) NOT NULL,
  `user_from` varchar(40) NOT NULL,
  `user_to` text,
  `user_cc` text,
  `user_bcc` text,
  `subject` varchar(255) DEFAULT NULL,
  `body` text,
  `hash` varchar(32) DEFAULT NULL,
  `replyto_hash` varchar(32) DEFAULT NULL,
  `date` int(14) DEFAULT NULL,
  `isRead` char(1) DEFAULT NULL,
  `isReplied` char(1) DEFAULT NULL,
  `isFlagged` char(1) DEFAULT NULL,
  `priority` int(2) DEFAULT NULL,
  PRIMARY KEY (`msgId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `messu_messages`
--

DROP TABLE IF EXISTS `messu_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messu_messages` (
  `msgId` int(14) NOT NULL AUTO_INCREMENT,
  `user` varchar(200) NOT NULL,
  `user_from` varchar(200) NOT NULL,
  `user_to` text,
  `user_cc` text,
  `user_bcc` text,
  `subject` varchar(255) DEFAULT NULL,
  `body` text,
  `hash` varchar(32) DEFAULT NULL,
  `replyto_hash` varchar(32) DEFAULT NULL,
  `date` int(14) DEFAULT NULL,
  `isRead` char(1) DEFAULT NULL,
  `isReplied` char(1) DEFAULT NULL,
  `isFlagged` char(1) DEFAULT NULL,
  `priority` int(2) DEFAULT NULL,
  PRIMARY KEY (`msgId`),
  KEY `userIsRead` (`user`,`isRead`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `messu_sent`
--

DROP TABLE IF EXISTS `messu_sent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messu_sent` (
  `msgId` int(14) NOT NULL AUTO_INCREMENT,
  `user` varchar(40) NOT NULL,
  `user_from` varchar(40) NOT NULL,
  `user_to` text,
  `user_cc` text,
  `user_bcc` text,
  `subject` varchar(255) DEFAULT NULL,
  `body` text,
  `hash` varchar(32) DEFAULT NULL,
  `replyto_hash` varchar(32) DEFAULT NULL,
  `date` int(14) DEFAULT NULL,
  `isRead` char(1) DEFAULT NULL,
  `isReplied` char(1) DEFAULT NULL,
  `isFlagged` char(1) DEFAULT NULL,
  `priority` int(2) DEFAULT NULL,
  PRIMARY KEY (`msgId`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
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
-- Table structure for table `se_weights`
--

DROP TABLE IF EXISTS `se_weights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `se_weights` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `type` set('weights','binary','withc') NOT NULL,
  `name` varchar(25) NOT NULL,
  `parentId` int(10) NOT NULL DEFAULT '0',
  `value` float DEFAULT NULL,
  PRIMARY KEY (`type`,`name`,`parentId`),
  UNIQUE KEY `id` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

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
-- Table structure for table `users_grouppermissions`
--

DROP TABLE IF EXISTS `users_grouppermissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_grouppermissions` (
  `groupName` varchar(255) NOT NULL,
  `permName` varchar(31) NOT NULL,
  `value` char(1) DEFAULT NULL,
  PRIMARY KEY (`groupName`(30),`permName`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_groups`
--

DROP TABLE IF EXISTS `users_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_groups` (
  `groupName` varchar(255) NOT NULL,
  `groupDesc` varchar(255) DEFAULT NULL,
  `groupHome` varchar(255) DEFAULT NULL,
  `usersTrackerId` int(11) DEFAULT NULL,
  `groupTrackerId` int(11) DEFAULT NULL,
  `usersFieldId` int(11) DEFAULT NULL,
  `groupFieldId` int(11) DEFAULT NULL,
  `registrationChoice` char(1) DEFAULT NULL,
  `registrationUsersFieldIds` text,
  `userChoice` char(1) DEFAULT NULL,
  `groupDefCat` int(12) DEFAULT '0',
  `groupTheme` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`groupName`(30))
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_objectpermissions`
--

DROP TABLE IF EXISTS `users_objectpermissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_objectpermissions` (
  `groupName` varchar(255) NOT NULL,
  `permName` varchar(31) NOT NULL,
  `objectType` varchar(20) NOT NULL,
  `objectId` varchar(32) NOT NULL,
  PRIMARY KEY (`objectId`,`objectType`,`groupName`(30),`permName`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_permissions`
--

DROP TABLE IF EXISTS `users_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_permissions` (
  `permName` varchar(31) NOT NULL,
  `permDesc` varchar(250) DEFAULT NULL,
  `level` varchar(80) DEFAULT NULL,
  `type` varchar(20) DEFAULT NULL,
  `admin` char(1) DEFAULT NULL,
  PRIMARY KEY (`permName`),
  UNIQUE KEY `permName` (`permName`),
  KEY `type` (`type`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
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
-- Table structure for table `users_usergroups`
--

DROP TABLE IF EXISTS `users_usergroups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_usergroups` (
  `userId` int(8) NOT NULL DEFAULT '0',
  `groupName` varchar(255) NOT NULL,
  PRIMARY KEY (`userId`,`groupName`(30))
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users_users`
--

DROP TABLE IF EXISTS `users_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users_users` (
  `userId` int(8) NOT NULL AUTO_INCREMENT,
  `email` varchar(200) DEFAULT NULL,
  `login` varchar(30) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `password` varchar(30) DEFAULT NULL,
  `provpass` varchar(30) DEFAULT NULL,
  `default_group` varchar(255) DEFAULT NULL,
  `lastLogin` int(14) DEFAULT NULL,
  `currentLogin` int(14) DEFAULT NULL,
  `registrationDate` int(14) DEFAULT NULL,
  `challenge` varchar(32) DEFAULT NULL,
  `pass_confirm` int(14) DEFAULT NULL,
  `email_confirm` int(14) DEFAULT NULL,
  `hash` varchar(34) DEFAULT NULL,
  `created` int(14) DEFAULT NULL,
  `avatarName` varchar(80) DEFAULT NULL,
  `avatarSize` int(14) DEFAULT NULL,
  `avatarFileType` varchar(250) DEFAULT NULL,
  `avatarData` longblob,
  `avatarLibName` varchar(200) DEFAULT NULL,
  `avatarType` char(1) DEFAULT NULL,
  `score` int(11) NOT NULL DEFAULT '0',
  `unsuccessful_logins` int(14) DEFAULT '0',
  `valid` varchar(32) DEFAULT NULL,
  `openid_url` varchar(255) DEFAULT NULL,
  `livechat_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`userId`),
  UNIQUE KEY `livechat_id` (`livechat_id`),
  UNIQUE KEY `users_users_login` (`login`),
  UNIQUE KEY `users_users_email` (`email`),
  KEY `score` (`score`),
  KEY `registrationDate` (`registrationDate`),
  KEY `login` (`login`),
  KEY `openid_url` (`openid_url`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
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
