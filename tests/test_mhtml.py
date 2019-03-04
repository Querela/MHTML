# pylint: disable=missing-docstring,invalid-name

import pytest

import mhtml


def test_get_content_type():
    # more verbose construction
    mock_headers = mhtml.ResourceHeader()
    mock_headers['Content-Type'] = 'text/html'
    assert mhtml.get_content_type(mock_headers) == 'text/html'

    # case insensitive
    assert mhtml.get_content_type(
        mhtml.ResourceHeader([('conTent-TyPe', 'text/html')])
        ) == 'text/html'

    # multipart/related
    assert mhtml.get_content_type(
        mhtml.ResourceHeader([('conTent-TyPe',
                               'multipart/related;\r\n\t...')])
        ) == 'multipart/related'

    # empty headers -> None
    assert mhtml.get_content_type(mhtml.ResourceHeader()) is None

    # no headers
    with pytest.raises(AttributeError):
        mhtml.get_content_type(None)

    # even standard dicts, but case sensitive
    assert mhtml.get_content_type({'Content-Type': 'text/abc'}) == 'text/abc'
    assert mhtml.get_content_type({'conTent-TyPe': 'text/abc'}) is None


def test_get_boundary():
    # no headers
    with pytest.raises(AttributeError):
        mhtml.get_boundary(None)

    # no content-type
    assert mhtml.get_boundary(mhtml.ResourceHeader()) is None
    # missing boundary declaration
    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('conTent-TyPe', 'text/html')])
        ) is None

    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('conTent-TyPe',
                               'text/html;\r\n\tabc\r\n\tboundary="'
                               '---test-boundary---'
                               '"')])
        ) is None

    # has to be multipart
    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('Content-Type',
                               'multipart/related;\r\n\tabc\r\n'
                               '\tnothing-here')])
        ) is None
    # has to be multipart and contain a boundary declaration
    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('Content-Type',
                               'multipart/related;\r\n\tabc\r\n\tboundary="'
                               '---test-boundary---'
                               '"')])
        ) == '---test-boundary---'


def test_make_filename():
    # no headers given
    assert mhtml.make_filename(None, default='abc') == 'abc'
    # empty header
    assert mhtml.make_filename(mhtml.ResourceHeader(), default='abd') == 'abd'
    assert mhtml.make_filename(mhtml.ResourceHeader([('CH', 'CV')]),
                               default='abd') == 'abd'

    # assume we have extensions
    mock_headers = mhtml.ResourceHeader()
    mock_headers['Content-Location'] = 'proto://path/to/file.ext'
    assert mhtml.make_filename(mock_headers,
                               guess_extension=False) == 'file.ext'
    assert mhtml.make_filename(mock_headers, folder='abc',
                               guess_extension=False) == 'abc/file.ext'
    assert mhtml.make_filename(mock_headers,
                               guess_extension=True) == 'file.ext'
    assert mhtml.make_filename(mock_headers) == 'file.ext'

    # test guessing extensions
    del mock_headers['Content-Location']
    mock_headers['Content-Location'] = 'proto://path/to/file'

    assert mhtml.make_filename(mock_headers, default='abc.hhh') == 'file.hhh'
    # if not extension, then .bin ?
    assert mhtml.make_filename(mock_headers, default=None) == 'file.bin'
    assert mhtml.make_filename(mock_headers, default='ooo') == 'file.bin'

    # add content-type
    mock_headers['Content-Type'] = 'myster/lexi'
    assert mhtml.make_filename(mock_headers, default='ooo.hhh') == 'file.lexi'
    assert mhtml.make_filename(mock_headers, folder='ddd/bbb/',
                               default='ooo.hhh') == 'ddd/bbb/file.lexi'
    del mock_headers['Content-Type']
    mock_headers['Content-Type'] = 'mystery'
    assert mhtml.make_filename(mock_headers) == 'file.mystery'


def test_make_uniq_filename():
    import os
    import shutil
    import tempfile

    with tempfile.NamedTemporaryFile() as fp:
        assert mhtml.make_uniq_filename(fp.name, pre_dup_str='dpp_') == \
            fp.name + '.dpp_1'

    assert mhtml.make_uniq_filename(__file__, pre_dup_str=None) == \
        __file__.rsplit('.', 1)[0] + '.1.' + __file__.rsplit('.', 1)[1]

    tempdir = tempfile.mkdtemp()
    try:
        fname = os.path.join(tempdir, 'abc')
        assert mhtml.make_uniq_filename(fname) == fname
        with open(fname, 'w'):
            pass
        fname1 = fname + '.dupi1'
        assert mhtml.make_uniq_filename(fname, pre_dup_str='dupi') == fname1
        with open(fname1, 'w'):
            pass
        fname2 = fname + '.dupi2'
        with open(fname2, 'w'):
            pass
        fname3 = fname + '.dupi3'
        assert mhtml.make_uniq_filename(fname, pre_dup_str='dupi') == fname3
        assert set(os.listdir(tempdir)) == {os.path.basename(fname),
                                            os.path.basename(fname1),
                                            os.path.basename(fname2)}
    finally:
        shutil.rmtree(tempdir)


# ---------------------------------------------------------------------------


def test_find_next_linebreak():
    assert mhtml.find_next_linebreak(b'', 0) == -1
    # index after linebreak, start of new content
    assert mhtml.find_next_linebreak(b'abc\r\ndef', 0) == 5
    assert mhtml.find_next_linebreak(b'abc\r\ndef', 6) == -1

    # currently wants '\r\n' as separator
    assert mhtml.find_next_linebreak(b'abc\rdef', 0) == -1
    assert mhtml.find_next_linebreak(b'abc\ndef', 0) == -1

    assert mhtml.find_next_linebreak(b'abc\r\ndef', -1) == -1

    # works on bytes
    with pytest.raises(TypeError):
        mhtml.find_next_linebreak('abc\r\ndef', 0)


def test_next_line():
    assert mhtml.next_line(b'', 0) == (b'', -1)
    assert mhtml.next_line(b'abc\r\ndef', 0) == (b'abc\r\n', 5)
    assert mhtml.next_line(b'abc\r\ndef', 1) == (b'bc\r\n', 5)

    # with linebreak continuation
    assert mhtml.next_line(b'abc;\r\n\tcba\r\ndef', 1) == \
        (b'bc;\r\n\tcba\r\n', 12)

    # unspecified, tries to get content from -1 to end
    # really should not happen -> so ignore it
    assert mhtml.next_line(b'abc\r\ndef', -1) == (b'f', -1)

    with pytest.raises(AttributeError):
        mhtml.next_line(None, -1)


def test_parse_header():
    assert mhtml.parse_header(b'', 0) == (mhtml.ResourceHeader(), -1)

    # needs two linebreaks (a single empty line) after the header fields
    with pytest.raises(AssertionError):
        assert mhtml.parse_header(b'CH: CV\r\n', 0) == \
            (mhtml.ResourceHeader([('CH', 'CV')]), -1)

    # really short header
    assert mhtml.parse_header(b'CH: CV\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV')]), -1)
    assert mhtml.parse_header(b'CH: CV\r\nCH2: CV2\r\nCH3: CV3\r\n\r\n', 0) \
        == (mhtml.ResourceHeader([('CH', 'CV'), ('CH2', 'CV2'),
                                  ('CH3', 'CV3')]), -1)

    # TODO: how to handle multiple spaces -> trim()?
    assert mhtml.parse_header(b'CH:     CV\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', '    CV')]), -1)
    # needs at least a single space
    assert mhtml.parse_header(b'CH:CV\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([]), -1)

    assert mhtml.parse_header(b'CH: CV\r\n\r\n\r\n-----boundary---', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV')]), 10)

    # value with linebreaks
    assert mhtml.parse_header(b'CH: CV;\r\n\tCV2\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV;\r\n\tCV2')]), -1)

    assert mhtml.parse_header(b'CH: CV;\r\n\tCV2\r\nCH2: CV3\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV;\r\n\tCV2'), ('CH2', 'CV3')]), -1)


def test_find_next_boundary():
    # no boundary found
    assert mhtml.find_next_boundary(b'', '---boundary---', 0) == (-1, -1)

    # missing linebreak beforehand
    assert mhtml.find_next_boundary(b'--'
                                    b'---boundary---'
                                    b'\r\n', '---boundary---', 0) == (-1, -1)

    # needs a linebreak before
    assert mhtml.find_next_boundary(b'\r\n'
                                    b'--'
                                    b'---boundary---'
                                    b'\r\n', '---boundary---', 0) == (2, 20)

    # end-of-parts (of file?) boundary
    assert mhtml.find_next_boundary(b'\r\n'
                                    b'--'
                                    b'---boundary---'
                                    b'--\r\n', '---boundary---', 0) == (2, -1)


def test_parse_part():
    # boundary is string (because from header)
    with pytest.raises(TypeError):
        mhtml.parse_part(b'', b'', 0)

    # this case should not happen, because there will always be a part when
    # the function is called?
    assert mhtml.parse_part(b'', '---boundary---', 0) == \
        ((mhtml.ResourceHeader(), 0, -1, 0), -1)
    # simulate last part (end-of-parts boundary) (see the extra dashes)
    assert mhtml.parse_part(b'CH: CV\r\n\r\ncontent\r\n'
                            b'-----boundary-----\r\n',
                            '---boundary---', 0) == \
        ((mhtml.ResourceHeader([('CH', 'CV')]), 0, 10, 19), -1)
    # simulate more parts (end-of-part boundary)
    assert mhtml.parse_part(b'CH: CV\r\n\r\ncontent\r\n'
                            b'-----boundary---\r\n',
                            '---boundary---', 0) == \
        ((mhtml.ResourceHeader([('CH', 'CV')]), 0, 10, 19), 37)


def test_parse_parts():
    assert mhtml.parse_parts(b'', '---boundary---', 0) == ([], -1)


# ---------------------------------------------------------------------------


def test_MHTMLArchive():  # noqa: N802
    pass


def test_ResourceHeader():  # noqa: N802
    pass


def test_Resource():  # noqa: N802
    pass
