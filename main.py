#!/usr/bin/env python3
import os
import re
from xmindparser import xmind_to_dict
from transliterate import translit


IP_ADDR_REGEX = (
    '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.'
    '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)
RESULT_FNAME = 'objects.cfg'

hostnames = list()


def main(filename):
    dat = xmind_to_dict(filename)[0]['topic']
    title = _norm_name(dat.get('title'))
    with open(RESULT_FNAME, 'w') as f:
        write_hub_to_conf(
            f, host_name=title,
            real_name=dat.get('title'),
            parents=None
        )
        parse_node(
            f, topics=dat['topics'],
            parent_device=title
        )


def _norm_name(name: str, replreg=None):
    name = translit(name, language_code='ru', reversed=True)
    if replreg is None:
        return re.sub(pattern='\W{1,255}', repl='', string=name, flags=re.IGNORECASE)
    return replreg.sub('', name)


def _norm_display_name(name: str, replreg=None):
    if replreg is None:
        return re.sub(pattern='\W{1,255}', repl='', string=name, flags=re.IGNORECASE)
    return replreg.sub('', name)


def die(msg):
    print(msg)
    exit()


def get_first_ip_from_labels(labels: list):
    ip_pattern = re.compile(IP_ADDR_REGEX)
    for label in labels:
        if ip_pattern.match(label):
            return label


def check_unique_hostname(hname):
    global hostnames
    match_count = hostnames.count(hname)
    if match_count > 0:
        new_hname = "%s_%d" % (hname, match_count)
        hostnames.append(new_hname)
        return new_hname
    hostnames.append(hname)
    return hname


def write_hub_to_conf(f, host_name, real_name, parents):
    cmds = [
        "define host{",
        "\tuse				hub",
        "\tdisplay_name	%s" % _norm_display_name(real_name),
        "\thost_name		%s" % host_name,
        "\tparents			%s" % parents if parents is not None else None,
        "}\n"
    ]
    f.write('\n'.join(i for i in cmds if i))
    print(host_name, 'is written')


def write_node_to_conf(f, host_name, real_name, ip_addr, parents, ip_pattern=re.compile(IP_ADDR_REGEX)):
    if not ip_pattern.match(ip_addr):
        die('ip address %s not valid' % str(ip_addr))
    cmds = [
        "define host{",
        "\tuse				generic-switch",
        "\tdisplay_name	%s" % _norm_display_name(real_name),
        "\thost_name		%s" % host_name,
        "\taddress			%s" % ip_addr,
        "\tparents			%s" % parents if parents is not None else None,
        "}\n"
    ]
    f.write('\n'.join(i for i in cmds if i))
    print(host_name, 'is written')


def parse_node(f, topics: list, parent_device: str):
    for topic in topics:
        title = topic.get('title')
        labels = topic.get('labels')
        translit_label = _norm_name(title)
        translit_label = check_unique_hostname(translit_label)
        if labels:
            # парсим подписи
            ip_addr = get_first_ip_from_labels(labels)
            if ip_addr:
                write_node_to_conf(
                    f, host_name=translit_label,
                    ip_addr=ip_addr,
                    parents=parent_device,
                    real_name=title
                )
            else:
                print(title, 'has no ip')
                write_hub_to_conf(
                    f, host_name=translit_label,
                    real_name=title,
                    parents=parent_device
                )
        else:
            write_hub_to_conf(
                f, host_name=translit_label,
                real_name=title,
                parents=parent_device
            )

        topics = topic.get('topics')
        if topics:
            parse_node(
                f, topics=topics,
                parent_device=translit_label
            )


if __name__ == '__main__':
    fname = './КартаСети.xmind'
    if not os.path.isfile(fname):
        die('File %s not exists' % fname)
    main(fname)
