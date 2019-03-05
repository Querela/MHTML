# pylint: disable=redefined-builtin,invalid-name
# pylint: disable=missing-docstring

import logging

import mhtml


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def main(output_filename, input_filenames):
    logger.info('Extracting "%s" into "%s" ...', output_filename,
                input_filenames)

    if len(input_filenames) < 2:
        logger.warning('Have to be at least two mhtml input files.')
        return False

    mhtarcs = list()
    for input_filename in input_filenames:
        mhtarc = mhtml.MHTMLArchive_from_file(input_filename)
        mhtarcs.append(mhtarc)

    mhtarc_final = mhtarcs[0]
    mhtarcs = mhtarcs[1:]
    # uniq files?

    known_urls = {r.location for r in mhtarc_final.resources}
    logger.info('%d resources, %d bytes', len(known_urls),
                len(mhtarc_final.content))

    new_urls = list()
    for mhtarc in mhtarcs:
        for resource in mhtarc.resources:
            res_url = resource.location
            if res_url in known_urls:
                logger.debug('Known resource location: %s', res_url)
                continue
            known_urls.add(res_url)
            new_urls.append(res_url)

            mhtarc_final.insert_resource(len(mhtarc_final.resources), resource)

    logger.info('%d resources, %d bytes', len(known_urls),
                len(mhtarc_final.content))
    logger.debug('Resources inserted: %s', new_urls)
    mhtml.MHTMLArchive_to_file(mhtarc_final, output_filename)
    return True


def cli_main():
    logging.basicConfig(format='%(levelname)-8s: %(message)s',
                        level=logging.DEBUG)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('output', help='MHT/MHTM/MHTML file')
    parser.add_argument('inputs', nargs='+',
                        help='more than one input file, first is main file')
    args = parser.parse_args()

    main(args.output, args.inputs)


if __name__ == '__main__':
    cli_main()
