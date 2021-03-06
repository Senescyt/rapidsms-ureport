import unittest
from ureport.tests.functional.poll_assertions import PollAssertions
from ureport.tests.functional.admin_helper import fill_form_and_submit, fill_form, rows_of_table_by_class
from ureport.tests.functional.splinter_wrapper import SplinterWrapper
from ureport.tests.functional.admin_base import AdminBase
from ureport.tests.functional.poll_base import PollBase
from ureport.tests.functional.clean_helper import login_as_admin, build_url, post


class PollFlowTest(unittest.TestCase,PollBase,PollAssertions):
    browser = SplinterWrapper.getBrowser()
    AdminBase.log_in_as_ureport()
    poll_id, question = PollBase.setup_poll(browser)
    opener = login_as_admin('ureport','ureport')

    @classmethod
    def setUpClass(cls):
        PollBase.start_poll(cls.browser,cls.poll_id)
        AdminBase.change_users_group("groupFT")

    @classmethod
    def cleanup(cls, url):
        SplinterWrapper.open(url)
        if cls.browser.is_element_present_by_id("action-toggle"):
            fill_form(cls.browser, {"action-toggle": True})
            fill_form_and_submit(cls.browser, {"action": "delete_selected"}, "index", True, True)
            cls.browser.find_by_value("Yes, I'm sure").first.click()

    @classmethod
    def delete_poll(cls):
        delete_url = build_url('/polls/%s/delete/' % cls.poll_id)
        post(cls.opener, delete_url)

    def tearDown(self):
        responses = PollBase.get_poll_responses_ids(self.browser, self.poll_id)
        for response in responses:
            delete_responses_url = build_url('/polls/responses/%s/delete/' % response.value)
            post(self.opener, delete_responses_url)

    @classmethod
    def tearDownClass(cls):
        cls.delete_poll()
        cls.cleanup("/admin/rapidsms/connection/")
        cls.cleanup("/admin/rapidsms/backend/")
        cls.cleanup("/admin/rapidsms/contact/")
        cls.cleanup("/admin/auth/group/")
        SplinterWrapper.open('/account/logout')

    def test_that_poll_status_changes_when_started(self):
        SplinterWrapper.open("/poll_status/%s" % self.poll_id)
        self.assert_that_poll_start_date_is_not_none(self.poll_id)

    def test_that_poll_can_be_sent_out_to_contacts(self):
         self.assert_that_poll_question_are_sent_out_to_contacts(1, 'What is your name')

    def test_that_polls_can_be_responded(self):
        SplinterWrapper.open('/router/console/')
        number_of_responses = len(rows_of_table_by_class(self.browser, "messages module"))
        self.respond_to_the_started_poll("0794339344", "yes")

        self.assert_that_number_of_responses_increase_by(number_of_responses, 1)

    def test_that_polls_can_be_reopen(self):
        SplinterWrapper.open("/view_poll/%s" % self.poll_id)
        PollBase.close_poll(self.poll_id)
        self.browser.find_link_by_text('Reopen Poll').first.click()

        self.assert_that_poll_end_date_is_none(self.poll_id)

    def test_that_admin_is_able_to_add_new_poll(self):
        SplinterWrapper.open('/mypolls/%s' % self.poll_id)
        self.assert_that_page_has_add_poll_button()

    def test_should_show_the_status_page(self):
        SplinterWrapper.open("/poll_status/%s" % self.poll_id)

        self.assertEqual(self.browser.is_element_present_by_id('poll-details'), True)
        self.assertTrue(self.poll_id in self.browser.find_by_id("poll-details").first.text)
        self.assertEqual(self.browser.find_by_id('contact-count').text, "1")
        self.assertEqual(self.browser.find_by_id('category-count').text, "3")
        self.assertEqual(self.browser.find_by_id('is-yesno').text, "yes")

    def test_admin_can_search_for_ureporter(self):
        group_name = "groupFT"
        self.respond_to_the_started_poll("0794339344", "yes")
        SplinterWrapper.open( '/reporter/')
        self.search_by_ureporter_group("%s" % group_name)
        self.assertEquals(True, self.browser.is_text_present("0794339344"))

    def search_by_ureporter_group(self, group_name):
        element_list_matching_option = self.browser.find_option_by_text(group_name)
        self.browser.select("groups", element_list_matching_option.first.value)
        self.browser.click_link_by_partial_text("Update")
        return self
