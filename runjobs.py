import os
import json
import subprocess
from datetime import datetime
from typing import List


def writeoutput(output, d, keys):
    for key in keys:
        output.write(key)
        output.write(": ")
        output.write(str(d[key]))
        output.write("\n")
    output.flush()


def run_subprocess(cmd_args, timeout, stdout, **args):
    starttime = datetime.now()
    result = {
        "cmd": " ".join(cmd_args),
        "cwd": args["cwd"],
        "start_time": starttime.isoformat()
    }
    writeoutput(stdout, result, ["start_time", "cmd", "cwd"])
    stdout.write("-" * 80)
    stdout.write("\n")
    stdout.flush()

    subprocess1 = subprocess.Popen(cmd_args, stdout=stdout, **args)
    try:
        return_code = subprocess1.wait(timeout)
        result["return_code"] = return_code
    except subprocess.TimeoutExpired:
        result["return_code"] = None
        result["timeout"] = True
    except:
        result["return_code"] = None
        result["exception"] = True
    finally:
        endtime = datetime.now()

    result["time_spend"] = (endtime - starttime).total_seconds()

    stdout.flush()
    stdout.write("-" * 80)
    stdout.write("\n")
    stdout.flush()

    writeoutput(stdout, result, ["return_code", "time_spend"])
    return result


def getcwd(job, context):
    cwd = os.path.normpath(os.path.join(context["workdir"], job["workdir"] if "workdir" in job else "."))
    return cwd


def getstdoutfilepath(context, job, jobnumber):
    filepath = os.path.normpath(os.path.join(
        context["jobsfiledir"],
        job["stdout"] if "stdout" in job else "{0}-job-{1}-console.log".format(context["jobsfilename"], jobnumber)))
    return filepath


def run_job(job, context, jobnumber):
    job["number"] = jobnumber
    cmd_args = [job["command"]]
    cmd_args.extend(job["args"])
    cwd = getcwd(job, context)
    if not os.path.isdir(cwd):
        job["error"] = "Not a directory: {0}".format(cwd)
        return job

    timeout = int(job["timeout"]) if "timeout" in job else None
    stdoutfilepath = getstdoutfilepath(context, job, jobnumber)

    with open(stdoutfilepath, "w", encoding="utf-8") as output:
        run_result = run_subprocess(cmd_args, timeout, cwd=cwd, stdout=output, stderr=subprocess.STDOUT)

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


def runjobsfile(input_jobs_path):
    if not os.path.isfile(input_jobs_path):
        print("Cannot find job file: {0}".format(input_jobs_path))
        return

    jobs_file_dir = os.path.dirname(input_jobs_path)
    jobs_file_name = os.path.basename(input_jobs_path)
    context = {
        "jobsfilepath": input_jobs_path,
        "jobsfiledir": jobs_file_dir,
        "jobsfilename": jobs_file_name,
        "workdir": jobs_file_dir,
    }

    with open(input_jobs_path, "r", encoding="utf-8") as file:
        jobs = json.load(file)
    jobresults = runjobs(jobs, context)
    return jobresults

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('jobsfile', nargs='?', default="jobs.json", help="Path of the jobs JSON file. Default to jobs.json in cwd.")
    parser.add_argument('-o', '--output', dest="results", help="Path of the output result JSON file. Default to stdout.")
    args = parser.parse_args()

    input_jobs_path = os.path.normpath(os.path.join(os.getcwd(), args.jobsfile))
    jobresults = runjobsfile(input_jobs_path)

    if args.results:
        output_results_path = os.path.normpath(os.path.join(os.getcwd(), args.results))
        with open(output_results_path, "w", encoding="utf-8") as outfile:
            print(json.dumps(jobresults, indent=4, separators=(',', ': ')), file=outfile)
    else:
        print(json.dumps(jobresults, indent=4, separators=(',', ': ')))
