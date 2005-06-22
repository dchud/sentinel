#!/usr/bin/env python

#from PyLucene import QueryParser, IndexSearcher, StandardAnalyzer, FSDirectory

import canary.context
from canary.search import SearchIndex


#def run (searcher, analyzer):
def run (search_index):
    while True:
        print
        print "Hit enter with no input to quit."
        command = raw_input("Query: ")
        if command == '':
            return

        #query_parser = QueryParser('all', analyzer)
        #query_parser.setOperator(query_parser.DEFAULT_OPERATOR_AND)
        #query = QueryParser.parse(unicode(command), 'all', analyzer)
        #query = query_parser.parseQuery(unicode(command))

        #print "[Parsed Query: %s]" % query
        #hits = searcher.search(query)
        #print "%s total matching documents." % hits.length()
        hits, searcher = search_index.search(command)
        for i, doc in hits:
            print doc.get('uid'), hits.score(i)
        searcher.close()

if __name__ == '__main__':
    context = canary.context.Context()
    #directory = FSDirectory.getDirectory(context.config.search_index_dir, False)
    #searcher = IndexSearcher(directory)
    #analyzer = StandardAnalyzer()
    #run(searcher, analyzer)
    search_index = SearchIndex(context)
    run(search_index)
