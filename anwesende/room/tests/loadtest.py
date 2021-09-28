#!/bin/env python
"""
A plain-Python (independent of Django) script that realizes 
a simple load test against an external instance of anwesende.
Exercises only the VisitView wrt the dummy_seat.
Reports to standard output.

Setup for stand-alone use:
pip3 install webtest WSGIProxy2 requests

Please do not run this too often, as it will strain the central redirect
service as well if your instance uses it in its SHORTURL_PREFIX.

This script hardcodes some knowledge about anwensende proper:
- structure of the seat URLs, link text of the dummy seat on the homepage
- integer code for status_3g G_IMPFT (and assumes USE_STATUS_3G_FIELD is True).
"""
import collections
import datetime as dt
import multiprocessing as mp
import random
import re
import statistics
import sys
import time
import typing as tg

import urllib3
import webtest as wt

usage_msg = """usage: python loadtest.py base_url nproc numrequests_total
  e.g. python loadtest.py https://anwesende.eine-universitaet.de 8 100
  base_url:  real-life URL of the anwesende instance to be exercised
  nproc:  number of parallel processes created to execute the requests 
  numrequests_total:  number of requests made (as fast as possible) overall.
     Work is done in blocks of 10 requests, so the actual total can be larger. 
     The example call leads to two rounds of 8*10 calls, 160 requests in total.
  Reports request execution speed after each round.
"""

GRANULARITY = 10  # num requests per worker per round


def run(args: tg.Sequence[str]):
    try:
        assert len(sys.argv) == 1 + 3
        base_url = sys.argv[1]
        assert 'http' in base_url  # matches https as well
        nproc = int(sys.argv[2])
        numrequests_total = int(sys.argv[3])
    except Exception:
        print(usage_msg)
        sys.exit(1)
    do_loadtest(base_url, nproc, numrequests_total)


def do_loadtest(base_url: str, nproc: int, numrequests_total: int):
    dummyseat_url = _get_dummyseat_url(base_url)
    starttime = dt.datetime.now()
    firstname = starttime.strftime("%H:%M:%S")
    print("# Load Test: Make %d requests, using %d parallel subprocesses" %
          (numrequests_total, nproc))
    print("# Report subprocess request rates per round, then gross total after")
    print("# waiting for the slowest subprocess each time.")
    print("# (uses '%s' as visitors' Given Name)" % firstname)
    requestsN = 0
    C = nproc*60*GRANULARITY  # converts duration in secs into requests per minute
    with mp.Pool(nproc) as pool:
        args = [(base_url, firstname, dummyseat_url, GRANULARITY) for idx in range(nproc)]
        while requestsN < numrequests_total:
            statuscount = collections.Counter()
            pairs = pool.starmap(subloadtest, args)  # seconds per granularity
            s_per_G = [p['duration'] for p in pairs]
            for p in pairs:
                statuscount.update(p['status'])
            all_200 = (statuscount[200] == nproc*GRANULARITY) 
            del statuscount[200]
            requestsN += nproc*GRANULARITY
            print("%6d: %4.0f to %4.0f reqs/min, avg %4.0f  %s" %
                  (requestsN, C/max(s_per_G), C/min(s_per_G), 
                   C/statistics.mean(s_per_G),
                   "" if all_200 else str(dict(statuscount))))
    endtime = dt.datetime.now()
    duration = (endtime - starttime).total_seconds()
    print("GROSS TOTAL: %d requests in %.1f minutes: %.0f reqs/minute" %
          (requestsN, duration/60, requestsN/(duration/60)))


def subloadtest(base_url: str, firstname: str, seat_url: str, 
                num_requests: int) -> float:
    time.sleep(random.random() * 0.1)  # avoid exact process tandems
    app = setup_app(base_url)
    starttime = dt.datetime.utcnow()
    results = collections.Counter()
    for i in range(num_requests):
        try:
            status = make_1_visit(app, seat_url, firstname, i)
        except wt.app.AppError as ex:
            mm = re.match(r"^\D+(\d\d\d)", str(ex))  # find first status code
            status = int(mm.group(1))
        results[status] += 1  # count status
    endtime = dt.datetime.utcnow()
    return dict(status=results, duration=(endtime - starttime).total_seconds())


def make_1_visit(app, seat_url: str, firstname: str, index: int) -> int:
    # visits are 20 or 80 mins long, spaced 1 min apart within each 'once' block
    visitpage = app.get(seat_url)
    if visitpage.status_int != 200:
        return visitpage.status_int
    hours = (dt.datetime.utcnow().hour + index / 60) % 24
    minutes = index % 60
    firstname_digits = firstname.replace(":", "")  # assumes firstname is "10:35:07" etc.
    data = dict(givenname=firstname, familyname="Loadtest",
                street_and_number="Str.1", zipcode="12345", town="Town",
                phone="+49 1234 1", 
                email=f"load{firstname_digits}@test.de",
                status_3g=22,  # G_IMPFT
                present_from_dt="%02d:%02d" % (hours, minutes), 
                present_to_dt="%02d:%02d" % (hours + 1, (minutes + 20) % 60))
    _fill_with(visitpage.form, data)
    resp = visitpage.form.submit()
    if resp.status_int == 200:
        # print("##########\m", visitpage.html.find('form').prettify())
        return 409  # form has failed
    elif resp.status_int == 302:
        pass  # the expected redirect
    else:
        return resp.status_int  # this is unlikely to happen
    resp = resp.follow()
    assert "thankyou" in resp.request.url
    return resp.status_code


def setup_app(base_url: str) -> wt.TestApp:
    # We use the requests 2.24 HTTP library, which internally uses urllib3 1.25.
    # These implicitly ought to employ certifi and provide a proper bundle
    # of root certificates, but for some reason, I nevertheless received 
    # "urllib3\connectionpool.py:988: InsecureRequestWarning: Unverified 
    #  HTTPS request is being made".
    # It is not obvious how to repair this properly, because
    # a) it should not really happen in the first place and
    # b) I have no direct access to the setup, because that is done by webtest.
    # On the other hand, we have no security concerns here -- it's a load test!
    # So we turn off these warnings in urllib3 globally instead. Works.
    app = wt.TestApp(f"{base_url}#requests")  # use 'requests' HTTP library
    urllib3.disable_warnings()  # our certificate store may be insufficient
    return app


def _get_dummyseat_url(base_url: str) -> str:
    app = setup_app(base_url)
    homepage_html = app.get("/").text
    # contains e.g.:  (<a href="/Sc2178e95a1">Beispiel<sup>*</sup></a>)
    regexp = r'<a href="(/S[0-9a-f]{5,15})">Beispiel'
    mm = re.search(regexp, homepage_html)
    assert mm, f"dummyseat URL '{regexp}' not found"
    return mm.group(1)


def _fill_with(form: wt.Form, data: dict):
    for k, v in data.items():
        form[k] = v


if __name__ == '__main__':
    run(sys.argv[1:])
