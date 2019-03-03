# pylint: disable=redefined-builtin,invalid-name
# pylint: disable=missing-docstring

import logging

import mhtml


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def main(filename, output_filename=None):
    if not output_filename:
        output_filename = filename.rsplit('.', 1)[0] + '.html'
    logger.info('Extracting main page from "%s" to "%s" ...',
                filename, output_filename)

    # rewrite, own tools
    with open(filename, 'rb') as fin:
        content = fin.read()

    headers, parts = mhtml.parse_mhtml(content)
    main_url = headers['Snapshot-Content-Location']

    for i, part in enumerate(parts):
        headers, _, start, end = part
        purl = headers['Content-Location']
        if purl != main_url:
            continue
        if i > 0:
            break

        pcontent = content[start:end]
        logger.debug('Write %d bytes to "%s" ...',
                     len(pcontent), output_filename)
        with open(output_filename, 'wb') as fout:
            fout.write(pcontent)


def cli_main():
    logging.basicConfig(format='%(levelname)-8s: %(message)s',
                        level=logging.DEBUG)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='MHT/MHTM/MHTML file')
    parser.add_argument('output', nargs='?', default=None,
                        help='output dir for extracted content')
    args = parser.parse_args()

    main(args.file, args.output)


if __name__ == '__main__':
    cli_main()
