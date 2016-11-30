import sys
import re

from collections import defaultdict
from bs4 import BeautifulSoup


def process_phillip(lines):
    s = BeautifulSoup(lines, 'lxml')
    try:
        out = s.hypothesis.string.strip()
        out = out.replace('  ', ' ')
        out = out.replace(') ', ')\n   ')
        return out
    except:
        sys.stderr.write('Error processing Phillip output:\n' + lines)


# Pattern for parsing: id(sentence_id,..)
sent_id_pattern = re.compile('id\((.+),.+\)')

# Pattern for parsing: [word id list]:pred_name(args)
id_prop_args_pattern = re.compile('\[([^\]]*)\]:([^\[\(]+)(\((.+)\))?')

# Pattern for parsing: pred_name_base-postfix
prop_name_pattern = re.compile('(.+)-([nvarp])$')

prepositions = set([
    'abaft', 'aboard', 'about', 'above', 'absent', 'across', 'afore', 'after',
    'against', 'along', 'alongside', 'amid', 'amidst', 'among', 'amongst',
    'around', 'as', 'aside', 'astride', 'at', 'athwart', 'atop', 'barring',
    'before', 'behind', 'below', 'beneath', 'beside', 'besides', 'between',
    'betwixt', 'beyond', 'but', 'by', 'concerning', 'despite', 'during',
    'except', 'excluding', 'failing', 'following', 'for', 'from', 'given',
    'in', 'including', 'inside', 'into', 'lest', 'like', 'minus', 'modulo',
    'near', 'next', 'of', 'off', 'on', 'onto', 'opposite', 'out', 'outside',
    'over', 'pace', 'past', 'plus', 'pro', 'qua', 'regarding', 'round',
    'sans', 'save', 'since', 'than', 'through', 'throughout', 'till',
    'times', 'to', 'toward', 'towards', 'under', 'underneath', 'unlike',
    'until', 'up', 'upon', 'versus', 'via', 'vice', 'with', 'within',
    'without', 'worth'])


def process_boxer(lines, nonmerge=None):
    """Process the output of a Boxer parse to an FOL observation suitable
    for sending to the abductive reasoner. Add non-merge constraints, which
    can be one or more of:
    - samepred: Arguments of a predicate cannot be merged.
    - sameid: The first arguments of predicates with the same ID cannot be
        merged.
    - samename: None of the arguments of predicates with the same name can be
        merged.
    - freqpred: Arguments of frequent predicates cannot be merged."""

    if nonmerge is None:
        nonmerge = []

    out = ''

    id2args = defaultdict(list)

    for line in lines.splitlines():
        # Ignore comments.
        if line.startswith('%'):
            continue
        # Ignore lemmatized word list.
        if line[0].isdigit():
            continue

        if line.startswith('id('):
            try:
                sent_id = sent_id_pattern.match(line).group(1)
                out += '(O (name ' + sent_id + ')\n   (^'
                continue
            except AttributeError:
                sys.stderr.write('Error: Malformed sentence ID:\n')
                sys.stderr.write('  ' + line + '\n')
                break

        line = line.strip()
        if not line:
            continue

        # Parse propositions.
        prop_id_counter = 0
        pred2farg = defaultdict(list)
        id2prop = defaultdict(list)

        for prop in line.split(' & '):
            m = id_prop_args_pattern.match(prop)
            if not m:
                continue

            prop_id_counter += 1
            word_id_str = m.group(1) or 'ID' + str(prop_id_counter)

            # Normalize predicate name.
            prop_name = re.sub(r'[\s_:./]+', '-', m.group(2))

            # Skip predicates that don't contain letters or numbers.
            if not re.search('[a-zA-Z0-9]', prop_name):
                continue

            if prop_id_counter > 1:
                out += '\n     '

            # Boxer sometimes fails to mark prepositions; fix.
            if prop_name in prepositions:
                prop_name += '-p'

            # Set predicate name to which nonmerge constraints are applied.
            pred4nm = None
            m2 = prop_name_pattern.match(prop_name)
            if m2:
                # Predicate name contains postfix.
                pname = m2.group(1)
                postfix = m2.group(2)

                # Normalize POS postfixes.
                for k, v in [('n', 'nn'), ('v', 'vb'), ('a', 'adj'),
                             ('r', 'rb'), ('p', 'in')]:
                    if postfix == k:
                        postfix = v
                prop_name = pname + '-' + postfix
                if postfix == 'in':
                    # It can be subject to nonmerge constraints.
                    pred4nm = prop_name

            prop_args = ''
            if m.group(4):
                prop_args = ' ' + m.group(4).replace(',', ' ')

            # Write Henry representation of the proposition.
            out += ' (' + prop_name + prop_args + ' :1:' + \
                   sent_id + '-' + str(prop_id_counter) + ':[' + \
                   word_id_str + '])'

            if not m.group(4):
                # No arguments.
                continue

            if 'samepred' in nonmerge:
                # Arguments of the same predicate cannot be unified.
                out += ' (!=' + prop_args + ')'

            args = m.group(4).replace(',', ' ').split()
            first_arg = args[0]

            # Generate nonmerge constraints so that propositions with the
            # same word IDs cannot be unified.
            if 'sameid' in nonmerge:
                for id in word_id_str.split(','):
                    id2prop[id].append(first_arg)

            if 'samename' in nonmerge:
                id2args[prop_name].append(args)

            # Generate nonmerge constraints so that frequent predicates
            # cannot be unified.
            if 'freqpred' in nonmerge:
                if pred4nm and first_arg not in pred2farg[pred4nm]:
                    # Frequent predicates cannot be unified.
                    pred2farg[pred4nm].append(first_arg)

        if 'sameid' in nonmerge:
            for id, args in id2prop.items():
                if len(args) > 1:
                    out += ' (!= ' + ' '.join(args) + ')'

        if 'samename' in nonmerge:
            for id, args in id2args.items():
                if len(args) < 2:
                    continue
                arity = all(len(x) == len(args[0]) for x in args)
                if arity:
                    for neq in apply(zip, args):
                        out += ' (!= ' + ' '.join(neq) + ')'

        if 'freqpred' in nonmerge:
            for pred, args in pred2farg.items():
                if len(args) > 1:
                    out += ' (!= ' + ' '.join(args) + ')'

        out += '))\n'

    print(out)
    return out
