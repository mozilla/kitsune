import mock
import waffle

from sumo.tests import TestCase
from wiki.cron import migrate_helpfulvotes
from wiki.models import (HelpfulVote, HelpfulVoteOld)
from wiki.tests import document, revision
from users.tests import user


class HelpfulMigrationTestCase(TestCase):
    @mock.patch.object(waffle, 'switch_is_active')
    def test_normal_migrate_anon(self, switch_is_active):
        switch_is_active.return_value = True
        rev = revision()
        rev.save()
        old = HelpfulVoteOld()
        old.document=rev.document
        old.helpful=1
        old.anonymous_id='69beab04be927353c2f0046db2232643'
        old.user_agent='''Mozilla/5.0 (Windows; U; Windows NT 6.1;
                        pt-BR; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'''
        old.save()
        migrate_helpfulvotes()
        new = HelpfulVote.objects.filter(revision=rev,
            helpful=1,
            anonymous_id='69beab04be927353c2f0046db2232643',
            user_agent='''Mozilla/5.0 (Windows; U; Windows NT 6.1;
                        pt-BR; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'''
            )
        assert new.exists()

        check_old = HelpfulVoteOld.objects.filter(id=old.id)
        assert not check_old.exists()

    @mock.patch.object(waffle, 'switch_is_active')
    def test_normal_migrate_user(self, switch_is_active):
        switch_is_active.return_value = True
        rev = revision()
        rev.save()
        usr = user(save=True)

        old = HelpfulVoteOld()
        old.document=rev.document
        old.helpful=1
        old.creator=usr
        old.user_agent='''Mozilla/5.0 (Windows; U; Windows NT 6.1;
                        pt-BR; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'''
        old.save()

        migrate_helpfulvotes()

        new = HelpfulVote.objects.filter(revision=rev,
            helpful=1,
            creator=usr,
            user_agent='''Mozilla/5.0 (Windows; U; Windows NT 6.1;
                        pt-BR; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12'''
            )
        assert new.exists()

        check_old = HelpfulVoteOld.objects.filter(id=old.id)
        assert not check_old.exists()