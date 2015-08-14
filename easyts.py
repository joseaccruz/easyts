import fcntl
import json
import os
import re
import sys
import urllib
from urlparse import parse_qs

import numpy
import tables

# global constants
STATUS_OK = "OK"
STATUS_NOK = "NOK"

TYPE_JSON = "text/json"
TYPE_PLAIN = "text/plain"

CFG_FNAME = "./config/easyts.cfg"

# append the current path so the local packages can be imported
SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(SCRIPT_PATH)

# import the local packages
from config import Config
import logger

# start the global 'log' and 'cfg' variables
cfg = Config(cfg_file=CFG_FNAME)
log   = logger.create_log(tofile=cfg.log_file, file_level=cfg.log_file_level, file_name=cfg.log_file_name,
                          toconsole=cfg.log_console, console_level=cfg.log_console_level,
                          tosyslog=cfg.log_syslog, syslog_level=cfg.log_syslog_level, syslog_address=cfg.log_syslog_address)

# log the entry call
log.debug("start LH Performance Data Service")


def err(msg):
    sys.stderr.write("%s\n" % msg)


class FileLock(object):

    def lock(self, fname, lkpath):
        self._fname = fname

        log.debug("locking %s" % fname)
        self._fp = open("%s/%s.lck" % (lkpath, os.path.basename(fname)), "w")
        fcntl.flock(self._fp, fcntl.LOCK_EX)
        log.debug("locked %s!" % self._fname)

    def unlock(self):
        fcntl.flock(self._fp, fcntl.LOCK_UN)
        self._fp.close()
        log.debug("unlocked %s!" % self._fname)

# for now we only care about "GET"


def get_params(env):
    ret = parse_qs(env['QUERY_STRING'])

    # we want only the first element of each parameter
    for k in ret.keys():
        ret[k] = urllib.unquote(ret[k][0])

    return ret


def get_int(s):
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def hdf5_add(fname, timestamp, data):
    hfile = tables.openFile(fname, "a")

    nodes = [n.name for n in hfile.listNodes('/')]

    for (k, v) in data.items():
        k = k.lower()
        if k in nodes:
            tb = hfile.getNode("/" + k)
        else:
            tb = hfile.createTable("/", k, {'t': tables.Int64Col(pos=1), 'v': tables.Float64Col(pos=2)})

        tb.append([(timestamp, v)])

    hfile.close()


def ets_parse(sets=None, ets=None):
    data = {}

    if ets is not None:
        try:
            data = json.loads(ets)
        except Exception as e:
            print "ERROR: ets_parse - %s; sets:%s; ets:%s" % (str(e), sets, ets)
            return None
    else:
        PC = re.compile("(?P<name>\w+)\=(?P<value>(\d+)(\.\d+)?)([^; ]*)(;+\d+(\.\d+)?)*")

        # some times the spaces are encoded as '+'. But we want spaces!
        sets = sets.replace('+', ' ')

        for s in sets.split():
            m = PC.match(s)

            if m is not None:
                data[m.group('name')] = float(m.group('value'))
            else:
                return None

    return data


def view_add(env, cfg):
    log.debug("request type 'add'")

    out = {}
    out['status'] = STATUS_NOK

    # get and check paremeters from querystring
    ps = get_params(env)

    sid = get_int(ps.get('sid', None))
    t   = get_int(ps.get('t', None))
    sets = ps.get('sets', None)
    ets  = ps.get('ets', None)

    if sid is None:
        out['msg'] = "The parameter 'sid' (session ID) is mandatory and must be an integer."

    elif t is None:
        out['msg'] = "The parameter 't' (event time) is mandatory and must be an integer."

    elif (sets is None) and (ets is None):
        out['msg'] = "One of the parameters 'sets' or 'ets' is mandatory and must contain valid data."

    else:
        data = ets_parse(sets, ets)

        if (data is None) or (data == {}):
            out['msg'] = "One of the parameters 'sets' or 'ets' must contain valid data."
        else:
            fname = "%s/%010d.h5" % (cfg.hdf5_path, sid)

            log.debug("add data to %s" % fname)

            fl = FileLock()
            fl.lock(fname, cfg.hdf5_lock_path)

            try:
                hdf5_add(fname, t, data)
                out['status'] = STATUS_OK

                log.debug("every thing's OK")
            except Exception as e:
                out['msg'] = "Unexpected error on add." + str(e)
                log.debug("Unexpected error on add." + str(e))

            fl.unlock()

    return (TYPE_JSON, json.dumps(out))


def view_get(env, cfg):
    log.debug("request type 'get'")

    out = {}
    out['status'] = STATUS_NOK

    # get and check paremeters from querystring
    ps = get_params(env)

    sid = get_int(ps.get('sid', None))
    ti  = get_int(ps.get('ti', None))
    tf  = get_int(ps.get('tf', None))
    m   = ps.get('m', "").lower()

    data_ok = False

    if (sid is None):
        out['msg'] = "The parameter 'sid' (session ID) is mandatory and must be an integer."

    elif (ti is None) or (tf is None):
        out['msg'] = "The parameters 'ti' (initial time) and 'tf' (final time) are mandatory and must be integers."

    elif (m == ""):
        out['msg'] = "The parameter 'm' (metric name) is mandatory."

    else:
        fname = "%s/%010d.h5" % (cfg.hdf5_path, sid)

        if os.path.isfile(fname):
            log.debug("get data from %s" % fname)

            fl = FileLock()
            fl.lock(fname, cfg.hdf5_lock_path)

            try:
                hfile = tables.openFile(fname, "r")

                try:
                    nodes = [n.name for n in hfile.listNodes('/')]

                    if m not in nodes:
                        out['msg'] = "Metric '%s' not found on table file '%s'." % (m, fname)
                    else:
                        tb = hfile.getNode("/" + m)

                        ts   = [r['t'] for r in tb.where('(t >= ti) & (t <= tf)')]
                        rows = [r['v'] for r in tb.where('(t >= ti) & (t <= tf)')]

                        data_ok = True

                        log.debug("data is OK")
                except Exception as e:
                    out['msg'] = "Unexpected error after openFile." + str(e)
                    log.debug("Unexpected error after openFile." + str(e))

                hfile.close()
            except Exception as e:
                out['msg'] = "Unexpected error on get." + str(e)
                log.debug("Unexpected error on get." + str(e))

            fl.unlock()

            if data_ok:
                nrows = len(rows)

                if nrows > cfg.max_pts:
                    step = int(nrows / cfg.max_pts)
                    k = [1.0 / min(step, 5)] * min(step, 5)
                    crows = numpy.convolve(rows, numpy.array(k), 'same')
                    data = (ts[::step], crows[::step].tolist())
                else:
                    data = (ts, rows)

                out['status'] = STATUS_OK
                out['data'] = data

                log.debug("every thing's OK")
        else:
            out['msg'] = "Data file '%s' not found." % fname

    return (TYPE_JSON, json.dumps(out))


def view_get_data(env, cfg):
    log.debug("request type 'get_data'")

    out = {}
    out['status'] = STATUS_NOK

    # get and check paremeters from querystring
    ps = get_params(env)

    sid = get_int(ps.get('sid', None))
    data_ok = False

    if (sid is None):
        out['msg'] = "The parameter 'sid' (session ID) is mandatory and must be an integer."

    else:
        fname = "%s/%010d.h5" % (cfg.hdf5_path, sid)

        if os.path.isfile(fname):
            log.debug("get data from %s" % fname)

            fl = FileLock()
            fl.lock(fname, cfg.hdf5_lock_path)

            try:
                hfile = tables.openFile(fname, "r")
                try:
                    nodes = [n.name for n in hfile.listNodes('/')]
                    data_ok = True

                    log.debug("data is OK")
                except Exception as e:
                    out['msg'] = "Unexpected error after openFile." + str(e)
                    log.debug("Unexpected error after openFile." + str(e))

                hfile.close()
            except Exception as e:
                out['msg'] = "Unexpected error on get." + str(e)
                log.debug("Unexpected error on get." + str(e))

            fl.unlock()

            if data_ok:
                data = nodes
                out['status'] = STATUS_OK
                out['data'] = data

                log.debug("every thing's OK")
        else:
            out['msg'] = "Data file '%s' not found." % fname

    return (TYPE_JSON, json.dumps(out))


def view_none(env, cfg):
    out = {}
    out['status'] = STATUS_NOK
    out['msg'] = "Unknown request: '%s'" % env['PATH_INFO']

    return (TYPE_JSON, json.dumps(out))


def view_debug(env, cfg):
    out = ""
    for k in env.keys():
        out += "'%s': '%s'\n" % (k, str(env.get(k, "NONE")))

    return (TYPE_PLAIN, out)


def router(path_info):
    url = {
        '/add': view_add,
        '/get': view_get,
        '/get_data': view_get_data,
        '/debug': view_debug
    }

    return url.get(path_info, view_none)


#
# WSGI entry point
#
def application(env, start_response):
    log.debug("new request")

    (type_name, output) = router(env['PATH_INFO'])(env, cfg)

    status = '200 OK'
    response_headers = [('Content-type', type_name),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    log.debug("response sent")

    logger.close_log()

    return [output]
