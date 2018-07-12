import imaplib, email, sys, argparse

""" Tests for proxy.py combined with the PyCIRCLeanMail module """

def run_tests(conn_proxy, username, password):
    test_mesg = ('From: IMAP proxy\nSubject: IMAP4 test\n\nEmail generated by ' \
                + 'IMAProxy + PyCIRCLeanMail tests\n').encode()
    test_seq1 = (
        ('login', (username, password)),
        ('create', ('tmp/xxx',)),
        ('append', ('tmp/xxx', None, None, test_mesg)),
        ('select', ('tmp/xxx',)),
        ('search', (None, 'SUBJECT', 'test')),
        ('fetch', ('1', '(FLAGS INTERNALDATE RFC822)')),
        ('uid', ('SEARCH', 'ALL')),
        ('response', ('EXISTS',)),
        ('create', ('Quarantine',)), # Should be comment if QUarantine already exists
        ('select', ('Quarantine',)),
        ('uid', ('SEARCH', 'ALL')),
        ('response', ('EXISTS',)),
        ('expunge', ()),
        ('delete', ('tmp/xxx',)),
        ('logout', ()))

    failed_tests = []

    def run(cmd, args):
        print("["+cmd+"]", end=" ")
        typ, dat = getattr(conn_proxy, cmd)(*args)
        print(typ)
        
        if typ == 'NO': 
            failed_tests.append('%s => %s %s' % (cmd, typ, dat))

        return dat

    for cmd,args in test_seq1:
        dat = run(cmd, args)

        if (cmd,args) != ('uid', ('SEARCH', 'ALL')):
            continue

        uid = dat[-1].split()
        if not uid: 
            continue

        print("Is the last email sanitized ?")
        # uid[-1] is the last email received
        result = run('uid', ('FETCH', '%s' % uid[-1].decode(),
                '(FLAGS INTERNALDATE RFC822.SIZE RFC822.HEADER RFC822.TEXT)'))
        mail = result[0][1]
        if 'CIRCL-Sanitizer' not in mail.decode():
            failed_tests.append('Email not sanitized')

    # Display results
    if not failed_tests:
        print('TESTS SUCCEEDED')
    else:
        print('SOME TESTS FAILED:')
        for test in failed_tests:
            print(test)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Email address of the user')
    parser.add_argument('password', help='Password of the user')
    parser.add_argument('ip_proxy', help='Ip address of the proxy')
    parser.add_argument('-s', '--ssl', help='Enable SSL/TLS connection')
    parser.add_argument('-p', '--port', type=int, help='Talk on the given port (Default: 143 or 993 with SSL/TLS enabled)')
    args = parser.parse_args()

    try:
        if args.ssl:
            if args.port:
                run_tests(imaplib.IMAP4_SSL(args.ip_proxy, args.port), args.username, args.password)
            else:
                run_tests(imaplib.IMAP4_SSL(args.ip_proxy), args.username, args.password)

        else:
            if args.port:
                run_tests(imaplib.IMAP4(args.ip_proxy, args.port), args.username, args.password)
            else:
                run_tests(imaplib.IMAP4(args.ip_proxy), args.username, args.password)
    except ConnectionRefusedError:
        print('Port blocked')
    