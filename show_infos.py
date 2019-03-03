# pylint: disable=invalid-name
# pylint: disable=missing-docstring

import email
import logging

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def load_message(filename):
    with open(filename, 'rb') as fin:
        return email.message_from_binary_file(fin)


def get_filename(url):
    fn = url  # pylint: disable=invalid-name
    fn = fn.split('?', 1)[0]
    fn = fn.split('#', 1)[0]
    fn = fn.rsplit('/', 1)[-1]
    fn = fn.split('=', 1)[0]
    return fn


def print_separator(length=40, char='-'):
    print(char * length)


def main(input_file):
    msg = load_message(input_file)

    main_url = msg.get('Snapshot-Content-Location', None)

    for key, value in msg.items():
        print('{}: {}'.format(key, value))
    print_separator()

    payload = msg.get_payload()
    if not isinstance(payload, list):
        print('Payload length: {}'.format(len(payload)))
        print('Payload Preview: {}'.format(payload[:100]))
        return

    print('Payload of {} files.'.format(len(payload)))
    print_separator()

    for i, part in enumerate(payload):
        ptype = part.get_content_type()
        purl = part.get('Content-Location', None)
        pfn = get_filename(purl) if purl else None
        plen = len(part.get_payload())

        if purl == main_url:
            print_separator(char='~')
        print(f'{i}\t{ptype}\t{pfn}\t{purl}\t{plen}')
        # print(f'{i}\t{ptype}\t{pfn}\t{plen}')
        if purl == main_url:
            print('--> main content file, url: {}'.format(main_url))
            print_separator(char='~')


def cli_main():
    logging.basicConfig(format='%(levelname)-8s: %(message)s',
                        level=logging.DEBUG)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='MHT/MHTM/MHTML file')
    args = parser.parse_args()

    main(args.input)


if __name__ == '__main__':
    cli_main()
