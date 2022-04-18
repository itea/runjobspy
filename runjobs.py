import os
import sys
import json
import subprocess
from datetime import datetime
from typing import List, Dict


def run_subprocess(cmd_args, timeout, **args):
    starttime = datetime.now()
    result = {
        "cmd": " ".join(cmd_args),
        "cwd": args["cwd"],
        "start_time": starttime.isoformat()
    }
    subprocess1 = subprocess.Popen(cmd_args, **args)
    try:
        return_code = subprocess1.wait(timeout)
        endtime = datetime.now()
        result["return_code"] = return_code
    except subprocess.TimeoutExpired:
        result["return_code"] = None
        result["timeout"] = True
    except:
        result["return_code"] = None
        result["exception"] = True

    result["time_spend"] = (endtime - starttime).total_seconds()
    return result


def getcwd(job, context):
    cwd = os.path.normpath(os.path.join(context["workdir"], job["workdir"] if "workdir" in job else "."))
    return cwd


def getstdoutfilepath(context, job, jobnumber):
    filepath = os.path.normpath(os.path.join(context["jobsfiledir"], job["stdout"] if "stdout" in job else "job-{0}-console.log".format(jobnumber)))
    return filepath

def run_job(job, context, jobnumber):
    job["number"] = jobnumber
    cmd_args = [job["command"]]
    cmd_args.extend(job["args"])
    cwd = getcwd(job, context)
    if not os.path.isdir(cwd):
        job["result"] = {
            "error": "Not a directory: {}".format(cwd)
        }
        return job

    stdoutfilepath = getstdoutfilepath(context, job, jobnumber)

    with open(stdoutfilepath, "w", encoding="utf-8") as output:
        run_result = run_subprocess(cmd_args, job["timeout"], cwd=cwd, stdout=output, stderr=subprocess.STDOUT)

    job["result"] = run_result
    return job


def runjobs(jobs: List, context: dict):
    jobresults = []
    jobnumber = 0
    for job in jobs:
        result = run_job(job, context, jobnumber)
        jobresults.append(result)
        jobnumber += 1
    return jobresults


def main():
    input_jobs_filename = sys.argv[1] if len(sys.argv) > 1 else "jobs.json"
    input_jobs_path = os.path.normpath(os.path.join(os.getcwd(), input_jobs_filename))
    if not os.path.isfile(input_jobs_path):
        print("Cannot find job file: {0}".format(input_jobs_path))
        exit()

    jobs_file_dir = os.path.dirname(input_jobs_path)
    context = {
        "jobsfilepath": input_jobs_path,
        "jobsfiledir": jobs_file_dir,
        "workdir": jobs_file_dir,
    }

    with open(input_jobs_path, "r", encoding="utf-8") as file:
        jobs = json.load(file)
    jobresults = runjobs(jobs, context)

    print(json.dumps(jobresults, indent=4, separators=(',', ': ')))

if __name__ == "__main__":
    main()