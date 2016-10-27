#!/usr/bin/env python3

import subprocess as sub

from flask import Flask, request, jsonify

from process import process_boxer

# Parameters

# Nonmerge constraints to introduce:
# - samepred: Arguments of a predicate cannot be merged.
# - sameid: arguments of predicates with the same ID cannot be merged.
# - freqpred: Arguments of frequent predicates cannot be merged.
nonmerge = ['samepred', 'sameid', 'freqpred']


app = Flask(__name__)

@app.route('/parse', methods=['POST'])
def parse():
    commands = [['/interpret/ext/candc/bin/t',
                 '--stdin'],
                ['/interpret/ext/candc/bin/soap_client',
                 '--url', 'localhost:8888'],
                ['/interpret/ext/candc/bin/boxer',
                 '--stdin',
                 '--semantics', 'tacitus',
                 '--resolve', 'true']]

    data = request.get_json(force=True)['s'].encode() + b'\n'

    for cmd in commands:
        try:
            p = sub.run(cmd, input=data, stdout=sub.PIPE,
                        stderr=sub.PIPE)
            data = p.stdout
        except Exception as e:
            return jsonify({'error': 'Exception communicating with ' + cmd +
                            '\n' + str(e)})
            break

    return jsonify({'parse': process_boxer(data.decode(), nonmerge)})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
