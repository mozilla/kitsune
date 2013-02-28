DELETE FROM `wiki_helpfulvotemetadata`
WHERE `wiki_helpfulvotemetadata`.`vote_id` in (
    SELECT `wiki_helpfulvote`.`id` FROM `wiki_helpfulvote`
    WHERE `wiki_helpfulvote`.`user_agent` LIKE '%Netsparker%'
    AND `created` BETWEEN '2013-02-17 0' AND '2013-02-19 0');

DELETE FROM `wiki_helpfulvote`
WHERE `wiki_helpfulvote`.`user_agent` LIKE '%Netsparker%'
AND `created` BETWEEN '2013-02-17 0' AND '2013-02-19 0';
