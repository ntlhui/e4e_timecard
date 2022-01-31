import datetime as dt
import os
import xml.etree.ElementTree as ET
from typing import List, Optional, Set, Dict, Tuple
from xml.dom import minidom

from timecard.data import Activity, Project, Timeslot


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

