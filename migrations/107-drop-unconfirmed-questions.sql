-- At a minimum, this is the necessary clean up for old questions.

DELETE FROM questions_questionmetadata WHERE question_id IN (SELECT id FROM questions_question WHERE status=0);

DELETE FROM questions_questionvote WHERE question_id IN (SELECT id FROM questions_question WHERE status=0);

UPDATE questions_question SET last_answer_id = NULL WHERE status = 0;

DELETE FROM questions_answervote WHERE answer_id IN (SELECT id FROM questions_answer WHERE question_id IN (SELECT id FROM questions_question WHERE status = 0));

DELETE FROM questions_answer WHERE question_id IN (SELECT id FROM questions_question WHERE status=0);

DELETE FROM questions_question WHERE status = 0;
