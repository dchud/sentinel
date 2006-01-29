-- MySQL dump 10.9
--
-- Host: localhost    Database: canary_sim
-- ------------------------------------------------------
-- Server version	4.1.12

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
CREATE TABLE `categories` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `name` varchar(50) NOT NULL default '',
  `concept_types` varchar(12) NOT NULL default '',
  PRIMARY KEY  (`uid`),
  UNIQUE KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `category_concept_groups`
--

DROP TABLE IF EXISTS `category_concept_groups`;
CREATE TABLE `category_concept_groups` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `category_concept_id` int(11) unsigned NOT NULL default '0',
  `category_group_id` int(11) unsigned NOT NULL default '0',
  PRIMARY KEY  (`uid`),
  KEY `category_concept_id` (`category_concept_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `category_concepts`
--

DROP TABLE IF EXISTS `category_concepts`;
CREATE TABLE `category_concepts` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `category_id` int(11) unsigned NOT NULL default '0',
  `concept_id` int(11) unsigned NOT NULL default '0',
  `is_default` int(1) unsigned NOT NULL default '0',
  `is_broad` int(1) unsigned NOT NULL default '0',
  PRIMARY KEY  (`uid`),
  KEY `category_id` (`category_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `category_groups`
--

DROP TABLE IF EXISTS `category_groups`;
CREATE TABLE `category_groups` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `category_id` int(11) unsigned NOT NULL default '0',
  `name` char(50) NOT NULL default '',
  PRIMARY KEY  (`uid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `duplicates`
--

DROP TABLE IF EXISTS `duplicates`;
CREATE TABLE `duplicates` (
  `uid` int(11) NOT NULL auto_increment,
  `new_record_id` int(11) NOT NULL default '0',
  `old_record_id` int(11) NOT NULL default '0',
  `term_id` int(4) NOT NULL default '0',
  PRIMARY KEY  (`uid`),
  UNIQUE KEY `new_record_id` (`new_record_id`,`old_record_id`,`term_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `dv_group`
--

DROP TABLE IF EXISTS `dv_group`;
CREATE TABLE `dv_group` (
  `dv_group_id` int(2) NOT NULL auto_increment,
  `group_name` tinytext NOT NULL,
  `description` tinytext,
  `allow_multiple` tinyint(1) unsigned NOT NULL default '0',
  PRIMARY KEY  (`dv_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `dv_values`
--

DROP TABLE IF EXISTS `dv_values`;
CREATE TABLE `dv_values` (
  `dv_id` int(11) NOT NULL auto_increment,
  `dv_group_id` tinyint(4) NOT NULL default '0',
  `serial_number` tinyint(4) NOT NULL default '0',
  `description` tinytext NOT NULL,
  PRIMARY KEY  (`dv_id`),
  KEY `dv_group_id` (`dv_group_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `exposure_routes`
--

DROP TABLE IF EXISTS `exposure_routes`;
CREATE TABLE `exposure_routes` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '0',
  `methodology_id` int(11) NOT NULL default '0',
  `route` tinyint(4) NOT NULL default '0',
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`),
  KEY `methodology_id` (`methodology_id`),
  KEY `route` (`route`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `exposures`
--

DROP TABLE IF EXISTS `exposures`;
CREATE TABLE `exposures` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '0',
  `concept_id` int(11) NOT NULL default '0',
  `concept_source_id` int(11) NOT NULL default '0',
  `term` text,
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `gazeteer`
--

DROP TABLE IF EXISTS `gazeteer`;
CREATE TABLE `gazeteer` (
  `uid` int(10) unsigned NOT NULL auto_increment,
  `data_source` char(1) NOT NULL default '',
  `latitude` float NOT NULL default '0',
  `longitude` float NOT NULL default '0',
  `dms_latitude` int(11) NOT NULL default '0',
  `dms_longitude` int(11) NOT NULL default '0',
  `feature_type` varchar(6) NOT NULL default '',
  `country_code` char(2) NOT NULL default '',
  `adm1` char(2) NOT NULL default '',
  `adm2` varchar(255) default NULL,
  `name` text NOT NULL,
  PRIMARY KEY  (`uid`),
  KEY `country_code` (`country_code`),
  FULLTEXT KEY `name` (`name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `gazeteer_countries`
--

DROP TABLE IF EXISTS `gazeteer_countries`;
CREATE TABLE `gazeteer_countries` (
  `uid` int(3) NOT NULL default '0',
  `name` varchar(75) NOT NULL default '',
  `code` char(2) NOT NULL default '',
  PRIMARY KEY  (`uid`),
  UNIQUE KEY `code` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `gazeteer_features`
--

DROP TABLE IF EXISTS `gazeteer_features`;
CREATE TABLE `gazeteer_features` (
  `uid` int(11) NOT NULL default '0',
  `designation` varchar(6) NOT NULL default '',
  `name` varchar(50) NOT NULL default '',
  `description` varchar(255) default NULL,
  PRIMARY KEY  (`uid`),
  UNIQUE KEY `designation` (`designation`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `gazeteer_fips_codes`
--

DROP TABLE IF EXISTS `gazeteer_fips_codes`;
CREATE TABLE `gazeteer_fips_codes` (
  `country_code` char(2) NOT NULL default '',
  `fips_code` char(3) NOT NULL default '',
  `name` varchar(100) NOT NULL default '',
  PRIMARY KEY  (`country_code`,`fips_code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
CREATE TABLE `locations` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '0',
  `feature_id` int(11) NOT NULL default '0',
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`),
  KEY `feature_id` (`feature_id`),
  KEY `feature_id_2` (`feature_id`),
  KEY `feature_id_3` (`feature_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `medline_journals`
--

DROP TABLE IF EXISTS `medline_journals`;
CREATE TABLE `medline_journals` (
  `uid` int(6) NOT NULL default '0',
  `journal_title` text NOT NULL,
  `abbreviation` varchar(255) default NULL,
  `issn` varchar(9) NOT NULL default '',
  `eissn` varchar(9) default NULL,
  `iso_abbr` varchar(255) default NULL,
  `nlm_id` varchar(25) default NULL,
  PRIMARY KEY  (`uid`),
  KEY `issn` (`issn`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `methodologies`
--

DROP TABLE IF EXISTS `methodologies`;
CREATE TABLE `methodologies` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '-1',
  `study_type_id` tinyint(1) NOT NULL default '0',
  `sample_size` varchar(50) default NULL,
  `timing` int(11) NOT NULL default '-1',
  `sampling` tinyint(4) NOT NULL default '-1',
  `controls` tinyint(4) NOT NULL default '-1',
  `is_mesocosm` tinyint(4) NOT NULL default '0',
  `is_enclosure` tinyint(4) NOT NULL default '0',
  `comments` text,
  `date_modified` datetime NOT NULL default '0000-00-00 00:00:00',
  `date_entered` datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `outcomes`
--

DROP TABLE IF EXISTS `outcomes`;
CREATE TABLE `outcomes` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '0',
  `concept_id` int(11) NOT NULL default '0',
  `concept_source_id` int(11) NOT NULL default '0',
  `term` text,
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `queued_batches`
--

DROP TABLE IF EXISTS `queued_batches`;
CREATE TABLE `queued_batches` (
  `uid` int(4) unsigned NOT NULL auto_increment,
  `file_name` varchar(200) NOT NULL default '',
  `source_id` int(3) unsigned NOT NULL default '0',
  `num_records` int(5) NOT NULL default '0',
  `name` varchar(255) default NULL,
  `notes` varchar(255) default NULL,
  `date_added` date NOT NULL default '0000-00-00',
  PRIMARY KEY  (`uid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `queued_record_metadata`
--

DROP TABLE IF EXISTS `queued_record_metadata`;
CREATE TABLE `queued_record_metadata` (
  `uid` int(11) NOT NULL auto_increment,
  `queued_record_id` int(11) NOT NULL default '0',
  `source_id` int(11) NOT NULL default '0',
  `term_id` int(11) NOT NULL default '0',
  `value` text NOT NULL,
  `extra` text,
  `sequence_position` int(4) unsigned default NULL,
  PRIMARY KEY  (`uid`),
  KEY `queued_record_id` (`queued_record_id`),
  KEY `term_id` (`term_id`),
  KEY `sequence_position` (`sequence_position`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `queued_records`
--

DROP TABLE IF EXISTS `queued_records`;
CREATE TABLE `queued_records` (
  `uid` int(6) unsigned NOT NULL auto_increment,
  `queued_batch_id` int(10) unsigned NOT NULL default '0',
  `status` tinyint(1) NOT NULL default '0',
  `user_id` varchar(25) default NULL,
  `study_id` int(11) NOT NULL default '-1',
  `title` text,
  `source` text,
  `unique_identifier` text,
  `duplicate_score` int(11) default '0',
  `needs_paper` tinyint(1) unsigned NOT NULL default '0',
  PRIMARY KEY  (`uid`),
  KEY `status` (`status`),
  KEY `queued_batch_id` (`queued_batch_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `risk_factors`
--

DROP TABLE IF EXISTS `risk_factors`;
CREATE TABLE `risk_factors` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '0',
  `concept_id` int(11) NOT NULL default '0',
  `concept_source_id` int(11) NOT NULL default '0',
  `term` text,
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
CREATE TABLE `sessions` (
  `session_id` varchar(20) NOT NULL default '',
  `user_id` varchar(50) NOT NULL default '',
  `remote_addr` text,
  `creation_time` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,
  `access_time` timestamp NOT NULL default '0000-00-00 00:00:00',
  `messages` text,
  `form_tokens` text,
  PRIMARY KEY  (`session_id`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `sources`
--

DROP TABLE IF EXISTS `sources`;
CREATE TABLE `sources` (
  `uid` int(3) NOT NULL auto_increment,
  `name` varchar(50) NOT NULL default '',
  `description` varchar(255) default NULL,
  `date_modified` date NOT NULL default '0000-00-00',
  `re_result_sep` varchar(255) default NULL,
  `re_term_token` varchar(255) default NULL,
  `sfx_pattern` varchar(255) default NULL,
  PRIMARY KEY  (`uid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `species`
--

DROP TABLE IF EXISTS `species`;
CREATE TABLE `species` (
  `uid` int(11) NOT NULL auto_increment,
  `study_id` int(11) NOT NULL default '0',
  `concept_id` int(11) NOT NULL default '0',
  `concept_source_id` int(11) NOT NULL default '0',
  `term` text,
  `types` varchar(24) default NULL,
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `studies`
--

DROP TABLE IF EXISTS `studies`;
CREATE TABLE `studies` (
  `uid` int(11) NOT NULL auto_increment,
  `record_id` int(11) NOT NULL default '0',
  `status` tinyint(4) NOT NULL default '0',
  `article_type` tinyint(1) NOT NULL default '0',
  `curator_user_id` varchar(255) NOT NULL default '',
  `has_outcomes` tinyint(1) NOT NULL default '0',
  `has_exposures` tinyint(1) NOT NULL default '0',
  `has_relationships` tinyint(1) NOT NULL default '0',
  `has_interspecies` tinyint(1) NOT NULL default '0',
  `has_exposure_linkage` tinyint(1) NOT NULL default '0',
  `has_outcome_linkage` tinyint(1) NOT NULL default '0',
  `has_genomic` tinyint(1) NOT NULL default '0',
  `comments` text,
  `date_modified` datetime NOT NULL default '0000-00-00 00:00:00',
  `date_entered` datetime NOT NULL default '0000-00-00 00:00:00',
  `date_curated` datetime default NULL,
  PRIMARY KEY  (`uid`),
  UNIQUE KEY `record_id` (`record_id`),
  KEY `article_type` (`article_type`),
  KEY `status` (`status`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `study_history`
--

DROP TABLE IF EXISTS `study_history`;
CREATE TABLE `study_history` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `study_id` int(11) unsigned NOT NULL default '0',
  `curator_user_id` varchar(255) default NULL,
  `message` text,
  `modified` datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (`uid`),
  KEY `study_id` (`study_id`),
  KEY `curator_user_id` (`curator_user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `terms`
--

DROP TABLE IF EXISTS `terms`;
CREATE TABLE `terms` (
  `uid` int(4) unsigned NOT NULL auto_increment,
  `name` varchar(255) default NULL,
  `description` varchar(255) default NULL,
  `date_modified` date NOT NULL default '0000-00-00',
  `token` varchar(8) default NULL,
  `vocabulary_uid` int(3) default NULL,
  `source_id` int(3) default NULL,
  `is_multivalue` tinyint(1) default '0',
  `re_multivalue_sep` varchar(255) default NULL,
  `mapped_term_id` int(5) default NULL,
  PRIMARY KEY  (`uid`),
  KEY `token` (`token`,`vocabulary_uid`,`source_id`),
  KEY `source_uid` (`source_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `umls_concepts`
--

DROP TABLE IF EXISTS `umls_concepts`;
CREATE TABLE `umls_concepts` (
  `umls_concept_id` int(11) NOT NULL default '0',
  `preferred_name` text NOT NULL,
  PRIMARY KEY  (`umls_concept_id`),
  KEY `umls_concept_id` (`umls_concept_id`),
  FULLTEXT KEY `preferred_name` (`preferred_name`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `umls_concepts_sources`
--

DROP TABLE IF EXISTS `umls_concepts_sources`;
CREATE TABLE `umls_concepts_sources` (
  `umls_source_id` int(11) NOT NULL default '0',
  `umls_concept_id` int(11) NOT NULL default '0',
  `umls_source_code` varchar(255) NOT NULL default '',
  KEY `umls_source_id` (`umls_source_id`),
  KEY `umls_concept_id` (`umls_concept_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `umls_terms`
--

DROP TABLE IF EXISTS `umls_terms`;
CREATE TABLE `umls_terms` (
  `umls_term_id` int(11) NOT NULL default '0',
  `term` text NOT NULL,
  `umls_concept_id` int(11) NOT NULL default '0',
  KEY `umls_concept_id` (`umls_concept_id`),
  FULLTEXT KEY `term` (`term`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `user_records`
--

DROP TABLE IF EXISTS `user_records`;
CREATE TABLE `user_records` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `user_id` int(11) unsigned NOT NULL default '0',
  `record_id` int(11) unsigned NOT NULL default '0',
  `notes` text,
  `date_created` datetime NOT NULL default '0000-00-00 00:00:00',
  PRIMARY KEY  (`uid`),
  KEY `user_id` (`user_id`),
  KEY `record_id` (`record_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `user_set_records`
--

DROP TABLE IF EXISTS `user_set_records`;
CREATE TABLE `user_set_records` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `user_set_id` int(11) unsigned NOT NULL default '0',
  `record_id` int(11) unsigned default '0',
  PRIMARY KEY  (`uid`),
  KEY `user_set_id` (`user_set_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `user_sets`
--

DROP TABLE IF EXISTS `user_sets`;
CREATE TABLE `user_sets` (
  `uid` int(11) unsigned NOT NULL auto_increment,
  `user_id` int(11) unsigned NOT NULL default '0',
  `name` varchar(255) default NULL,
  `is_locked` tinyint(1) default '0',
  PRIMARY KEY  (`uid`),
  KEY `user_id` (`user_id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `uid` int(11) NOT NULL auto_increment,
  `id` varchar(25) NOT NULL default '',
  `is_active` tinyint(1) unsigned NOT NULL default '0',
  `is_admin` tinyint(1) unsigned NOT NULL default '0',
  `is_editor` tinyint(1) unsigned NOT NULL default '0',
  `name` varchar(50) NOT NULL default '',
  `passwd` varchar(50) NOT NULL default '',
  `is_assistant` tinyint(1) unsigned NOT NULL default '0',
  `email` varchar(50) NOT NULL default '',
  `netid` varchar(25) default '',
  `token` varchar(25) default '',
  `wants_news` tinyint(1) unsigned default '0',
  PRIMARY KEY  (`uid`),
  UNIQUE KEY `id` (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

