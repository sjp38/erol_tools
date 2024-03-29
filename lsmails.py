#!/usr/bin/env python3

import argparse
import datetime
import subprocess

class Mail:
    gitid = None
    date = None
    subject = None
    orig_subject = None
    tags = None
    series = None

    def __init__(self, gitid, date, subject_fields):
        self.gitid = gitid
        self.date = date
        self.subject = ' '.join(subject_fields)
        self.orig_subject = self.subject
        self.tags = []

        re_depth = 0
        for f in subject_fields:
            if f.lower() == 're:':
                re_depth += 1
            else:
                break
        if re_depth > 0:
            self.tags.append('reply')
            self.orig_subject = ' '.join(subject_fields[re_depth:])

        if self.orig_subject[0] == '[':
            tag = self.orig_subject[1:].split(']')[0].strip().lower()
            self.tags += tag.split()

            series = self.tags[-1].split('/')
            if series[0].isdigit() and series[1].isdigit():
                self.series = [int(x) for x in series]

def valid_to_show(mail):
    has_tag = False
    if filters:
        for tag in filters:
            if tag in mail.tags:
                has_tag = True
                break
        if has_tag:
            return False

    if tags:
        for tag in tags:
            if tag in mail.tags:
                has_tag = True
                break
        if not has_tag:
            return False
    return True

def pr_line_wrap(line, len_indent, nr_cols):
    words = line.split(' ')
    line = ""
    words_to_print = []
    for w in words:
        words_to_print.append(w)
        line_len = len(' '.join(words_to_print))
        if line_len > nr_cols:
            if len(words_to_print) == 1:
                print(words_to_print[0])
            else:
                print(' '.join(words_to_print[:-1]))
                words_to_print = [' ' * len_indent + words_to_print[-1]]
    print(' '.join(words_to_print))

def show_mail(mail):
    cmd = ["git", "--git-dir=%s" % mdir,
            'show', '%s:m' % mail.gitid]
    mail_content = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode(
            'utf-8').strip()
    if show_lore_link:
        for line in mail_content.split('\n'):
            fields = line.split()
            if len(fields) == 2 and fields[0].lower() == 'message-id:':
                print("https://lore.kernel.org/r/%s\n" % fields[1][1:-1])
                break
    print(mail_content)

def show_mails(mails):
    for idx, mail in enumerate(mails_to_show):
        indent = ""
        if (mail.series and mail.series[0] > 0) or ('reply' in mail.tags):
            indent = "    "

        # date: <YYYY-MM-DD>T<HH>:<MM>:<SS>+<UTC offset>
        #       e.g., 2019-09-30T09:57:38+08:00
        date = '/'.join(mail.date.split('T')[0].split('-')[1:])
        line_prefix = "[%04d] %s " % (idx, date)
        if pr_git_id:
            line_prefix += "%s " % mail.gitid
        line = "%s%s%s" % (line_prefix, indent, mail.subject)
        if 'reply' in mail.tags:
            line += " (%d replies)" % duplicate_re_map[mail.orig_subject]
        pr_line_wrap(line, len(line_prefix) + len(indent), nr_cols_in_line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--since', metavar='since', type=str,
            help='Show mails more recent than a specific date.')
    parser.add_argument('--tags', metavar='tag', type=str, nargs='+',
            help='Show mails having the tags (e.g., patch, rfc, reply, ...) only.')
    parser.add_argument('--filters', metavar='tag', type=str, nargs='+',
            help='Filter out mails having the tags.')
    parser.add_argument('--mdir', metavar='mdir', type=str,
            help='Directory containing the mail data.')
    parser.add_argument('--cols', metavar='cols', type=int,
            help='Number of columns for each line.')
    parser.add_argument('--gitid', action='store_true',
            help='Print git id of each mail')
    parser.add_argument('content', metavar='idx', type=int, nargs='?',
            help='Show content of specific mail.')
    parser.add_argument('--lore', action='store_true',
            help='Print lore link for the <content> mail.')

    args = parser.parse_args()
    since = args.since
    tags = args.tags
    filters = args.filters
    mdir = args.mdir
    nr_cols_in_line = args.cols
    pr_git_id = args.gitid
    idx_of_mail = args.content
    show_lore_link = args.lore

    if show_lore_link and idx_of_mail == None:
        print("--lore option works with content argument only.\n")
        parser.print_help()
        exit(1)

    if not since:
        since_date = datetime.datetime.now() - datetime.timedelta(days=3)
        since = "%s-%s-%s" % (since_date.year, since_date.month,
                since_date.day)

    if not mdir:
        mdir = "./.git"

    if not nr_cols_in_line:
        nr_cols_in_line = 130

    cmd = ["git", "--git-dir=%s" % mdir, "log",
            '--date=iso-strict', '--pretty=%h %ad %s', "--since=%s" % since]

    mails_to_show = []
    duplicate_re_map = {}
    for line in subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode(
            'utf-8').strip().split('\n'):
        fields = line.split()
        if len(fields) < 3:
            continue
        mail = Mail(fields[0], fields[1], fields[2:])

        if not valid_to_show(mail):
            continue

        # Shows only latest reply for given mail
        if mail.tags and 'reply' in mail.tags:
            if mail.orig_subject in duplicate_re_map:
                duplicate_re_map[mail.orig_subject] += 1
                continue
            duplicate_re_map[mail.orig_subject] = 1

        mails_to_show.append(mail)

    mails_to_show.reverse()
    if idx_of_mail != None:
        show_mail(mails_to_show[idx_of_mail])
    else:
        show_mails(mails_to_show)
