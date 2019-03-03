# pylint: disable=redefined-builtin,invalid-name
# pylint: disable=missing-docstring

import logging
import os

import mhtml


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def make_filename(headers, dir=None, auto_rename=True,
                  default_filename='index.html'):
    fn = headers.get('Content-Location', default_filename)
    fn = fn.split('?', 1)[0]
    fn = fn.split('#', 1)[0]
    fn = fn.rsplit('/', 1)[-1]
    fn = fn.split('=', 1)[0]

    if '.' not in fn:
        ext = headers.get('Content-Type', 'bin').split('/')[-1]
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


def main(filename, folder):
    logger.info('Extracting "%s" into "%s" ...', filename, folder)

    if not os.path.exists(folder):
        logger.debug('Make output folder: "%s"', folder)
        os.mkdir(folder)

    # rewrite, own tools
    with open(filename, 'rb') as fin:
        content = fin.read()

    _, parts = mhtml.parse_mhtml(content)

    for part in parts:
        headers, _, start, end = part
        pcontent = content[start:end]
        # TODO: defailt name with part number
        pfn = make_filename(headers, folder)

        logger.debug('Write %d bytes to "%s" ...', len(pcontent), pfn)
        with open(pfn, 'wb') as fout:
            fout.write(pcontent)


def cli_main():
    logging.basicConfig(format='%(levelname)-8s: %(message)s',
                        level=logging.DEBUG)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='MHT/MHTM/MHTML file')
    parser.add_argument('dir', help='output dir for extracted content')
    args = parser.parse_args()

    main(args.file, args.dir)


if __name__ == '__main__':
    cli_main()
