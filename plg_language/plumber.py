#
# Copyright 2009 Eigenlabs Ltd.  http://www.eigenlabs.com
#
# This file is part of EigenD.
#
# EigenD is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EigenD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EigenD.  If not, see <http://www.gnu.org/licenses/>.
#

from pi.logic.shortcuts import *
from pi import action,logic,async,domain,utils,resource,rpc,timeout,plumber
from . import interpreter,noun,imperative,referent
import re

def find_conn(aproxy,id):
    r = []
    for cnx in cnxs:
        if logic.is_pred_arity(cnx,'conn',5) and cnx.args[2]==id:
            r.append(logic.render_term(cnx))

    return r

class Plumber:
    def __init__(self,agent,database):
        self.database = database
        self.agent = agent

    @async.coroutine('internal error')
    def verb2_18_unconnect(self,subject,t):
        """
        connect([un],global_unconnect,role(None,[concrete]))
        """
        print 'un connect',t
        for o in action.concrete_objects(t):
            t2 = self.database.to_database_id(o)
            tproxy = self.database.find_item(t2)
            print '__unconnect',t2
            objs = self.database.search_any_key('W',T('input_list',t2,V('W')))
            print '__unconnect',t2,objs

            for (s,m) in objs:
                sproxy = self.database.find_item(s)
                yield interpreter.RpcAdapter(sproxy.invoke_rpc('clrconnect',''))

        yield async.Coroutine.success()

    @async.coroutine('internal error')
    def verb2_19_unconnect_from(self,subject,t,f):
        """
        connect([un],global_unconnect_from,role(None,[concrete]),role(from,[concrete,singular]))
        """
        f = self.database.to_database_id(action.concrete_object(f))
        for o in action.concrete_objects(t):
            t2 = self.database.to_database_id(o)
            print 'un connect',t2,'from',f
            tproxy = self.database.find_item(t2)
            objs = self.database.search_any_key('W',T('unconnect_from_list',t2,f,V('W')))

            for (s,m) in objs:
                sproxy = self.database.find_item(s)
                cnxs = logic.parse_clauselist(sproxy.get_master())
                for cnx in cnxs:
                    if logic.is_pred_arity(cnx,'conn',5) and self.database.to_database_id(cnx.args[2])==m:
                        print 'disconnect',cnx,'from',s
                        yield interpreter.RpcAdapter(sproxy.invoke_rpc('disconnect',logic.render_term(cnx)))

        yield async.Coroutine.success()


    @async.coroutine('internal error')
    def verb2_20_connect(self,subject,src,dst,dst_chan,src_chan):
        """
        connect([],global_connect,role(None,[or([concrete],[composite([descriptor])])]),role(to,[concrete,singular]),option(into,[mass([channel])]),option(from,[abstract]))
        """

        if dst_chan is not None:
            dst_chan=int(action.mass_quantity(dst_chan))

        if src_chan is not None:
            src_chan = action.abstract_string(src_chan)
            src_match = re.match('^channel\s+([\d\.]+)$',src_chan,re.IGNORECASE)
            if src_match:
                src_chan = src_match.group(1)
            else:
                yield async.Coroutine.failure("%s is not valid" % src_chan)

        to_descriptor = (action.concrete_object(dst),None)
        to_descriptor = self.database.to_database_term(to_descriptor)

        for ff in action.arg_objects(src):
            if action.is_concrete(ff):
                from_descriptors = [(action.crack_concrete(ff),None)]
            else:
                from_descriptors = action.crack_composite(ff,action.crack_descriptor)

            from_descriptors = self.database.to_database_term(from_descriptors)

            r = plumber.plumber(self.database,to_descriptor,from_descriptors,dst_chan=dst_chan,src_chan=src_chan)
            yield r
            if not r.status():
                yield async.Coroutine.failure(*r.args(),**r.kwds())

        yield async.Coroutine.success()
