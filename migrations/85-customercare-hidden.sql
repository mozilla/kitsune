-- Allow tweets to be hidden on Army of Awesome page.
ALTER TABLE `customercare_tweet` ADD `hidden` TINYINT(1) NOT NULL DEFAULT '0';
ALTER TABLE `customercare_tweet` ADD INDEX ( `hidden` ) ;
