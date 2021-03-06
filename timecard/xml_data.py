import datetime as dt
import enum
import os
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set, Tuple
from xml.dom import minidom


class Activity(enum.Enum):
    Development = "DEV"
    Meetings = "MTG"
    Planning = "PLAN"
    Support = "SUPPORT"


class Project:
    def __init__(self, name: str, desc: str, uuidHex: str = None):
        self._validateName(name)
        self._name: str = name
        self._desc: str = desc
        if uuidHex is None:
            self._uuid: uuid.UUID = uuid.uuid4()
        else:
            self._uuid = uuid.UUID(uuidHex)

    def getName(self) -> str:
        return self._name

    def setName(self, name: str):
        self._validateName(name)
        self._name = name

    def getDesc(self) -> str:
        return self._desc

    def setDesc(self, desc: str):
        self._desc = desc

    def _validateName(self, name: str):
        if name.find('.') > 0:
            raise RuntimeError

    def __str__(self) -> str:
        return self._name

    @classmethod
    def fromDict(cls, data: dict):
        assert('name' in data)
        assert('desc' in data)
        assert('uuid' in data)
        assert(len(list(data.keys())) == 3)
        return cls(
            name=data['name'],
            desc=data['desc'],
            uuidHex=data['uuid']
        )

    def toDict(self) -> dict:
        return {
            "name": self._name,
            "desc": self._desc,
            "uuid": self._uuid.hex
        }


class Timeslot:
    def __init__(self, startTime: Optional[dt.datetime] = None,
                 endTime: Optional[dt.datetime] = None,
                 project: Optional[Project] = None,
                 activity: Optional[Activity] = None,
                 uuidHex: Optional[str] = None,
                 msg: str = ""):
        if not startTime:
            startTime = dt.datetime.now()
        self._start: dt.datetime = startTime
        self._end: Optional[dt.datetime] = endTime
        self._project: Optional[Project] = project
        self._activity: Optional[Activity] = activity
        self._msg: str = msg
        self._uuid: uuid.UUID = uuid.uuid4()
        if uuidHex:
            self._uuid = uuid.UUID(uuidHex)

    def __str__(self) -> str:
        return f'Timeslot({self._start}, {self._end}, {self._project}, {self._activity}, {self._uuid}, {self._msg})'

    def __repr__(self) -> str:
        return f'Timeslot({self._start}, {self._end}, {self._project}, {self._activity}, {self._uuid}, {self._msg})'

    def setProject(self, project: Project, activity: Activity):
        self._project = project
        self._activity = activity

    def getActivity(self) -> Optional[Activity]:
        return self._activity

    def getProject(self) -> Optional[Project]:
        return self._project

    def setEndTime(self, endTime: dt.datetime = None):
        if endTime is None:
            endTime = dt.datetime.now()
        self._end = endTime

    def getEndTime(self) -> Optional[dt.datetime]:
        return self._end

    def setStartTime(self, startTime: dt.datetime):
        self._start = startTime

    def getStartTime(self) -> dt.datetime:
        return self._start

    def getTotalTime(self) -> dt.timedelta:
        if not self._end:
            return dt.timedelta(0)
        return self._end - self._start

    def __lt__(self, other):
        if not isinstance(other, Timeslot):
            return False
        return self._start < other._start

    def getMsg(self) -> str:
        return self._msg

    def setMsg(self, msg: str):
        self._msg = msg

    def toDict(self) -> dict:
        retval = {
            "startTime": str(self._start.timestamp()),
            "endTime": None,
            "code": None,
            "uuid": self._uuid.hex,
            "msg": self._msg
        }
        if self._end:
            retval['endTime'] = str(self._end.timestamp())
        if self._project and self._activity:
            retval['code'] = self._project.getName() + "." + \
                self._activity.value
        return retval

    @classmethod
    def fromDict(cls, data: dict, projects: set):
        assert("startTime" in data)
        assert("endTime" in data)
        assert("code" in data)
        assert('uuid' in data)
        assert(data["code"] is not None)
        if "msg" not in data:
            data['msg'] = ""

        projectCode = data['code'].split('.')[0]
        project = next(
            project for project in projects if project.getName() == projectCode)
        activity = Activity(data['code'].split('.')[1])

        return cls(
            startTime=dt.datetime.fromtimestamp(float(data['startTime'])),
            endTime=dt.datetime.fromtimestamp(float(data['endTime'])),
            project=project,
            activity=activity,
            uuidHex=data['uuid'],
            msg=data['msg'])


class Timecard:
    PROJECTS_TAG = "projects"
    PROJECT_TAG = "project"
    TIMESLOTS_TAG = "timeslots"
    TIMESLOT_TAG = "timeslot"

    def __init__(self, filename: str):
        self._projects: Set[Project] = set()
        self._filename: str = filename
        self._activeSlot: Optional[Timeslot] = None
        self._timeslots: List[Timeslot] = []
        self.__dirty = True

        self.__enter__()

    def __enter__(self):
        # cred_obj = firebase_admin.credentials.Certificate('e4e-timecard-firebase-adminsdk-2tx0f-6d6696558b.json')
        # default_app = firebase_admin.initialize_app(cred_obj, {
        # 'databaseURL':'https://e4e-timecard-default-rtdb.firebaseio.com/'
        # })
        # ref = fdb.reference('/projects')
        # for key, value in ref.get().items():
        #     value
        #     self._projects.add(Project.fromDict())
        # ref = fdb.reference('/timeslots')
        # for key, value in ref.get().items()
        #     self._timeslots.append(Timeslot.fromDict(child.attrib, self._projects))

        # self.__dirty = False
        # return self
        if os.path.isfile(self._filename):
            tree = ET.parse(self._filename)
            root = tree.getroot()
            projectsLeaf = root.find(self.PROJECTS_TAG)
            timeslotsLeaf = root.find(self.TIMESLOTS_TAG)
            self._projects = set()
            self._timeslots = []
            if projectsLeaf:
                for child in projectsLeaf:
                    if child.tag == self.PROJECT_TAG:
                        # child.attrib.pop('key')
                        self._projects.add(Project.fromDict(child.attrib))

            if timeslotsLeaf:
                for child in timeslotsLeaf:
                    if child.tag == self.TIMESLOT_TAG:
                        # child.attrib.pop('key')
                        self._timeslots.append(Timeslot.fromDict(
                            child.attrib, self._projects))

            self.__dirty = False
            return self
        else:
            self._projects = set()
            self._timeslots = []
            self.__dirty = False
            return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.flush()

    def flush(self):
        tree = ET.Element('root')
        projectsLeaf = ET.SubElement(tree, self.PROJECTS_TAG)
        timeslotsLeaf = ET.SubElement(tree, self.TIMESLOTS_TAG)
        for project in self._projects:
            ET.SubElement(projectsLeaf, self.PROJECT_TAG,
                          attrib=project.toDict())
        for timeslot in self._timeslots:
            ET.SubElement(timeslotsLeaf, self.TIMESLOT_TAG,
                          attrib=timeslot.toDict())

        roughString = ET.tostring(tree, 'utf-8')
        reparsed = minidom.parseString(roughString)
        with open(self._filename, 'w') as f:
            f.write(reparsed.toprettyxml(indent="  "))
        self.__dirty = False
        # cred_obj = firebase_admin.credentials.Certificate('e4e-timecard-firebase-adminsdk-2tx0f-6d6696558b.json')
        # default_app = firebase_admin.initialize_app(cred_obj, {
        # 'databaseURL':'https://e4e-timecard-default-rtdb.firebaseio.com/'
        # })

    def close(self):
        self.__exit__(None, None, None)

    def open(self):
        self.__enter__()

    def addProject(self, project: Project):
        for existingProject in self._projects:
            assert(str(project) != str(existingProject))
        self._projects.add(project)
        self.__dirty = True

    def start(self, startTime: dt.datetime = None):
        if self._activeSlot is not None:
            raise RuntimeError
        self._activeSlot = Timeslot(startTime=startTime)
        self.__dirty = True

    def stop(self, project: Project, activity: Activity, endTime: dt.datetime = None, msg: str = ""):
        if project not in self._projects:
            raise RuntimeError("Project not registered")
        if self._activeSlot is None:
            raise RuntimeError("Timeslot not started")
        self._activeSlot.setProject(project, activity)
        self._activeSlot.setEndTime(endTime=endTime)
        self._activeSlot.setMsg(msg)
        self._timeslots.append(self._activeSlot)
        self._activeSlot = None
        self.__dirty = True
        self.flush()

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
            1] == weekNum]
        return timeslots

    def getProjects(self) -> Dict[str, Project]:
        return {project.getName(): project for project in self._projects}

    def getLastEntry(self) -> Timeslot:
        return self._timeslots[-1]

    