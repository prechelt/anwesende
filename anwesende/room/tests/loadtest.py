"""
A plain-Python (independent of Django) script that realizes 
a simple load test against an external instance of anwesende.
Exercises only the VisitView wrt the dummy_seat.
Reports to standard output.

Please do not run this too often, as it will strain the central redirect
service as well if your instance uses it in its SHORTURL_PREFIX.
"""
import datetime as dt
import multiprocessing as mp
import random
import re
import sys
import time
import typing as tg

import urllib3
import webtest as wt

usage_msg = """usage: python loadtest.py base_url numproclist numrequests
  e.g. python loadtest.py https://anwesende.eine-universitaet.de 4,8,16 100
  base_url:  real-life URL of the anwesende instance to be exercised
  numproclist:  comma-separated list of numbers of parallel request-making 
     processes to use. Each number leads to one sub-loadtest with a separate
     sub-report.
  numrequests:  number of requests made (as fast as possible) by each 
     request-making process.
     The example call leads to 4*100+8*100+16*100 = 2800 requests in total.
"""


def run(args: tg.Sequence[str]):
    try:
        assert len(sys.argv) == 1 + 3
        base_url = sys.argv[1]
        assert 'http' in base_url
        num_processes = list(map(int, sys.argv[2].split(',')))
        num_requests = int(sys.argv[3])
    except Exception:
        print(usage_msg)
        sys.exit(1)
    do_loadtest(base_url, num_processes, num_requests)


def do_loadtest(base_url: str, num_processes: tg.Sequence[int], num_requests: int):
    dummyseat_url = _get_dummyseat_url(base_url)
    print(f"Load Test: Make {num_requests} requests {num_processes} times in parallel")
    for nproc in num_processes:
        print(f"Making {num_requests} requests {nproc} times in parallel") 
        with mp.Pool(nproc) as pool:
            args = [(base_url, dummyseat_url, num_requests, idx) for idx in range(nproc)]
            durations = pool.starmap(subloadtest, args)
        fdurations = "/".join("%.1f" % dur for dur in durations)
        reqs_per_sec = (nproc * num_requests) / max(durations)
        print(f"  => {nproc} runs of {fdurations} secs ({reqs_per_sec:.1f} reqs/s)")


def subloadtest(base_url: str, seat_url: str, num_requests: int, subrun: int) -> float:
    time.sleep(random.random() * 0.1)  # avoid exact process tandems
    app = setup_app(base_url)
    starttime = dt.datetime.utcnow()
    for i in range(num_requests):
        make_1_visit(app, seat_url, i)
    endtime = dt.datetime.utcnow()
    return (endtime - starttime).total_seconds()


def make_1_visit(app, dummyseat_url, index: int):
    # visits are 20 or 80 mins long, spaced 1 min apart within each 'once' block
    visitpage = app.get(dummyseat_url)
    hours = (dt.datetime.utcnow().hour + index / 60) % 24
    minutes = index % 60
    data = dict(givenname="Load", familyname="Test",
                street_and_number="Str.1", zipcode="12345", town="Town",
                phone="+49 1234 1", email="load@test.de",
                present_from_dt="%02d:%02d" % (hours, minutes), 
                present_to_dt="%02d:%02d" % (hours + 1, (minutes + 20) % 60))
    _fill_with(visitpage.form, data)
    resp = visitpage.form.submit().follow()
    assert "thankyou" in resp.request.url


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
    regexp = r'<a href="(/v[0-9a-f]{5,15})">Beispiel'
    mm = re.search(regexp, homepage_html)
    assert mm, f"dummyseat URL '{regexp}' not found"
    return mm.group(1)


def _fill_with(form: wt.Form, data: dict):
    for k, v in data.items():
        form[k] = v


if __name__ == '__main__':
    run(sys.argv[1:])
