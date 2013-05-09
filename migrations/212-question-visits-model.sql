CREATE TABLE `questions_questionvisits` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL UNIQUE,
    `visits` integer NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `questions_questionvisits` ADD CONSTRAINT `question_id_refs_id_f067137b` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`);
CREATE INDEX `questions_questionvisits_5bfc8463` ON `questions_questionvisits` (`visits`);
