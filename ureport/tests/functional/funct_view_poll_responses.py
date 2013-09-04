from splinter import Browser
from ureport.tests.functional.poll_base import PollBase
from ureport.tests.functional.create_poll_for_tests import start_poll_queues_messages_in_table


class UreportTest(PollBase):
    fixtures = ['0004_migration_initial_data.json']

    def setUp(self):
        self.browser = Browser()
        self.poll, self.connections_list = start_poll_queues_messages_in_table()

    def tearDown(self):
        self.open('/account/logout')
        self.browser.quit()

    def test_that_poll_responses_are_shown_up_at_report_page(self):
        self.log_as_admin_and_visit('/')
        self.start_poll()
        self.respond_to_poll(self.poll)
        self.open('/polls/%s/report/' % self.poll.id)

        self.assert_that_question_is(self.poll.question)
        self.assert_the_number_of_participants_of_the_poll_is(self.poll.responses)

        location = self.get_first_poll_response_location(self.poll)
        self.assert_that_response_location_is(location)

        self.assert_that_number_of_responses_is(self.poll.responses)