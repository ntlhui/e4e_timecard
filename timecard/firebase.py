import datetime as dt
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.error import HTTPError
from uuid import UUID

import pyrebase
from pyrebase.pyrebase import Database, Firebase

from timecard.config import Config
from timecard.data import Activity, Project, Timeslot
from timecard.serializable import Serializable


class Timecard:
    config = {
        "apiKey": "AIzaSyCccHZTUqfdwluGLJVN_hBAyKLE3-h-EgU",
        "authDomain": "e4e-timecard.firebaseapp.com",
        "databaseURL": "https://e4e-timecard-default-rtdb.firebaseio.com/",
        "storageBucket": "e4e-timecard.appspot.com"
    }
    def __init__(self):
        self._projects: Set[Project] = set()
        self._activeSlot: Optional[Timeslot] = None
        self._timeslots: List[Timeslot] = []

        self.__firebase = pyrebase.initialize_app(self.config)
        self.__token = ''
        self.__db: Optional[Database] = None
        self.__dataRoot: Optional[Path] = None

        self.authenticate(username=Config.instance().email, password=Config.instance().password)

    def addProject(self, project: Project) -> None:
        if self.__dataRoot is None or self.__db is None:
            raise RuntimeError
        for existingProject in self._projects:
            assert(str(project) != str(existingProject))
        self._projects.add(project)

        data = {
            self.__dataRoot.joinpath('projects', project.uid.hex).as_posix():project.toDict()
        }
        self.__db.update(data, token=self.__token)

    def start(self, startTime: dt.datetime = None) -> None:
        if self._activeSlot is not None:
            raise RuntimeError
        self._activeSlot = Timeslot(startTime=startTime)

    def stop(self, project: Project, activity: Activity, endTime: dt.datetime = None, msg:str = '') -> None:
        if self.__db is None or self.__dataRoot is None:
            raise RuntimeError
        if project not in self._projects:
            raise RuntimeError("Project not registered")
        if self._activeSlot is None:
            raise RuntimeError("Timeslot not started")
        self._activeSlot.setProject(project, activity)
        self._activeSlot.setEndTime(endTime=endTime)
        self._activeSlot.setMsg(msg)
        self._timeslots.append(self._activeSlot)

        self.update_timeslot(self._activeSlot)

        self._activeSlot = None

    def update_timeslot(self, timeslot: Timeslot):
        data = {
            self.__dataRoot.joinpath('timeslots', timeslot.uid.hex).as_posix():timeslot.toDict()
        }
        self.__db.update(data, token=self.__token)
        


    def getDayTotals(self, date: dt.date = None) -> Dict[Tuple[Project, Activity], dt.timedelta]:
        if date is None:
            date = dt.date.today()

        timeslots = self.getDayEntries(date)
        report: Dict[Tuple[Project, Activity], dt.timedelta] = {}
        for ts in timeslots:
            ts_project = ts.getProject()
            ts_activity = ts.getActivity()
            if not ts_project or not ts_activity:
                continue
            if (ts_project, ts_activity) in report:
                report[(ts_project, ts_activity)
                       ] += ts.getTotalTime()
            else:
                report[(ts_project, ts_activity)] = ts.getTotalTime()
        return report


    def getWeekTotals(self, weekNum: int = None) -> Dict[Tuple[Project, Activity], dt.timedelta]:
        if weekNum is None:
            weekNum = dt.date.today().isocalendar()[1]

        timeslots = self.getWeekEntries(weekNum)
        report: Dict[Tuple[Project, Activity], dt.timedelta] = {}
        for ts in timeslots:
            ts_project = ts.getProject()
            ts_activity = ts.getActivity()
            if not ts_project or not ts_activity:
                continue
            if (ts_project, ts_activity) in report:
                report[(ts_project, ts_activity)
                       ] += ts.getTotalTime()
            else:
                report[(ts_project, ts_activity)] = ts.getTotalTime()
        return report

    def getDayEntries(self, date: dt.date = None) -> List[Timeslot]:
        if date is None:
            date = dt.date.today()
        timeslots = [
            ts for ts in self._timeslots if ts.getStartTime().date() == date]
        return timeslots

    def getWeekEntries(self, weekNum: int = None) -> List[Timeslot]:
        if weekNum is None:
            weekNum = dt.date.today().isocalendar()[1]

        timeslots = [ts for ts in self._timeslots if ts.getStartTime().date().isocalendar()[
            1] == weekNum and ts.getStartTime().year == dt.date.today().year]
        return timeslots

    def getProjects(self) -> Dict[str, Project]:
        return {project.name: project for project in self._projects}


    def getLastEntry(self) -> Timeslot:
        return sorted(self._timeslots, key=lambda x:x.getEndTime())[-1]

    def authenticate(self, username:str, password:str):
        auth = self.__firebase.auth()
        try:
            self.__user = auth.sign_in_with_email_and_password(username, password)
            assert(isinstance(self.__user, dict))
            self.__token = self.__user['idToken']
            self.__db = self.__firebase.database()
            self.__dataRoot = Path('data', self.__user['localId'])
            self.__setUpDb()
            self.__loadFromDb()
            threading.Thread(target=self.__autoRefresh, daemon=True).start()
        except HTTPError:
            raise Timecard.AuthenticationError
    class AuthenticationError(RuntimeError):
        pass

    def __setUpDb(self):
        if self.__dataRoot is None or self.__db is None:
            raise RuntimeError
        self.__db.update({
            self.__dataRoot.joinpath('initialized').as_posix(): True
        }, token=self.__token)
    
    def refreshAuth(self):
        if self.__user is None:
            raise RuntimeError
        auth = self.__firebase.auth()
        self.__user = auth.refresh(self.__user['refreshToken'])
        self.__token = self.__user['idToken']
        
    def __autoRefresh(self):
        while(1):
            time.sleep(1800)
            self.refreshAuth()

    def __loadFromDb(self):
        if self.__db is None or self.__dataRoot is None:
            raise RuntimeError
        objMap: Dict[UUID, Serializable] = {}

        response = self.__db.child(self.__dataRoot.as_posix()).get(token=self.__token)
        data = response.val()

        assert(isinstance(data, dict))

        if 'projects' in data:
            for id, project_data in data['projects'].items():
                project_object = Project.fromDict(project_data)
                objMap[project_object.uid] = project_object
                self._projects.add(project_object)
        if 'timeslots' in data:
            for id, timeslot_data in data['timeslots'].items():
                timeslot_object = Timeslot.fromDict(timeslot_data)
                objMap[timeslot_object.uid] = timeslot_object
                self._timeslots.append(timeslot_object)
        
        for timeslot in self._timeslots:
            timeslot.complete(objMap)

    def close(self):
        pass
