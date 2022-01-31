import datetime as dt
import enum
import uuid
from typing import Optional


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

