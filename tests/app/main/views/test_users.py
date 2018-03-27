# -*- coding: utf-8 -*-
import copy
from datetime import datetime

import mock
import pytest
from lxml import html

from ...helpers import LoggedInApplicationTest


@mock.patch('app.main.views.users.data_api_client')
class TestUsersView(LoggedInApplicationTest):
    @pytest.mark.parametrize("role,expected_code", [
        ("admin", 200),
        ("admin-ccs-category", 200),
        ("admin-ccs-sourcing", 403),
        ("admin-manager", 403),
        ("admin-framework-manager", 403),
    ])
    def test_find_users_page_is_only_accessible_to_specific_user_roles(self, data_api_client, role, expected_code):
        self.user_role = role
        data_api_client.get_user.return_value = self.load_example_listing("user_response")
        response = self.client.get('/admin/users?email_address=some@email.com')
        actual_code = response.status_code
        assert actual_code == expected_code, "Unexpected response {} for role {}".format(actual_code, role)

    def test_should_show_find_users_page(self, data_api_client):
        data_api_client.get_user.return_value = None
        response = self.client.get('/admin/users')
        page_html = response.get_data(as_text=True)
        document = html.fromstring(page_html)
        heading = document.xpath(
            '//header[@class="page-heading page-heading-without-breadcrumb"]//h1/text()')[0].strip()

        assert response.status_code == 200
        assert "Sorry, we couldn't find an account with that email address" not in page_html
        assert heading == "Find a user"

    def test_should_be_a_404_if_user_not_found(self, data_api_client):
        data_api_client.get_user.return_value = None
        response = self.client.get('/admin/users?email_address=some@email.com')
        assert response.status_code == 404

        document = html.fromstring(response.get_data(as_text=True))

        page_title = document.xpath(
            '//p[@class="banner-message"]//text()')[0].strip()
        assert page_title == "Sorry, we couldn't find an account with that email address"

        page_title = document.xpath(
            '//p[@class="summary-item-no-content"]//text()')[0].strip()
        assert page_title == "No users to show"

    def test_should_be_a_404_if_no_email_provided(self, data_api_client):
        data_api_client.get_user.return_value = None
        response = self.client.get('/admin/users?email_address=')
        assert response.status_code == 404

        document = html.fromstring(response.get_data(as_text=True))

        page_title = document.xpath(
            '//p[@class="banner-message"]//text()')[0].strip()
        assert page_title == "Sorry, we couldn't find an account with that email address"

        page_title = document.xpath(
            '//p[@class="summary-item-no-content"]//text()')[0].strip()
        assert page_title == "No users to show"

    def test_should_show_buyer_user(self, data_api_client):
        buyer = self.load_example_listing("user_response")
        buyer.pop('supplier', None)
        buyer['users']['role'] = 'buyer'
        data_api_client.get_user.return_value = buyer
        response = self.client.get('/admin/users?email_address=test.user@sme.com')
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))

        name = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[0].strip()
        assert name == "Test User"

        role = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[1].strip()
        assert role == "buyer"

        supplier = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[2].strip()
        assert supplier == ''

        last_login = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[3].strip()
        assert last_login == '09:33:53'

        last_login_day = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[4].strip()
        assert last_login_day == '23 July'

        last_password_changed = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[5].strip()
        assert last_password_changed == '12:46:01'

        last_password_changed_day = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[6].strip()
        assert last_password_changed_day == '29 June'

        locked = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[7].strip()
        assert locked == 'No'

        button = document.xpath(
            '//input[@class="button-destructive"]')[0].value
        assert button == 'Deactivate'

    def test_should_show_supplier_user(self, data_api_client):
        buyer = self.load_example_listing("user_response")
        data_api_client.get_user.return_value = buyer
        response = self.client.get('/admin/users?email_address=test.user@sme.com')
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))

        role = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/text()')[1].strip()
        assert role == "supplier"

        supplier = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/a/text()')[0].strip()
        assert supplier == 'SME Corp UK Limited'

        supplier_link = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/a')[0]
        assert supplier_link.attrib['href'] == '/admin/suppliers?supplier_id=1000'

    def test_should_show_unlock_button(self, data_api_client):
        buyer = self.load_example_listing("user_response")
        buyer['users']['locked'] = True

        data_api_client.get_user.return_value = buyer
        response = self.client.get('/admin/users?email_address=test.user@sme.com')
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))

        unlock_button = document.xpath(
            '//input[@class="button-secondary"]')[0].attrib['value']
        unlock_link = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/form')[0]
        return_link = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/form/input')[1]
        assert unlock_link.attrib['action'] == '/admin/suppliers/users/999/unlock'
        assert unlock_button == 'Unlock'
        assert return_link.attrib['value'] == '/admin/users?email_address=test.user%40sme.com'

    def test_should_show_deactivate_button(self, data_api_client):
        buyer = self.load_example_listing("user_response")

        data_api_client.get_user.return_value = buyer
        response = self.client.get('/admin/users?email_address=test.user@sme.com')
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))

        deactivate_button = document.xpath(
            '//input[@class="button-destructive"]')[0].attrib['value']
        deactivate_link = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/form')[0]
        return_link = document.xpath(
            '//tr[@class="summary-item-row"]//td/span/form/input')[1]
        assert deactivate_link.attrib['action'] == '/admin/suppliers/users/999/deactivate'
        assert deactivate_button == 'Deactivate'
        assert return_link.attrib['value'] == '/admin/users?email_address=test.user%40sme.com'


@mock.patch('app.main.views.users.data_api_client')
class TestUserListPage(LoggedInApplicationTest):
    user_role = 'admin-framework-manager'

    _framework = {
        'name': 'G-Cloud 9',
        'slug': 'g-cloud-9',
        'status': 'live'
    }

    @pytest.mark.parametrize("role,expected_code", [
        ("admin", 403),
        ("admin-ccs-category", 403),
        ("admin-ccs-sourcing", 403),
        ("admin-framework-manager", 200),
        ("admin-manager", 403),
    ])
    def test_get_user_lists_is_only_accessible_to_specific_user_roles(self, data_api_client, role, expected_code):
        self.user_role = role
        response = self.client.get("/admin/frameworks/g-cloud-9/users")
        actual_code = response.status_code
        assert actual_code == expected_code, "Unexpected response {} for role {}".format(actual_code, role)

    def test_get_user_lists_shows_framework_name_in_heading(self, data_api_client):
        data_api_client.get_framework.return_value = {"frameworks": self._framework}
        response = self.client.get("/admin/frameworks/g-cloud-9/users")
        document = html.fromstring(response.get_data(as_text=True))

        page_heading = document.xpath(
            '//h1//text()')[0].strip()
        assert page_heading == "Download supplier lists for G-Cloud 9"


@mock.patch('app.main.views.users.data_api_client')
class TestUsersExport(LoggedInApplicationTest):
    user_role = 'admin-framework-manager'
    _bad_statuses = ['coming', 'expired']

    _valid_framework = {
        'name': 'G-Cloud 7',
        'slug': 'g-cloud-7',
        'status': 'live'
    }

    _invalid_framework = {
        'name': 'G-Cloud 8',
        'slug': 'g-cloud-8',
        'status': 'coming'
    }

    _supplier_user = {
        "application_result": "fail",
        "application_status": "no_application",
        "declaration_status": "unstarted",
        "framework_agreement": False,
        "supplier_id": 1,
        "email address": "test.user@sme.com",
        "user_name": "Test User",
        "variations_agreed": "var1",
        "published_service_count": "0",
        "user_research_opted_in": True
    }

    @pytest.mark.parametrize("role, url_params, expected_code", [
        ("admin", "?user_research_opted_in=True", 200),
        ("admin", "?user_research_opted_in=False", 403),
        ("admin-ccs-category", "", 403),
        ("admin-ccs-sourcing", "", 403),
        ("admin-framework-manager", "?on_framework_only=True", 200),
        ("admin-framework-manager", "?on_framework_only=False", 200),
        ("admin-manager", "", 403),
    ])
    def test_supplier_csv_is_only_accessible_to_specific_user_roles(self, data_api_client, role,
                                                                    url_params, expected_code):
        self.user_role = role
        users = [self._supplier_user]
        data_api_client.export_users.return_value = {"users": copy.copy(users)}
        data_api_client.find_frameworks.return_value = {"frameworks": [self._valid_framework]}
        data_api_client.get_framework.return_value = {"frameworks": self._valid_framework}

        response = self.client.get(
            '/admin/frameworks/{}/users/download{}'.format(
                self._valid_framework['slug'],
                url_params
            ),
            data={'framework_slug': self._valid_framework['slug']}
        )

        assert response.status_code == expected_code

    def test_download_csv_for_all_framework_users(self, data_api_client):
        users = [self._supplier_user]

        data_api_client.export_users.return_value = {"users": copy.copy(users)}
        data_api_client.find_frameworks.return_value = {"frameworks": [self._valid_framework]}

        data_api_client.get_framework.return_value = {"frameworks": self._valid_framework}
        response = self.client.get(
            '/admin/frameworks/{}/users/download'.format(
                self._valid_framework['slug']
            ),

            data={'framework_slug': self._valid_framework['slug']}
        )
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert (response.headers['Content-Disposition'] ==
                'attachment;filename=g-cloud-7-suppliers-who-applied-or-started-application.csv')

        rows = [line.split(",") for line in response.get_data(as_text=True).splitlines()]

        assert len(rows) == len(users) + 1
        expected_headings = [
            'email address',
            'user_name',
            'supplier_id',
            'declaration_status',
            'application_status',
            'application_result',
            'framework_agreement',
            'variations_agreed',
            'published_service_count',
        ]

        assert rows[0] == expected_headings
        # All users returned from the API should appear in the CSV
        for index, user in enumerate(users):
            assert sorted(
                [str(val) for key, val in user.items() if key in expected_headings]
            ) == sorted(rows[index + 1])

    def test_download_csv_for_on_framework_only(self, data_api_client):
        users = [
            self._supplier_user,
            {
                "application_result": "pass",
                "application_status": "application",
                "declaration_status": "complete",
                "framework_agreement": False,
                "supplier_id": 2,
                "email address": "test.user@sme2.com",
                "user_name": "Test User 2",
                "variations_agreed": "",
                "published_service_count": 0,
            }
        ]

        data_api_client.export_users.return_value = {"users": copy.copy(users)}
        data_api_client.find_frameworks.return_value = {"frameworks": [self._valid_framework]}

        data_api_client.get_framework.return_value = {"frameworks": self._valid_framework}
        response = self.client.get(
            '/admin/frameworks/{}/users/download?on_framework_only=True'.format(
                self._valid_framework['slug'],
            ),
            data={'framework_slug': self._valid_framework['slug']}
        )
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert response.headers['Content-Disposition'] == 'attachment;filename=suppliers-on-g-cloud-7.csv'

        rows = [line.split(",") for line in response.get_data(as_text=True).splitlines()]

        assert len(rows) == 2
        assert rows[0] == ["email address", "user_name", "supplier_id"]
        # Only users with application_result = "pass" should appear in the CSV
        assert rows[1] == ["test.user@sme2.com", "Test User 2", "2"]


@mock.patch('app.main.views.users.data_api_client')
class TestBuyersExport(LoggedInApplicationTest):
    user_role = "admin-framework-manager"

    @pytest.mark.parametrize('user_role', ('admin', 'admin-framework-manager'))
    def test_csv_is_sorted_by_name(self, data_api_client, user_role):
        self.user_role = user_role
        data_api_client.find_users_iter.return_value = [
            {
                'id': 1,
                "name": "Zebedee",
                "emailAddress": "zebedee@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-04T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
            {
                'id': 2,
                "name": "Dougal",
                "emailAddress": "dougal@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-05T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
            {
                'id': 3,
                "name": "Brian",
                "emailAddress": "brian@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-06T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
            {
                'id': 4,
                "name": "Florence",
                "emailAddress": "florence@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-07T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
        ]

        response = self.client.get('/admin/users/download/buyers')

        assert response.status_code == 200

        rows = [line.split(",") for line in response.get_data(as_text=True).splitlines()]

        assert [row[1] for row in rows[1:5]] == ['Brian', 'Dougal', 'Florence', 'Zebedee']

    @pytest.mark.parametrize('user_role', ('admin', 'admin-framework-manager'))
    def test_response_is_a_csv(self, data_api_client, user_role):
        self.user_role = user_role
        data_api_client.find_users_iter.return_value = [
            {
                'id': 1,
                "name": "Chris",
                "emailAddress": "chris@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-04T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
        ]

        response = self.client.get('/admin/users/download/buyers')

        assert response.mimetype == 'text/csv'

    @pytest.mark.parametrize('user_role', ('admin', 'admin-framework-manager'))
    def test_filename_includes_a_timestamp(self, data_api_client, user_role):
        self.user_role = user_role
        with mock.patch('app.main.views.users.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime(2016, 8, 5, 16, 0, 0)
            data_api_client.find_users_iter.return_value = [
                {
                    'id': 1,
                    "name": "Chris",
                    "emailAddress": "chris@gov.uk",
                    "phoneNumber": "01234567891",
                    "createdAt": "2016-08-04T12:00:00.000000Z",
                },
            ]

            response = self.client.get('/admin/users/download/buyers')
            assert '2016-08-05-at-16-00-00' in response.headers['Content-Disposition']

    @pytest.mark.parametrize("role, expected_code", [
        ("admin", 200),
        ("admin-ccs-category", 403),
        ("admin-ccs-sourcing", 403),
        ("admin-framework-manager", 200),
        ("admin-manager", 403),
    ])
    def test_buyer_csv_is_only_accessible_to_specific_user_roles(self, data_api_client, role, expected_code):
        self.user_role = role
        data_api_client.find_users_iter.return_value = [
            {
                'id': 1,
                "name": "Chris",
                "emailAddress": "chris@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-04T12:00:00.000000Z",
            }
        ]

        response = self.client.get('/admin/users/download/buyers')
        actual_code = response.status_code
        assert actual_code == expected_code, "Unexpected response {} for role {}".format(actual_code, role)

    def test_response_data_has_correct_buyer_info_for_framework_manager_role(self, data_api_client):
        self.user_role = "admin-framework-manager"
        data_api_client.find_users_iter.return_value = [
            {
                'id': 1,
                "name": "Chris",
                "emailAddress": "chris@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-04T12:00:00.000000Z",
            },
            {
                'id': 2,
                "name": "Topher",
                "emailAddress": "topher@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-05T12:00:00.000000Z",
            },
        ]
        with mock.patch('app.main.views.users.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime(2016, 8, 5, 16, 0, 0)
            response = self.client.get('/admin/users/download/buyers')
        assert response.status_code == 200

        rows = [line.split(",") for line in response.get_data(as_text=True).splitlines()]

        assert response.headers['Content-Disposition'] == 'attachment;filename=all-buyers-on-2016-08-05-at-16-00-00.csv'
        assert len(rows) == 3
        assert rows == [
            ['email address', 'name'],
            ['chris@gov.uk', 'Chris'],
            ['topher@gov.uk', 'Topher'],
        ]

    def test_response_data_has_correct_buyer_info_for_admin_role(self, data_api_client):
        self.user_role = "admin"

        data_api_client.find_users_iter.return_value = [
            {
                'id': 1,
                "name": "Chris",
                "emailAddress": "chris@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-04T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
            {
                'id': 2,
                "name": "Topher",
                "emailAddress": "topher@gov.uk",
                "phoneNumber": "01234567891",
                "createdAt": "2016-08-05T12:00:00.000000Z",
                "userResearchOptedIn": False
            },
            {
                'id': 3,
                "name": "Winifred",
                "emailAddress": "winifred@gov.uk",
                "phoneNumber": "34567890987",
                "createdAt": "2016-08-02T12:00:00.000000Z",
                "userResearchOptedIn": True
            },
        ]
        with mock.patch('app.main.views.users.datetime') as mock_date:
            mock_date.utcnow.return_value = datetime(2016, 8, 5, 16, 0, 0)
            response = self.client.get('/admin/users/download/buyers')
        assert response.status_code == 200

        rows = [line.split(",") for line in response.get_data(as_text=True).splitlines()]

        assert (
            response.headers['Content-Disposition'] ==
            'attachment;filename=user-research-buyers-on-2016-08-05-at-16-00-00.csv'
        )
        assert len(rows) == 3
        assert rows == [
            ['email address', 'name'],
            ['chris@gov.uk', 'Chris'],
            ['winifred@gov.uk', 'Winifred'],
        ]


class TestUserResearchParticipantsExport(LoggedInApplicationTest):
    user_role = 'admin'

    _valid_framework = {
        'name': 'G-Cloud 7',
        'slug': 'g-cloud-7',
        'status': 'live'
    }

    _invalid_framework = {
        'name': 'G-Cloud 8',
        'slug': 'g-cloud-8',
        'status': 'coming'
    }

    @pytest.mark.parametrize(
        ('role', 'exists'),
        (
            ('admin', True),
            ('admin-ccs-category', False),
            ('admin-ccs-sourcing', False),
            ('admin-manager', False),
            ('admin-framework-manager', False)
        )
    )
    def test_correct_role_can_view_download_buyer_user_research_participants_link(self, role, exists):
        self.user_role = role

        xpath = "//a[@href='{href}'][normalize-space(text()) = '{selector_text}']".format(
            href='/admin/users/download/buyers',
            selector_text='Download list of potential user research participants'
        )

        response = self.client.get('/admin')
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))
        assert bool(document.xpath(xpath)) is exists

    @pytest.mark.parametrize(
        ('role', 'exists'),
        (
            ('admin', True),
            ('admin-ccs-category', False),
            ('admin-ccs-sourcing', False),
            ('admin-manager', False),
            ('admin-framework-manager', False)
        )
    )
    def test_correct_role_can_view_supplier_user_research_participants_link(self, role, exists):
        self.user_role = role

        xpath = "//a[@href='{href}'][normalize-space(text()) = '{selector_text}']".format(
            href='/admin/users/download/suppliers',
            selector_text='Download lists of potential user research participants'
        )

        response = self.client.get('/admin')
        assert response.status_code == 200

        document = html.fromstring(response.get_data(as_text=True))
        assert bool(document.xpath(xpath)) is exists

    @pytest.mark.parametrize(
        ('role', 'status_code'),
        (
            ('admin', 200),
            ('admin-ccs-category', 403),
            ('admin-ccs-sourcing', 403),
            ('admin-manager', 403),
            ('admin-framework-manager', 403)
        )
    )
    def test_correct_role_can_view_supplier_user_research_participants_page(self, role, status_code):
        self.user_role = role

        response = self.client.get('/admin/users/download/suppliers')
        assert response.status_code == status_code

    @mock.patch('app.main.views.users.data_api_client')
    def test_supplier_csvs_shown_for_valid_frameworks(self, data_api_client):
        data_api_client.find_frameworks.return_value = {'frameworks': [self._valid_framework, self._invalid_framework]}

        response = self.client.get('/admin/users/download/suppliers')
        assert response.status_code == 200

        text = response.get_data(as_text=True)
        document = html.fromstring(text)
        href_xpath = "//a[@href='/admin/frameworks/{}/users/download?user_research_opted_in=True']"

        assert document.xpath(href_xpath.format(self._valid_framework['slug']))
        assert 'User research participants on {}'.format(self._valid_framework['name']) in text

        assert not document.xpath(href_xpath.format(self._invalid_framework['slug']))
        assert not 'User research participants on {}'.format(self._invalid_framework['name']) in text

    @mock.patch('app.main.views.users.data_api_client')
    def test_supplier_csvs_shown_in_alphabetical_name_order(self, data_api_client):
        framework_1 = self._valid_framework.copy()
        framework_2 = self._valid_framework.copy()
        framework_3 = self._valid_framework.copy()
        framework_1['name'] = 'aframework_1'
        framework_2['name'] = 'bframework_1'
        framework_3['name'] = 'bframework_2'

        data_api_client.find_frameworks.return_value = {'frameworks': [framework_3, framework_1, framework_2]}

        response = self.client.get('/admin/users/download/suppliers')
        assert response.status_code == 200

        text = response.get_data(as_text=True)

        framework_1_link_text = 'User research participants on ' + framework_1['name']
        framework_2_link_text = 'User research participants on ' + framework_2['name']
        framework_3_link_text = 'User research participants on ' + framework_3['name']
        assert text.find(framework_1_link_text) < text.find(framework_2_link_text) < text.find(framework_3_link_text)
