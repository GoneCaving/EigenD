
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

from pi import agent,atom,action,domain,bundles,utils,logic,node,async,schedproxy,const,upgrade,policy,paths,talker,collection
from . import talker_version as version
import piw
import operator

class PhraseBrowser(atom.Atom):
    def __init__(self,eventlist,keylist):
        atom.Atom.__init__(self,names='phrase',protocols='virtual browse')

        self.__eventlist = eventlist
        self.__keylist = keylist
        self.__timestamp = piw.tsd_time()
        self.update()

    def rpc_displayname(self,arg):
        return 'phrases'
   
    def rpc_setselected(self,arg):
        pass
    
    def rpc_activated(self,arg):
        return logic.render_term(('',''))

    def update(self):
        self.__timestamp = self.__timestamp+1
        self.set_property_string('timestamp',str(self.__timestamp))

    def __ideal(self,e):
        return 'ideal([~server,event],[~server,%s])' % logic.render_term(e.id())

    def rpc_fideal(self,arg):
        (path,uid) = logic.parse_clause(arg)
        all = [e for k in self.__keylist() for e in self.__eventlist(k)]
        e = all[uid]
        return self.__ideal(e)

    def rpc_current(self,arg):
        return '[]'

    def resolve_name(self,name):
        try:
            o=int(name)
        except:
            return '[]'

        events=[ self.__ideal(e) for e in self.__eventlist(o)]
        return '[%s]' % ','.join(events)

    def rpc_resolve(self,arg):
        (a,o) = logic.parse_clause(arg)

        if a:
            return '[]'

        events=[ self.__ideal(e) for k in self.__keylist() for e in self.__eventlist(k)]

        if o:
            o=int(o)
            if o>0 and o<=len(events):
                return '[%s]' % events[o-1]
            return '[]'

        return '[%s]' % ','.join(events)

    def rpc_enumerate(self,a):
        path=logic.parse_clause(a)
        if len(path)==0:
            k=reduce(operator.add,[len(self.__eventlist(k)) for k in self.__keylist()],0)
            c=0
        else:
            k=0
            c=0
        return logic.render_term((k,c))

    def rpc_cinfo(self,a):
        return '[]'

    def rpc_finfo(self,a):
        (dlist,cnum) = logic.parse_clause(a)
        all = list(enumerate([e for k in self.__keylist() for e in self.__eventlist(k)]))
        map = tuple([(i,e.describe(),None) for (i,e) in all[cnum:] ])
        return logic.render_term(map)

class Event(talker.Talker):
    def __init__(self,key,fast,index):
        self.__key = key
        self.__index = index
        cookie = self.__key.key_aggregator.get_output(self.__index)

        talker.Talker.__init__(self,self.__key.agent.finder,fast,cookie,names='event',ordinal=index,protocols='remove')

    def detach_event(self):
        self.__key.key_aggregator.clear_output(self.__index)

    def property_change(self,key,value,delegate):
        if key=='help' and value and value.is_string():
            self.__key.agent.update()

    def describe(self):
        return self.get_property_string('help')

class Key(collection.Collection):
    def __init__(self,agent,controller,index):
        collection.Collection.__init__(self,creator=self.__create,wrecker=self.__wreck,ordinal=index,names='key',protocols='hidden-connection remove explicit')
        self.__event = piw.fasttrigger(const.light_unknown)
        self.__event.attach_to(controller,index)
        self.__handler = piw.change2_nb(self.__event.trigger(),utils.changify(self.event_triggered))

        self.key_mapper = piw.function1(True,2,2,piw.data(),agent.light_aggregator.get_output(index+1))
        self.key_mapper.set_functor(piw.d2d_const(utils.maketuple_longs((0,0),0)))
        self.key_aggregator = piw.aggregator(self.key_mapper.cookie(),agent.domain)

        self.agent = agent
        self.index = index

        self.set_private(node.Server(rtransient=True)) # kept in there for backwards compatibility
        self.set_internal(250,atom.Atom(domain=domain.Trigger(),init=False,names='activate',policy=policy.TriggerPolicy(self.__handler),transient=True))

        self.set_internal(247, atom.Atom(domain=domain.BoundedInt(0,3),names='default colour',init=3,policy=atom.default_policy(self.set_color)))
        self.set_internal(248, atom.Atom(domain=domain.BoundedInt(-32767,32767),names='key column',init=0,policy=atom.default_policy(self.__change_key_column)))
        self.set_internal(249, atom.Atom(domain=domain.BoundedInt(-32767,32767),names='key row',init=0,policy=atom.default_policy(self.__change_key_row)))
        self.set_internal(245, atom.Atom(domain=domain.Bool(),names='key column end relative',init=False,policy=atom.default_policy(self.__change_key_column_endrel)))
        self.set_internal(246, atom.Atom(domain=domain.Bool(),names='key row end relative',init=False,policy=atom.default_policy(self.__change_key_row_endrel)))

        self.agent.light_convertor.set_status_handler(self.index,self.__make_key_coordinate(),piw.slowchange(utils.changify(self.set_status)))

    def __change_key_column(self,val):
        self.get_internal(248).set_value(val)
        self.__key_changed()
        return False

    def __change_key_row(self,val):
        self.get_internal(249).set_value(val)
        self.__key_changed()
        return False

    def __change_key_column_endrel(self,val):
        self.get_internal(245).set_value(val)
        self.__key_changed()
        return False

    def __change_key_row_endrel(self,val):
        self.get_internal(246).set_value(val)
        self.__key_changed()
        return False

    def __make_key_coordinate(self):
        return piw.coordinate(self.get_internal(248).get_value(),self.get_internal(249).get_value(),self.get_internal(245).get_value(),self.get_internal(246).get_value())

    def __key_changed(self):
        self.agent.light_convertor.remove_status_handler(self.index)
        t = self.__make_key_coordinate()
        self.__event.set_key(t) 
        self.key_mapper.set_functor(piw.d2d_const(t.make_data(0)))
        self.agent.light_convertor.set_status_handler(self.index,t,piw.slowchange(utils.changify(self.set_status)))
        self.agent.light_convertor.set_default_color(self.index,self.get_internal(247).get_value())

    def rpc_instancename(self,a):
        return 'action'

    @async.coroutine('internal error')
    def instance_create(self,name):
        e = Event(self,self.__event.fastdata(),name)
        self[name] = e
        e.attached()
        yield async.Coroutine.success(e)

    @async.coroutine('internal error')
    def instance_wreck(self,k,e,name):
        print 'killing event',k
        del self[k]
        e.detach_event()
        r = e.clear_phrase()
        yield r
        print 'killed event',k
        yield async.Coroutine.success()

    def event_triggered(self,v):
        self.get_internal(250).get_policy().set_status(piw.makelong(0,0))
        self.set_status(piw.makelong(self.agent.light_convertor.get_status(self.__make_key_coordinate()),piw.tsd_time()))

    def set_status(self,v):
        self.get_internal(250).get_policy().set_status(v)

    def isinternal(self,k):
        if k == 245 or k == 246 or k == 247 or k == 248 or k == 249 or k == 250: return True
        return atom.Atom.isinternal(self,k)

    def set_color(self,c):
        self.agent.light_convertor.set_default_color(self.index,c)
        self.get_internal(247).set_value(c)

    def __create(self,i):
        self.agent.update()
        return Event(self,self.__event.fastdata(),i)

    def __wreck(self,k,v):
        v.detach_event()
        self.agent.update()

    def detach_key(self):
        self.agent.light_convertor.remove_status_handler(self.index)
        self.agent.light_aggregator.clear_output(self.index+1)
        self.__event.detach()

    @async.coroutine('internal error')
    def create_event(self,text,called=None):
        if called:
            if called in self:
                yield async.Coroutine.failure('phrase exists')
            index = called
        else:
            index = self.find_hole()

        print 'create event on key',self.id()

        e = Event(self,self.__event.fastdata(),index)
        self[index] = e
        e.attached()
        r = e.set_phrase(text)
        yield r

    @async.coroutine('internal error')
    def redo(self):
        for c,e in self.items():
            yield e.redo()

    @async.coroutine('internal error')
    def cancel_event(self,called=None):
        for c,e in self.items():
            if not called or called==c:
                del self[c]
                e.detach_event()
                r = e.clear_phrase()
                yield r

class Agent(agent.Agent):
    def __init__(self, address, ordinal):
        agent.Agent.__init__(self,signature=version,names='talker',ordinal=ordinal,protocols='talker')

        self.add_verb2(2,'do([],None,role(None,[abstract]),role(when,[numeric]),option(called,[numeric]))', self.__do_verb)
        self.add_verb2(8,'cancel([],None,role(None,[numeric]),option(called,[numeric]))', self.__cancel_verb)
        self.add_verb2(5,'colour([],None,role(None,[numeric]),role(to,[numeric]))', self.__color_verb)
        self.add_verb2(6,'colour([],None,role(None,[numeric]),role(to,[numeric]),role(from,[numeric]))', self.__all_color_verb)
        self.add_verb2(9,'do([re],None,role(None,[numeric]))', self.__redo_k_verb)
        self.add_verb2(10,'do([re],None)', self.__redo_all_verb)

        self.domain = piw.clockdomain_ctl()
        self.domain.set_source(piw.makestring('*',0))
        self.__size = 0
        self.finder = talker.TalkerFinder()

        self[1] = bundles.Output(1,False, names='light output',protocols='revconnect')

        self.light_output = bundles.Splitter(self.domain,self[1])
        self.light_convertor = piw.lightconvertor(False,self.light_output.cookie())
        self.light_aggregator = piw.aggregator(self.light_convertor.cookie(),self.domain)
        self.controller = piw.controller(self.light_aggregator.get_output(1),utils.pack_str(1,2))

        self.activation_input = bundles.VectorInput(self.controller.event_cookie(), self.domain,signals=(1,2))

        self[3] = collection.Collection(creator=self.__create,wrecker=self.__wreck,names='key',inst_creator=self.__create_inst,inst_wrecker=self.__wreck_inst,protocols='hidden-connection explicit')
        self[4] = PhraseBrowser(self.__eventlist,self.__keylist)

        self[5] = atom.Atom(domain=domain.Aniso(),policy=self.activation_input.merge_nodefault_policy(2,False),names='controller input')
        self[6] = atom.Atom(domain=domain.Aniso(),policy=self.activation_input.vector_policy(1,False), names='key input')

    def __eventlist(self,k):
        el=[]
        if k in self[3]:
            for e in self[3][k].itervalues():
                el.append(e)
        return el

    def __keylist(self):
        kl=[]
        for k in self[3].iterkeys():
            kl.append(k)
        return kl

    def __update_lights(self,k):
        if k > self.__size:
            self.__size = k

    def update(self):
        self[4].update()
            
    def __create(self,k):
        self.__update_lights(k)
        return Key(self,self.controller,k)

    def __wreck(self,k,v):
        v.detach_key()

    @async.coroutine('internal error')
    def __create_inst(self,k):
        self.__update_lights(k)
        e = Key(self,self.controller,k)
        self[3][k] = e
        yield async.Coroutine.success(e)

    @async.coroutine('internal error')
    def __wreck_inst(self,k,e,name):
        e.detach_key()
        r = e.cancel_event()
        yield r
        yield async.Coroutine.success()

    def __all_color_verb(self,subject,k,c,f):
        k = int(action.abstract_string(k))
        c = int(action.abstract_string(c))
        f = int(action.abstract_string(f))

        for (i,t) in self[3].items():
            t.set_color(c if (k==i) else f)

    def __color_verb(self,subject,k,c):
        k = int(action.abstract_string(k))
        c = int(action.abstract_string(c))
        if k in self[3]:
            self[3][k].set_color(c)

    @async.coroutine('internal error')
    def __redo_all_verb(self,subject):
        for k,e in self[3].items():
            yield e.redo()

        yield async.Coroutine.success()

    @async.coroutine('internal error')
    def __redo_k_verb(self,subject,k):
        k = int(action.abstract_string(k))
        
        if k in self[3]:
            yield self[3][k].redo()

        yield async.Coroutine.success()

    @async.coroutine('internal error')
    def __do_verb(self,subject,t,k,c):
        t = action.abstract_string(t)
        k = int(action.abstract_string(k))
        c = int(action.abstract_string(c)) if c else None
        
        if k not in self[3]:
            self.__update_lights(k)
            self[3][k] = Key(self,self.controller,k)

        if c and c in self[3][k]:
                yield async.Coroutine.success(action.error_return('name in use','','do'))

        r = self[3][k].create_event(t,c)
        yield r
        yield async.Coroutine.success()

    @async.coroutine('internal error')
    def __cancel_verb(self,subject,k,c):
        k = int(action.abstract_string(k))
        c = int(action.abstract_string(c)) if c else None

        if k not in self[3]:
            yield async.Coroutine.success()

        if c and c not in self[3][k]:
            yield async.Coroutine.success()

        r = self[3][k].cancel_event(c)

        if c is None:
            self[3][k].detach_key()
            del self[3][k]

        yield r
        yield async.Coroutine.success()


agent.main(Agent)
