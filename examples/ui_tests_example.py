from .. import actions_webdriver
import json
import requests
import time
import pprint
from .navigation import WrapClient
from ..data_storage import CodeTexts
from ..data_storage import DataStep
from ..data_storage import DomainUrls
from ..selectors import GeneralElements
from ..selectors import Navbar
import logging


logger = logging.getLogger(__name__)

pp = pprint.PrettyPrinter(indent=1)


class BasicAPI(object):
    def __init__(self, domain):
        self.domain = domain
        logger.info("!!!domain = %s" % self.domain)
        self.API_TOKEN_URL = self.domain + DomainUrls.API_TOKEN
        logger.info("api_token_url = %s" % self.API_TOKEN_URL)
        self.API_LESSONS_URL = self.domain + DomainUrls.API_LESSONS
        logger.info("api_lessons_url = %s" % self.API_LESSONS_URL)
        self.API_STEP_SOURCES = self.domain + DomainUrls.API_STEP_SOURCES
        self.API_INSTRUCTIONS = self.domain + DomainUrls.API_INSTRUCTIONS
        self.API_RUBRICS = self.domain + DomainUrls.API_RUBRICS
        self.API_COURSES = self.domain + DomainUrls.API_COURSES
        self.API_SECTIONS = self.domain + DomainUrls.API_SECTIONS
        self.API_UNITS = self.domain + DomainUrls.API_UNITS
        self.API_ENROLLMENTS = self.domain + DomainUrls.API_ENROLMENTS
        # get credentials
        if 'dev.' in self.domain:
            self.client_id = 'dev'
            self.client_secret = '512'
        elif 'release.' in self.domain:
            self.client_id = 'release'
            self.client_secret = '512'
        else:
            self.client_id = ''
            self.client_secret = ''
        logger.info('client_id = %s, client_secret = %s', self.client_id, self.client_secret)


class UserFactory(BasicAPI):
    def __init__(self, domain='http://127.0.0.1:8000', session=None, user_data=None):
        BasicAPI.__init__(self, domain)
        # setup name csrftoken and sessionid
        if 'dev.' in domain:
            domain_prefix = 'dev_'
        elif 'release.' in domain:
            domain_prefix = 'release_'
        else:
            domain_prefix = ''

        self.csrftoken = domain_prefix + 'csrftoken'
        self.sessionid = domain_prefix + 'sessionid'
        self.user_data = user_data
        #check if session is already exist
        if not session:
            ts = '%f' % time.time()
            api_url = self.domain + '/api/users'
            logger.info("api_url = %s" % api_url)
            session = requests.Session()
            session.get(self.domain, verify=False)
            # set necessary HTTP headers
            session.headers.update({'Referer': self.domain})
            session.headers.update({'X-CSRFToken': session.cookies.get_dict()[self.csrftoken]})
            user_rawdata = {
                'user': {
                    'first_name': 'robot' + ts,
                    'last_name': ts,
                    'email': '%s@stepic.org' % ts,
                    'password': ts
                }
            }
            response = session.post(api_url, json=user_rawdata)
            # persist user data and session
            self.user_data = json.loads(response.text)['users'][0]
            logger.info("New User Data = %s" % self.user_data)
            # logger.info("New User ID = %s" % self.user_data['id'])
            self.user_data['email'] = user_rawdata['user']['email']
            self.user_data['password'] = user_rawdata['user']['password']
            self.session = session
            logger.info('new_cookies are created= %s' % self.session.cookies.get_dict())
        else:
            self.user_data['email'] = user_data['email']
            self.user_data['password'] = user_data['password']
            self.session = session

    def login_user(self, driver):
        #auto-login new user
        driver.get(self.domain)
        #needs full load for page to avoid getting new cookies
        #wait for footer appearance
        actions_webdriver.find_element_by_css_and_scroll_to_view(driver, GeneralElements.PAGE_FOOTER)
        logger.debug("current sessionid = %s" % driver.get_cookie(self.sessionid))
        logger.debug("current csrftoken = %s" % driver.get_cookie(self.csrftoken))
        driver.delete_cookie(self.sessionid)
        logger.debug("try to delete session_id: session_id = %s" % driver.get_cookie(self.sessionid))
        driver.add_cookie({'name': self.sessionid, 'value': self.session.cookies.get_dict()[self.sessionid],
                           'path': '/', 'expiry': time.time() + 600})
                           # 'path': '/'})
        logger.debug("new sessionid = %s" % driver.get_cookie(self.sessionid))
        logger.debug("new csrftoken = %s" % driver.get_cookie(self.csrftoken))
        driver.get(self.domain)
        logger.debug("check if new sessionid is set= %s" % driver.get_cookie(self.sessionid))
        #check if login was successfull
        actions_webdriver.find_element_by_css(driver, Navbar.username)

    def delete_lesson_by_id(self, lesson_id):
        lesson_url = self.API_LESSONS_URL + '/' + str(lesson_id)
        self.session.delete(lesson_url)
        logger.info('Lesson id=' + str(lesson_id) + ' has been successfully deleted')

    def delete_lesson_by_url(self, lesson_url):
        lesson_id = WrapClient.get_lesson_id(lesson_url)
        return self.delete_lesson_by_id(lesson_id)

    def join_course(self, course_id):
        new_enrollment = {
            'enrollment': {
                'course': course_id
            }
        }
        response = self.session.post(self.API_ENROLLMENTS, json=new_enrollment)
        logger.info("Should be response 201: %s", response)



class LessonFactory(UserFactory):
    def __init__(self, domain='http://127.0.0.1:8000', session=None, user_data=None, is_comments_enabled=True):
        UserFactory.__init__(self, domain, session, user_data)
        new_lesson_data = {
           'lesson': {
                'title': 'lesson by test robot',
                # 'owner': self.user.user_data['id'],
                'owner': self.user_data['id'],
                'is_comments_enabled': is_comments_enabled
           }
        }
        logger.info('new lesson post data = %s', new_lesson_data)
        # persist lesson data
        response = self.session.post(self.API_LESSONS_URL, json=new_lesson_data)
        self.source = json.loads(response.text)
        logger.info('new lesson response = %s' % self.source)
        self.url = self.API_LESSONS_URL + '/' + str(self.source['lessons'][0]['id'])
        logger.debug('Lesson url = %s' % self.url)
        self.id = self.source['lessons'][0]['id']
        logger.debug('Lesson id = %s' % self.id)

    def create_text_step(self, step_position='1'):
        step_data = {
            'step-source': {
                'block': {
                    'name': 'text',
                    'text': 'This is New Theory Step<script>!</script>'
                },
                'lesson': self.id,
                'position': step_position
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_matching_step(self, step_position='1'):
        step_data = {
            'step-source': {
                'block': {
                    'name': 'matching',
                    'text': '<p>This is your new problem step (matching)!',
                    "video": None,
                    "animation": None,
                    "options": None,
                    "source": {
                        "preserve_firsts_order": True,
                        "pairs": [{
                            "first": "Sky",
                            "second": "Blue"
                            },
                            {
                            "first": "Sun",
                            "second": "Orange"
                            },
                            {
                            "first": "Grass",
                            "second": "Green"
                            }
                        ]
                    }
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_sorting_step(self, step_position='1'):
        step_data = {
            'step-source': {
                'block': {
                    'name': 'sorting',
                    'text': '<p>This is your new problem step (sorting)!',
                    "video": None,
                    "animation": None,
                    "options": None,
                    "source": {
                        "options": [
                            "One",
                            "Two",
                            "Three"
                        ]
                    }
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_math_step(self, step_position):
        default_source = {
                        'answer': '2*x+y/z',
                        'numerical_test': {
                            'z_re_min': '2',
                            'z_re_max': '3',
                            'z_im_min': '-1',
                            'z_im_max': '1',
                            'max_error': '1e-06',
                            'integer_only': False,
                        }
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'math',
                    'text': '<p>This is your new problem step (math)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_free_answer_step(self, step_position):
        step_data = {
            'step-source': {
                'block': {
                    'name': 'free-answer',
                    'text': '<p>This is your new problem step (free-answer)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': {
                        'manual_scoring': False,
                    }
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_free_answer_step_with_review(self, lesson_id, step_position, instruction_type, reviews_number):
        step_data = {
            'step-source': {
                'block': {
                    'name': 'free-answer',
                    'text': '<p>This is your new problem step (free-answer)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': {
                        'manual_scoring': False,
                    }
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = ', step_source)
        step_id = self.get_step_id(step_source)
        instruction_review = self.create_instruction_for_review(step_id, instruction_type, reviews_number)
        logger.info('new instruction= %s' % instruction_review)
        instruction_id = self.get_instruction_id(instruction_review)
        rubric_review = self.create_rubric_for_review(instruction_id)
        logger.info('new rubric review= %s' % rubric_review)
        return instruction_review

    def create_table_step(self, step_position):
        default_rows = [
            {
                'name': 'First row',
                'columns': [
                    {'choice': True}, {'choice': False}, {'choice': False}
                ]
            },
            {
                'name': 'Second row',
                'columns': [
                    {'choice': False}, {'choice': True}, {'choice': False}
                ]
            },
            {
                'name': 'Third row',
                'columns': [
                    {'choice': False}, {'choice': False}, {'choice': True}
                ],
            }
        ]
        default_columns = [{'name': "1st column"},
                           {'name': "2nd column"},
                           {'name': "3rd column"}]
        default_choice_options = [{'value': 'radio', 'label': 'Single choice per row'},
                                  {'value': 'checkbox', 'label': 'Multiple choices per row'}]
        step_data = {
            'step-source': {
                'block': {
                    'name': 'table',
                    'text': '<p>This is your new problem step (table)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': {
                        'description': "Rows:",
                        'columns': default_columns,
                        'rows': default_rows,
                        'options': {
                            'is_checkbox': False,
                            'is_randomize_rows': False,
                            'is_randomize_columns': False,
                            'sample_size': -1,
                        },
                        'is_always_correct': False
                    },
                    'choice_type_options': default_choice_options
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_string_step(self, step_position):
        default_source = {
            'pattern': 'text',
            'use_re': False,
            'match_substring': False,
            'case_sensitive': False,
            'code': '',
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'string',
                    'text': '<p>This is your new problem step (string)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_choice_step(self, step_position):
        default_options = [
            {'is_correct': False, 'text': 'Choice A'},
            {'is_correct': True, 'text': 'Choice B'},
            {'is_correct': False, 'text': 'Choice C'},
        ]
        default_source = {
            'is_multiple_choice': True,
            'is_always_correct': False,
            'preserve_order': False,
            'sample_size': 3,
            'is_html_enabled': True,
            'options': default_options,
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'choice',
                    'text': '<p>This is your new problem step (choice)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_number_step(self, step_position):
        default_source = {
            'options': [{
                'answer': '42',
                'max_error': '1',
            }]
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'number',
                    'text': '<p>This is your new problem step (number)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_dataset_step(self, step_position):
        default_source = {
            'code': DataStep.default_code,
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'dataset',
                    'text': '<p>This is your new problem step (dataset)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source

    def create_code_quiz_for_hints(self, step_position):
        default_source = {
            'code': CodeTexts.default_code_for_hints,
            'execution_time_limit': 5,
            'execution_memory_limit': 256,
            'samples_count': 1,
            'templates_data': '',
            'is_time_limit_scaled': False,
            'is_memory_limit_scaled': False,
            'manual_time_limits': [],
            'manual_memory_limits': [],
            'test_archive': [],
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'code',
                    'text': '<p>This is your new problem step (code)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source


    def create_code_quiz(self, step_position):
        default_source = {
            'code': CodeTexts.default_code,
            'execution_time_limit': 5,
            'execution_memory_limit': 256,
            'samples_count': 1,
            'templates_data': '',
            'is_time_limit_scaled': False,
            'is_memory_limit_scaled': False,
            'manual_time_limits': [],
            'manual_memory_limits': [],
            'test_archive': [],
        }
        step_data = {
            'step-source': {
                'block': {
                    'name': 'code',
                    'text': '<p>This is your new problem step (code)!',
                    'video': None,
                    'animation': None,
                    'options': None,
                    'source': default_source,
                },
                'position': step_position,
                'status': 'ready',
                'instruction_type': None,
                'instruction': None,
                'lesson': self.id,
            }
        }
        new_step = self.session.post(self.API_STEP_SOURCES, json=step_data)
        step_source = json.loads(new_step.text)
        logger.info('new step = %s' % step_source)
        return step_source


    def change_title_dev(self):
        api_lesson_url = 'https://dev.stepic.org/api/lessons/4600'
        new_lesson_data = {'lesson': {'title': 'new title22'}}
        json_answer = requests.put(api_lesson_url, headers=self.headers, data=json.dumps(new_lesson_data), verify=False).text
        resp_lesson = json.loads(json_answer)
        pp.pprint(resp_lesson)

    def delete(self):
        self.delete_lesson_by_id(self.id)

    def delete_lesson_by_id(self, lesson_id):
        lesson_url = self.API_LESSONS_URL + '/' + str(lesson_id)
        self.session.delete(lesson_url)
        logger.info('Lesson id=' + str(lesson_id) + ' has been successfully deleted')

    def delete_lesson_by_url(self, lesson_url):
        lesson_id = WrapClient.get_lesson_id(lesson_url)
        return self.delete_lesson_by_id(lesson_id)

    def get_lesson_id(self, lesson_source):
        lesson_id = lesson_source['lessons'][0]['id']
        pp.pprint('lesson_id = %s' % lesson_id)
        return lesson_id

    def get_step_url(self, lesson_id, step_position='1'):
        step_url = self.domain + "/lesson/-" + str(lesson_id) + "/step/" + str(step_position)
        logger.info("step_url = %s" % step_url)
        return step_url

    def get_step_url_for_reminder(self, step_url):
        new_step_url = step_url + "?is_solving_again=True"
        print ("step_url_for_reminder=", new_step_url)
        return new_step_url

    def get_step_id(self, step_source):
        return step_source['step-sources'][0]['id']

    def get_step_position(self, step_source):
        return step_source['step-sources'][0]['position']

    def get_instruction_id(self, instructions):
        return instructions['instructions'][0]['id']

    def create_instruction_for_review(self, step_source, instruction_type, reviews_number):
        instruction_data = {
            'instruction': {
                'min_reviews': reviews_number,
                'step': step_source,
                'strategy_type': instruction_type,
                'text': '',
                },
        }
        response = self.session.post(self.API_INSTRUCTIONS, json=instruction_data)
        new_instruction = json.loads(response.text)
        logger.info('new instruction = ', new_instruction)
        return new_instruction

    def create_rubric_for_review(self, instruction_id):
        position = 1
        text = 'Rubric 1'
        rubric_data = {
            'rubric': {
                'cost': 3,
                'instruction': instruction_id,
                'position': position,
                'text': text,
                },
        }
        response = self.session.post(self.API_RUBRICS, json=rubric_data)
        new_rubric = json.loads(response.text)
        logger.info('new rubric = %s' % new_rubric)
        return new_rubric

class CourseFactory(UserFactory):
    def __init__(self, domain='http://127.0.0.1:8000'):
        UserFactory.__init__(self, domain)
        new_course_data = {
            "course": {
                "grading_policy": "halved",
                "begin_date": None,
                "end_date": None,
                "soft_deadline": None,
                "hard_deadline": None,
                "grading_policy_source": "halved",
                "begin_date_source": None,
                "end_date_source": None,
                "soft_deadline_source": None,
                "hard_deadline_source": None,
                "progress_id": None,
                "has_progress": False,
                "discussions_count": 0,
                "title": "test course by robot",
                "summary": "Robot created this course",
                "workload": None,
                # "slug": "test-course-%s" % "",
                "slug": None,
                "cover": None,
                "certificate_footer": None,
                "certificate_cover_org": None,
                "total_units": None,
                "is_featured": False,
                "is_adaptive": False,
                "description": None,
                "intro": None,
                "target_audience": None,
                "course_format": None,
                "certificate": None,
                "requirements": None,
                "requirements_literature": None,
                "language": "en",
                "schedule_link": None,
                "schedule_long_link": None,
                "certificate_link": None,
                "certificate_distinction_link": None,
                "certificate_regular_link": None,
                "is_certificate_auto_issued": False,
                "certificate_regular_threshold": None,
                "certificate_distinction_threshold": None,
                "first_deadline": None,
                "last_deadline": None,
                "is_contest": False,
                "is_public": True,
                "owner_id": self.user_data['id'],
                "update_date": None,
                "sections_ids": [],
                "announcements_ids": [],
                "social_providers": [],
                "tags_ids": [],
                "progress": None,
                "discussion_proxy": None,
                "owner": self.user_data['id'],
                "enrollment": None,
                "last_step": None,
                "instructors": [],
                "tags": []}
        }

        logger.info('new course data = %s', new_course_data)
        # create course
        response = self.session.post(self.API_COURSES, json=new_course_data)
        self.source = json.loads(response.text)
        logger.info('new course response = %s' % self.source)
        logger.info('course id = %s' % self.source['courses'][0]['id'])
        self.id = self.source['courses'][0]['id']
        self.slug = self.source['courses'][0]['slug']
        self.url = domain + '/course/' + self.slug
        logger.debug("Course url = %s" % self.url)
        self.api_url = self.API_COURSES + '/' + str(self.id)

    def delete(self):
        logger.debug('cookies now = %s' % self.session.cookies.get_dict())
        self.delete_url = self.url + '/delete/'
        self.session.post(self.delete_url)
        r = self.session.get(self.url)
        if r.status_code == 404:
            logger.info('Course =' + self.url + ' has been successfully deleted')
        else:
            raise Warning("Course has not been deleted!")

    def add_lesson(self, section_id, lesson_id, position=1):
        new_unit_data = {
            "unit": {
                "begin_date": None,
                "begin_date_source": self.source['courses'][0]['begin_date_source'],
                "end_date": None,
                "end_date_source": self.source['courses'][0]['end_date_source'],
                "grading_policy": None,
                "grading_policy_source": self.source['courses'][0]['grading_policy_source'],
                "hard_deadline": None,
                "hard_deadline_source": self.source['courses'][0]['hard_deadline_source'],
                "has_progress": False,
                "is_active": False,
                "lesson": lesson_id,
                "lesson_id": None,
                "position": position,
                "progress": None,
                "progress_id": None,
                "section": section_id,
                "soft_deadline": None,
                "soft_deadline_source": self.source['courses'][0]['soft_deadline_source'],
            }
        }
        logger.debug('new unit data = ', new_unit_data)
        response = self.session.post(self.API_UNITS, json=new_unit_data)
        self.source = json.loads(response.text)
        logger.info('new unit source = %s' % self.source)
        self.units_id = self.source['units'][0]['id']
        logger.info('new unit id = %s' % self.units_id)


class SectionFactory(BasicAPI):

    def __init__(self, course, domain='http://127.0.0.1:8000', session=None, position=1):
        BasicAPI.__init__(self, domain)
        self.domain = domain
        self.session = session

        new_section_data = {
            "section": {
                "begin_date": None,
                "begin_date_source": course.source['courses'][0]['begin_date_source'],
                "course": course.id,
                "discounting_policy": "no_discount",
                "end_date": None,
                "end_date_source": course.source['courses'][0]['end_date_source'],
                "grading_policy": None,
                "grading_policy_source": course.source['courses'][0]['grading_policy_source'],
                "hard_deadline": None,
                "hard_deadline_source": course.source['courses'][0]['hard_deadline_source'],
                "has_progress": False,
                "position": position,
                "progress": None,
                "progress_id": None,
                "required_percent": 100,
                "required_section": None,
                "slug": None,
                "soft_deadline": None,
                "soft_deadline_source": course.source['courses'][0]['soft_deadline_source'],
                "title": "module by test robot %s" % position,
            }
        }
        logger.info('new section data = %s', new_section_data)
        # create section
        response = self.session.post(self.API_SECTIONS, json=new_section_data)
        self.source = json.loads(response.text)
        logger.info('new section source = %s' % self.source)
        self.id = self.source['sections'][0]['id']
        logger.info('new section id = %s' % self.id)
        self.API_SECTIONS = self.domain + DomainUrls.API_SECTIONS
        self.api_url = self.API_SECTIONS + '/' + str(self.id)

