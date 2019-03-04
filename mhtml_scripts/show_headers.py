# pylint: disable=invalid-name
# pylint: disable=missing-docstring

import glob
import logging

import mhtml


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def get_filename(url):
    # Currently not used, may be removed later
    fn = url  # pylint: disable=invalid-name
    fn = fn.split('?', 1)[0]
    fn = fn.split('#', 1)[0]
    fn = fn.rsplit('/', 1)[-1]
    fn = fn.split('=', 1)[0]
    return fn


def print_separator(length=40, char='-'):
    print(char * length)


def main(input_file, only_main_header=False, print_preview=False,
         filter_resources=None):
    mhtarc = mhtml.MHTMLArchive_from_file(input_file,
                                          only_header=only_main_header)

    max_name_len = max([len(n) for n in mhtarc.headers.as_dict().keys()])
    for name, value in mhtarc.headers.as_list():
        print('{:>{mnl}}:\t{}'.format(name, value, mnl=max_name_len))

    if only_main_header:
        return

    print_separator(char='=')

    for rnr, resource in enumerate(mhtarc.resources):
        if filter_resources is not None:
            if not glob.fnmatch.fnmatch(resource.content_type,
                                        filter_resources):
                logger.debug('Skip resource %s because content-type '
                             'mismatch: %s', rnr, resource.content_type)
                continue

        print('Resource {}:  ({} bytes) [Offset: {} -- {}]'
              .format(rnr, len(resource.content),
                      *resource.get_resource_range()))
        if resource.location == mhtarc.location:
            print('--> main content file!')

        max_name_len = max([len(n) for n in resource.headers.as_dict().keys()])
        for name, value in resource.headers.as_list():
            print('{:>{mnl}}:\t{}'.format(name, value, mnl=max_name_len))

        if print_preview:
            print('Payload Preview: {}'.format(resource.content[:100]))

        print_separator()


def cli_main():
    logging.basicConfig(format='%(levelname)-8s: %(message)s',
                        level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='MHT/MHTM/MHTML file')
    parser.add_argument('-m', '--only-main-header', action='store_true',
                        help='Parse only main header.')
    parser.add_argument('-p', '--print-preview', action='store_true',
                        help='Print a preview of the resources (100 bytes)')
    parser.add_argument('-f', '--filter-resources', default='*',
                        help='Filter resources only matching the given '
                             'mime-type pattern. (default: *)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print more logging output.')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    main(args.input, args.only_main_header, args.print_preview,
         args.filter_resources)


if __name__ == '__main__':
    cli_main()
