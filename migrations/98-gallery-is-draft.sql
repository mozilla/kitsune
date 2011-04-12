-- Add is_draft column to gallery media

ALTER TABLE `gallery_video`
    ADD `is_draft` bool DEFAULT NULL;

ALTER TABLE `gallery_image`
    ADD `is_draft` bool DEFAULT NULL;

ALTER TABLE `gallery_video`
    ADD UNIQUE `gallery_video_is_draft_creator_id` (`is_draft`, `creator_id`);

ALTER TABLE `gallery_image`
    ADD UNIQUE `gallery_image_is_draft_creator_id` (`is_draft`, `creator_id`);

-- Drop an unnecessary index on locale
ALTER TABLE `gallery_video`
    DROP INDEX `gallery_video_locale`;

ALTER TABLE `gallery_image`
    DROP INDEX `gallery_image_locale`;
