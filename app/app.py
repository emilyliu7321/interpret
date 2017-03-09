#!/usr/bin/env python3

import os
import sys
import tempfile
import re
import subprocess as sub

from flask import Flask, request, jsonify, send_file

from process import process_phillip, process_boxer


# Nonmerge constraints to introduce:
# - samepred: Arguments of a predicate cannot be merged.
# - sameid: Arguments of predicates with the same ID cannot be merged.
# - freqpred: Arguments of frequent predicates cannot be merged.
# - samename: None of the arguments of predicates with the same name can be
#     merged.
nonmerge = set(['sameid', 'freqpred'])

commands = {
    'tokenize':
      ['/interpret/ext/candc/bin/t',
       '--stdin'],
    'candc':
      ['/interpret/ext/candc/bin/soap_client',
       '--url', 'localhost:8888'],
    'boxer':
      ['/interpret/ext/candc/bin/boxer',
       '--stdin',
       '--semantics', 'tacitus',
       '--resolve', 'true',
       '--roles', 'verbnet'],
    'phillip':
      ['/interpret/ext/phillip/bin/phil',
       '-m', 'infer',
       '-k', '/interpret/kb/compiled',
       '-H',
       '-c', 'lhs=depth',
       '-c', 'ilp=weighted',
       '-c', 'sol=lpsolve']}


def run_commands(cmds, data):
    for cmd in cmds:
        try:
            p = sub.run(commands[cmd], input=data, stdout=sub.PIPE,
                        stderr=sub.PIPE)
            data = p.stdout
        except Exception as e:
            return None, 'Exception communicating with ' + cmd + '\n' + str(e)
    return data.decode(), None


app = Flask(__name__)


@app.route('/parse', methods=['POST'])
def parse():
    data = request.get_json(force=True)['s'].encode() + b'\n'
    out, err = run_commands(['tokenize', 'candc', 'boxer'], data)
    if err:
        return jsonify({'error': err})
    return jsonify({'parse': process_boxer(out, nonmerge)})


@app.route('/interpret', methods=['POST'])
def interpret():
    data = request.get_json(force=True)['s'].encode() + b'\n'

    out, err = run_commands(['tokenize', 'candc', 'boxer'], data)
    if err:
        return jsonify({'error': err})

    parse = process_boxer(out, nonmerge)

    data = parse.encode() + b'\n'
    out, err = run_commands(['phillip'], data)
    if err:
        return jsonify({'parse': parse,
                        'error': err})

    interpret = process_phillip(out)

    path = graph_output(out)

    if path == 'error':
        return jsonify({'parse': parse,
                        'interpret': interpret,
                        'error': 'Failed to generate proof graph.'})

    return jsonify({'parse': parse,
                    'interpret': interpret,
                    'graph': request.url_root + 'graph/' + path})


def graph_output(lines):
    with tempfile.NamedTemporaryFile(mode='w', prefix='') as temp:
        temp.writelines(lines)
        temp.flush()

        try:
            sub.run(['python', '/interpret/ext/phillip/tools/graphviz.py',
                     temp.name])
            sub.run(['dot', '-Tpdf', temp.name + '.dot',
                     '-o', temp.name + '.pdf'])
            os.remove(temp.name + '.dot')
            return re.sub('.+/', '', temp.name)
        except Exception as e:
            sys.stderr.write(str(e))
            return 'error'


@app.route('/graph/<graphname>', methods=['GET'])
def graph(graphname):
    return send_file(tempfile.gettempdir() + '/' + graphname + '.pdf')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
