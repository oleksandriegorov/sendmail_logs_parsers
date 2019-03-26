#!/usr/bin/env python

import re
import argparse

def is_queueid(logline,pattern):
    queueid_pattern=pattern
    res=re.match(queueid_pattern,logline)
    if res:
        return res[1]
    return False

def is_from(logline,pattern):
    from_pattern=pattern
    res=re.match(from_pattern,logline)
    if res:
        return res[1]
    return False

def is_rcpt(logline,pattern):
    rcpt_pattern=pattern
    res=re.match(rcpt_pattern,logline)
    if res:
        strip_braces=str.maketrans('','',"<>")
        return res[1].translate(strip_braces)

def get_logs(emailaddress,fromstore,tostore,qidstore):
    wanted_from = emailaddress
    wanted_queueids = []
    res=[]
    # Find unique queueids
    if wanted_from in fromstore:
        wanted_queueids += fromstore[wanted_from]
    if wanted_from in rcptstore:
        wanted_queueids += rcptstore[wanted_from]
    for queueid in set(wanted_queueids):
        for entry in qidstore[queueid]:
            res.append(entry)
    if res:
        return res
    return False

def store_data(what,where,context):
    if what in where:
        where[what].append(context)
        return True
    else:
        where[what] = []
        where[what].append(context)
        return True

    return False

def is_excluded(logline,pattern):
    internal_logs=pattern
    if re.match(internal_logs,logline):
        return True
    return False

parser=argparse.ArgumentParser()
parser.add_argument("-e","--emailaddress",help="email address to search in log file")
parser.add_argument("-f","--logfile",help="path to log file to parse")
args=parser.parse_args()
if not(args.emailaddress) or not(args.logfile):
    parser.print_help()
    exit(0)
wanted_from=args.emailaddress
maillogsfile=args.logfile
# Compile regex patterns once
queueid_pattern=re.compile('.*\s(\w{14}):\s.*')
from_pattern = re.compile('.*\sfrom=\<(\S+)\>,\s.*')
rcpt_pattern = re.compile('.*\sto=(\S+),\s.*')
internal_logs = re.compile('.*graylog\sjson:\s.*|.*\sMilter\s(add|insert.*):\sheader:\s.*')

maillogsbulk=[]
qidstore={'qid':['line1','line2']}
fromstore={'from':['qid1','qid2']}
rcptstore={'rcpt':['qid1','qid2']}
logline=''

with open(maillogsfile,'r') as fh:
    next_line=fh.readline()
    while next_line != '':
        if not(is_excluded(next_line,internal_logs)):
            maillogsbulk.append(next_line)
            queueid=is_queueid(next_line,queueid_pattern)
            if queueid:
                store_data(queueid,qidstore,next_line.strip())
                fromid=is_from(next_line,from_pattern)
                store_data(fromid,fromstore,queueid)
                rcptid=is_rcpt(next_line,rcpt_pattern)
                if rcptid:
                    if ',' in rcptid:
                        rcptsid=rcptid.split(',')
                    else:
                        rcptsid=[]
                        rcptsid.append(rcptid)
                    for rcpt in rcptsid:
                        store_data(rcpt,rcptstore,queueid)
        try:
            next_line=fh.readline()
        except:
            next_line='contains bad encoding'

wanted_logs=get_logs(wanted_from,fromstore,rcptstore,qidstore)
if wanted_logs:
    for line in wanted_logs:
        print(line)
