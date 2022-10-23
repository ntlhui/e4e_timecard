#!/usr/bin/env python3.7
import datetime as dt
import sys
import traceback
from pathlib import Path

import appdirs
import IPython

import timecard
from timecard.config import Config
from timecard.data import Activity, Project, Timeslot
from timecard.firebase import Timecard


class TimeCardCLI:
    def __init__(self):
        self.tc = Timecard()
        print("E4E Timecard Application")

        lut = {
            "help": self.printHelp,
            "exit": self.exit,
            "start": self.start,
            "stop": self.stop,
            "continue": self.cont,
            "report": self.report,
            "entries": self.entries,
            "cli": self.cli,
            "weekrpt": self.weekReport,
            "weekentries": self.weekEntries,
            "addproject": self.addProjectCmd,
            "listprojects": self.listProjectCmd,
        }

        self._run = True

        while self._run:
            userInput = input("> ")
            if userInput == '':
                continue
            try:
                lut[userInput.strip().lower().split()[0]](userInput)
            except Exception as e:
                print("Invalid input")
                print(e)
                print(traceback.format_exc())

    def cli(self, input):
        IPython.terminal.embed.embed()

    def __roundTime(self, time: dt.datetime) -> dt.datetime:
        nearestMinute = round(time.minute / 15) * 15
        hour = time.hour
        if nearestMinute == 60:
            nearestMinute = 0
            hour += 1
        if hour == 24:
            hour = 0
            time += dt.timedelta(days=1)
        return time.replace(hour=hour, minute=nearestMinute, second=0, microsecond=0)

    def __roundTimeDelta(self, time: dt.timedelta) -> dt.timedelta:
        return dt.timedelta(minutes=round(time.total_seconds() / 60 / 15) * 15)

    def entries(self, input):
        if len(input.strip().split()) == 1:
            date = dt.date.today()
        else:
            date = dt.datetime.strptime(
                input.strip().split()[1], "%Y.%m.%d").date()

        entries = self.tc.getDayEntries(date)
        if len(entries) == 0:
            print("No data to report")
            return

        timeFmt = "%I:%M %p"
        for timeSlot in sorted(entries):
            startTime = self.__roundTime(timeSlot.getStartTime())
            endTime = startTime + \
                self.__roundTimeDelta(timeSlot.getTotalTime())
            ts_proj = timeSlot.getProject()
            if ts_proj:
                ts_proj_name = ts_proj.name
            else:
                ts_proj_name = 'Unknown'
            ts_act = timeSlot.getActivity()
            if ts_act:
                ts_act_name = ts_act.value
            else:
                ts_act_name = 'Unknown'
            print("%s - %s: %s.%s" % (startTime.strftime(timeFmt), endTime.strftime(timeFmt),
                  ts_proj_name, ts_act_name))

    def report(self, input):
        if len(input.strip().split()) == 1:
            date = dt.date.today()
        else:
            date = dt.datetime.strptime(
                input.strip().split()[1], "%Y.%m.%d").date()
        report = self.tc.getDayTotals(date)
        totalHours = 0
        for projectTuple, interval in report.items():
            hours = interval.total_seconds() / 60 / 60
            print("%s.%s: %.2f" %
                  (projectTuple[0].name, projectTuple[1].value, hours))
            totalHours += hours

        print("Total: %.2f" % totalHours)

    def stop(self, input):
        if len(input.strip().split()) == 3:
            projectCode = input.strip().upper().split()[1].strip()
            activityCode = input.strip().upper().split()[2].strip()
            assert(projectCode in self.tc.getProjects())
            Activity(activityCode)
            self.tc.stop(self.tc.getProjects()[
                         projectCode], Activity(activityCode))
        else:
            projectCode = input.strip().upper().split()[1].strip()
            activityCode = input.strip().upper().split()[2].strip()
            dateCode = dt.datetime.strptime(input.strip().upper().split()[
                                            3].strip(), "%Y.%m.%d.%H.%M")
            assert(projectCode in self.tc.getProjects())
            Activity(activityCode)
            self.tc.stop(self.tc.getProjects()[projectCode], Activity(
                activityCode), endTime=dateCode)

    def start(self, input):
        if len(input.strip().split()) == 1:
            self.tc.start()
        else:
            dateCode = dt.datetime.strptime(input.strip().upper().split()[
                                            1].strip(), "%Y.%m.%d.%H.%M")
            self.tc.start(startTime=dateCode)

    def cont(self, input: str) -> None:
        today_entries = self.tc.getDayEntries()
        if len(today_entries) == 0:
            lastEntry = self.tc.getLastEntry()
            t = lastEntry.getEndTime()
        else:
            t = max([ts.getEndTime() for ts in self.tc.getDayEntries() if ts.getEndTime()])
        self.tc.start(t)

    def exit(self, *args):
        self.tc.close()
        self._run = False

    def listProjectCmd(self, *args):
        projects = self.tc.getProjects()
        for name, project in projects.items():
            print(project.name, project.desc)

    def addProjectCmd(self, cmd:str):
        cmd_tokens = cmd.split()
        if len(cmd_tokens) < 3:
            raise RuntimeError("usage: addproject [name] [description]")
        proj_name = cmd_tokens[1]
        proj_desc = cmd[cmd.find(proj_name) + len(proj_name) : ].strip()
        new_proj = Project(proj_name, proj_desc)
        self.tc.addProject(new_proj)
        print("New project added")

    def printHelp(self, *args):
        print("help - print this message")
        print("start - start an activity")
        print("        usage: start [DATETIME]")
        print("          where DATETIME is YYYY.MM.DD.HH.MM")
        print("end - end an activity")
        print("      usage: end PROJECT.ACTIVITY [DATETIME]")
        print("        where PROJECT is one of: ")
        for project in sorted(list(self.tc._projects), key=lambda x: x._name):
            print("            %s: %s" %
                  (project.name, project.desc))
        print("              DATETIME is YYYY.MM.DD.HH.MM")

        print("cmd - start command line")
        print("report - generate report")
        print("         usage: report [DATE]")
        print("           where DATE is YYYY.MM.DD")
        print("entries - generate entries")
        print("          usage: report [DATE]")
        print("            where DATE is YYYY.MM.DD")

    def weekReport(self, input):
        weeknum = dt.date.today().isocalendar()[1]
        if len(input.strip().split()) == 2:
            weeknum = int(input.strip().split()[1])
        report = self.tc.getWeekTotals(weeknum)
        totalHours = 0

        print("Report for Week %d\n" % (weeknum))
        projectDict = {}
        for projectTuple in report.keys():
            if projectTuple[0] in projectDict:
                projectDict[projectTuple[0]].append(projectTuple)
            else:
                projectDict[projectTuple[0]] = [projectTuple]

        meetingHours = 0
        for project in projectDict.keys():
            projectHours = 0
            for projectTuple in projectDict[project]:
                interval = report[projectTuple]
                hours = interval.total_seconds() / 60 / 60
                if projectTuple[1] == Activity.Meetings:
                    meetingHours += hours
                else:
                    projectHours += hours
                totalHours += hours
            print("%s: %.2f" % (project.name, projectHours))

        print("\nMeetings: %.2f" % (meetingHours))
        print("\nTotal: %.2f" % totalHours)

    def weekEntries(self, input):
        if len(input.strip().split()) == 1:
            weeknum = dt.date.today().isocalendar()[1]
        else:
            weeknum = int(input.strip().split()[1])

        entries = self.tc.getWeekEntries(weeknum)
        if len(entries) == 0:
            print("No data to report")
            return

        print("Entries for Week %d\n" % (weeknum))

        timeFmt = "%m/%d %I:%M %p"
        for timeSlot in sorted(entries):
            startTime = timeSlot.getStartTime()
            endTime = startTime + timeSlot.getTotalTime()
            ts_end = timeSlot.getEndTime()
            if not ts_end:
                continue
            hours = (ts_end - timeSlot.getStartTime()
                     ).total_seconds() / 60 / 60
            ts_proj = timeSlot.getProject()
            if ts_proj:
                ts_proj_name = ts_proj.name
            else:
                ts_proj_name = 'Unknown'
            ts_act = timeSlot.getActivity()
            if ts_act:
                ts_act_name = ts_act.value
            else:
                ts_act_name = 'Unknown'
            print("%s - %s: %.2f\t%s.%s" % (startTime.strftime(timeFmt), endTime.strftime(
                timeFmt), hours, ts_proj_name, ts_act_name))

def main():
    configPath = Path(appdirs.user_config_dir(timecard.__appname__), 'config.yaml')
    print(f'Config path is {configPath}')
    config = Config.instance(configPath=configPath)
    tc = TimeCardCLI()


if __name__ == '__main__':
    main()
