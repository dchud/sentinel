#!/usr/bin/env python

from PyLucene import QueryParser, IndexSearcher, StandardAnalyzer, FSDirectory

import canary.context


def run (searcher, analyzer):
    while True:
        print
        print "Hit enter with no input to quit."
        command = raw_input("Query: ")
        if command == '':
            return

        print
        query = QueryParser.parse(unicode(command), 'all', analyzer)
        print " [Query: %s]" % query
        hits = searcher.search(query)
        print "%s total matching documents." % hits.length()
        for i, doc in hits:
            print doc.get('uid'), hits.score(i)

if __name__ == '__main__':
    context = canary.context.Context()
    directory = FSDirectory.getDirectory(context.config.search_index_dir, False)
    searcher = IndexSearcher(directory)
    analyzer = StandardAnalyzer()
    run(searcher, analyzer)
    searcher.close()
