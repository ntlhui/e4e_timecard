from __future__ import annotations
import datetime as dt
import enum
import uuid
from typing import Any, Optional, Dict, Union
from uuid import UUID

import schema

from timecard.serializable import Serializable


class Activity(enum.Enum):
    Development = "DEV"
    Meetings = "MTG"
    Planning = "PLAN"
    Support = "SUPPORT"


class Project(Serializable):

    def __init__(self, name: str, desc: str, uid: UUID = None):
        self._validateName(name)
        self._name: str = name
        self._desc: str = desc
        if uid is None:
            self._uuid: uuid.UUID = uuid.uuid4()
        else:
            self._uuid = uid

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._validateName(name)
        self._name = name

    @property
    def desc(self) -> str:
        return self._desc

    @desc.setter
    def desc(self, desc: str):
        self._desc = desc

    @property
    def uid(self) -> UUID:
        return self._uuid

    def _validateName(self, name: str):
        if name.find('.') > 0:
            raise RuntimeError

    def __str__(self) -> str:
        return self._name

    SCHEMA = schema.Schema(
        {
            'name': str,
            'desc': str,
            'uuid': str
        }
    )

    @classmethod
    def fromDict(cls, data: dict) -> Project:
        cls.SCHEMA.validate(data)
        return Project(
            name=data['name'],
            desc=data['desc'],
            uid=UUID(data['uuid'])
        )


    def toDict(self) -> dict:
        return {
            "name": self._name,
            "desc": self._desc,
            "uuid": self._uuid.hex
        }

    def complete(self, objects: Dict[UUID, Serializable]):
        return

    def isComplete(self) -> bool:
        return True

class Timeslot (Serializable):
    def __init__(self, 
                 project: Optional[Union[Project, UUID]] = None,
                 startTime: Optional[dt.datetime] = None,
                 endTime: Optional[dt.datetime] = None,
                 activity: Optional[Activity] = None,
                 uid: UUID = None,
                 msg: str = ""):
        if not startTime:
            startTime = dt.datetime.now()
        self._start: dt.datetime = startTime
        self._end: Optional[dt.datetime] = endTime
        self._project = project
        self._activity: Optional[Activity] = activity
        self._msg: str = msg
        if uid:
            self._uuid = uid
        else:
            self._uuid = uuid.uuid4()

    @property
    def uid(self) -> UUID:
        return self._uuid

    def __str__(self) -> str:
        return f'Timeslot({self._start}, {self._end}, {self._project}, {self._activity}, {self._uuid}, {self._msg})'

    def __repr__(self) -> str:
        return f'Timeslot({self._start}, {self._end}, {self._project}, {self._activity}, {self._uuid}, {self._msg})'

    def setProject(self, project: Project, activity: Activity):
        self._project = project
        self._activity = activity

    def getActivity(self) -> Optional[Activity]:
        return self._activity

    def getProject(self) -> Union[Project, UUID]:
        return self._project

    def setEndTime(self, endTime: dt.datetime = None):
        if endTime is None:
            endTime = dt.datetime.now()
        if endTime <= self._start:
            raise RuntimeError("Slot cannot end before start")
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

    def toDict(self) -> Dict[str, Any]:
        if isinstance(self._project, UUID):
            project = self._project.hex
        elif isinstance(self._project, Project):
            project = self._project.uid.hex
        else:
            raise RuntimeError
        if self._activity is not None:
            activity = self._activity.value
        else:
            activity = None
        if self._end:
            endTime = int(self._end.timestamp())
        else:
            endTime = None
        retval = {
            "startTime": int(self._start.timestamp()),
            "endTime": endTime,
            "project": project,
            "uuid": self._uuid.hex,
            "msg": self._msg,
            'activity': activity
        }
        return retval

    SCHEMA = schema.Schema(
        {
            'startTime': int,
            'endTime': int,
            'project': str,
            'uuid': str,
            schema.Optional('msg'): str,
            'activity': str
        }
    )

    @classmethod
    def fromDict(cls, data: dict) -> Timeslot:
        cls.SCHEMA.validate(data)

        return Timeslot(
            startTime=dt.datetime.fromtimestamp(float(data['startTime'])),
            endTime=dt.datetime.fromtimestamp(float(data['endTime'])),
            project=UUID(data['project']),
            activity=Activity(data['activity']),
            uid=uuid.UUID(data['uuid']),
            msg=data['msg'])

    def complete(self, objects: Dict[UUID, Serializable]):
        if isinstance(self._project, UUID):
            project_obj = self._resolveObj(self._project, Project, objects)
            if project_obj is not None:
                self._project = project_obj

    def isComplete(self) -> bool:
        return isinstance(self._project, Project)


