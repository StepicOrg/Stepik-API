#!/usr/bin/env python
import click
import json
import os
import re
import requests
import sys
import time

STEPIC_URL = "https://stepic.org/api"
APP_FOLDER = ".stepic"
CLIENT_FILE = APP_FOLDER + "/client_file"
ATTEMPT_FILE = APP_FOLDER + "/attempt_file"
file_manager = None
stepic_client = None


def exit_util(message):
    """
    Main program method 
    """
    click.secho(message, fg="red", bold=True)
    sys.exit(0)


class StepicClient:
    """
    Client to communicate with api
    """

    def __init__(self, file_manager):
        self.file_manager = file_manager
        data = self.file_manager.read_json(CLIENT_FILE)
        self.client_id = data['client_id']
        self.secret = data['client_secret']
        self.time_out_limit = 5
        self.headers = None
        self.check_user()
        self.update_client()

    def request(self, request_type, link, **kwargs):
        resp = None
        try:
            resp = requests.__dict__[request_type](link, **kwargs)
        except Exception as e:
            exit_util(e.args[0])
        if resp.status_code >= 400:
            exit_util("Something went wrong.")
        return resp

    def post_request(self, link, **kwargs):
        return self.request("post", link, **kwargs)

    def get_request(self, link, **kwargs):
        return self.request("get", link, **kwargs)

    def check_user(self):
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.secret)
        try:
            resp = requests.post('https://stepic.org/oauth2/token/',
                                 data={'grant_type': 'client_credentials'}, auth=auth)
            assert resp.status_code < 300
        except Exception:
            exit_util("Check yourClient id and Client secret.")

    def update_client(self):
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.secret)
        resp = self.post_request('https://stepic.org/oauth2/token/',
                             data={'grant_type': 'client_credentials'}, auth=auth)
        token = (resp.json())['access_token']
        self.headers = {'Authorization': 'Bearer ' + token, "content-type": "application/json"}

    def get_lesson(self, lesson_id):
        self.update_client()
        lesson = self.get_request(STEPIC_URL + "/lessons/{}".format(lesson_id), headers=self.headers)
        return lesson.json()

    def get_submission(self, attempt_id):
        self.update_client()
        resp = self.get_request(STEPIC_URL + "/submissions/{}".format(attempt_id), headers=self.headers)
        return resp.json()

    def get_attempt(self, data):
        resp = self.post_request(STEPIC_URL + "/attempts", data=data, headers=self.headers)
        return resp.json()

    def get_attempt_id(self, lesson, step_id):
        self.update_client()
        steps = None
        try:
            steps = lesson['lessons'][0]['steps']
        except Exception:
            exit_util("Didn't receive such lesson.")
        if len(steps) < step_id or step_id < 1:
            exit_util("Too few steps in the lesson.")
        data = self.file_manager.read_json(ATTEMPT_FILE)
        data['steps'] = steps
        data['current_position'] = step_id
        step_id = steps[step_id - 1]
        data['current_step'] = step_id
        self.file_manager.write_json(ATTEMPT_FILE, data)
        attempt = self.get_attempt(json.dumps({"attempt": {"step": str(step_id)}}))
        try:
            return attempt['attempts'][0]['id']
        except Exception:
            exit_util("Wrong attempt")
        return None

    def get_submit(self, url, data):
        self.update_client()
        resp = self.post_request(url, data=data, headers=self.headers)
        return resp.json()

    def get_step(self, step_id):
        step = self.get_request(STEPIC_URL + "/steps/{}".format(step_id), headers=self.headers)
        return step.json()

    def get_languages_list(self):
        self.update_client()
        data = self.file_manager.read_json(ATTEMPT_FILE)
        step = self.get_step(data['current_step'])
        block = step['steps'][0]['block']
        if block['name'] != 'code':
            exit_util('Set correct link.')
        languages = block['options']['code_templates']
        return [lang for lang in languages]

    def next_problem(self, problem_type):
        data = self.file_manager.read_json(ATTEMPT_FILE)
        steps = data['steps']
        position = data['current_position']
        for step_id in range(position + 1, len(steps) + 1):
            step = self.get_step(steps[step_id - 1])
            if step['steps'][0]['block']['name'] == problem_type:
                data['current_position'] = step_id
                attempt = self.get_attempt(json.dumps({"attempt": {"step": str(steps[step_id - 1])}}))
                data['attempt_id'] = attempt['attempts'][0]['id']
                self.file_manager.write_json(ATTEMPT_FILE, data)
                return True
        return False


class FileManager:
    """
    Local file manager
    """

    def __init__(self):
        self.home = os.path.expanduser("~")

    def create_dir(self, dir_name):
        dir_name = self.get_name(dir_name)
        try:
            os.mkdir(dir_name)
        except FileExistsError as e:
            return

    def get_name(self, filename):
        return os.path.join(self.home, filename)

    def read_file(self, filename):
        filename = self.get_name(filename)
        with open(filename, "r") as file:
            for line in file:
                yield line

    def write_to_file(self, filename, content):
        filename = self.get_name(filename)
        with open(filename, "w") as file:
            file.writelines(content)

    def write_json(self, filename, data):
        filename = self.get_name(filename)
        with open(filename, "w") as file:
            json.dump(data, file)

    def read_json(self, filename):
        filename = self.get_name(filename)
        return json.loads(open(filename).read())

    @staticmethod
    def is_local_file(filename):
        return os.path.isfile(filename)


class LanguageManager:

    programming_language = {'.cpp': 'c++11', '.c': 'c++11', '.py': 'python3',
                            '.java': 'java8', '.hs': 'haskel 7.10', '.sh': 'shell',
                            '.r': 'r', '.js': 'javascript', '.rs': 'rust', '.m': 'octave',
                            '.asm': 'asm32', '.clj': 'clojure', '.cs': 'mono c#'}

    def __init__(self):
        pass


def set_client(cid, secret):
    data = file_manager.read_json(CLIENT_FILE)
    if cid:
        data['client_id'] = cid
    if secret:
        data['client_secret'] = secret
    file_manager.write_json(CLIENT_FILE, data)


def get_lesson_id(problem_url):
    match = re.search(r'lesson/.*?(\d+)/', problem_url)
    if match is None:
        return match
    return match.group(1)


def get_step_id(problem_url):
    match = re.search(r'step/(\d+)', problem_url)
    if match is None:
        return 0
    return int(match.group(1))


def set_problem(problem_url):
    request_inf = stepic_client.get_request(problem_url)
    click.secho("\nSetting connection to the page..", bold=True)
    lesson_id = get_lesson_id(problem_url)
    step_id = get_step_id(problem_url)

    if lesson_id is None or not step_id:
        exit_util("The link is incorrect.")

    lesson = stepic_client.get_lesson(lesson_id)
    attempt_id = stepic_client.get_attempt_id(lesson, step_id)
    try:
        data = file_manager.read_json(ATTEMPT_FILE)
        data['attempt_id'] = attempt_id
        file_manager.write_json(ATTEMPT_FILE, data)
    except Exception as e:
        exit_util("You do not have permission to perform this action.")
    click.secho("Connecting completed!", fg="green", bold=True)


def evaluate(attempt_id):
    click.secho("Evaluating", bold=True, fg='white')
    time_out = 0.1
    while True:
        result = stepic_client.get_submission(attempt_id)
        status = result['submissions'][0]['status']
        hint = result['submissions'][0]['hint']
        if status != 'evaluation':
            break
        click.echo("..", nl=False)
        time.sleep(time_out)
        time_out += time_out
    click.echo("")
    click.secho("You solution is {}\n{}".format(status, hint), fg=['red', 'green'][status == 'correct'], bold=True)


def submit_code(code, lang=None):
    if not file_manager.is_local_file(code):
        exit_util("FIle {} not found".format(code))
    file_name = code
    code = "".join(open(code).readlines())
    url = STEPIC_URL + "/submissions"
    current_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    file = file_manager.read_json(ATTEMPT_FILE)
    attempt_id = None
    try:
        attempt_id = file['attempt_id']
    except Exception:
        pass
    if attempt_id is None:
        exit_util("Plz, set the problem link!")
    available_languages = stepic_client.get_languages_list()
    if lang in available_languages:
        language = lang
    else:
        language = LanguageManager().programming_language.get(os.path.splitext(file_name)[1])
    if language is None:
        exit_util("Doesn't correct extension for programme.")
    if language not in available_languages:
        exit_util("This language not available for current problem.")
    submission = {"submission":
                    {
                        "time": current_time,
                        "reply":
                            {
                                "code": code,
                                "language": language
                            },
                        "attempt": attempt_id
                    }
    }
    submit = stepic_client.get_submit(url, json.dumps(submission))
    evaluate(submit['submissions'][0]['id'])


@click.group()
@click.version_option()
def main():
    """
    Submitter 0.2
    Tools for submitting solutions to stepic.org
    """
    global file_manager
    file_manager = FileManager()
    try:
        file_manager.create_dir(APP_FOLDER)
    except OSError:
        exit_util("Can't do anything. Not enough rights to edit folders.")
    lines = 0
    try:
        data = file_manager.read_json(CLIENT_FILE)
        lines += 1
    except Exception:
        pass
    if lines < 1:
        file_manager.write_json(CLIENT_FILE, {"client_id": "id", "client_secret": "secret"})
        file_manager.write_json(ATTEMPT_FILE, {})


@main.command()
def init():
    """
    Initializes utility: entering client_id and client_secret
    """
    click.echo("Before using, create new Application on https://stepic.org/oauth2/applications/")
    click.secho("Client type - Confidential, Authorization grant type - Client credentials.", fg="red", bold=True)

    try:
        click.secho("Enter your Client id:", bold=True)
        new_client_id = input()
        click.secho("Enter your Client secret:", bold=True)
        new_client_secret = input()
        set_client(new_client_id, new_client_secret)
        global stepic_client
        stepic_client = StepicClient(FileManager())
    except Exception:
        exit_util("Enter right Client id and Client secret")
    click.secho("Submitter was inited successfully!", fg="green", bold=True)


@main.command()
@click.argument("link")
def problem(link=None):
    """
    Setting new problem as current target.
    """
    global stepic_client
    stepic_client = StepicClient(FileManager())

    if link is not None:
        set_problem(link)


@main.command()
@click.argument("solution")
@click.option("-l", help="language")
def submit(solution=None, l=None):
    """
    Submit a solution to stepic system.
    """
    global stepic_client
    stepic_client = StepicClient(FileManager())

    if solution is not None:
        submit_code(solution, l)


@main.command()
def lang():
    """
    Displays all available languages for current problem
    """

    global stepic_client
    stepic_client = StepicClient(FileManager())

    for lang in stepic_client.get_languages_list():
        click.secho("{} ".format(lang), bold=True, nl=False)


@main.command()
def next():
    """
    Switches to the next code challenge in the lesson
    """

    global stepic_client
    stepic_client = StepicClient(FileManager())
    message = "Stayed for current problem."
    color = "red"
    if stepic_client.next_problem("code"):
        message = "Switched to the next problem successful."
        color = "green"

    click.secho(message, bold=True, fg=color)
