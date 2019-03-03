# pylint: disable=redefined-builtin,invalid-name
# pylint: disable=missing-docstring

import email
import logging
import os


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def make_filename(part, dir=None, auto_rename=True):
    fn = part.get('Content-Location', 'index.html')
    fn = fn.split('?', 1)[0]
    fn = fn.split('#', 1)[0]
    fn = fn.rsplit('/', 1)[-1]
    fn = fn.split('=', 1)[0]

    if '.' not in fn:
        ext = part.get('Content-Type', 'bin').split('/')[-1]
        fn = '{}.{}'.format(fn, ext)

    if dir:
        fn = '{}/{}'.format(dir.rstrip('/'), fn)

    if auto_rename:
        if os.path.exists(fn):
            base, ext = fn.rsplit('.', 1)
            dup_cnt = 1
            fn = '{}.dup_{}.{}'.format(base, dup_cnt, ext)
            while os.path.exists(fn):
                dup_cnt += 1
                fn = '{}.dup_{}.{}'.format(base, dup_cnt, ext)
            logger.debug('Found duplicate output name, auto rename to: "%s"',
                         fn)

    return fn


def load_message(file):
    # with open(file, 'rb') as f:
    #     content = f.read()
    # return email.message_from_bytes(content)
    with open(file, 'rb') as f:
        return email.message_from_binary_file(f)


def write_part(part, dir):
    fn = make_filename(part, dir)
    content = part.get_payload(decode=True)
    logger.debug('Write %d bytes to "%s" ...', len(content), fn)
    with open(fn, 'wb') as f:
        f.write(content)


def store_parts(msg, dir):
    for part in msg.get_payload():
        write_part(part, dir)


def main(file, dir):
    logger.info('Extracting "%s" into "%s" ...', file, dir)

    if not os.path.exists(dir):
        logger.debug('Make output folder: "%s"', dir)
        os.mkdir(dir)

    msg = load_message(file)
    if msg.get_content_type() == 'multipart/related':
        store_parts(msg, dir)
    else:
        logger.warning('Main message not multipart? "%s"',
                       msg.get_content_type())
        write_part(msg, dir)


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)-8s: %(message)s',
                        level=logging.DEBUG)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='MHT/MHTM/MHTML file')
    parser.add_argument('dir', help='output dir for extracted content')
    args = parser.parse_args()

    main(args.file, args.dir)
