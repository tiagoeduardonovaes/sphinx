# -*- coding: utf-8 -*-
"""
    sphinx.builders.manpage
    ~~~~~~~~~~~~~~~~~~~~~~~

    Manual pages builder.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path

from docutils.frontend import OptionParser
from docutils.io import FileOutput

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.environment import NoUri
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.console import bold, darkgreen  # type: ignore
from sphinx.util.nodes import inline_all_toctrees
from sphinx.util.osutil import make_filename_from_project
from sphinx.writers.manpage import ManualPageWriter, ManualPageTranslator

if False:
    # For type annotation
    from typing import Any, Dict, List, Set, Tuple, Union  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.config import Config  # NOQA
    from sphinx.util.typing import unicode  # NOQA


logger = logging.getLogger(__name__)


class ManualPageBuilder(Builder):
    """
    Builds groff output in manual page format.
    """
    name = 'man'
    format = 'man'
    epilog = __('The manual pages are in %(outdir)s.')

    default_translator_class = ManualPageTranslator
    supported_image_types = []  # type: List[unicode]

    def init(self):
        # type: () -> None
        if not self.config.man_pages:
            logger.warning(__('no "man_pages" config value found; no manual pages '
                              'will be written'))

    def get_outdated_docs(self):
        # type: () -> Union[unicode, List[unicode]]
        return 'all manpages'  # for now

    def get_target_uri(self, docname, typ=None):
        # type: (unicode, unicode) -> unicode
        if typ == 'token':
            return ''
        raise NoUri

    def write(self, *ignored):
        # type: (Any) -> None
        docwriter = ManualPageWriter(self)
        docsettings = OptionParser(
            defaults=self.env.settings,
            components=(docwriter,),
            read_config_files=True).get_default_values()  # type: Any

        logger.info(bold(__('writing... ')), nonl=True)

        for info in self.config.man_pages:
            docname, name, description, authors, section = info
            if docname not in self.env.all_docs:
                logger.warning(__('"man_pages" config value references unknown '
                                  'document %s'), docname)
                continue
            if isinstance(authors, str):
                if authors:
                    authors = [authors]
                else:
                    authors = []

            docsettings.title = name
            docsettings.subtitle = description
            docsettings.authors = authors
            docsettings.section = section

            targetname = '%s.%s' % (name, section)
            logger.info(darkgreen(targetname) + ' { ', nonl=True)
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')

            tree = self.env.get_doctree(docname)
            docnames = set()  # type: Set[unicode]
            largetree = inline_all_toctrees(self, docnames, docname, tree,
                                            darkgreen, [docname])
            largetree.settings = docsettings
            logger.info('} ', nonl=True)
            self.env.resolve_references(largetree, docname, self)
            # remove pending_xref nodes
            for pendingnode in largetree.traverse(addnodes.pending_xref):
                pendingnode.replace_self(pendingnode.children)

            docwriter.write(largetree, destination)
        logger.info('')

    def finish(self):
        # type: () -> None
        pass


def default_man_pages(config):
    # type: (Config) -> List[Tuple[unicode, unicode, unicode, List[unicode], int]]
    """ Better default man_pages settings. """
    filename = make_filename_from_project(config.project)
    return [(config.master_doc, filename, '%s %s' % (config.project, config.release),
             [config.author], 1)]


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_builder(ManualPageBuilder)

    app.add_config_value('man_pages', default_man_pages, None)
    app.add_config_value('man_show_urls', False, None)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
