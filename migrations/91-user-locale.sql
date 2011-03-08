-- Add a preferred locale to profiles.
ALTER TABLE `users_profile`
    ADD `locale` varchar(7) NOT NULL DEFAULT 'en-US';
